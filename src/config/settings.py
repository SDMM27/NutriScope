from pathlib import Path


# ============================================================
# Configuration des fichiers
# ============================================================

INPUT_DIR = Path("data/extracts")

REQUIRED_FILES = [
    "brands.parquet",
    "categories.parquet",
    "products.parquet",
    "products_categories.parquet",
    "nutrients.parquet",
]


# ============================================================
# Configuration PostgreSQL
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "nutriscope",
    "user": "postgres",
    "password": "postgres",
}

POSTGRES_DB_ALIAS = "pg"