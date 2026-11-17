"""Fiches produits du corpus : un texte court par produit, pour le RAG.

Sous-ensemble retenu (le catalogue entier est trop gros) :
- 5000 produits au plus : le temps de vectorisation sur un portable reste raisonnable ;
- on garde les plus complets (colonne `completeness`) : des fiches utiles, peu de « non renseigné » ;
- Nutri-Score a-e valide, nom et marque renseignés ;
- on ajoute toujours les codes du jeu d'évaluation, même peu complets, pour que
  les questions « produit » aient leur fiche dans le corpus.

Usage : python -m src.corpus.fiches
"""
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.assistant.catalogue import RACINE, charger_catalogue, construire_fiche

NB_PRODUITS = 5000
CODES_EVAL = [
    "3017620422003", "5449000000996", "7622210449283", "3229820129488",
    "3175680011480", "3033710065967", "3168930010265", "3046920022606",
    "8000500310427", "3017760000109", "3270190207924", "5000159407236",
]
NON_RENSEIGNE = "non renseigné"
FICHIER_PRODUITS = RACINE / "data" / "extracts" / "products.parquet"
DOSSIER_SORTIE = RACINE / "data" / "corpus" / "fiches"

# (clé du nutriment, libellé, unité)
LIBELLES = {
    "kcal": ("énergie", "kcal"),
    "lipides": ("matières grasses", "g"),
    "satures": ("dont saturées", "g"),
    "sucres": ("sucres", "g"),
    "sel": ("sel", "g"),
    "fibres": ("fibres", "g"),
    "proteines": ("protéines", "g"),
}


def _nombre(v) -> str:
    """Valeur sans zéros inutiles : 0.0 -> '0', 5.50 -> '5.5'."""
    return f"{v:g}"


def _valeur_texte(v, unite: str) -> str:
    return NON_RENSEIGNE if v is None else f"{_nombre(v)} {unite}"


def fiche_en_texte(fiche: dict, rayon, date_export) -> str:
    """Texte de la fiche. Une valeur None s'écrit « non renseigné », jamais 0."""
    nut = fiche["nutriments"]
    manquants = [cle for cle in LIBELLES if nut.get(cle) is None]
    if fiche.get("nutriscore") is None:
        manquants.insert(0, "Nutri-Score")
    incompletes = f"oui ({', '.join(manquants)})" if manquants else "non"

    kcal = _valeur_texte(nut.get("kcal"), "kcal")
    lipides = _valeur_texte(nut.get("lipides"), "g")
    satures = _valeur_texte(nut.get("satures"), "g")
    valeurs = (
        f"énergie {kcal} ; matières grasses {lipides}, dont saturées {satures} ; "
        f"sucres {_valeur_texte(nut.get('sucres'), 'g')} ; sel {_valeur_texte(nut.get('sel'), 'g')} ; "
        f"fibres {_valeur_texte(nut.get('fibres'), 'g')} ; protéines {_valeur_texte(nut.get('proteines'), 'g')}"
    )
    return "\n".join([
        f"Produit : {fiche.get('nom') or NON_RENSEIGNE} — {fiche.get('marque') or NON_RENSEIGNE}",
        f"Code-barres : {fiche['code']}",
        f"Rayon : {rayon or NON_RENSEIGNE}",
        f"Nutri-Score : {fiche.get('nutriscore') or NON_RENSEIGNE}",
        f"Valeurs pour 100 g : {valeurs}",
        f"Données incomplètes : {incompletes}",
        f"Source : Open Food Facts (licence ODbL), export du {date_export}",
    ])


def _rayon(tags) -> str | None:
    """Premier tag de food_groups_tags sans le préfixe « en: »."""
    if tags is None or len(tags) == 0:
        return None
    return str(tags[0]).removeprefix("en:")


def choisir_produits(cat: pd.DataFrame) -> pd.DataFrame:
    valide = cat[
        cat["nutriscore_grade"].isin(list("abcde"))
        & cat["name"].fillna("").str.strip().ne("")
        & cat["brand_name"].fillna("").str.strip().ne("")
    ]
    top = valide.sort_values("completeness", ascending=False).head(NB_PRODUITS)
    eval_ = cat[cat["code"].isin(CODES_EVAL)]
    return pd.concat([top, eval_]).drop_duplicates("code")


def generer(dossier_sortie=DOSSIER_SORTIE) -> int:
    dossier_sortie = Path(dossier_sortie)
    dossier_sortie.mkdir(parents=True, exist_ok=True)
    date_export = datetime.fromtimestamp(FICHIER_PRODUITS.stat().st_mtime).strftime("%Y-%m-%d")
    cat = charger_catalogue()
    rayons = pd.read_parquet(FICHIER_PRODUITS, columns=["code", "food_groups_tags"])
    rayons = dict(zip(rayons["code"], rayons["food_groups_tags"]))
    produits = choisir_produits(cat)

    with open(dossier_sortie / "metadonnees.jsonl", "w", encoding="utf-8") as meta:
        for _, ligne in produits.iterrows():
            fiche = construire_fiche(ligne)
            rayon = _rayon(rayons.get(ligne["code"]))
            texte = fiche_en_texte(fiche, rayon, date_export)
            (dossier_sortie / f"{fiche['code']}.txt").write_text(texte, encoding="utf-8")
            meta.write(json.dumps({
                "code": fiche["code"],
                "nom": fiche["nom"],
                "marque": fiche["marque"],
                "rayon": rayon,
                "nutriscore": fiche["nutriscore"],
                "source": f"Open Food Facts (licence ODbL), export du {date_export}",
            }, ensure_ascii=False) + "\n")
    return len(produits)


if __name__ == "__main__":
    n = generer()
    absents = [c for c in CODES_EVAL if not (DOSSIER_SORTIE / f"{c}.txt").exists()]
    print(f"{n} fiches écrites dans {DOSSIER_SORTIE}")
    if absents:
        print("Codes d'évaluation absents du catalogue :", ", ".join(absents))
