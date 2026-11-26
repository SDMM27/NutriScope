try:
    from src.config.settings import INPUT_DIR, POSTGRES_DB_ALIAS
    from src.storage.commun import sql_chemin
except ModuleNotFoundError:
    from config.settings import INPUT_DIR, POSTGRES_DB_ALIAS
    from storage.commun import sql_chemin


def insert_brands(connection, dossier_import=INPUT_DIR):
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
            '{sql_chemin(dossier_import / "brands.parquet")}'
        )
        WHERE name IS NOT NULL;
        """
    )
