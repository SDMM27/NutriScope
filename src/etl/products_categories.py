try:
    from src.config.settings import INPUT_DIR, POSTGRES_DB_ALIAS
    from src.storage.commun import sql_chemin
except ModuleNotFoundError:
    from config.settings import INPUT_DIR, POSTGRES_DB_ALIAS
    from storage.commun import sql_chemin


def insert_products_categories(connection, dossier_import=INPUT_DIR):
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
                '{sql_chemin(dossier_import / "products_categories.parquet")}'
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
