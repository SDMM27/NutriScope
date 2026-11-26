"""Contrats du point d'entrée TP13 sur un échantillon synthétique."""

import json
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from nutriscope import pipeline


@pytest.fixture
def config(tmp_path):
    source = tmp_path / "source.csv"
    pd.DataFrame(
        {
            "code": [f"{i:04}" for i in range(10)],
            "product_name": ["Produit"] * 10,
            "pnns_groups_1": ["Fruits"] * 10,
            "nutriscore_grade": ["a"] * 5 + ["b"] * 5,
            "energy_100g": [418.4] * 10,
            "energy-kcal_100g": [100] * 10,
            "fat_100g": [4] * 10,
            "saturated-fat_100g": [1] * 10,
            "carbohydrates_100g": [12] * 10,
            "sugars_100g": [6] * 10,
            "proteins_100g": [4] * 10,
            "fiber_100g": [2] * 10,
            "salt_100g": [0.2] * 10,
            "sodium_100g": [0.08] * 10,
        }
    ).to_csv(source, index=False)
    return pipeline.Configuration(source, tmp_path / "sorties", date(2026, 11, 25))


@pytest.fixture
def partitions(config):
    pipeline.charger(config)
    pipeline.nettoyer(config)
    return pipeline.parquet(config)


def test_charger_fige_la_source(config):
    resultat = pipeline.charger(config)
    brut, manifeste = resultat.fichiers
    assert resultat.lignes == 10
    assert brut.read_bytes() == config.source.read_bytes()
    assert json.loads(manifeste.read_text(encoding="utf-8"))["SHA_256"] == pipeline.sha256(brut)


def test_charger_rejoue_sans_changer_la_copie(config):
    copie, manifeste = pipeline.charger(config).fichiers
    avant = [f.read_bytes() for f in (copie, manifeste)]
    assert pipeline.charger(config).fichiers == (copie, manifeste)
    assert [f.read_bytes() for f in (copie, manifeste)] == avant


def test_charger_refuse_un_conflit(config):
    copie, _ = pipeline.charger(config).fichiers
    avant = copie.read_bytes()
    config.source.write_text("code\n9999\n", encoding="utf-8")
    with pytest.raises(FileExistsError):
        pipeline.charger(config)
    assert copie.read_bytes() == avant


@pytest.mark.parametrize(
    ("etape", "dependance"),
    [("nettoyer", "charger"), ("charger_base", "nettoyer"), ("parquet", "nettoyer"), ("exports", "parquet")],
)
def test_etape_sans_entree_indique_sa_dependance(config, etape, dependance):
    with pytest.raises(FileNotFoundError, match=rf"étape {dependance}"):
        pipeline.ETAPES[etape](config)


def test_nettoyer_ecrit_les_trois_sorties(config):
    pipeline.charger(config)
    resultat = pipeline.nettoyer(config)
    propre, rapport, journal = resultat.fichiers
    assert resultat.lignes == 10
    assert pd.read_parquet(propre)["code"].tolist() == [f"{i:04}" for i in range(10)]
    assert rapport.is_file()
    regles = json.loads(journal.read_text(encoding="utf-8"))
    assert len(regles) == 7
    assert all(type(regle["lignes_touchees"]) is int for regle in regles)


def test_parquet_rejoue_avec_le_meme_contenu(config, partitions):
    dossier, schema, marqueur = partitions.fichiers
    avant = {f.relative_to(dossier): f.read_bytes() for f in dossier.rglob("*") if f.is_file()}
    assert schema.is_file() and marqueur.is_file()
    assert pipeline.parquet(config).lignes == 10
    assert {f.relative_to(dossier): f.read_bytes() for f in dossier.rglob("*") if f.is_file()} == avant


def test_exports_decrit_et_fige_le_split(config, partitions):
    resultat = pipeline.exports(config)
    export, schema = resultat.fichiers
    donnees = pd.read_parquet(export)
    assert donnees.groupby(["nutriscore_grade", "split"]).size().to_dict() == {
        ("a", "train"): 4,
        ("a", "test"): 1,
        ("b", "train"): 4,
        ("b", "test"): 1,
    }
    description = json.loads(schema.read_text(encoding="utf-8"))
    assert description["lignes"] == resultat.lignes == len(donnees)
    assert description["sha256"] == pipeline.sha256(export)
    with pytest.raises(FileExistsError):
        pipeline.exports(config)
    assert pipeline.sha256(export) == description["sha256"]


def test_executer_all_journalise_les_etapes_dans_l_ordre(config, monkeypatch):
    ordre = list(pipeline.ETAPES)

    def simuler(cfg):
        assert cfg is config
        return pipeline.ResultatEtape(0.25, 2, (Path("sortie"),))

    monkeypatch.setattr(pipeline, "ETAPES", dict.fromkeys(ordre, simuler))
    pipeline.executer("all", config)
    journal = config.dossier_donnees / "logs" / "pipeline.jsonl"
    entrees = [json.loads(ligne) for ligne in journal.read_text(encoding="utf-8").splitlines()]
    assert [e["etape"] for e in entrees] == ordre
    assert all(e["statut"] == "succes" and e["fichiers"] == ["sortie"] for e in entrees)


def test_executer_all_s_arrete_et_journalise_l_echec(config, monkeypatch):
    def echec(cfg):
        raise ValueError("échec volontaire")

    def inattendu(cfg):
        pytest.fail("L'étape suivante a été appelée")

    monkeypatch.setattr(pipeline, "ETAPES", {"charger": echec, "nettoyer": inattendu})
    with pytest.raises(ValueError, match="échec volontaire"):
        pipeline.executer("all", config)
    journal = config.dossier_donnees / "logs" / "pipeline.jsonl"
    entree = json.loads(journal.read_text(encoding="utf-8"))
    assert entree["etape"] == "charger"
    assert entree["statut"] == "echec"
    assert entree["erreur"] == "échec volontaire"
