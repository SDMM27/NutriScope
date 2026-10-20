"""Données nettoyées (TP 9) → Parquet partitionné par rayon.

    python -m src.storage.convert_parquet [--brut data/extracts/france_brut.parquet]

1. applique `nettoyer()` au brut et écrit le CSV nettoyé (lu aussi par le benchmark) ;
2. relit ce CSV avec des types explicites et écrit
   `data/parquet/produits/rayon=<slug>/…` (ZSTD) ;
3. écrit `schema_produits.json` à côté du dossier.

Données : © Open Food Facts contributors — ODbL.
"""

import argparse
import json
import re
import shutil
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from src.cleaning import lire_brut, nettoyer
from src.storage.commun import BRUT, CSV_NETTOYE, LICENCE, PARQUET_PRODUITS, SCHEMA_PRODUITS, sql_chemin

RAYON_INCONNU = "unknown"
# libellés pnns_groups_1 de l'export CSV dont le slug diffère du food group OFF
ALIAS_RAYONS = {"fat-and-sauces": "fats-and-sauces", "baby-foods": "baby-foods-and-milks"}

# colonne : (type DuckDB, justification) — l'ordre est celui du Parquet
SCHEMA = {
    "code": ("VARCHAR", "code-barres : texte, garde les zéros de tête"),
    "product_name": ("VARCHAR", "nom affiché (français si disponible)"),
    "brand": ("VARCHAR", "première marque, pour les agrégats par marque"),
    "sous_rayon": ("VARCHAR", "food group de niveau 2 (ex. breakfast-cereals)"),
    "nutriscore_grade": ("VARCHAR", "a-e, unknown, not-applicable : catégoriel"),
    "nutriscore_score": ("SMALLINT", "entier de -15 à 40"),
    "nova_group": ("TINYINT", "entier de 1 à 4"),
    "additives_n": ("SMALLINT", "compteur, quelques dizaines au plus"),
    "completeness": ("FLOAT", "ratio 0-1, la précision simple suffit"),
    "created_t": ("TIMESTAMP", "epoch Unix converti en date lisible"),
    "last_modified_t": ("TIMESTAMP", "epoch Unix converti en date lisible"),
    "energy-kcal_100g": ("FLOAT", "kcal/100 g, 0-900 : FLOAT suffit (7 chiffres)"),
    "energy_100g": ("FLOAT", "kJ/100 g"),
    "fat_100g": ("FLOAT", "g/100 g, 0-100"),
    "saturated-fat_100g": ("FLOAT", "g/100 g, 0-100"),
    "carbohydrates_100g": ("FLOAT", "g/100 g, 0-100"),
    "sugars_100g": ("FLOAT", "g/100 g, 0-100"),
    "fiber_100g": ("FLOAT", "g/100 g, 0-100"),
    "proteins_100g": ("FLOAT", "g/100 g, 0-100"),
    "salt_100g": ("FLOAT", "g/100 g, 0-100"),
    "sodium_100g": ("FLOAT", "g/100 g, 0-40"),
}
EPOCHS = {"created_t", "last_modified_t"}


def slug(texte) -> str | None:
    """'Milk and dairy products' ou 'en:milk-and-dairy-products' → 'milk-and-dairy-products'."""
    if texte is None or pd.isna(texte):
        return None
    s = re.sub(r"^[a-z]{2}:", "", str(texte).strip().lower())
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if not s or s == RAYON_INCONNU:
        return None
    return ALIAS_RAYONS.get(s, s)


def _liste(valeur) -> list:
    if isinstance(valeur, (list, tuple, np.ndarray)):
        return list(valeur)
    if isinstance(valeur, str) and valeur.strip():
        return [v.strip() for v in valeur.split(",") if v.strip()]
    return []


def _nom(valeur):
    """Texte simple (CSV) ou liste [{lang, text}] (Parquet OFF) → nom français si possible."""
    if isinstance(valeur, (list, tuple, np.ndarray)):
        textes = {d.get("lang"): d.get("text") for d in valeur if isinstance(d, dict)}
        return textes.get("fr") or textes.get("main") or next(iter(textes.values()), None)
    return None if valeur is None or pd.isna(valeur) else str(valeur)


def _niveau(groupes, i: int):
    groupes = _liste(groupes)
    return slug(groupes[i]) if len(groupes) > i else None


def preparer(propre: pd.DataFrame) -> pd.DataFrame:
    """Sortie de `nettoyer()` → table plate : rayon, sous-rayon, nom, marque."""
    groupes = propre.get("food_groups_tags", pd.Series(None, index=propre.index))
    pnns = propre.get("pnns_groups_1", pd.Series(None, index=propre.index)).map(slug)
    rayon = pnns.fillna(groupes.map(lambda g: _niveau(g, 0))).fillna(RAYON_INCONNU)

    marques = propre["brands_tags"] if "brands_tags" in propre else propre.get("brands")
    table = pd.DataFrame({
        "code": propre["code"],
        "product_name": propre["product_name"].map(_nom),
        "brand": marques.map(lambda m: next(iter(_liste(m)), None)) if marques is not None else None,
        "sous_rayon": propre.get("pnns_groups_2", pd.Series(None, index=propre.index)).map(slug)
                      .fillna(groupes.map(lambda g: _niveau(g, 1))),
        "rayon": rayon,
    }, index=propre.index)
    for colonne in SCHEMA:
        if colonne not in table:
            table[colonne] = propre[colonne] if colonne in propre else np.nan
    return table[list(SCHEMA) + ["rayon"]]


def ecrire_csv_nettoye(brut_chemin: str | Path, csv_chemin: str | Path) -> int:
    """Nettoie le brut (TP 9) et écrit le CSV nettoyé ; renvoie le nombre de lignes."""
    brut = lire_brut(brut_chemin)
    if "food_groups_tags" not in brut:  # export CSV (échantillon) : rayon porté par pnns_groups_1
        brut["food_groups_tags"] = None
    propre, _ = nettoyer(brut)
    table = preparer(propre)
    Path(csv_chemin).parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(csv_chemin, index=False)
    return len(table)


def _selection() -> str:
    colonnes = []
    for nom, (type_sql, _) in SCHEMA.items():
        source = f'to_timestamp("{nom}")' if nom in EPOCHS else f'"{nom}"'
        colonnes.append(f'CAST({source} AS {type_sql}) AS "{nom}"')
    return ", ".join(colonnes) + ", rayon"


def types_lecture_csv() -> dict[str, str]:
    """Types à poser à chaque lecture du CSV nettoyé (DuckDB)."""
    types = {nom: ("DOUBLE" if nom in EPOCHS else t) for nom, (t, _) in SCHEMA.items()}
    types["rayon"] = "VARCHAR"
    return types


def convertir(csv_chemin: str | Path, dossier: str | Path, schema_chemin: str | Path | None = None) -> int:
    """CSV nettoyé → Parquet partitionné par rayon. Rejouable : le dossier est recréé."""
    dossier = Path(dossier)
    if dossier.exists():
        shutil.rmtree(dossier)
    dossier.mkdir(parents=True)

    connexion = duckdb.connect()
    try:
        connexion.execute(f"""
            COPY (
                SELECT {_selection()}
                FROM read_csv('{sql_chemin(csv_chemin)}', header = true, types = {types_lecture_csv()})
                ORDER BY rayon, code
            ) TO '{sql_chemin(dossier)}'
            (FORMAT PARQUET, PARTITION_BY (rayon), COMPRESSION ZSTD, OVERWRITE_OR_IGNORE)
        """)
        lignes = connexion.execute(
            f"SELECT count(*) FROM read_parquet('{sql_chemin(dossier)}/**/*.parquet', hive_partitioning = true)"
        ).fetchone()[0]
    finally:
        connexion.close()

    ecrire_schema(schema_chemin or dossier.parent / "schema_produits.json", lignes)
    return lignes


def ecrire_schema(chemin: str | Path, lignes: int) -> None:
    schema = {
        "jeu": "produits",
        "licence": LICENCE,
        "partition": "rayon (food group OFF de niveau 1, slug ; 'unknown' si absent)",
        "compression": "ZSTD",
        "lignes": lignes,
        "colonnes": [{"nom": n, "type": t, "justification": j} for n, (t, j) in SCHEMA.items()],
    }
    Path(chemin).write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--brut", default=BRUT, help="extrait France (sortie de extract_perimeter.py)")
    parser.add_argument("--csv", default=CSV_NETTOYE)
    parser.add_argument("--sortie", default=PARQUET_PRODUITS)
    parser.add_argument("--schema", default=SCHEMA_PRODUITS)
    args = parser.parse_args()

    nettoyees = ecrire_csv_nettoye(args.brut, args.csv)
    lignes = convertir(args.csv, args.sortie, args.schema)
    rayons = sorted(p.name for p in Path(args.sortie).iterdir())
    print(f"{nettoyees:,} lignes nettoyées → {lignes:,} lignes Parquet, {len(rayons)} partitions")
    print("\n".join(rayons))


if __name__ == "__main__":
    main()
