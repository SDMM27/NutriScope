import os

import duckdb

INPUT_FILE = "data/food.parquet"
OUTPUT_DIR = "data/extracts"

con = duckdb.connect()

print(f"Lecture de {INPUT_FILE}...")

'''
On garde uniquement les produits vendus en France, et on met en forme les
colonnes qui en ont besoin :
- product_name est une liste {lang, text} par langue -> on prend le texte en
  français (ou, à défaut, le premier disponible) ;
- brands_tags est une liste de marques -> on ne garde que la première ;
- nutriments est une liste {name, value, "100g", ...}, un élément par
   nutriment -> pour chaque nutriment qui nous intéresse, on va chercher
   l'élément qui a ce name et on prend sa valeur "100g".
 Ce résultat est stocké dans une table temporaire "scope" : les 5 fichiers de
 sortie sont ensuite chacun une simple sélection dedans, sans avoir à relire
 tout le fichier de 7,7 Go à chaque fois.
'''

con.execute(f"""
    CREATE TEMP TABLE scope AS
    SELECT
        code,
        COALESCE(
            list_extract(list_filter(product_name, x -> x.lang = 'fr'), 1)."text",
            list_extract(product_name, 1)."text"
        ) AS name,
        list_extract(brands_tags, 1) AS brand_name,
        categories_tags,
        nutriscore_grade,
        nutriscore_score,
        list_extract(list_filter(nutriments, x -> x.name = 'energy'), 1)."100g" AS energy,
        list_extract(list_filter(nutriments, x -> x.name = 'energy-kcal'), 1)."100g" AS energy_kcal,
        list_extract(list_filter(nutriments, x -> x.name = 'proteins'), 1)."100g" AS proteins,
        list_extract(list_filter(nutriments, x -> x.name = 'carbohydrates'), 1)."100g" AS carbohydrates,
        list_extract(list_filter(nutriments, x -> x.name = 'sugars'), 1)."100g" AS sugars,
        list_extract(list_filter(nutriments, x -> x.name = 'fat'), 1)."100g" AS fat,
        list_extract(list_filter(nutriments, x -> x.name = 'saturated-fat'), 1)."100g" AS saturated_fat,
        list_extract(list_filter(nutriments, x -> x.name = 'fiber'), 1)."100g" AS fiber,
        list_extract(list_filter(nutriments, x -> x.name = 'salt'), 1)."100g" AS salt
    FROM '{INPUT_FILE}'
    WHERE 'en:france' IN countries_tags
""")

os.makedirs(OUTPUT_DIR, exist_ok=True)

con.execute(f"""
    COPY (
        SELECT code, name, brand_name, nutriscore_grade, nutriscore_score
        FROM scope
    ) TO '{OUTPUT_DIR}/products.parquet' (FORMAT PARQUET)
""")

con.execute(f"""
    COPY (
        SELECT DISTINCT brand_name AS name
        FROM scope
        WHERE brand_name IS NOT NULL
    ) TO '{OUTPUT_DIR}/brands.parquet' (FORMAT PARQUET)
""")

con.execute(f"""
    COPY (
        SELECT DISTINCT unnest(categories_tags) AS tag
        FROM scope
        WHERE categories_tags IS NOT NULL
    ) TO '{OUTPUT_DIR}/categories.parquet' (FORMAT PARQUET)
""")

con.execute(f"""
    COPY (
        SELECT code, unnest(categories_tags) AS tag
        FROM scope
        WHERE categories_tags IS NOT NULL
    ) TO '{OUTPUT_DIR}/products_categories.parquet' (FORMAT PARQUET)
""")

con.execute(f"""
    COPY (
        SELECT code, energy, energy_kcal, proteins, carbohydrates, sugars,
               fat, saturated_fat, fiber, salt
        FROM scope
    ) TO '{OUTPUT_DIR}/nutrients.parquet' (FORMAT PARQUET)
""")

for filename in [
    "products.parquet",
    "brands.parquet",
    "categories.parquet",
    "products_categories.parquet",
    "nutrients.parquet",
]:
    path = f"{OUTPUT_DIR}/{filename}"
    n_rows = con.sql(f"SELECT count(*) FROM '{path}'").fetchone()[0]
    print(f"  {filename} : {n_rows:,} lignes")
