"""Recherche exacte dans les Parquets complets via le CLI DuckDB local.

Évite de charger tout le catalogue en RAM et ne dépend pas de pandas/pyarrow.
Les doublons sont conservés : ils doivent provoquer une abstention du scanner.
"""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]


def trouver_duckdb(executable=None):
    candidat = executable or os.environ.get("DUCKDB_EXE") or shutil.which("duckdb")
    if not candidat:
        candidat = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "DuckDB/duckdb.exe"
    chemin = Path(candidat).resolve(strict=True)
    if not chemin.is_file():
        raise FileNotFoundError("CLI DuckDB absent : définir DUCKDB_EXE")
    return chemin


def _literal(valeur):
    return "'" + str(valeur).replace("'", "''") + "'"


class CatalogueParquet:
    """Même colonnes produit/nutriments que TP18 ; accès par code uniquement."""

    def __init__(self, dossier=None, executable=None):
        self.dossier = Path(dossier or RACINE / "data/extracts").resolve()
        self.executable = trouver_duckdb(executable)
        self.produits = (self.dossier / "products.parquet").resolve(strict=True)
        self.nutriments = (self.dossier / "nutrients.parquet").resolve(strict=True)
        self.statistiques = self._requete(
            f"SELECT count(*) AS lignes_produits, count(DISTINCT code) AS codes_distincts "
            f"FROM read_parquet({_literal(self.produits.as_posix())})"
        )[0]

    def _requete(self, sql):
        r = subprocess.run([str(self.executable), "-json", "-c", sql],
                           capture_output=True, encoding="utf-8", timeout=60)
        if r.returncode:
            raise RuntimeError("Erreur de lecture du catalogue DuckDB : " + r.stderr.strip())
        return json.loads(r.stdout) if r.stdout.strip() else []

    def chercher_code(self, code):
        # Ni texte libre ni fragment SQL ne peut atteindre la requête.
        if not isinstance(code, str) or not re.fullmatch(r"(?:\d{8}|\d{13})", code, re.ASCII):
            raise ValueError("Le catalogue scanner attend un code EAN-8/EAN-13")
        colonnes = ("energy_kcal", "fat", "saturated_fat", "sugars", "salt", "fiber", "proteins")
        # Le CLI sérialise les DECIMAL en chaînes ; l'API scanner attend des nombres.
        selection = ",".join(f"CAST(n.{c} AS DOUBLE) AS {c}" for c in colonnes)
        return self._requete(
            "SELECT p.code,p.name,p.brand_name,p.nutriscore_grade," + selection + " "
            f"FROM read_parquet({_literal(self.produits.as_posix())}) p "
            f"LEFT JOIN read_parquet({_literal(self.nutriments.as_posix())}) n USING(code) "
            f"WHERE CAST(p.code AS VARCHAR) = {_literal(code)} LIMIT 2"
        )
