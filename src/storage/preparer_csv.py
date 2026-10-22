"""Données brutes (extrait France) → CSV nettoyé (TP 9), étape préalable à la conversion Parquet.

    python -m src.storage.preparer_csv [--brut data/extracts/france_brut.parquet] [--csv data/clean/produits_nettoyes.csv]

1. applique `nettoyer()` au brut ;
2. ajoute rayon, sous-rayon, nom et marque, et écrit le CSV nettoyé
   (lu par `convert_parquet.py` et par le benchmark).

Données : © Open Food Facts contributors — ODbL.
"""

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.cleaning import lire_brut, nettoyer
from src.storage.commun import BRUT, CSV_NETTOYE
from src.storage.convert_parquet import SCHEMA

RAYON_INCONNU = "unknown"
# libellés pnns_groups_1 de l'export CSV dont le slug diffère du food group OFF
ALIAS_RAYONS = {"fat-and-sauces": "fats-and-sauces", "baby-foods": "baby-foods-and-milks"}


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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--brut", default=BRUT, help="extrait France (sortie de extract_perimeter.py)")
    parser.add_argument("--csv", default=CSV_NETTOYE)
    args = parser.parse_args()

    lignes = ecrire_csv_nettoye(args.brut, args.csv)
    print(f"{lignes:,} lignes nettoyées -> {args.csv}")


if __name__ == "__main__":
    main()
