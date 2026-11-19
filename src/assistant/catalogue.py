"""Chargement du catalogue NutriScope.

Le corrigé lit le CSV du lot de l'atelier (22 produits Open Food Facts réels).
Une équipe branche ici son propre catalogue (Parquet / DuckDB du TP 12 ou base du TP 4) :
seul le format des dictionnaires rendus compte pour la suite.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any

RACINE = Path(__file__).resolve().parents[2]
CATALOGUE_PAR_DEFAUT = RACINE / "data" / "catalogue_off_lot.csv"

NUTRIMENTS_FICHE = ("kcal", "lipides", "satures", "sucres", "fibres", "proteines", "sel")
NUTRIMENTS_CATALOGUE = ("kj", "kcal", "lipides", "satures", "glucides", "sucres", "fibres", "proteines", "sel")


def _nombre(valeur: str | None) -> float | None:
    """Case vide -> None. Jamais 0 par défaut : une valeur inconnue reste inconnue."""
    if valeur is None or str(valeur).strip() == "":
        return None
    return float(str(valeur).replace(",", "."))


def _base(valeur: str | None) -> str | None:
    v = (valeur or "").replace(" ", "").lower()
    return {"100g": "100 g", "100ml": "100 ml"}.get(v)


def charger_catalogue(chemin: str | Path | None = None) -> list[dict[str, Any]]:
    """Rend une liste de produits normalisés (un dictionnaire par produit)."""
    chemin = Path(chemin or os.environ.get("NUTRISCOPE_CATALOGUE", CATALOGUE_PAR_DEFAUT))
    with open(chemin, encoding="utf-8", newline="") as f:
        lignes = list(csv.DictReader(f))
    produits = []
    for ligne in lignes:
        nutriscore = (ligne.get("nutriscore") or "").strip().upper() or None
        produits.append({
            "code": ligne["code"].strip(),
            "nom": ligne["nom"].strip(),
            "marque": (ligne.get("marque") or "").strip() or None,
            "rayon": (ligne.get("rayon") or "").strip() or None,
            "nutriscore": nutriscore if nutriscore in {"A", "B", "C", "D", "E"} else None,
            "base": _base(ligne.get("base")),
            "nutriments": {k: _nombre(ligne.get(k)) for k in NUTRIMENTS_CATALOGUE},
            "ingredients": (ligne.get("ingredients") or "").strip() or None,
            "extrait_le": (ligne.get("extrait_le") or "").strip() or None,
        })
    return produits
