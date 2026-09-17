from config.settings import INPUT_DIR, POSTGRES_DB_ALIAS


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