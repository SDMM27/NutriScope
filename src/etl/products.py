from config.settings import INPUT_DIR, POSTGRES_DB_ALIAS


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