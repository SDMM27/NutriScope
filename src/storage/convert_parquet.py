"""CSV nettoyé (TP 9) → Parquet partitionné par rayon.

    python -m src.storage.convert_parquet [--csv data/clean/produits_nettoyes.csv]

Le CSV est produit par `preparer_csv.py`, à lancer avant.

1. lit le CSV nettoyé (qui porte déjà la colonne `rayon`), avec des types explicites ;
2. écrit `data/parquet/produits/rayon=<slug>/…` (COPY PARTITION_BY, ZSTD) ;
3. écrit `schema_produits.json` à côté du dossier.

Données : © Open Food Facts contributors — ODbL.
"""

import argparse
import json
import shutil
from pathlib import Path

import duckdb

from src.storage.commun import CSV_NETTOYE, LICENCE, PARQUET_PRODUITS, SCHEMA_PRODUITS, sql_chemin

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


def nommer_fichiers(dossier: Path) -> None:
    """DuckDB écrit `data_0.parquet` dans chaque `rayon=<slug>/` : on le renomme `<slug>.parquet`."""
    for partition in dossier.glob("rayon=*"):
        fichiers = list(partition.glob("*.parquet"))
        if len(fichiers) != 1:
            raise RuntimeError(f"{partition.name} : {len(fichiers)} fichiers Parquet, attendu 1")
        slug = partition.name.removeprefix("rayon=")
        fichiers[0].rename(partition / f"{slug}.parquet")


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
        nommer_fichiers(dossier)
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
    parser.add_argument("--csv", default=CSV_NETTOYE)
    parser.add_argument("--sortie", default=PARQUET_PRODUITS)
    parser.add_argument("--schema", default=SCHEMA_PRODUITS)
    args = parser.parse_args()

    lignes = convertir(args.csv, args.sortie, args.schema)
    rayons = sorted(p.name for p in Path(args.sortie).iterdir())
    print(f"{lignes:,} lignes Parquet, {len(rayons)} partitions")
    print("\n".join(rayons))


if __name__ == "__main__":
    main()
