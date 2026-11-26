try:
    from src.config.settings import INPUT_DIR, POSTGRES_DB_ALIAS
    from src.storage.commun import sql_chemin
except ModuleNotFoundError:
    from config.settings import INPUT_DIR, POSTGRES_DB_ALIAS
    from storage.commun import sql_chemin


def insert_products(connection, dossier_import=INPUT_DIR):
    """
    Importe les produits.

    Étapes :
        1. nettoyage des chaînes
        2. dédoublonnage des codes selon la completeness
        3. recherche de la marque
        4. insertion PostgreSQL
    """

    connection.execute(
        f"""
        WITH cleaned AS (

            SELECT
                REPLACE(code, chr(0), '') AS code,
                completeness,
                REPLACE(name, chr(0), '') AS name,
                REPLACE(brand_name, chr(0), '') AS brand_name,
                REPLACE(nutriscore_grade, chr(0), '')
                    AS nutriscore_grade,
                nutriscore_score

            FROM read_parquet(
                '{sql_chemin(dossier_import / "products.parquet")}'
            )

            WHERE code IS NOT NULL
        ),

        deduplicated AS (

            SELECT *
            FROM cleaned

            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY code
                ORDER BY completeness DESC NULLS LAST
            ) = 1
        )

        INSERT INTO {POSTGRES_DB_ALIAS}.public.products (
            code,
            completeness,
            name,
            brand_id,
            nutriscore_grade,
            nutriscore_score
        )

        SELECT
            p.code,
            p.completeness,
            p.name,
            b.id,
            p.nutriscore_grade,
            p.nutriscore_score

        FROM deduplicated AS p

        LEFT JOIN {POSTGRES_DB_ALIAS}.public.brands AS b
            ON p.brand_name = b.name;
        """
    )
