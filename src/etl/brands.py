from config.settings import INPUT_DIR, POSTGRES_DB_ALIAS


def insert_brands(connection):
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
            '{INPUT_DIR / "brands.parquet"}'
        )
        WHERE name IS NOT NULL;
        """
    )