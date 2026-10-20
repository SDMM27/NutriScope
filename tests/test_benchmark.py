"""Tests du benchmark (TP 12) sur l'échantillon partagé.

Données : © Open Food Facts contributors — ODbL.
"""

import json
import subprocess
import sys

import pytest

from src.storage import benchmark
from src.storage.commun import RACINE
from src.storage.convert_parquet import convertir, ecrire_csv_nettoye

ECHANTILLON = RACINE / "data/echantillon_france.csv"

pytestmark = pytest.mark.skipif(not ECHANTILLON.exists(), reason="échantillon absent")


@pytest.fixture(scope="session")
def chemins(tmp_path_factory):
    dossier = tmp_path_factory.mktemp("bench")
    csv = dossier / "nettoye.csv"
    ecrire_csv_nettoye(ECHANTILLON, csv)
    parquet = dossier / "produits"
    convertir(csv, parquet)
    base = dossier / "produits.sqlite"
    benchmark.construire_sqlite(csv, base)
    return {"csv": csv, "parquet": parquet, "sqlite": base}


@pytest.mark.parametrize("requete", list(benchmark.REQUETES_SQL))
def test_moteurs_meme_nombre_de_lignes(chemins, requete):
    tailles = {m: len(benchmark.executer(m, requete, chemins)) for m in benchmark.MOTEURS}
    assert len(set(tailles.values())) == 1, tailles
    assert next(iter(tailles.values())) > 0


def test_verifier_coherence(chemins):
    assert set(benchmark.verifier_coherence(chemins)) == set(benchmark.REQUETES_SQL)


def test_une_mesure_en_sous_processus(chemins):
    res = subprocess.run(
        [sys.executable, "-m", "src.storage.benchmark", "--une", "duckdb_parquet", "agregat_rayon",
         "--csv", str(chemins["csv"]), "--parquet", str(chemins["parquet"]), "--sqlite", str(chemins["sqlite"])],
        cwd=RACINE, capture_output=True, text=True, encoding="utf-8", check=True,
    )
    mesure = json.loads(res.stdout.strip().splitlines()[-1])
    assert mesure["pic_mo"] > 0
    assert mesure["secondes"] > 0
    assert mesure["lignes"] > 0
