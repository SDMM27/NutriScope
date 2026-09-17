from config.settings import INPUT_DIR, REQUIRED_FILES, POSTGRES_DB_ALIAS
from utils.timer import timer, print_duration


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