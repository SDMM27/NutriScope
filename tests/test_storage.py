"""Tests du stockage Parquet / DuckDB (TP 12), sur l'échantillon uniquement.

Données : © Open Food Facts contributors — ODbL.
"""

import json
import subprocess
from pathlib import Path

import duckdb
import pytest

from src.storage.commun import EXPORTS, NUTRIMENTS_CLES, RACINE, SQL_CONTROLES
from src.storage.convert_parquet import SCHEMA, convertir
from src.storage.preparer_csv import ecrire_csv_nettoye
from src.storage.export_features import chemin_schema, exporter
from src.storage.run_queries import executer, lire_requetes

ECHANTILLON = RACINE / "data/echantillon_france.csv"
NOMS_CONTROLES = ["comptage_par_rayon", "completude", "doublons", "bornes_coherences", "distribution_nutriscore"]

pytestmark = pytest.mark.skipif(not ECHANTILLON.exists(), reason="échantillon data/echantillon_france.csv absent")


@pytest.fixture(scope="session")
def jeu(tmp_path_factory):
    base = tmp_path_factory.mktemp("storage")
    csv = base / "nettoye.csv"
    dossier = base / "parquet" / "produits"
    lignes_csv = ecrire_csv_nettoye(ECHANTILLON, csv)
    lignes = convertir(csv, dossier, base / "parquet" / "schema_produits.json")
    return {"base": base, "csv": csv, "dossier": dossier, "lignes_csv": lignes_csv, "lignes": lignes}


def _sql(jeu, requete: str):
    glob = (jeu["dossier"] / "**/*.parquet").as_posix()
    con = duckdb.connect()
    try:
        return con.execute(requete.replace("{p}", f"read_parquet('{glob}', hive_partitioning = true)")).fetchall()
    finally:
        con.close()


def test_une_partition_par_rayon_et_toutes_les_lignes(jeu):
    partitions = [p.name for p in jeu["dossier"].iterdir()]
    assert partitions and all(p.startswith("rayon=") and p != "rayon=" for p in partitions)
    rayons = _sql(jeu, "SELECT count(DISTINCT rayon) FROM {p}")[0][0]
    assert rayons == len(partitions)
    assert jeu["lignes"] == jeu["lignes_csv"] > 0


def test_fichier_nomme_d_apres_son_rayon(jeu):
    for partition in jeu["dossier"].iterdir():
        slug = partition.name.removeprefix("rayon=")
        assert [f.name for f in partition.iterdir()] == [f"{slug}.parquet"]


def test_types_du_parquet_conformes_au_schema(jeu):
    fichier = next(jeu["dossier"].rglob("*.parquet"))
    con = duckdb.connect()
    try:
        types = dict(con.execute(
            f"SELECT column_name, column_type FROM (DESCRIBE SELECT * FROM read_parquet('{fichier.as_posix()}'))"
        ).fetchall())
    finally:
        con.close()
    for nom, (type_sql, _) in SCHEMA.items():
        assert types[nom] == type_sql, nom


def test_schema_produits_ecrit(jeu):
    schema = json.loads((jeu["base"] / "parquet" / "schema_produits.json").read_text(encoding="utf-8"))
    assert schema["lignes"] == jeu["lignes"]
    assert [c["nom"] for c in schema["colonnes"]] == list(SCHEMA)


def test_zeros_de_tete_conserves(jeu):
    assert _sql(jeu, "SELECT count(*) FROM {p} WHERE code LIKE '0%'")[0][0] > 0


def test_reconversion_sans_orphelin(jeu, tmp_path):
    dossier = tmp_path / "produits"
    convertir(jeu["csv"], dossier, tmp_path / "schema.json")
    faux = dossier / "rayon=zzz"
    faux.mkdir()
    (faux / "data_0.parquet").write_bytes(b"orphelin")
    assert convertir(jeu["csv"], dossier, tmp_path / "schema.json") == jeu["lignes"]
    assert not faux.exists()


def test_cinq_requetes_lues_depuis_le_sql():
    requetes = lire_requetes(SQL_CONTROLES)
    assert list(requetes) == NOMS_CONTROLES
    assert all(sql.lstrip().upper().startswith("SELECT") for sql in requetes.values())


def test_cinq_requetes_s_executent(jeu):
    resultats = executer(jeu["dossier"], SQL_CONTROLES)
    assert list(resultats) == NOMS_CONTROLES
    assert all(len(table) > 0 for table in resultats.values())


def test_comptage_par_rayon_totalise_le_jeu(jeu):
    comptage = executer(jeu["dossier"], SQL_CONTROLES)["comptage_par_rayon"]
    assert comptage["nb_produits"].sum() == jeu["lignes"]
    assert comptage["part_pct"].sum() == pytest.approx(100, abs=0.1)
    assert comptage["nb_produits"].is_monotonic_decreasing


def test_zero_doublon_et_zero_hors_bornes(jeu):
    resultats = executer(jeu["dossier"], SQL_CONTROLES)
    doublons = resultats["doublons"].iloc[0]
    assert doublons["codes_en_double_groupes"] == 0
    assert doublons["lignes_en_trop"] == 0
    bornes = resultats["bornes_coherences"].set_index("controle")["nb"]
    hors = bornes[bornes.index.str.contains("hors")]
    assert len(hors) == 9 and (hors == 0).all(), hors[hors > 0]


def test_export_date_decrit_et_cible_complete(jeu, tmp_path):
    fichier = exporter(jeu["dossier"], tmp_path, "20251014")
    assert fichier.name == "features_nutriscore_20251014.parquet"
    schema = json.loads(chemin_schema(fichier).read_text(encoding="utf-8"))
    con = duckdb.connect()
    try:
        colonnes = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{fichier.as_posix()}')").fetchall()]
        manquants, grades = con.execute(
            f"SELECT count(*) FILTER (WHERE nutriscore_grade IS NULL), "
            f"count(*) FILTER (WHERE nutriscore_grade NOT IN ('a','b','c','d','e')) "
            f"FROM read_parquet('{fichier.as_posix()}')"
        ).fetchone()
    finally:
        con.close()
    assert [c["nom"] for c in schema["colonnes"]] == colonnes
    assert colonnes[:2] == ["code", "rayon"] and colonnes[-2:] == ["nutriscore_grade", "split"]
    assert set(NUTRIMENTS_CLES) <= set(colonnes)
    assert manquants == 0 and grades == 0
    assert schema["lignes"] == sum(schema["repartition_cible"].values()) > 0
    assert {c["nom"]: c["pct_manquants"] for c in schema["colonnes"]}["nutriscore_grade"] == 0


def test_export_refuse_d_ecraser_et_reste_reproductible(jeu, tmp_path):
    fichier = exporter(jeu["dossier"], tmp_path, "20251014")
    premier = json.loads(chemin_schema(fichier).read_text(encoding="utf-8"))["sha256"]
    with pytest.raises(FileExistsError):
        exporter(jeu["dossier"], tmp_path, "20251014")
    exporter(jeu["dossier"], tmp_path, "20251014", force=True)
    second = json.loads(chemin_schema(fichier).read_text(encoding="utf-8"))["sha256"]
    assert premier == second
    assert Path(fichier).exists()


def test_split_stratifie_vingt_pourcent_par_grade(jeu, tmp_path):
    fichier = exporter(jeu["dossier"], tmp_path, "20251014")
    con = duckdb.connect()
    try:
        parts = con.execute(
            f"SELECT nutriscore_grade, count(*), avg(CASE WHEN split = 'test' THEN 1 ELSE 0 END) "
            f"FROM read_parquet('{fichier.as_posix()}') GROUP BY ALL ORDER BY 1"
        ).fetchall()
        valeurs = {r[0] for r in con.execute(f"SELECT DISTINCT split FROM read_parquet('{fichier.as_posix()}')").fetchall()}
    finally:
        con.close()
    assert valeurs == {"train", "test"}
    assert [g for g, _, _ in parts] == ["a", "b", "c", "d", "e"]
    for grade, effectif, part in parts:
        # arrondi au produit près : l'écart à 20 % est au plus d'un demi-produit
        assert abs(part * effectif - 0.2 * effectif) <= 0.5, grade


def test_split_identique_produit_par_produit(jeu, tmp_path):
    premier = exporter(jeu["dossier"], tmp_path / "1", "20251014")
    second = exporter(jeu["dossier"], tmp_path / "2", "20251015")
    con = duckdb.connect()
    try:
        differences = con.execute(
            f"SELECT count(*) FROM read_parquet('{premier.as_posix()}') p "
            f"JOIN read_parquet('{second.as_posix()}') s USING (code) WHERE p.split <> s.split"
        ).fetchone()[0]
    finally:
        con.close()
    schema = json.loads(chemin_schema(premier).read_text(encoding="utf-8"))
    assert differences == 0
    assert schema["split"]["graine"] == 42 and schema["split"]["part_test"] == 0.2


def test_schema_decrit_le_split_ecrit(jeu, tmp_path):
    fichier = exporter(jeu["dossier"], tmp_path, "20251014")
    schema = json.loads(chemin_schema(fichier).read_text(encoding="utf-8"))
    con = duckdb.connect()
    try:
        lus = con.execute(
            f"SELECT nutriscore_grade, split, count(*) FROM read_parquet('{fichier.as_posix()}') GROUP BY ALL"
        ).fetchall()
    finally:
        con.close()
    effectifs = schema["split"]["effectifs_par_grade"]
    assert {(g, s, n) for g, d in effectifs.items() for s, n in d.items()} == set(lus)
    assert sum(n for d in effectifs.values() for n in d.values()) == schema["lignes"]
    assert any("train seulement" in regle for regle in schema["split"]["regle_usage"])


def test_exports_hors_git():
    # l'export est régénérable (commande + graine versionnées) : le fichier lui-même ne doit jamais être suivi
    fichier = EXPORTS / "features_nutriscore_20251014.parquet"
    ignore = subprocess.run(["git", "check-ignore", "-q", str(fichier)], cwd=RACINE)
    assert EXPORTS == RACINE / "data" / "exports"
    assert ignore.returncode == 0


def test_un_schema_par_export(jeu, tmp_path):
    ancien = exporter(jeu["dossier"], tmp_path, "20251014")
    nouveau = exporter(jeu["dossier"], tmp_path, "20251015")
    assert chemin_schema(ancien).name == "features_nutriscore_20251014.schema.json"
    assert json.loads(chemin_schema(ancien).read_text(encoding="utf-8"))["nom"] == ancien.name
    assert json.loads(chemin_schema(nouveau).read_text(encoding="utf-8"))["nom"] == nouveau.name
    assert not (tmp_path / "schema.json").exists()
