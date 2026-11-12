"""Tests du catalogue et de l'outil chercher_produit (catalogue factice)."""
import json

import numpy as np
import pandas as pd
import pytest

from src.assistant.catalogue import COLONNES_NUTRIMENTS, construire_fiche, normaliser
from src.assistant.outils import chercher_produit, executer_outil, valider_arguments


def faire_catalogue(lignes):
    base = {c: np.nan for c in COLONNES_NUTRIMENTS.values()}
    df = pd.DataFrame([{**base, "brand_name": None, "completeness": np.nan, **l} for l in lignes])
    df["nom_normalise"] = df["name"].map(normaliser)
    df["marque_normalisee"] = df["brand_name"].map(normaliser)
    return df


@pytest.fixture
def cat():
    return faire_catalogue([
        {"code": "1", "name": "Nutella", "nutriscore_grade": "e", "completeness": 0.9,
         "sugars": 56.3, "energy_kcal": 539.0},
        {"code": "2", "name": "Nutella biscuits", "nutriscore_grade": "d", "completeness": 0.95},
        {"code": "3", "name": "Pâte à tartiner Nutella bio", "nutriscore_grade": "unknown", "completeness": 0.5},
        {"code": "4", "name": "Crème brûlée", "nutriscore_grade": "c", "completeness": 0.7},
        {"code": "5", "name": None, "nutriscore_grade": None},
    ])


def test_normaliser():
    assert normaliser("Crème BRÛLÉE") == "creme brulee"
    assert normaliser(None) == ""
    assert normaliser(float("nan")) == ""


def test_fiche_nan_jamais_zero():
    f = construire_fiche(pd.Series({"code": "9", "name": "X", "nutriscore_grade": "b",
                                    "sugars": 1.234, "fat": np.nan}))
    assert f["nutriments"]["sucres"] == 1.23
    assert f["nutriments"]["lipides"] is None
    assert f["nutriments"]["sel"] is None
    assert f["nutriscore"] == "B"
    assert f["donnees_incompletes"] is True
    json.dumps(f)


@pytest.mark.parametrize("grade", ["unknown", "not-applicable", None, np.nan])
def test_fiche_grade_invalide(grade):
    assert construire_fiche({"code": "1", "nutriscore_grade": grade})["nutriscore"] is None


def test_fiche_complete():
    ligne = {"code": "1", "name": "A", "brand_name": "M", "nutriscore_grade": "a",
             **{c: np.float32(1.5) for c in COLONNES_NUTRIMENTS.values()}}
    f = construire_fiche(ligne)
    assert f["donnees_incompletes"] is False
    assert f["marque"] == "M"
    json.dumps(f)


def test_fiche_nom_absent():
    assert construire_fiche({"code": "1", "name": None})["nom"] is None


def test_valider_json_str():
    args, err = valider_arguments('{"nom": "nutella"}')
    assert err is None and args == {"nom": "nutella", "code": None, "limite": 3}


def test_valider_json_illisible():
    assert "JSON illisible" in valider_arguments("{pas du json")[1]


def test_valider_argument_inconnu():
    assert "marque" in valider_arguments({"nom": "a", "marque": "b"})[1]


@pytest.mark.parametrize("limite", [0, 6, "3", 3.0, True])
def test_valider_limite_invalide(limite):
    assert valider_arguments({"nom": "a", "limite": limite})[1] is not None


def test_valider_ni_nom_ni_code():
    assert valider_arguments({})[1] is not None
    assert valider_arguments({"nom": "  "})[1] is not None


@pytest.mark.parametrize("bizarre", [None, [], 42, ["nom"], {"nom": 3}, {"code": ["1"]}])
def test_aucune_exception(cat, bizarre):
    assert "erreur" in chercher_produit(cat, bizarre)
    assert valider_arguments(bizarre)[1] is not None


def test_code_prime_sur_nom(cat):
    r = chercher_produit(cat, {"code": "4", "nom": "nutella"})
    assert r["statut"] == "ok" and r["produits"][0]["code"] == "4"


def test_recherche_insensible(cat):
    r = chercher_produit(cat, {"nom": "CREME brulee"})
    assert r["total"] == 1 and r["produits"][0]["nom"] == "Crème brûlée"


def test_partie_de_nom_et_statuts(cat):
    assert chercher_produit(cat, {"nom": "tartiner"})["statut"] == "ok"
    assert chercher_produit(cat, {"nom": "nutella"})["statut"] == "ambigu"
    r = chercher_produit(cat, {"nom": "zzz"})
    assert r == {"statut": "introuvable", "total": 0, "produits": []}


def test_total_superieur_limite(cat):
    r = chercher_produit(cat, {"nom": "nutella", "limite": 2})
    assert r["total"] == 3 and len(r["produits"]) == 2


def test_exact_d_abord(cat):
    # "Nutella biscuits" a une meilleure completeness mais "Nutella" est exact
    r = chercher_produit(cat, {"nom": "nutella"})
    assert [p["code"] for p in r["produits"]] == ["1", "2", "3"]


def test_tri_completeness_nan_en_dernier():
    c = faire_catalogue([
        {"code": "a", "name": "lait demi", "completeness": np.nan},
        {"code": "b", "name": "lait entier", "completeness": 0.2},
    ])
    r = chercher_produit(c, {"nom": "lait"})
    assert [p["code"] for p in r["produits"]] == ["b", "a"]


def test_mots_dans_le_desordre(cat):
    r = chercher_produit(cat, {"nom": "tartiner nutella"})
    assert r["statut"] == "ok" and r["produits"][0]["code"] == "3"


def test_mot_de_marque():
    c = faire_catalogue([
        {"code": "l", "name": "Pâte à tartiner noir", "brand_name": "xx:lindt", "completeness": 0.5},
        {"code": "n", "name": "Pâte à tartiner", "brand_name": "xx:nutella", "completeness": 0.9},
    ])
    r = chercher_produit(c, {"nom": "pâte lindt"})
    assert r["statut"] == "ok" and r["produits"][0]["code"] == "l"


def test_partie_de_mot(cat):
    assert chercher_produit(cat, {"nom": "nutel"})["total"] == 3


def test_requete_sans_mot_exploitable(cat):
    assert "erreur" in chercher_produit(cat, {"nom": "?!"})


def test_executer_outil(cat):
    assert "outil inconnu" in executer_outil("supprimer_tout", {}, cat)["erreur"]
    assert "outil inconnu" in executer_outil(None, {}, cat)["erreur"]
    assert executer_outil("chercher_produit", {"code": "1"}, cat)["statut"] == "ok"
