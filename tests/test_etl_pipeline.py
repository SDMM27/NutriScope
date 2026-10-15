"""Tests d'intégration locaux de l'extraction jusqu'aux Parquets SQL."""

import duckdb
import pandas as pd

from src.etl_pipeline import preparer_pipeline, vers_tables_sql


def test_preparation_pipeline_nettoie_et_conserve_integrite(tmp_path):
    source = tmp_path / "source.parquet"
    connexion = duckdb.connect()
    connexion.execute("""
        CREATE TABLE source AS
        SELECT * FROM (VALUES
          (' ' || '0001' || chr(0) || ' ', 0.5, ['en:france'],
           [struct_pack(name := 'energy-kcal', "100g" := 999.0),
            struct_pack(name := 'energy', "100g" := 4182.0),
            struct_pack(name := 'fat', "100g" := 10.0),
            struct_pack(name := 'saturated-fat', "100g" := 3.0),
            struct_pack(name := 'carbohydrates', "100g" := 20.0),
            struct_pack(name := 'sugars', "100g" := 150.0),
            struct_pack(name := 'fiber', "100g" := 2.0),
            struct_pack(name := 'proteins', "100g" := 10.0),
            struct_pack(name := 'salt', "100g" := 1.0),
            struct_pack(name := 'sodium', "100g" := 0.4)],
           ['en:snacks'], 'a', 5, [struct_pack(lang := 'fr', "text" := 'Produit ancien')], ['marque-a'],
           100, 10, 3, 2),
          ('0001', 0.9, ['en:france'],
           [struct_pack(name := 'energy-kcal', "100g" := 999.0),
            struct_pack(name := 'energy', "100g" := 4182.0),
            struct_pack(name := 'fat', "100g" := 10.0),
            struct_pack(name := 'saturated-fat', "100g" := 3.0),
            struct_pack(name := 'carbohydrates', "100g" := 20.0),
            struct_pack(name := 'sugars', "100g" := 150.0),
            struct_pack(name := 'fiber', "100g" := 2.0),
            struct_pack(name := 'proteins', "100g" := 10.0),
            struct_pack(name := 'salt', "100g" := 1.0),
            struct_pack(name := 'sodium', "100g" := 0.4)],
           ['en:beverages'], 'b', 7, [struct_pack(lang := 'fr', "text" := 'Produit conservé')], ['marque-b'],
           200, 20, 4, 3),
          ('0002', 0.8, ['en:belgium'],
           []::STRUCT(name VARCHAR, "100g" DOUBLE)[], ['en:hors-france'], 'c', 8,
           [struct_pack(lang := 'fr', "text" := 'Hors France')], ['marque-c'], 300, 30, 5, 3)
        ) AS t(code, completeness, countries_tags, nutriments, food_groups_tags,
               nutriscore_grade, nutriscore_score, product_name, brands_tags,
               created_t, last_modified_t, additives_n, nova_group)
    """)
    connexion.execute(f"COPY source TO '{str(source).replace(chr(39), chr(39) * 2)}' (FORMAT PARQUET)")
    connexion.close()

    rapport = tmp_path / "rapport.md"
    brut, propre, journal, tables = preparer_pipeline(
        source, tmp_path / "sortie", rapport
    )

    assert len(brut) == 2  # Le produit belge est écarté avant les règles.
    assert propre["code"].tolist() == ["0001"]
    assert propre.iloc[0]["name"] == "Produit conservé"
    assert propre.iloc[0]["energy-kcal_100g"] == 210
    assert pd.isna(propre.iloc[0]["sugars_100g"])
    assert propre.iloc[0]["food_groups_tags"] == ["en:beverages"]
    assert journal[1].details["doublons_supprimes"] == 1
    assert journal[0].details["codes_normalises"] == 1
    assert journal[0].details["codes_espaces_normalises"] == 1

    assert set(tables) == {"products", "brands", "categories", "products_categories", "nutrients"}
    assert tables["products"]["code"].tolist() == ["0001"]
    assert tables["products"]["brand_name"].tolist() == ["marque-b"]
    assert {"code", "completeness", "name", "brand_name", "nutriscore_grade", "nutriscore_score"} <= set(tables["products"].columns)
    assert tables["brands"]["name"].tolist() == ["marque-b"]
    assert tables["categories"]["tag"].tolist() == ["en:beverages"]
    assert tables["products_categories"].to_dict("records") == [
        {"code": "0001", "tag": "en:beverages"}
    ]
    assert tables["nutrients"].iloc[0]["energy_kcal"] == 210
    assert pd.isna(tables["nutrients"].iloc[0]["sugars"])
    for nom in set(tables):
        assert (tmp_path / "sortie" / f"{nom}.parquet").is_file()
    contenu_rapport = rapport.read_text(encoding="utf-8")
    assert "Lignes touchées par règle" in contenu_rapport
    assert "| lignes | 2 | 1 | -1 |" in contenu_rapport


def test_mapping_sql_convertit_nan_en_null_et_borne_aux_contraintes():
    propre = pd.DataFrame({
        "code": pd.Series(["0007"], dtype="string"),
        "completeness": [0.8], "name": ["Produit"], "brand_name": [None],
        "nutriscore_grade": ["a"], "nutriscore_score": [1],
        "food_groups_tags": [["en:test"]],
        "energy_100g": [float("nan")], "energy-kcal_100g": [12.345],
        "proteins_100g": [101.0], "carbohydrates_100g": [-1.0],
        "sugars_100g": [None], "fat_100g": [1.0],
        "saturated-fat_100g": [1.0], "fiber_100g": [1.0], "salt_100g": [1.0],
    })
    tables = vers_tables_sql(propre)
    assert tables["products"]["code"].iloc[0] == "0007"
    assert pd.isna(tables["nutrients"]["energy"].iloc[0])
    assert tables["nutrients"]["energy_kcal"].iloc[0] == 12.35
    assert pd.isna(tables["nutrients"]["proteins"].iloc[0])
    assert pd.isna(tables["nutrients"]["carbohydrates"].iloc[0])
