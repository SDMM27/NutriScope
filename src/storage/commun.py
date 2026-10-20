"""Chemins et constantes partagés par les scripts du TP 12.

Données : © Open Food Facts contributors — ODbL.
"""

from pathlib import Path

import duckdb

RACINE = Path(__file__).resolve().parents[2]

BRUT = RACINE / "data/extracts/france_brut.parquet"
CSV_NETTOYE = RACINE / "data/clean/produits_nettoyes.csv"
PARQUET_PRODUITS = RACINE / "data/parquet/produits"
SCHEMA_PRODUITS = RACINE / "data/parquet/schema_produits.json"
EXPORTS = RACINE / "data/exports"
SQL_CONTROLES = RACINE / "sql/controles.sql"
DOCS_DATA = RACINE / "docs/data"

LICENCE = "© Open Food Facts contributors — ODbL 1.0 (https://opendatacommons.org/licenses/odbl/1-0/)"

NUTRIMENTS_CLES = [
    "energy-kcal_100g",
    "fat_100g",
    "saturated-fat_100g",
    "carbohydrates_100g",
    "sugars_100g",
    "proteins_100g",
    "salt_100g",
]


def sql_chemin(chemin: str | Path) -> str:
    """Chemin absolu en slashs, protégé pour une chaîne SQL DuckDB."""
    return Path(chemin).resolve().as_posix().replace("'", "''")


def creer_vue_produits(connexion: duckdb.DuckDBPyConnection, dossier: str | Path = PARQUET_PRODUITS) -> None:
    """Crée la vue `produits` sur le jeu partitionné (clé `rayon` relue depuis les dossiers)."""
    connexion.execute(f"""
        CREATE OR REPLACE VIEW produits AS
        SELECT * FROM read_parquet('{sql_chemin(dossier)}/**/*.parquet', hive_partitioning = true)
    """)
