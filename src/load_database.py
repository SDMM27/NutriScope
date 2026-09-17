from database.cleanup import clear_database
from database.connection import create_duckdb_connection
from etl.brands import insert_brands
from etl.categories import insert_categories
from etl.products import insert_products
from etl.products_categories import insert_products_categories
from etl.nutrients import insert_nutrients
from utils.timer import timer, elapsed
from validation.checks import check_input_files, final_check


def main():
    total_start = timer()

    print()
    print("=" * 60)
    print("NutriScope - Import Parquet -> PostgreSQL")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Vérification des fichiers
    # --------------------------------------------------------

    print("\nVérification des fichiers...")

    check_input_files()

    print("Tous les fichiers sont présents.")

    # --------------------------------------------------------
    # 2. Connexion
    # --------------------------------------------------------

    print("\nConnexion à PostgreSQL via DuckDB...")

    connection = create_duckdb_connection()

    print("Connexion réussie.")

    try:

        # ----------------------------------------------------
        # 3. Nettoyage
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("Nettoyage de la BDD")
        print("=" * 60)

        clear_database()

        # ----------------------------------------------------
        # 4. Import
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("Import des données")
        print("=" * 60)

        insert_brands(connection)
        insert_categories(connection)
        insert_products(connection)
        insert_products_categories(connection)
        insert_nutrients(connection)

        # ----------------------------------------------------
        # 5. Contrôle final
        # ----------------------------------------------------

        final_check(connection)

        # ----------------------------------------------------
        # 6. Temps total
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("Import terminé avec succès.")
        print("=" * 60)

        print(
            f"\nTemps total : "
            f"{elapsed(total_start):.2f} secondes"
        )

    finally:

        connection.close()

        print("\nConnexion fermée.")


if __name__ == "__main__":
    main()