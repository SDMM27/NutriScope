from pathlib import Path
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
    "nutrients.parquet",
    "products.parquet",
    "products_categories.parquet",
]

# Nom de la base telle qu'elle sera vue par DuckDB
POSTGRES_DB_ALIAS = "pg"


# ============================================================
# Connexion PostgreSQL via DuckDB
# ============================================================

def create_duckdb_connection():
    """
    Crée une connexion DuckDB et charge l'extension PostgreSQL.
    """

    connection = duckdb.connect()

    connection.execute("INSTALL postgres;")
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
    missing_files = []

    for filename in REQUIRED_FILES:
        path = INPUT_DIR / filename

        if not path.exists():
            missing_files.append(path)

    if missing_files:
        print("Erreur : fichiers Parquet manquants :")

        for path in missing_files:
            print(f"  - {path}")

        raise FileNotFoundError(
            "Certains fichiers Parquet sont absents."
        )


# ============================================================
# Affichage des informations d'un Parquet
# ============================================================

def inspect_parquet(connection, parquet_path):
    """
    Affiche le nombre de lignes et les colonnes du fichier.
    """

    print(f"\nInspection : {parquet_path}")

    result = connection.execute(
        f"""
        SELECT COUNT(*)
        FROM read_parquet('{parquet_path}')
        """
    ).fetchone()

    row_count = result[0]

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

    return row_count


# ============================================================
# Import générique
# ============================================================

def import_parquet(
    connection,
    parquet_filename,
    postgres_table, cols=""
):
    
    print(cols)
    """
    Insère le contenu d'un fichier Parquet
    dans une table PostgreSQL.

    DuckDB lit le Parquet directement puis écrit
    dans PostgreSQL.
    """

    parquet_path = INPUT_DIR / parquet_filename

    print()
    print("=" * 60)
    print(f"Import : {parquet_filename}")
    print(f"       -> {postgres_table}")
    print("=" * 60)

    if not parquet_path.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {parquet_path}"
        )

    # Nombre de lignes source
    source_count = connection.execute(
        f"""
        SELECT COUNT(*)
        FROM read_parquet('{parquet_path}')
        """
    ).fetchone()[0]

    print(f"Lignes dans le Parquet : {source_count}")

    # Insertion
    connection.execute(
        f"""
        INSERT INTO {POSTGRES_DB_ALIAS}.public.{postgres_table} ({cols})
        SELECT DISTINCT *
        FROM read_parquet('{parquet_path}');
        """
    )

    # Nombre de lignes après insertion
    destination_count = connection.execute(
        f"""
        SELECT COUNT(*)
        FROM {POSTGRES_DB_ALIAS}.public.{postgres_table};
        """
    ).fetchone()[0]

    print(
        f"Lignes dans PostgreSQL après import : "
        f"{destination_count}"
    )

# ============================================================
# Import principal
# ============================================================

def clear_database(connection):
    """
    Vide toutes les tables NutriScope avant un nouvel import.
    """

    tables = [
        "products_categories",
        "nutrients",
        "products",
        "categories",
        "brands",
    ]

    for table in tables:
        connection.execute(
            f"""
            TRUNCATE TABLE
            {POSTGRES_DB_ALIAS}.public.{table}
            """
        )

    print("Base de données vidée.")


# ============================================================
# Import principal
# ============================================================

def main():

    print()
    print("=" * 60)
    print("NutriScope - Import Parquet -> PostgreSQL")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Vérification des fichiers
    # --------------------------------------------------------

    check_input_files()

    # --------------------------------------------------------
    # 2. Connexion DuckDB + PostgreSQL
    # --------------------------------------------------------

    print("\nConnexion à PostgreSQL via DuckDB...")

    connection = create_duckdb_connection()

    print("Connexion réussie.")

    try:

        # ----------------------------------------------------
        # 3. Inspection des fichiers
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("Inspection des fichiers")
        print("=" * 60)

        for filename in REQUIRED_FILES:
            inspect_parquet(
                connection,
                INPUT_DIR / filename,
            )

        # ----------------------------------------------------
        # 4. Nettoyage de la BDD
        # ----------------------------------------------------
        print()
        print("=" * 60)
        print("Nettoyage de la BDD")
        print("=" * 60)
        clear_database(connection)

        # ----------------------------------------------------
        # 5. Import des tables
        # ----------------------------------------------------
        #
        # L'ordre est important :
        #
        # brands/categories/nutrients
        #       ↓
        # products
        #       ↓
        # products_categories
        #
        # afin de respecter les FOREIGN KEY.
        # ----------------------------------------------------

        import_parquet(
            connection,
            "brands.parquet",
            "brands",
            "name"
        )

        import_parquet(
            connection,
            "categories.parquet",
            "categories",
            "tag",
        )

        import_parquet(
            connection,
            "nutrients.parquet",
            "nutrients",
            "code, energy, energy_kcal, proteins, carbohydrates, sugars, fat, saturated_fat, fiber, salt",
)

        import_parquet(
            connection,
            "products.parquet",
            "products",
        )

        import_parquet(
            connection,
            "products_categories.parquet",
            "products_categories",
        )

        # ----------------------------------------------------
        # 6. Contrôle final
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("Contrôle final")
        print("=" * 60)

        tables = [
            "brands",
            "categories",
            "nutrients",
            "products",
            "products_categories",
        ]

        for table in tables:

            count = connection.execute(
                f"""
                SELECT COUNT(*)
                FROM {POSTGRES_DB_ALIAS}.public.{table};
                """
            ).fetchone()[0]

            print(f"{table:25} {count:>12} lignes")

        print()
        print("=" * 60)
        print("Import terminé avec succès.")
        print("=" * 60)

    finally:

        connection.close()

        print("\nConnexion fermée.")


# ============================================================
# Point d'entrée
# ============================================================

if __name__ == "__main__":
    main()