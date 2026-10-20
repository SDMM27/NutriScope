"""Préparation commune du périmètre France, du rapport et des fichiers SQL."""

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

try:  # module `src.*` depuis la racine ou modules frères depuis `src/`
    from src.cleaning import nettoyer
    from src.report import generer_rapport
except ModuleNotFoundError:  # compatibilité avec les scripts historiques exécutés dans src/
    from cleaning import nettoyer
    from report import generer_rapport


def _sql_chaine(chemin: Path) -> str:
    """Protège un chemin local utilisé dans une chaîne SQL DuckDB."""
    return str(chemin.resolve()).replace("'", "''")


def _colonnes_source(connexion: duckdb.DuckDBPyConnection, source: Path) -> set[str]:
    return set(connexion.execute(
        f"DESCRIBE SELECT * FROM read_parquet('{_sql_chaine(source)}')"
    ).df()["column_name"])


def extraire_brut(source: str | Path, destination: str | Path) -> pd.DataFrame:
    """Projette en un scan DuckDB les champs utiles à TP9 et les met en cache.

    La projection France est écrite une fois en Parquet intermédiaire. Le
    DataFrame est limité à ces champs; aucun des cinq fichiers SQL n'est
    produit directement depuis les données non nettoyées.
    """
    source, destination = Path(source), Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    connexion = duckdb.connect()
    try:
        colonnes = _colonnes_source(connexion, source)
        obligatoires = {"code", "countries_tags", "nutriments", "food_groups_tags"}
        absentes = obligatoires - colonnes
        if absentes:
            raise ValueError(f"Colonnes Open Food Facts indispensables absentes : {sorted(absentes)}")

        def champ(colonne: str, alias: str | None = None) -> str:
            nom = alias or colonne
            return f'"{colonne}" AS "{nom}"' if colonne in colonnes else f'NULL AS "{nom}"'

        selections = [
            champ("code"), champ("completeness"), champ("created_t"),
            champ("last_modified_t"), champ("additives_n"), champ("nova_group"),
            champ("nutriscore_grade"), champ("nutriscore_score"),
            champ("food_groups_tags"), champ("pnns_groups_1"),
            # Frontière explicite : les règles existantes utilisent les noms OFF.
            champ("product_name", "product_name"),
            champ("brands_tags", "brands_tags"),
        ]
        nutriments = {
            "energy-kcal_100g": "energy-kcal",
            "energy_100g": "energy",
            "fat_100g": "fat",
            "saturated-fat_100g": "saturated-fat",
            "carbohydrates_100g": "carbohydrates",
            "sugars_100g": "sugars",
            "fiber_100g": "fiber",
            "proteins_100g": "proteins",
            "salt_100g": "salt",
            "sodium_100g": "sodium",
        }
        selections.extend(
            f'''list_extract(list_filter(nutriments, x -> x.name = '{nom}'), 1)."100g" AS "{cible}"'''
            for cible, nom in nutriments.items()
        )
        requete = f"""
            SELECT {', '.join(selections)}
            FROM read_parquet('{_sql_chaine(source)}')
            WHERE 'en:france' IN countries_tags
        """
        connexion.execute(
            f"COPY ({requete}) TO '{_sql_chaine(destination)}' (FORMAT PARQUET)"
        )
    finally:
        connexion.close()

    brut = pd.read_parquet(destination)
    # Les noms de présentation restent informatifs, tandis que les colonnes
    # consommées par les règles gardent le vocabulaire attendu du module TP9.
    brut["name"] = brut["product_name"].map(_texte_langue)
    brut["brand_name"] = brut["brands_tags"].map(_premier_tag)
    return brut


def _texte_langue(valeur):
    if isinstance(valeur, (list, tuple, np.ndarray)) and len(valeur):
        francais = [item.get("text") for item in valeur if isinstance(item, dict) and item.get("lang") == "fr"]
        return francais[0] if francais else (valeur[0].get("text") if isinstance(valeur[0], dict) else None)
    return None


def _premier_tag(valeur):
    return valeur[0] if isinstance(valeur, (list, tuple, np.ndarray)) and len(valeur) else None


def vers_tables_sql(propre: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Construit les cinq relations uniquement depuis les produits retenus."""
    produits = propre[["code", "completeness", "name", "brand_name", "nutriscore_grade", "nutriscore_score"]].copy()
    produits["code"] = produits["code"].astype("string")
    produits["nutriscore_grade"] = produits["nutriscore_grade"].replace({"": None})
    produits.loc[~produits["nutriscore_grade"].isin(
        ["a", "b", "c", "d", "e", "not-applicable", "unknown"]
    ), "nutriscore_grade"] = pd.NA
    marques = (produits.loc[produits["brand_name"].notna(), ["brand_name"]]
               .drop_duplicates().rename(columns={"brand_name": "name"}).reset_index(drop=True))

    relations = []
    for code, tags in propre[["code", "food_groups_tags"]].itertuples(index=False, name=None):
        if isinstance(tags, (list, tuple, np.ndarray)):
            relations.extend((str(code), str(tag)) for tag in tags if tag is not None and str(tag).strip())
    pc = pd.DataFrame(relations, columns=["code", "tag"]).drop_duplicates()
    categories = pc[["tag"]].drop_duplicates().reset_index(drop=True)

    nutrition_source_vers_sql = {
        "energy_100g": "energy", "energy-kcal_100g": "energy_kcal",
        "proteins_100g": "proteins", "carbohydrates_100g": "carbohydrates",
        "sugars_100g": "sugars", "fat_100g": "fat",
        "saturated-fat_100g": "saturated_fat", "fiber_100g": "fiber",
        "salt_100g": "salt",
    }
    nutriments = propre[["code", *nutrition_source_vers_sql]].rename(columns=nutrition_source_vers_sql).copy()
    colonnes_num = list(nutrition_source_vers_sql.values())
    nutriments[colonnes_num] = nutriments[colonnes_num].apply(pd.to_numeric, errors="coerce")
    nutriments = nutriments.replace([float("inf"), float("-inf")], pd.NA)
    # Limites et précision des colonnes NUMERIC du schéma PostgreSQL.
    for colonne in ["proteins", "carbohydrates", "sugars", "fat", "saturated_fat", "fiber", "salt"]:
        nutriments.loc[~nutriments[colonne].between(0, 100), colonne] = pd.NA
    for colonne in ["energy", "energy_kcal"]:
        nutriments.loc[~nutriments[colonne].between(0, 99999.99), colonne] = pd.NA
    def arrondir_sql(valeur):
        if pd.isna(valeur):
            return pd.NA
        return float(Decimal(str(valeur)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    nutriments[colonnes_num] = nutriments[colonnes_num].apply(
        lambda colonne: colonne.map(arrondir_sql)
    )

    return {
        # brand_name est consommée par insert_products pour résoudre brand_id.
        "products": produits,
        "brands": marques,
        "categories": categories,
        "products_categories": pc,
        "nutrients": nutriments,
    }


def preparer_pipeline(source="data/food.parquet", repertoire="data/extracts",
                      rapport="docs/data/rapport_nettoyage.md"):
    """Exécute une fois extraction → TP9 → rapport → cinq fichiers SQL."""
    repertoire = Path(repertoire)
    brut = extraire_brut(source, repertoire / "france_brut.parquet")
    propre, journal = nettoyer(brut)
    generer_rapport(brut, propre, journal, rapport, source=str(source))
    tables = vers_tables_sql(propre)
    for nom, table in tables.items():
        table.to_parquet(repertoire / f"{nom}.parquet", index=False)
    return brut, propre, journal, tables
