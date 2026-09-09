from pathlib import Path
from time import perf_counter

import duckdb


# ============================================================
# Configuration
# ============================================================

INPUT_DIR = Path("data/extracts")

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "nutriscope",
    "user": "postgres",
    "password": "postgres",
}

REQUIRED_FILES = [
    "brands.parquet",
    "categories.parquet",
    "products.parquet",
    "products_categories.parquet",
    "nutrients.parquet",
]

POSTGRES_DB_ALIAS = "pg"


# ============================================================
# Configuration des imports
# ============================================================

IMPORT_CONFIG = [
    {
        "file": "brands.parquet",
        "table": "brands",
        "columns": "name",
    },
    {
        "file": "categories.parquet",
        "table": "categories",
        "columns": "tag",
    },
    {
        "file": "products.parquet",
        "table": "products",
        "columns": None,
        "custom": True,
    },
    {
        "file": "products_categories.parquet",
        "table": "products_categories",
        "columns": None,
        "custom": True,
    },
    {
        "file": "nutrients.parquet",
        "table": "nutrients",
        "columns": None,
        "custom": True,
    },
]


# ============================================================
# Utilitaires
# ============================================================

def timer():
    """Retourne un chronomètre haute précision."""
    return perf_counter()


def elapsed(start):
    """Retourne le temps écoulé en secondes."""
    return perf_counter() - start


def print_duration(label, start):
    """Affiche la durée d'une opération."""
    print(f"{label:<40} {elapsed(start):>8.2f} s")


# ============================================================
# Connexion PostgreSQL via DuckDB
# ============================================================

def create_duckdb_connection():
    """
    Crée une connexion DuckDB et charge l'extension PostgreSQL.

    L'extension doit avoir été installée au préalable avec :

        INSTALL postgres;

    Une fois installée, seul LOAD est nécessaire.
    """

    connection = duckdb.connect()

    connection.execute("LOAD postgres;")

    connection_string = (
        f"host={DB_CONFIG['host']} "
        f"port={DB_CONFIG['port']} "
        f"dbname={DB_CONFIG['dbname']} "
        f"user={DB_CONFIG['user']} "
        f"password={DB_CONFIG['password']}"
    )

    connection.execute(
        f"""
        ATTACH '{connection_string}'
        AS {POSTGRES_DB_ALIAS}
        (TYPE postgres);
        """
    )

    return connection


# ============================================================
# Vérification des fichiers
# ============================================================

def check_input_files():
    """
    Vérifie que tous les fichiers Parquet nécessaires existent.
    """

    missing_files = [
        INPUT_DIR / filename
        for filename in REQUIRED_FILES
        if not (INPUT_DIR / filename).exists()
    ]

    if missing_files:
        print("Erreur : fichiers Parquet manquants :")

        for path in missing_files:
            print(f"  - {path}")

        raise FileNotFoundError(
            "Certains fichiers Parquet sont absents."
        )


# ============================================================
# Inspection optionnelle
# ============================================================

def inspect_parquet(connection, parquet_path):
    """
    Inspecte un fichier Parquet.

    Cette fonction est volontairement séparée du processus
    d'import afin de ne pas effectuer systématiquement
    des scans complets des fichiers.
    """

    print(f"\nInspection : {parquet_path}")

    start = timer()

    row_count = connection.execute(
        f"""
        SELECT COUNT(*)
        FROM read_parquet('{parquet_path}')
        """
    ).fetchone()[0]

    print(f"  Nombre de lignes : {row_count}")

    columns = connection.execute(
        f"""
        DESCRIBE SELECT *
        FROM read_parquet('{parquet_path}')
        """
    ).fetchall()

    print("  Colonnes :")

    for column in columns:
        print(f"    - {column[0]} ({column[1]})")

    print_duration("Inspection", start)

    return row_count


# ============================================================
# Nettoyage de la base
# ============================================================

from sqlalchemy import create_engine, text

def clear_database():
    """
    Vide toutes les tables NutriScope.

    Le TRUNCATE est exécuté directement par PostgreSQL
    via SQLAlchemy afin d'éviter le surcoût du connecteur
    PostgreSQL de DuckDB.
    """

    start = timer()

    engine = create_engine(
        "postgresql+psycopg2://postgres:postgres@localhost:5432/nutriscope"
    )

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                TRUNCATE TABLE
                    nutrients,
                    products_categories,
                    products,
                    categories,
                    brands
                CASCADE;
                """
            )
        )

    engine.dispose()

    print_duration("Nettoyage de la BDD", start)


# ============================================================
# Import brands
# ============================================================

def insert_brands(connection):
    """
    Importe les marques.

    Le Parquet est dédoublonné sur le nom de marque.
    """

    connection.execute(
        f"""
        INSERT INTO {POSTGRES_DB_ALIAS}.public.brands (name)
        SELECT DISTINCT
            REPLACE(name, chr(0), '')
        FROM read_parquet(
            '{INPUT_DIR / "brands.parquet"}'
        )
        WHERE name IS NOT NULL;
        """
    )


# ============================================================
# Import categories
# ============================================================

def insert_categories(connection):
    """
    Importe les catégories.

    Les catégories sont dédoublonnées sur leur tag.
    """

    connection.execute(
        f"""
        INSERT INTO {POSTGRES_DB_ALIAS}.public.categories (tag)
        SELECT DISTINCT
            REPLACE(tag, chr(0), '')
        FROM read_parquet(
            '{INPUT_DIR / "categories.parquet"}'
        )
        WHERE tag IS NOT NULL;
        """
    )


# ============================================================
# Import products
# ============================================================

def insert_products(connection):
    """
    Importe les produits.

    Étapes :
        1. nettoyage des chaînes
        2. dédoublonnage des codes
        3. recherche de la marque
        4. insertion PostgreSQL
    """

    connection.execute(
        f"""
        WITH cleaned AS (

            SELECT
                REPLACE(code, chr(0), '') AS code,
                REPLACE(name, chr(0), '') AS name,
                REPLACE(brand_name, chr(0), '') AS brand_name,
                REPLACE(nutriscore_grade, chr(0), '')
                    AS nutriscore_grade,
                nutriscore_score

            FROM read_parquet(
                '{INPUT_DIR / "products.parquet"}'
            )

            WHERE code IS NOT NULL
        ),

        deduplicated AS (

            SELECT *
            FROM cleaned

            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY code
            ) = 1
        )

        INSERT INTO {POSTGRES_DB_ALIAS}.public.products (
            code,
            name,
            brand_id,
            nutriscore_grade,
            nutriscore_score
        )

        SELECT
            p.code,
            p.name,
            b.id,
            p.nutriscore_grade,
            p.nutriscore_score

        FROM deduplicated AS p

        LEFT JOIN {POSTGRES_DB_ALIAS}.public.brands AS b
            ON p.brand_name = b.name;
        """
    )


# ============================================================
# Import products_categories
# ============================================================

def insert_products_categories(connection):
    """
    Importe les relations produits / catégories.

    Le nettoyage et le dédoublonnage sont réalisés avant
    les JOIN afin de réduire le volume traité.
    """

    connection.execute(
        f"""
        WITH cleaned AS (

            SELECT DISTINCT
                REPLACE(code, chr(0), '') AS code,
                REPLACE(tag, chr(0), '') AS tag

            FROM read_parquet(
                '{INPUT_DIR / "products_categories.parquet"}'
            )

            WHERE code IS NOT NULL
              AND tag IS NOT NULL
        )

        INSERT INTO {POSTGRES_DB_ALIAS}.public.products_categories (
            code,
            category_id
        )

        SELECT
            pc.code,
            c.id

        FROM cleaned AS pc

        JOIN {POSTGRES_DB_ALIAS}.public.categories AS c
            ON pc.tag = c.tag

        JOIN {POSTGRES_DB_ALIAS}.public.products AS p
            ON pc.code = p.code;
        """
    )

# ============================================================
# Import nutrients
# ============================================================

def insert_nutrients(connection):
    """
    Importe les données nutritionnelles.

    Les valeurs hors limites sont remplacées par NULL.

    Les codes produits sont nettoyés puis dédoublonnés avant
    le JOIN avec la table products.
    """

    connection.execute(
        f"""
        WITH cleaned AS (

            SELECT
                REPLACE(code, chr(0), '') AS code,

                energy,
                energy_kcal,
                proteins,
                carbohydrates,
                sugars,
                fat,
                saturated_fat,
                fiber,
                salt

            FROM read_parquet(
                '{INPUT_DIR / "nutrients.parquet"}'
            )

            WHERE code IS NOT NULL
        ),

        deduplicated AS (

            SELECT *
            FROM cleaned

            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY code
            ) = 1
        )

        INSERT INTO {POSTGRES_DB_ALIAS}.public.nutrients (
            code,
            energy,
            energy_kcal,
            proteins,
            carbohydrates,
            sugars,
            fat,
            saturated_fat,
            fiber,
            salt
        )

        SELECT
            n.code,

            CASE
                WHEN n.energy BETWEEN 0 AND 99999.99
                THEN n.energy
                ELSE NULL
            END,

            CASE
                WHEN n.energy_kcal BETWEEN 0 AND 99999.99
                THEN n.energy_kcal
                ELSE NULL
            END,

            CASE
                WHEN n.proteins BETWEEN 0 AND 100
                THEN n.proteins
                ELSE NULL
            END,

            CASE
                WHEN n.carbohydrates BETWEEN 0 AND 100
                THEN n.carbohydrates
                ELSE NULL
            END,

            CASE
                WHEN n.sugars BETWEEN 0 AND 100
                THEN n.sugars
                ELSE NULL
            END,

            CASE
                WHEN n.fat BETWEEN 0 AND 100
                THEN n.fat
                ELSE NULL
            END,

            CASE
                WHEN n.saturated_fat BETWEEN 0 AND 100
                THEN n.saturated_fat
                ELSE NULL
            END,

            CASE
                WHEN n.fiber BETWEEN 0 AND 100
                THEN n.fiber
                ELSE NULL
            END,

            CASE
                WHEN n.salt BETWEEN 0 AND 100
                THEN n.salt
                ELSE NULL
            END

        FROM deduplicated AS n

        JOIN {POSTGRES_DB_ALIAS}.public.products AS p
            ON n.code = p.code;
        """
    )


# ============================================================
# Import générique
# ============================================================

def import_parquet(connection, config):
    """
    Importe un fichier Parquet vers PostgreSQL.
    """

    parquet_filename = config["file"]
    postgres_table = config["table"]

    parquet_path = INPUT_DIR / parquet_filename

    print()
    print("=" * 60)
    print(f"Import : {parquet_filename}")
    print(f"       -> {postgres_table}")
    print("=" * 60)

    start = timer()

    if not parquet_path.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {parquet_path}"
        )

    # --------------------------------------------------------
    # Import spécialisé
    # --------------------------------------------------------

    if parquet_filename == "brands.parquet":

        insert_brands(connection)

    elif parquet_filename == "categories.parquet":

        insert_categories(connection)

    elif parquet_filename == "products.parquet":

        insert_products(connection)

    elif parquet_filename == "products_categories.parquet":

        insert_products_categories(connection)

    elif parquet_filename == "nutrients.parquet":

        insert_nutrients(connection)

    else:

        raise ValueError(
            f"Aucune stratégie d'import définie pour "
            f"{parquet_filename}"
        )

    print_duration(
        f"Import {postgres_table}",
        start
    )

    # --------------------------------------------------------
    # Contrôle du nombre de lignes
    # --------------------------------------------------------

    count = connection.execute(
        f"""
        SELECT COUNT(*)
        FROM {POSTGRES_DB_ALIAS}.public.{postgres_table};
        """
    ).fetchone()[0]

    print(
        f"Lignes dans PostgreSQL : {count:,}"
        .replace(",", " ")
    )


# ============================================================
# Contrôle final
# ============================================================

def final_check(connection):
    """
    Affiche le volume final des tables.
    """

    print()
    print("=" * 60)
    print("Contrôle final")
    print("=" * 60)

    tables = [
        "brands",
        "categories",
        "products",
        "products_categories",
        "nutrients",
    ]

    for table in tables:

        count = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM {POSTGRES_DB_ALIAS}.public.{table};
            """
        ).fetchone()[0]

        print(
            f"{table:25} {count:>12,} lignes"
            .replace(",", " ")
        )


# ============================================================
# Import principal
# ============================================================

def main():

    total_start = timer()

    print()
    print("=" * 60)
    print("NutriScope - Import Parquet -> PostgreSQL")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Vérification des fichiers
    # --------------------------------------------------------

    print("\nVérification des fichiers...")

    check_input_files()

    print("Tous les fichiers sont présents.")

    # --------------------------------------------------------
    # 2. Connexion
    # --------------------------------------------------------

    print("\nConnexion à PostgreSQL via DuckDB...")

    connection = create_duckdb_connection()

    print("Connexion réussie.")

    try:

        # ----------------------------------------------------
        # 3. Nettoyage
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("Nettoyage de la BDD")
        print("=" * 60)

        clear_database()

        # ----------------------------------------------------
        # 4. Import
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("Import des données")
        print("=" * 60)

        for config in IMPORT_CONFIG:

            import_parquet(
                connection,
                config
            )

        # ----------------------------------------------------
        # 5. Contrôle final
        # ----------------------------------------------------

        final_check(connection)

        # ----------------------------------------------------
        # 6. Temps total
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("Import terminé avec succès.")
        print("=" * 60)

        print(
            f"\nTemps total : "
            f"{elapsed(total_start):.2f} secondes"
        )

    finally:

        connection.close()

        print("\nConnexion fermée.")


# ============================================================
# Point d'entrée
# ============================================================

if __name__ == "__main__":
    main()
