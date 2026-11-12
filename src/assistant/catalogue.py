"""Chargement du catalogue produits/nutriments et construction des fiches."""
import unicodedata
from pathlib import Path

import pandas as pd

COLONNES_NUTRIMENTS = {
    "kcal": "energy_kcal",
    "lipides": "fat",
    "satures": "saturated_fat",
    "sucres": "sugars",
    "sel": "salt",
    "fibres": "fiber",
    "proteines": "proteins",
}

RACINE = Path(__file__).resolve().parents[2]


def normaliser(texte) -> str:
    """Minuscules sans accents ; toute valeur non texte donne ''."""
    if not isinstance(texte, str):
        return ""
    decompose = unicodedata.normalize("NFD", texte.lower())
    return "".join(c for c in decompose if unicodedata.category(c) != "Mn")


def charger_catalogue(dossier="data/extracts") -> pd.DataFrame:
    """Charge products + nutrients (jointure left sur code), sans filtrer."""
    dossier = Path(dossier)
    if not dossier.is_absolute():
        dossier = RACINE / dossier
    produits = pd.read_parquet(
        dossier / "products.parquet",
        columns=["code", "name", "brand_name", "nutriscore_grade", "completeness"],
    )
    nutriments = pd.read_parquet(
        dossier / "nutrients.parquet",
        columns=["code", *COLONNES_NUTRIMENTS.values()],
    )
    # codes en double dans les deux fichiers : on garde le premier (évite un produit cartésien)
    produits = produits.drop_duplicates("code")
    nutriments = nutriments.drop_duplicates("code")
    cat = produits.merge(nutriments, on="code", how="left")
    cat["nom_normalise"] = cat["name"].map(normaliser)
    cat["marque_normalisee"] = cat["brand_name"].map(normaliser)
    return cat


def _valeur(v):
    """None si absent (NaN/None), sinon la valeur."""
    return None if v is None or pd.isna(v) else v


def construire_fiche(ligne) -> dict:
    """Fiche JSON-sérialisable ; un nutriment inconnu reste None (jamais 0)."""
    grade = _valeur(ligne.get("nutriscore_grade"))
    nutriscore = grade.upper() if isinstance(grade, str) and grade in "abcde" and len(grade) == 1 else None
    nutriments = {}
    for cle, col in COLONNES_NUTRIMENTS.items():
        v = _valeur(ligne.get(col))
        nutriments[cle] = None if v is None else round(float(v), 2)
    nom = _valeur(ligne.get("name"))
    marque = _valeur(ligne.get("brand_name"))
    return {
        "code": str(ligne.get("code")),
        "nom": None if nom is None else str(nom),
        "marque": None if marque is None else str(marque),
        "nutriscore": nutriscore,
        "nutriments": nutriments,
        "donnees_incompletes": nutriscore is None or any(v is None for v in nutriments.values()),
    }
