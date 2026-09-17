import duckdb

from config.settings import DB_CONFIG, POSTGRES_DB_ALIAS


def create_duckdb_connection():
    """
    Crée une connexion DuckDB et charge l'extension PostgreSQL.

    L'extension doit avoir été installée au préalable avec :

        INSTALL postgres;

    Une fois installée, seul LOAD est nécessaire.
    """

    connection = duckdb.connect()

    connection.execute("LOAD postgres;")

    connection_string = (
        f"host={DB_CONFIG['host']} "
        f"port={DB_CONFIG['port']} "
        f"dbname={DB_CONFIG['dbname']} "
        f"user={DB_CONFIG['user']} "
        f"password={DB_CONFIG['password']}"
    )

    connection.execute(
        f"""
        ATTACH '{connection_string}'
        AS {POSTGRES_DB_ALIAS}
        (TYPE postgres);
        """
    )

    return connection