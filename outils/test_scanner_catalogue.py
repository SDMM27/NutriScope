"""Intégration sur de vrais Parquets temporaires : recherche exacte et doublons."""
import subprocess

import pytest

from src.scanner.catalogue import CatalogueParquet, trouver_duckdb, _literal
from src.scanner.scanner import aiguiller
from test_scanner_contrat import TEXTE, EXTRACTION


@pytest.fixture
def catalogue(tmp_path):
    executable = trouver_duckdb()
    dossier = tmp_path / "catalogue d'essai"
    dossier.mkdir()
    requete = (
        "COPY (SELECT * FROM (VALUES "
        "('3017620422003','Nutella','xx:nutella','e'),"
        "('5449000000996','Doublon','Marque','d'),"
        "('5449000000996','Autre variante','Marque','d')) "
        "p(code,name,brand_name,nutriscore_grade)) TO "
        + _literal((dossier / "products.parquet").as_posix()) + " (FORMAT PARQUET);"
        "COPY (SELECT '3017620422003' code,539.0 energy_kcal,30.9 fat,"
        "NULL::DOUBLE saturated_fat,56.3 sugars,0.107 salt,NULL::DOUBLE fiber,"
        "NULL::DOUBLE proteins) TO "
        + _literal((dossier / "nutrients.parquet").as_posix()) + " (FORMAT PARQUET);"
    )
    subprocess.run([str(executable), "-c", requete], check=True, capture_output=True)
    return CatalogueParquet(dossier, executable)


def test_parquets_lus_et_rattachement(catalogue):
    assert catalogue.statistiques == {"lignes_produits": 3, "codes_distincts": 2}
    assert aiguiller(TEXTE, EXTRACTION, catalogue)["statut"] == "verifie"
    assert catalogue.chercher_code("3017620422003")[0]["fiber"] is None


def test_absence_et_doublons_conserves(catalogue):
    assert catalogue.chercher_code("0000000000000") == []
    assert len(catalogue.chercher_code("5449000000996")) == 2
    r = aiguiller(TEXTE.replace("3017620422003", "5449000000996"), EXTRACTION, catalogue)
    assert r["statut"] == "non_verifie"
    assert r["raison"] == "code_absent_ou_ambigu"


@pytest.mark.parametrize("code", ["'; DROP TABLE products; --", "3017620422003 OR 1=1", None, 3017620422003])
def test_entree_sql_impossible(catalogue, code):
    with pytest.raises(ValueError):
        catalogue.chercher_code(code)
