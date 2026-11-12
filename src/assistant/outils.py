"""Outil chercher_produit exposé au LLM, avec validation stricte des arguments."""
import json
import re

from src.assistant.catalogue import construire_fiche, normaliser

SCHEMA_CHERCHER_PRODUIT = {
    "type": "function",
    "function": {
        "name": "chercher_produit",
        "description": (
            "Recherche dans le catalogue NutriScope et renvoie les fiches des produits "
            "trouvés (nutriments pour 100 g, Nutri-Score). Si un code est fourni, il "
            "prime sur le nom."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "nom": {"type": "string", "description": "Nom (ou partie du nom) du produit."},
                "code": {"type": "string", "description": "Code-barres exact du produit."},
                "limite": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 5,
                    "description": "Nombre maximal de fiches renvoyées (défaut 3).",
                },
            },
            "additionalProperties": False,
        },
    },
}

_CLES_AUTORISEES = {"nom", "code", "limite"}


def valider_arguments(arguments):
    """Renvoie (arguments_normalisés, None) ou (None, message d'erreur). Ne lève jamais."""
    try:
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except ValueError:
                return None, "JSON illisible : les arguments doivent être un objet JSON valide"
        if not isinstance(arguments, dict):
            return None, "les arguments doivent être un objet (dictionnaire)"
        inconnus = sorted(str(k) for k in arguments if k not in _CLES_AUTORISEES)
        if inconnus:
            return None, f"argument inconnu : {', '.join(inconnus)} (autorisés : code, limite, nom)"
        valeurs = {}
        for cle in ("nom", "code"):
            v = arguments.get(cle)
            if v is not None and (not isinstance(v, str) or not v.strip()):
                return None, f"l'argument {cle} doit être une chaîne non vide"
            valeurs[cle] = v.strip() if v is not None else None
        if valeurs["nom"] is None and valeurs["code"] is None:
            return None, "il faut fournir au moins nom ou code"
        limite = arguments.get("limite", 3)
        if isinstance(limite, bool) or not isinstance(limite, int):
            return None, "l'argument limite doit être un entier"
        if not 1 <= limite <= 5:
            return None, "l'argument limite doit être compris entre 1 et 5"
        valeurs["limite"] = limite
        return valeurs, None
    except Exception as e:  # dernier recours
        return None, f"arguments invalides : {e}"


def chercher_produit(catalogue, arguments) -> dict:
    """Cherche par code (prioritaire) ou par nom ; renvoie statut, total, fiches."""
    try:
        args, erreur = valider_arguments(arguments)
        if erreur:
            return {"erreur": erreur}
        exact = None
        if args["code"] is not None:
            trouves = catalogue[catalogue["code"] == args["code"]]
        else:
            cible = normaliser(args["nom"])
            mots = re.findall(r"\w+", cible)
            if not mots:
                return {"erreur": "l'argument nom ne contient aucun caractère exploitable"}
            # chaque mot doit figurer dans nom + marque ; filtrage progressif pour rester rapide
            trouves = catalogue
            for mot in mots:
                texte = trouves["nom_normalise"]
                if "marque_normalisee" in trouves.columns:
                    texte = texte + " " + trouves["marque_normalisee"].fillna("")
                trouves = trouves[texte.str.contains(mot, regex=False)]
            exact = (trouves["nom_normalise"] == cible)
        if exact is not None:
            trouves = trouves.assign(_exact=exact)
            trouves = trouves.sort_values(
                ["_exact", "completeness"], ascending=[False, False],
                na_position="last", kind="stable",
            )
        else:
            trouves = trouves.sort_values("completeness", ascending=False, na_position="last", kind="stable")
        total = len(trouves)
        statut = "introuvable" if total == 0 else "ok" if total == 1 else "ambigu"
        produits = [construire_fiche(l) for _, l in trouves.head(args["limite"]).iterrows()]
        return {"statut": statut, "total": total, "produits": produits}
    except Exception as e:  # dernier recours : ne jamais planter la boucle
        return {"erreur": f"erreur interne : {e}"}


OUTILS = {"chercher_produit": chercher_produit}


def executer_outil(nom_outil, arguments, catalogue) -> dict:
    """Exécute un outil du registre ; nom inconnu = erreur renvoyée au modèle."""
    fonction = OUTILS.get(nom_outil) if isinstance(nom_outil, str) else None
    if fonction is None:
        return {"erreur": f"outil inconnu : {nom_outil}"}
    return fonction(catalogue, arguments)
