try:
    from src.config.settings import INPUT_DIR, POSTGRES_DB_ALIAS
    from src.storage.commun import sql_chemin
except ModuleNotFoundError:
    from config.settings import INPUT_DIR, POSTGRES_DB_ALIAS
    from storage.commun import sql_chemin


def insert_categories(connection, dossier_import=INPUT_DIR):
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
            '{sql_chemin(dossier_import / "categories.parquet")}'
        )
        WHERE tag IS NOT NULL;
        """
    )
