"""Bloc 3 — famille 1 : une fiche texte par produit du catalogue.

Usage : python -m src.corpus.fiches [--catalogue data/catalogue_off_lot.csv] [--sortie data/corpus/fiches]
Écrit <code>.txt pour chaque produit et metadonnees.jsonl (une ligne JSON par produit).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.assistant.catalogue import charger_catalogue

NON_RENSEIGNE = "non renseigné"
LIBELLES = [  # (clé, libellé, unité) — ordre de lecture d'une étiquette
    ("kcal", "énergie", "kcal"),
    ("lipides", "matières grasses", "g"),
    ("satures", "dont acides gras saturés", "g"),
    ("glucides", "glucides", "g"),
    ("sucres", "dont sucres", "g"),
    ("fibres", "fibres", "g"),
    ("proteines", "protéines", "g"),
    ("sel", "sel", "g"),
]


def formater(valeur: float | None, unite: str) -> str:
    """12.0 -> « 12 g », 143.333 -> « 143.3 kcal », None -> « non renseigné ». Jamais 0 inventé."""
    if valeur is None:
        return NON_RENSEIGNE
    arrondi = round(valeur, 1) if abs(valeur) >= 10 else round(valeur, 3)
    return f"{arrondi:g} {unite}"


def fiche_texte(produit: dict[str, Any], source: str = "Open Food Facts (licence ODbL)") -> str:
    base = produit.get("base") or "100 g"
    n = produit["nutriments"]
    manquants = [libelle for cle, libelle, _ in LIBELLES if n.get(cle) is None]
    if produit.get("nutriscore") is None:
        manquants.insert(0, "Nutri-Score")
    valeurs = " ; ".join(f"{libelle} {formater(n.get(cle), unite)}" for cle, libelle, unite in LIBELLES)
    lignes = [
        f"Produit : {produit['nom']}" + (f" — {produit['marque']}" if produit.get("marque") else ""),
        f"Code-barres : {produit['code']}",
        f"Rayon : {produit.get('rayon') or NON_RENSEIGNE}",
        f"Nutri-Score : {produit.get('nutriscore') or NON_RENSEIGNE}",
        f"Valeurs pour {base} : {valeurs}",
        "Données incomplètes : " + (f"oui ({', '.join(manquants)})" if manquants else "non"),
    ]
    if produit.get("ingredients"):
        lignes.append(f"Ingrédients : {produit['ingredients']}")
    date = f", export du {produit['extrait_le']}" if produit.get("extrait_le") else ""
    lignes.append(f"Source : {source}{date}")
    return "\n".join(lignes) + "\n"


def metadonnees(produit: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"fiche:{produit['code']}",
        "code": produit["code"],
        "nom": produit["nom"],
        "marque": produit.get("marque"),
        "rayon": produit.get("rayon"),
        "nutriscore": produit.get("nutriscore"),
        "base": produit.get("base"),
        "source": "Open Food Facts",
        "licence": "ODbL",
        "extrait_le": produit.get("extrait_le"),
    }


def ecrire_fiches(catalogue: list[dict[str, Any]], dossier: Path) -> int:
    dossier.mkdir(parents=True, exist_ok=True)
    with open(dossier / "metadonnees.jsonl", "w", encoding="utf-8") as meta:
        for produit in catalogue:
            (dossier / f"{produit['code']}.txt").write_text(fiche_texte(produit), encoding="utf-8")
            meta.write(json.dumps(metadonnees(produit), ensure_ascii=False) + "\n")
    return len(catalogue)


def main() -> None:
    parser = argparse.ArgumentParser(description="Génère une fiche texte par produit du catalogue.")
    parser.add_argument("--catalogue", default=None)
    parser.add_argument("--sortie", default="data/corpus/fiches")
    args = parser.parse_args()
    n = ecrire_fiches(charger_catalogue(args.catalogue), Path(args.sortie))
    print(f"{n} fiches écrites dans {args.sortie}")


if __name__ == "__main__":
    main()
