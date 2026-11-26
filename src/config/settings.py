import os
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
    "host": os.environ.get("NUTRISCOPE_DB_HOST", "localhost"),
    "port": int(os.environ.get("NUTRISCOPE_DB_PORT", "5432")),
    "dbname": os.environ.get("NUTRISCOPE_DB_NAME", "nutriscope"),
    "user": os.environ.get("NUTRISCOPE_DB_USER", "postgres"),
    "password": os.environ.get("NUTRISCOPE_DB_PASSWORD", "postgres"),
}

POSTGRES_DB_ALIAS = "pg"
