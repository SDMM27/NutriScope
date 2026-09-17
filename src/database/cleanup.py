from sqlalchemy import create_engine, text

from config.settings import DB_CONFIG
from utils.timer import timer, print_duration


def clear_database():
    """
    Vide toutes les tables NutriScope.

    Le TRUNCATE est exécuté directement par PostgreSQL
    via SQLAlchemy afin d'éviter le surcoût du connecteur
    PostgreSQL de DuckDB.
    """

    start = timer()

    connection_string = (
        f"postgresql+psycopg2://"
        f"{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}"
        f"/{DB_CONFIG['dbname']}"
    )

    engine = create_engine(connection_string)

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                TRUNCATE TABLE
                    nutrients,
                    products_categories,
                    products,
                    categories,
                    brands
                CASCADE;
                """
            )
        )

    engine.dispose()

    print_duration("Nettoyage de la BDD", start)