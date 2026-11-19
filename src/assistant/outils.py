"""L'outil chercher_produit, conforme au contrat imposé au TP 18.

Arguments : nom (texte, facultatif), code (texte, facultatif, prime sur nom),
limite (entier de 1 à 5, 3 par défaut). Aucun autre argument.
Résultat : {"statut": "ok" | "ambigu" | "introuvable", "total": n, "produits": [fiche, ...]}
ou {"erreur": "<explication>"} si les arguments sont invalides. Jamais d'exception.
"""

from __future__ import annotations

import json
import unicodedata
from typing import Any

from .catalogue import NUTRIMENTS_FICHE, charger_catalogue

ARGUMENTS_PERMIS = {"nom", "code", "limite"}

# Description de l'outil, au format attendu par l'API compatible OpenAI (Ollama, OpenRouter).
SCHEMA_CHERCHER_PRODUIT = {
    "type": "function",
    "function": {
        "name": "chercher_produit",
        "description": (
            "Cherche un produit dans le catalogue NutriScope et rend sa fiche : Nutri-Score et "
            "valeurs nutritionnelles pour 100 g ou 100 ml. Donner le code-barres s'il est connu, "
            "sinon le nom ou une partie du nom."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "nom": {"type": "string", "description": "Nom ou partie du nom du produit."},
                "code": {"type": "string", "description": "Code-barres exact. Prime sur le nom."},
                "limite": {"type": "integer", "minimum": 1, "maximum": 5,
                           "description": "Nombre maximal de fiches (3 par défaut)."},
            },
            "additionalProperties": False,
        },
    },
}


def normaliser(texte: str) -> str:
    """Minuscules, sans accents, espaces réduits : « Pâte À tartiner » -> « pate a tartiner »."""
    sans_accents = unicodedata.normalize("NFKD", texte)
    sans_accents = "".join(c for c in sans_accents if not unicodedata.combining(c))
    return " ".join(sans_accents.lower().split())


def fiche(produit: dict[str, Any]) -> dict[str, Any]:
    """La fiche rendue au modèle : clés du contrat, plus marque et base."""
    nutriments = {k: produit["nutriments"].get(k) for k in NUTRIMENTS_FICHE}
    return {
        "code": produit["code"],
        "nom": produit["nom"],
        "marque": produit["marque"],
        "base": produit["base"],
        "nutriscore": produit["nutriscore"],
        "nutriments": nutriments,
        "donnees_incompletes": produit["nutriscore"] is None or any(v is None for v in nutriments.values()),
    }


def _valider(arguments: Any) -> tuple[dict[str, Any] | None, str | None]:
    """Contrôle des arguments écrits par le modèle : donnée non fiable, jamais exécutée telle quelle."""
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments) if arguments.strip() else {}
        except json.JSONDecodeError:
            return None, "arguments illisibles : le JSON est mal formé"
    if not isinstance(arguments, dict):
        return None, "les arguments doivent être un objet JSON"
    inconnus = set(arguments) - ARGUMENTS_PERMIS
    if inconnus:
        return None, f"argument(s) inconnu(s) : {', '.join(sorted(inconnus))} ; permis : nom, code, limite"
    nom, code = arguments.get("nom"), arguments.get("code")
    if nom is not None and not isinstance(nom, str):
        return None, "nom doit être un texte"
    if code is not None and not isinstance(code, str):
        return None, "code doit être un texte"
    if not (nom and nom.strip()) and not (code and code.strip()):
        return None, "il faut au moins un nom ou un code"
    limite = arguments.get("limite", 3)
    if isinstance(limite, bool) or not isinstance(limite, int) or not 1 <= limite <= 5:
        return None, "limite doit être un entier de 1 à 5"
    return {"nom": nom, "code": code, "limite": limite}, None


def chercher_produit(arguments: Any, catalogue: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Exécute la recherche. Ne lève jamais d'exception sur des arguments invalides."""
    args, erreur = _valider(arguments)
    if erreur:
        return {"erreur": erreur}
    catalogue = catalogue if catalogue is not None else charger_catalogue()

    if args["code"] and args["code"].strip():
        code = args["code"].strip()
        trouves = [p for p in catalogue if p["code"] == code]
    else:
        cherche = normaliser(args["nom"])
        trouves = [p for p in catalogue if cherche in normaliser(p["nom"])]
        if not trouves:  # second essai sur la marque : « Pringles », « Herta »…
            trouves = [p for p in catalogue if p["marque"] and cherche in normaliser(p["marque"])]

    total = len(trouves)
    statut = "introuvable" if total == 0 else ("ok" if total == 1 else "ambigu")
    return {"statut": statut, "total": total, "produits": [fiche(p) for p in trouves[: args["limite"]]]}


OUTILS = {"chercher_produit": chercher_produit}
SCHEMAS = [SCHEMA_CHERCHER_PRODUIT]
