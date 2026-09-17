from config.settings import INPUT_DIR, POSTGRES_DB_ALIAS


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