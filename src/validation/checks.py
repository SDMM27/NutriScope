from pathlib import Path

try:
    from src.config.settings import INPUT_DIR, REQUIRED_FILES, POSTGRES_DB_ALIAS
    from src.utils.timer import timer, print_duration
except ModuleNotFoundError:  # exécution de src/load_database.py
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


def check_product_codes_unique(connection, parquet_path: str | Path | None = None):
    """Refuse l'import si le Parquet produits contient une clé invalide ou dupliquée.

    Ce contrôle doit être exécuté avant `clear_database` afin qu'un fichier
    incohérent ne puisse pas vider les tables avant d'être rejeté.
    """
    parquet_path = Path(parquet_path or INPUT_DIR / "products.parquet")
    chemin_sql = str(parquet_path.resolve()).replace("'", "''")

    codes_invalides, lignes_dupliquees = connection.execute(
        f"""
        SELECT
            COUNT(*) FILTER (
                WHERE code IS NULL OR TRIM(code) = ''
            ),
            COUNT(code) - COUNT(DISTINCT code)
        FROM read_parquet('{chemin_sql}')
        """
    ).fetchone()

    erreurs = []
    if codes_invalides:
        nom = "code nul ou vide" if codes_invalides == 1 else "codes nuls ou vides"
        erreurs.append(f"{codes_invalides} {nom}")
    if lignes_dupliquees:
        nom = "ligne en doublon" if lignes_dupliquees == 1 else "lignes en doublon"
        erreurs.append(f"{lignes_dupliquees} {nom}")

    if erreurs:
        raise ValueError(
            "Chargement annulé avant le vidage de la base : "
            + "; ".join(erreurs)
            + "."
        )

    print("Les codes produits sont présents et uniques.")


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
