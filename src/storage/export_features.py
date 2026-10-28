"""Export d'entraînement figé pour le Nutri-Score (TP 12, étape 5).

    python -m src.storage.export_features [--date AAAAMMJJ] [--force]

Lit la vue `produits` (Parquet partitionné), garde les produits utilisables et écrit
`data/exports/features_nutriscore_<AAAAMMJJ>.parquet` + `features_nutriscore_<AAAAMMJJ>.schema.json`
(un schéma par export : un nouvel export ne réécrit pas la description d'un ancien).
La colonne `split` (TP 13) sépare train et test, stratifiée sur le grade, graine fixée.

Données : © Open Food Facts contributors — ODbL.
"""

import argparse
import hashlib
import json
import subprocess
from datetime import date as Date
from datetime import datetime
from pathlib import Path

import duckdb

from src.storage.commun import EXPORTS, LICENCE, NUTRIMENTS_CLES, PARQUET_PRODUITS, RACINE, creer_vue_produits, sql_chemin

CIBLE = "nutriscore_grade"
IDENTIFIANT = "code"
# split train / test stratifié sur la cible (TP 13) : 20 % de test dans chaque grade
PART_TEST = 0.2
GRAINE = 42

FILTRES_SQL = [
    "nutriscore_grade IN ('a', 'b', 'c', 'd', 'e')",
    *(f'"{n}" IS NOT NULL' for n in NUTRIMENTS_CLES),
    "sugars_100g <= carbohydrates_100g",
    '"saturated-fat_100g" <= fat_100g',
    '"energy-kcal_100g" > 0',
]
PHRASES_FILTRES = [
    "nutriscore_grade entre a et e (unknown, not-applicable et manquant exclus)",
    "les sept nutriments clés (energy-kcal, fat, saturated-fat, carbohydrates, sugars, proteins, salt) renseignés",
    "sucres <= glucides",
    "acides gras saturés <= lipides",
    "énergie > 0 kcal/100 g",
]

SELECTION = """
    code, rayon,
    "energy-kcal_100g", fat_100g, "saturated-fat_100g", carbohydrates_100g, sugars_100g, proteins_100g, salt_100g,
    fiber_100g, additives_n, nova_group,
    CAST(CASE WHEN carbohydrates_100g > 0 THEN sugars_100g / carbohydrates_100g END AS FLOAT) AS ratio_sucres_glucides,
    CAST(CASE WHEN fat_100g > 0 THEN "saturated-fat_100g" / fat_100g END AS FLOAT) AS ratio_satures_lipides,
    CAST(fat_100g * 9 / "energy-kcal_100g" AS FLOAT) AS part_energie_lipides,
    nutriscore_score, nutriscore_grade
"""

# colonne : (unité, description, politique des manquants pour le TP 14)
COLONNES = {
    "code": ("", "Code-barres (texte, zéros de tête conservés). Identifiant : jamais une feature.", "aucun manquant"),
    "rayon": ("", "Food group OFF de niveau 1 (slug), 'unknown' si absent. Catégorielle.", "aucun manquant ('unknown' est une modalité)"),
    "energy-kcal_100g": ("kcal/100 g", "Énergie, > 0 dans cet export.", "aucun manquant (filtre)"),
    "fat_100g": ("g/100 g", "Lipides.", "aucun manquant (filtre)"),
    "saturated-fat_100g": ("g/100 g", "Acides gras saturés, <= lipides.", "aucun manquant (filtre)"),
    "carbohydrates_100g": ("g/100 g", "Glucides.", "aucun manquant (filtre)"),
    "sugars_100g": ("g/100 g", "Sucres, <= glucides.", "aucun manquant (filtre)"),
    "proteins_100g": ("g/100 g", "Protéines.", "aucun manquant (filtre)"),
    "salt_100g": ("g/100 g", "Sel.", "aucun manquant (filtre)"),
    "fiber_100g": ("g/100 g", "Fibres.", "imputer par la médiane du rayon (calculée sur le train seulement) + indicateur de manquant"),
    "additives_n": ("nombre", "Nombre d'additifs déclarés.", "imputer par la médiane du rayon (train seulement) + indicateur de manquant"),
    "nova_group": ("1 à 4", "Degré de transformation NOVA.", "imputer par le mode du rayon (train seulement) + indicateur de manquant"),
    "ratio_sucres_glucides": ("ratio 0-1", "sucres / glucides ; NULL si glucides = 0.", "mettre 0 (sans glucides, pas de sucres) + indicateur de manquant"),
    "ratio_satures_lipides": ("ratio 0-1", "saturés / lipides ; NULL si lipides = 0.", "mettre 0 (sans lipides, pas de saturés) + indicateur de manquant"),
    "part_energie_lipides": ("ratio", "Part de l'énergie venant des lipides : fat * 9 / energy-kcal.", "aucun manquant (énergie > 0)"),
    "nutriscore_score": ("points, -15 à 40", "Score numérique dont dérive le grade. JAMAIS une feature : fuite de la cible.", "aucun manquant"),
    "nutriscore_grade": ("a-e", "Cible : grade Nutri-Score.", "aucun manquant (filtre)"),
    "split": ("train / test", "Jeu figé du TP 13, stratifié sur nutriscore_grade. Jamais une feature.", "aucun manquant"),
}


def _date(valeur) -> Date:
    if isinstance(valeur, Date):
        return valeur
    return datetime.strptime(str(valeur), "%Y%m%d").date()


def sha256(chemin: str | Path) -> str:
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def commit_git() -> str | None:
    try:
        sortie = subprocess.run(["git", "rev-parse", "HEAD"], cwd=RACINE, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return (sortie.stdout.strip() or None) if sortie.returncode == 0 else None


def chemin_schema(fichier: Path) -> Path:
    """`features_nutriscore_<AAAAMMJJ>.parquet` → `features_nutriscore_<AAAAMMJJ>.schema.json`."""
    return fichier.with_suffix(".schema.json")


def exporter(dossier_parquet: str | Path, dossier_sortie: str | Path, date: Date | str, force: bool = False) -> Path:
    """Écrit le Parquet daté et son `<nom>.schema.json` ; refuse d'écraser sans `force`."""
    jour = _date(date)
    dossier_sortie = Path(dossier_sortie)
    fichier = dossier_sortie / f"features_nutriscore_{jour:%Y%m%d}.parquet"
    if fichier.exists() and not force:
        raise FileExistsError(f"{fichier} existe déjà : changer la date ou passer --force")
    dossier_sortie.mkdir(parents=True, exist_ok=True)
    fichier.unlink(missing_ok=True)

    connexion = duckdb.connect()
    try:
        creer_vue_produits(connexion, dossier_parquet)
        connexion.execute("SET threads = 1")  # un seul fil : ordre et octets stables d'une exécution à l'autre
        # Dans chaque grade, les produits sont rangés par md5(code + graine) — un ordre pseudo-aléatoire
        # qui ne dépend que du produit — et les PART_TEST premiers partent en test.
        connexion.execute(f"""
            COPY (
                WITH retenus AS (
                    SELECT {SELECTION} FROM produits
                    WHERE {" AND ".join(f"({f})" for f in FILTRES_SQL)}
                ), tirage AS (
                    SELECT *,
                        row_number() OVER (PARTITION BY {CIBLE} ORDER BY md5(code || ':{GRAINE}'), code) AS rang,
                        count(*) OVER (PARTITION BY {CIBLE}) AS effectif
                    FROM retenus
                )
                SELECT * EXCLUDE (rang, effectif),
                    CASE WHEN rang <= round(effectif * {PART_TEST}) THEN 'test' ELSE 'train' END AS split
                FROM tirage
                ORDER BY code
            ) TO '{sql_chemin(fichier)}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """)
        source = f"read_parquet('{sql_chemin(fichier)}')"
        lignes = connexion.execute(f"SELECT count(*) FROM {source}").fetchone()[0]
        types = dict(connexion.execute(f"SELECT column_name, column_type FROM (DESCRIBE SELECT * FROM {source})").fetchall())
        manquants = connexion.execute(
            "SELECT " + ", ".join(f'count(*) - count("{c}")' for c in types) + f" FROM {source}"
        ).fetchone()
        repartition = dict(connexion.execute(
            f"SELECT {CIBLE}, count(*) FROM {source} GROUP BY {CIBLE} ORDER BY {CIBLE}"
        ).fetchall())
        effectifs_split = {}
        for grade, split, nombre in connexion.execute(
            f"SELECT {CIBLE}, split, count(*) FROM {source} GROUP BY ALL ORDER BY ALL"
        ).fetchall():
            effectifs_split.setdefault(grade, {})[split] = nombre
    finally:
        connexion.close()

    schema = {
        "nom": fichier.name,
        "date_gel": jour.isoformat(),
        "source": "vue `produits` sur le Parquet partitionné par rayon (data/parquet/produits)",
        "commit_git": commit_git(),
        "lignes": lignes,
        "sha256": sha256(fichier),
        "cible": CIBLE,
        "identifiant": IDENTIFIANT,
        "filtres": PHRASES_FILTRES,
        "repartition_cible": repartition,
        "split": {
            "methode": f"stratifié sur {CIBLE} : dans chaque grade, produits rangés par md5(code || ':{GRAINE}'), "
                       f"les {PART_TEST:.0%} premiers en test",
            "graine": GRAINE,
            "part_test": PART_TEST,
            "justification_part_test": "20 % : 80 % des produits pour apprendre, et assez de produits de test "
                                       "dans le grade le plus rare pour des métriques par classe stables.",
            "effectifs_par_grade": effectifs_split,
            "regle_usage": [
                "fit (imputation, normalisation, modèle) sur le train seulement.",
                "Le test n'est regardé qu'une fois, à la fin, pour la note finale.",
                "La validation croisée se fait à l'intérieur du train.",
                "Ne pas recalculer le split : utiliser la colonne split telle quelle.",
            ],
        },
        "colonnes": [
            {
                "nom": nom,
                "type": types[nom],
                "unite": COLONNES[nom][0],
                "description": COLONNES[nom][1],
                "pct_manquants": round(100 * manquants[i] / lignes, 2) if lignes else 0.0,
                "politique_manquants": COLONNES[nom][2],
            }
            for i, nom in enumerate(types)
        ],
        "avertissements": [
            "nutriscore_score n'est JAMAIS une feature : le grade en dérive directement (fuite de la cible).",
            "code est un identifiant, pas une feature.",
        ],
        "licence": LICENCE,
        "usage_prevu": "TP 14 : classification du Nutri-Score, sur le split figé de cet export (voir `split`).",
    }
    chemin_schema(fichier).write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return fichier


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--parquet", default=PARQUET_PRODUITS)
    parser.add_argument("--sortie", default=EXPORTS, help="dossier des exports")
    parser.add_argument("--date", default=None, help="AAAAMMJJ (défaut : aujourd'hui)")
    parser.add_argument("--force", action="store_true", help="écrase un export existant")
    args = parser.parse_args()

    try:
        fichier = exporter(args.parquet, args.sortie, _date(args.date) if args.date else Date.today(), args.force)
    except FileExistsError as erreur:  # export figé : un message, pas une trace Python
        parser.exit(1, f"Refusé : {erreur}\n")
    schema = json.loads(chemin_schema(fichier).read_text(encoding="utf-8"))
    print(f"{fichier} : {schema['lignes']:,} lignes, sha256 {schema['sha256']}")


if __name__ == "__main__":
    main()
