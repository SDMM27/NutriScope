"""Rejoue les cinq contrôles de `sql/controles.sql` sur le Parquet et écrit `docs/data/controle.md`.

    python -m src.storage.run_queries [--parquet data/parquet/produits] [--sql sql/controles.sql]

Données : © Open Food Facts contributors — ODbL.
"""

import argparse
import re
from datetime import date
from numbers import Integral, Real
from pathlib import Path

import duckdb
import pandas as pd

from src.storage.commun import DOCS_DATA, LICENCE, PARQUET_PRODUITS, RACINE, SQL_CONTROLES, creer_vue_produits

MARQUEUR = re.compile(r"^--\s*@nom:\s*(\S+)\s*$", re.MULTILINE)
ESPACE_FINE = " "


def lire_requetes(chemin: str | Path = SQL_CONTROLES) -> dict[str, str]:
    """Découpe le fichier SQL sur les marqueurs `-- @nom: x` ; renvoie {nom: requête}."""
    texte = Path(chemin).read_text(encoding="utf-8")
    marqueurs = list(MARQUEUR.finditer(texte))
    requetes = {}
    for i, m in enumerate(marqueurs):
        fin = marqueurs[i + 1].start() if i + 1 < len(marqueurs) else len(texte)
        requetes[m.group(1)] = texte[m.end():fin].strip()
    return requetes


def executer(dossier_parquet: str | Path = PARQUET_PRODUITS, chemin_sql: str | Path = SQL_CONTROLES) -> dict[str, pd.DataFrame]:
    """Crée la vue `produits`, exécute chaque requête, renvoie {nom: DataFrame}."""
    connexion = duckdb.connect()
    try:
        creer_vue_produits(connexion, dossier_parquet)
        return {nom: connexion.execute(sql).df() for nom, sql in lire_requetes(chemin_sql).items()}
    finally:
        connexion.close()


def _cellule(valeur) -> str:
    if pd.isna(valeur):
        return ""
    if isinstance(valeur, Integral) or (isinstance(valeur, Real) and float(valeur).is_integer()):
        return f"{int(valeur):,}".replace(",", ESPACE_FINE)
    if isinstance(valeur, Real):
        return f"{valeur:,.2f}".replace(",", ESPACE_FINE).replace(".", ",")
    return str(valeur).replace("|", "\\|")


def tableau_markdown(table: pd.DataFrame) -> str:
    lignes = ["| " + " | ".join(map(str, table.columns)) + " |",
              "|" + "|".join("---" for _ in table.columns) + "|"]
    for _, ligne in table.iterrows():
        lignes.append("| " + " | ".join(_cellule(v) for v in ligne) + " |")
    return "\n".join(lignes)


def ecrire_rapport(resultats: dict[str, pd.DataFrame], chemin_md: str | Path = DOCS_DATA / "controle.md",
                   source: str = "data/parquet/produits") -> None:
    """Un tableau Markdown par contrôle."""
    parties = [
        "# Contrôles qualité sur le Parquet (TP 12)",
        f"Données : {LICENCE}.",
        f"Date : {date.today().isoformat()} · source : `{source}` (vue `produits`, requêtes dans `sql/controles.sql`).",
    ]
    for nom, table in resultats.items():
        parties.append(f"## {nom}\n\n{tableau_markdown(table)}")
    chemin = Path(chemin_md)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text("\n\n".join(parties) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--parquet", default=PARQUET_PRODUITS)
    parser.add_argument("--sql", default=SQL_CONTROLES)
    parser.add_argument("--sortie", default=DOCS_DATA / "controle.md")
    args = parser.parse_args()

    resultats = executer(args.parquet, args.sql)
    try:
        source = Path(args.parquet).resolve().relative_to(RACINE).as_posix()
    except ValueError:
        source = Path(args.parquet).as_posix()
    ecrire_rapport(resultats, args.sortie, source)
    print(f"{len(resultats)} contrôles → {args.sortie}")


if __name__ == "__main__":
    main()
