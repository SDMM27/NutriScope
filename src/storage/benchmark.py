"""Benchmark honnête : pandas/CSV, SQLite, DuckDB/Parquet (et DuckDB/CSV) sur trois requêtes.

    python -m src.storage.benchmark [--csv …] [--parquet …] [--sqlite …] [--repetitions 3] [--sortie docs/data/benchmark.md]

Méthode : chaque mesure tourne dans un sous-processus neuf (`--une MOTEUR REQUETE`, mode interne) qui
imprime un JSON ; temps = lecture + requête (imports exclus, SQLite : connexion + requête) ;
pic mémoire du processus ; médiane des temps, maximum des pics. Avant de chronométrer, on vérifie que
les moteurs rendent le même nombre de lignes et la même clé en première ligne.
Coûts de construction : CSV = 0 (sortie du nettoyage) ; SQLite = construction par ce script ;
Parquet = `convertir` relancé sur une copie temporaire.

Données : © Open Food Facts contributors — ODbL.
"""

import argparse
import json
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from src.storage.commun import CSV_NETTOYE, LICENCE, PARQUET_PRODUITS, RACINE, creer_vue_produits, sql_chemin

SQLITE = RACINE / "data/bench/produits.sqlite"
SORTIE = RACINE / "docs/data/benchmark.md"

GRADES = "'a', 'b', 'c', 'd', 'e'"
REQUETES_SQL = {
    "agregat_rayon": """
        SELECT rayon, count(*) AS nb, avg(sugars_100g) AS sucres_moy, avg(salt_100g) AS sel_moy,
               avg(nutriscore_score) AS score_moy
        FROM produits GROUP BY rayon ORDER BY rayon""",
    "filtre_tri": f"""
        SELECT code, product_name, brand, sugars_100g, nutriscore_grade
        FROM produits
        WHERE sous_rayon = 'breakfast-cereals' AND nutriscore_grade IN ({GRADES})
        ORDER BY sugars_100g DESC NULLS LAST, code ASC LIMIT 20""",
    "forte_cardinalite": f"""
        SELECT brand, count(*) AS nb,
               100.0 * sum(CASE WHEN nutriscore_grade IN ({GRADES}) THEN 1 ELSE 0 END) / count(*) AS pct_nutriscore
        FROM produits WHERE brand IS NOT NULL
        GROUP BY brand ORDER BY nb DESC, brand ASC LIMIT 20""",
}
# colonnes lues par pandas pour chaque requête (usecols)
COLONNES_PANDAS = {
    "agregat_rayon": ["rayon", "sugars_100g", "salt_100g", "nutriscore_score"],
    "filtre_tri": ["code", "product_name", "brand", "sugars_100g", "nutriscore_grade", "sous_rayon"],
    "forte_cardinalite": ["brand", "nutriscore_grade"],
}
MOTEURS = ["pandas_csv", "sqlite", "duckdb_parquet", "duckdb_csv"]
GRADES_LISTE = ["a", "b", "c", "d", "e"]


# ---------------------------------------------------------------- moteurs

def _pandas(requete: str, csv: Path) -> list[list]:
    import pandas as pd

    d = pd.read_csv(csv, dtype={"code": "string"}, usecols=COLONNES_PANDAS[requete],
                    keep_default_na=False, na_values=[""])
    if requete == "agregat_rayon":
        g = d.groupby("rayon").agg(nb=("rayon", "size"), sucres=("sugars_100g", "mean"),
                                   sel=("salt_100g", "mean"), score=("nutriscore_score", "mean"))
        return g.reset_index().values.tolist()
    if requete == "filtre_tri":
        d = d[(d["sous_rayon"] == "breakfast-cereals") & d["nutriscore_grade"].isin(GRADES_LISTE)]
        d = d.sort_values(["sugars_100g", "code"], ascending=[False, True], na_position="last").head(20)
        return d[["code", "product_name", "brand", "sugars_100g", "nutriscore_grade"]].values.tolist()
    d = d[d["brand"].notna()].assign(ok=lambda x: x["nutriscore_grade"].isin(GRADES_LISTE))
    g = d.groupby("brand").agg(nb=("brand", "size"), pct=("ok", "mean"))
    g["pct"] *= 100
    return g.reset_index().sort_values(["nb", "brand"], ascending=[False, True]).head(20).values.tolist()


def _sqlite(requete: str, base: Path) -> list[list]:
    import sqlite3

    connexion = sqlite3.connect(base)
    try:
        return [list(ligne) for ligne in connexion.execute(REQUETES_SQL[requete])]
    finally:
        connexion.close()


def _duckdb(requete: str, source: Path, format_source: str) -> list[list]:
    import duckdb

    from src.storage.convert_parquet import types_lecture_csv

    connexion = duckdb.connect()
    try:
        if format_source == "parquet":
            creer_vue_produits(connexion, source)
        else:
            connexion.execute(f"""
                CREATE VIEW produits AS
                SELECT * FROM read_csv('{sql_chemin(source)}', header = true, types = {types_lecture_csv()})
            """)
        return [list(ligne) for ligne in connexion.execute(REQUETES_SQL[requete]).fetchall()]
    finally:
        connexion.close()


def executer(moteur: str, requete: str, chemins: dict[str, Path]) -> list[list]:
    if moteur == "pandas_csv":
        return _pandas(requete, chemins["csv"])
    if moteur == "sqlite":
        return _sqlite(requete, chemins["sqlite"])
    if moteur == "duckdb_parquet":
        return _duckdb(requete, chemins["parquet"], "parquet")
    if moteur == "duckdb_csv":
        return _duckdb(requete, chemins["csv"], "csv")
    raise ValueError(f"moteur inconnu : {moteur}")


# ---------------------------------------------------------------- construction

def construire_sqlite(csv: Path, base: Path, taille_bloc: int = 100_000) -> int:
    """SQLite construit depuis le CSV nettoyé, sans index ; tirets des colonnes remplacés par `_`."""
    import pandas as pd
    import sqlite3

    base.parent.mkdir(parents=True, exist_ok=True)
    base.unlink(missing_ok=True)
    connexion = sqlite3.connect(base)
    lignes = 0
    try:
        for bloc in pd.read_csv(csv, dtype={"code": "string"}, keep_default_na=False, na_values=[""],
                                chunksize=taille_bloc):
            bloc.columns = [c.replace("-", "_") for c in bloc.columns]
            bloc.to_sql("produits", connexion, if_exists="append", index=False)
            lignes += len(bloc)
        connexion.commit()
    finally:
        connexion.close()
    return lignes


def cout_parquet(csv: Path) -> float:
    """Durée de `convertir` relancé sur une copie temporaire (le Parquet de référence n'est pas touché)."""
    from src.storage.convert_parquet import convertir

    with tempfile.TemporaryDirectory() as tmp:
        debut = time.perf_counter()
        convertir(csv, Path(tmp) / "produits")
        return time.perf_counter() - debut


def taille(chemin: Path) -> int:
    if chemin.is_file():
        return chemin.stat().st_size
    return sum(f.stat().st_size for f in chemin.rglob("*") if f.is_file())


# ---------------------------------------------------------------- mesure

def pic_memoire_mo() -> float:
    """Pic de mémoire résidente du processus, en Mo (Windows, Linux, macOS)."""
    if sys.platform == "win32":
        import psutil

        return psutil.Process().memory_info().peak_wset / 2**20
    import resource

    pic = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return pic / 2**20 if sys.platform == "darwin" else pic * 1024 / 2**20


def une_mesure(moteur: str, requete: str, chemins: dict[str, Path]) -> dict:
    """Mode interne : une mesure dans ce processus. `imports` = moteur à importer, rien d'autre."""
    if moteur == "imports":
        import importlib

        for nom in {"pandas_csv": ["pandas"], "sqlite": ["sqlite3"],
                    "duckdb_parquet": ["duckdb"], "duckdb_csv": ["duckdb"]}[requete]:
            importlib.import_module(nom)
        return {"moteur": moteur, "requete": requete, "secondes": 0.0, "lignes": 0,
                "premiere_ligne": [], "pic_mo": pic_memoire_mo()}
    # imports hors chronomètre : on les déclenche avant de mesurer
    if moteur == "pandas_csv":
        import pandas  # noqa: F401
    elif moteur == "sqlite":
        import sqlite3  # noqa: F401
    else:
        import duckdb  # noqa: F401
        from src.storage import convert_parquet  # noqa: F401
    debut = time.perf_counter()
    lignes = executer(moteur, requete, chemins)
    duree = time.perf_counter() - debut
    return {"moteur": moteur, "requete": requete, "secondes": duree, "lignes": len(lignes),
            "premiere_ligne": lignes[0] if lignes else [], "pic_mo": pic_memoire_mo()}


def sous_processus(moteur: str, requete: str, args: argparse.Namespace) -> dict:
    cmd = [sys.executable, "-m", "src.storage.benchmark", "--une", moteur, requete,
           "--csv", str(args.csv), "--parquet", str(args.parquet), "--sqlite", str(args.sqlite)]
    env_utf8 = {"PYTHONIOENCODING": "utf-8"}
    import os

    res = subprocess.run(cmd, cwd=RACINE, capture_output=True, text=True, encoding="utf-8",
                         env={**os.environ, **env_utf8})
    if res.returncode != 0:
        raise RuntimeError(f"{moteur}/{requete} a échoué :\n{res.stderr}")
    return json.loads(res.stdout.strip().splitlines()[-1])


def verifier_coherence(chemins: dict[str, Path]) -> dict[str, int]:
    """Même nombre de lignes et même clé en première ligne pour tous les moteurs, sinon erreur."""
    lignes_par_requete = {}
    for requete in REQUETES_SQL:
        resultats = {m: executer(m, requete, chemins) for m in MOTEURS}
        vus = {m: (len(r), r[0][0] if r else None) for m, r in resultats.items()}
        if len(set(vus.values())) != 1:
            raise RuntimeError(f"résultats différents pour {requete} : {vus}")
        lignes_par_requete[requete] = len(resultats[MOTEURS[0]])
    return lignes_par_requete


# ---------------------------------------------------------------- rapport

def machine() -> list[str]:
    import psutil

    return [f"- Système : {platform.platform()}",
            f"- Processeur : {platform.processor() or 'inconnu'} ({psutil.cpu_count(logical=False)} cœurs physiques, "
            f"{psutil.cpu_count()} logiques)",
            f"- Mémoire vive : {psutil.virtual_memory().total / 2**30:.1f} Go"]


def versions() -> list[str]:
    import duckdb
    import pandas
    import pyarrow
    import sqlite3

    return [f"- Python {platform.python_version()}, pandas {pandas.__version__}, DuckDB {duckdb.__version__}",
            f"- SQLite {sqlite3.sqlite_version}, pyarrow {pyarrow.__version__}"]


def plan_elagage(parquet: Path) -> str:
    """EXPLAIN DuckDB d'une requête filtrée sur la clé de partition."""
    import duckdb

    rayons = sorted(p.name.split("=", 1)[1] for p in parquet.iterdir() if p.is_dir() and "=" in p.name)
    rayon = "beverages" if "beverages" in rayons else rayons[0]
    connexion = duckdb.connect()
    try:
        creer_vue_produits(connexion, parquet)
        plan = connexion.execute(
            f"EXPLAIN SELECT count(*), avg(sugars_100g) FROM produits WHERE rayon = '{rayon}'"
        ).fetchall()[0][1]
    finally:
        connexion.close()
    return f"WHERE rayon = '{rayon}' ({len(rayons)} partitions) :\n\n{plan}"


def ecrire_rapport(args, lignes_csv: int, couts: dict, mesures: dict, references: dict) -> None:
    mo = lambda o: f"{o / 2**20:.1f} Mo"
    sortie = ["# Benchmark : pandas, SQLite, DuckDB", "", f"Données : {LICENCE}", "",
              "## Machine et versions", "", *machine(), *versions(), "",
              "## Jeu mesuré", "",
              f"- {lignes_csv:,} lignes (sortie du nettoyage, TP 9)",
              f"- CSV nettoyé : {mo(taille(args.csv))}",
              f"- Parquet partitionné par rayon (ZSTD) : {mo(taille(args.parquet))}",
              f"- SQLite sans index : {mo(taille(args.sqlite))}", "",
              "## Coût de construction", "",
              "| Support | Durée (s) | Remarque |", "|---|---:|---|",
              "| CSV nettoyé | 0 | sortie du nettoyage, pas de construction propre |",
              f"| SQLite | {couts['sqlite']:.2f} | construit depuis le CSV, sans index |",
              f"| Parquet | {couts['parquet']:.2f} | `convertir` relancé sur une copie temporaire |", "",
              "## Méthode", "",
              "- Chaque mesure tourne dans un sous-processus neuf ; "
              f"{args.repetitions} répétition(s), médiane des temps, maximum des pics mémoire.",
              "- Temps = lecture + requête, imports exclus ; SQLite : connexion + requête (la base est déjà construite).",
              "- pandas lit le CSV avec `dtype={'code': 'string'}` et `usecols` limité aux colonnes utiles à "
              "chaque requête (agrégat : 4 colonnes, filtre et tri : 6, forte cardinalité : 2).",
              "- DuckDB/Parquet lit une vue sur le dossier partitionné ; DuckDB/CSV relit le CSV avec types explicites.",
              "- Pic mémoire : pic de mémoire résidente du processus ; la ligne `imports` donne le poids de "
              "l'interpréteur et des bibliothèques seuls.",
              "- Avant de chronométrer, tous les moteurs rendent le même nombre de lignes et la même clé en première ligne.",
              "", "## Résultats", "",
              "| Requête | Moteur | Temps médian (s) | Pic mémoire (Mo) |", "|---|---|---:|---:|"]
    for requete in REQUETES_SQL:
        for moteur in MOTEURS:
            m = mesures[(moteur, requete)]
            sortie.append(f"| {requete} | {moteur} | {m['secondes']:.3f} | {m['pic_mo']:.0f} |")
    for moteur in MOTEURS:
        sortie.append(f"| (référence) imports | {moteur} | – | {references[moteur]:.0f} |")
    sortie += ["", "### Ratio pandas_csv / duckdb_parquet", "", "| Requête | Ratio des temps |", "|---|---:|"]
    for requete in REQUETES_SQL:
        ratio = mesures[("pandas_csv", requete)]["secondes"] / mesures[("duckdb_parquet", requete)]["secondes"]
        sortie.append(f"| {requete} | ×{ratio:.1f} |")
    sortie += ["", "## Élagage de partitions (EXPLAIN DuckDB)", "", "```", plan_elagage(args.parquet), "```", "",
               "## Lecture", "", "<!-- lecture -->", ""]
    args.sortie.parent.mkdir(parents=True, exist_ok=True)
    args.sortie.write_text("\n".join(sortie), encoding="utf-8")


def lancer(args: argparse.Namespace) -> None:
    chemins = {"csv": args.csv, "parquet": args.parquet, "sqlite": args.sqlite}
    debut = time.perf_counter()
    lignes_sqlite = construire_sqlite(args.csv, args.sqlite)
    couts = {"sqlite": time.perf_counter() - debut, "parquet": cout_parquet(args.csv)}
    print(f"SQLite construit ({lignes_sqlite:,} lignes) en {couts['sqlite']:.2f} s ; Parquet en {couts['parquet']:.2f} s")

    attendues = verifier_coherence(chemins)
    print("Cohérence vérifiée :", attendues)

    mesures, references = {}, {}
    for moteur in MOTEURS:
        refs = [sous_processus("imports", moteur, args)["pic_mo"] for _ in range(args.repetitions)]
        references[moteur] = max(refs)
        for requete in REQUETES_SQL:
            essais = [sous_processus(moteur, requete, args) for _ in range(args.repetitions)]
            mesures[(moteur, requete)] = {"secondes": statistics.median(e["secondes"] for e in essais),
                                          "pic_mo": max(e["pic_mo"] for e in essais)}
            print(f"{moteur:15s} {requete:18s} {mesures[(moteur, requete)]['secondes']:.3f} s "
                  f"{mesures[(moteur, requete)]['pic_mo']:.0f} Mo")
    ecrire_rapport(args, lignes_sqlite, couts, mesures, references)
    print(f"Rapport écrit : {args.sortie}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--csv", type=Path, default=CSV_NETTOYE)
    parser.add_argument("--parquet", type=Path, default=PARQUET_PRODUITS)
    parser.add_argument("--sqlite", type=Path, default=SQLITE)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--sortie", type=Path, default=SORTIE)
    parser.add_argument("--une", nargs=2, metavar=("MOTEUR", "REQUETE"), help="mode interne : une mesure en JSON")
    args = parser.parse_args()

    if args.une:
        chemins = {"csv": args.csv, "parquet": args.parquet, "sqlite": args.sqlite}
        print(json.dumps(une_mesure(*args.une, chemins), default=str))
    else:
        lancer(args)


if __name__ == "__main__":
    main()
