"""Règles de nettoyage NutriScope (TP 9).

Contrat commun : chaque règle est une fonction pure
`regle(df) -> (DataFrame, CompteRendu)`. Elle travaille sur une copie,
ne modifie jamais son entrée et documente ses seuils, qui sont des
constantes nommées ci-dessous.

`lignes_touchees` compte des lignes dont une valeur a réellement changé
(ou qui ont été supprimées) : une ligne touchée par trois sous-règles
compte une fois, mais trois fois dans `details`. Relancer une règle sur
sa propre sortie doit donc donner zéro ligne touchée.
"""

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

if int(pd.__version__.split(".")[0]) < 3:
    pd.options.mode.copy_on_write = True  # déjà le comportement par défaut en pandas 3


# ============================================================
# Constantes métier
# ============================================================

KJ_PAR_KCAL = 4.184
SEL_PAR_SODIUM = 2.5

# ============================================================
# Colonnes
# ============================================================

COLONNES_NUTRIMENTS = [
    "energy-kcal_100g", "energy_100g", "fat_100g", "saturated-fat_100g",
    "carbohydrates_100g", "sugars_100g", "fiber_100g", "proteins_100g",
    "salt_100g", "sodium_100g", "fruits-vegetables-legumes_100g",
]
COLONNES_REELS = COLONNES_NUTRIMENTS + ["completeness", "created_t", "last_modified_t"]
COLONNES_COMPTEURS = ["additives_n", "nova_group", "nutriscore_score"]


# ============================================================
# Contrat commun
# ============================================================

@dataclass
class CompteRendu:
    regle: str
    lignes_avant: int
    lignes_apres: int
    lignes_touchees: int
    details: dict[str, int] = field(default_factory=dict)


def _compte_rendu(regle: str, avant: pd.DataFrame, apres: pd.DataFrame,
                  masques: dict[str, pd.Series]) -> CompteRendu:
    """Construit le compte rendu à partir d'un masque booléen par sous-règle."""
    touchees = pd.Series(False, index=avant.index)
    for masque in masques.values():
        touchees = touchees | masque.reindex(avant.index, fill_value=False)
    return CompteRendu(
        regle=regle,
        lignes_avant=len(avant),
        lignes_apres=len(apres),
        lignes_touchees=int(touchees.sum()),
        details={nom: int(masque.sum()) for nom, masque in masques.items()},
    )


def _a_change(avant: pd.Series, apres: pd.Series) -> pd.Series:
    """Vrai là où la valeur a changé (NA → NA n'est pas un changement)."""
    identiques = (avant == apres).fillna(False) | (avant.isna() & apres.isna())
    return ~identiques.astype(bool)


# ============================================================
# Règles
# ============================================================

def typer_colonnes(df: pd.DataFrame) -> tuple[pd.DataFrame, CompteRendu]:
    """Fixe les types : `code` en `string`, compteurs en `Int64`, nutriments en `float64`.

    - `code` : texte, jamais numérique (les zéros de tête font partie du
      code-barres). Il doit déjà être lu en texte (`lire_brut`) : un code lu
      en entier a perdu ses zéros, on ne peut pas les retrouver ici.
    - compteurs (`additives_n`, `nova_group`, `nutriscore_score`) : entiers
      nullables ; une valeur non numérique ou non entière devient NA.
    - nutriments, `completeness`, dates Unix : `float64` ; une valeur non
      numérique devient NA.

    Détail compté : `valeurs_non_numeriques`, lignes dont au moins une
    valeur illisible a été passée à NA. Les colonnes absentes sont ignorées.
    """
    res = df.copy()
    illisibles = pd.Series(False, index=df.index)

    if "code" in res.columns:
        res["code"] = res["code"].astype("string")

    for col in [c for c in COLONNES_REELS if c in res.columns]:
        valeurs = pd.to_numeric(res[col], errors="coerce").astype("float64")
        illisibles |= res[col].notna() & valeurs.isna()
        res[col] = valeurs

    for col in [c for c in COLONNES_COMPTEURS if c in res.columns]:
        valeurs = pd.to_numeric(res[col], errors="coerce").astype("float64")
        valeurs = valeurs.where(valeurs.round() == valeurs)
        illisibles |= res[col].notna() & valeurs.isna()
        res[col] = valeurs.astype("Int64")

    return res, _compte_rendu("typer_colonnes", df, res, {"valeurs_non_numeriques": illisibles})


# ============================================================
# Pipeline
# ============================================================

# Ordre imposé : types, textes, doublons, unités, bornes, énergie,
# catégories, manquants. Chaque règle ajoutée se branche ici.
REGLES = [
    typer_colonnes,
]


def lire_brut(chemin: str | Path) -> pd.DataFrame:
    """Lit un export CSV Open Food Facts en gardant `code` en texte."""
    return pd.read_csv(chemin, dtype={"code": "string"}, low_memory=False)


def nettoyer(brut: pd.DataFrame, regles=None) -> tuple[pd.DataFrame, list[CompteRendu]]:
    """Applique les règles dans l'ordre et renvoie (propre, journal des comptes rendus)."""
    df, journal = brut, []
    for regle in regles if regles is not None else REGLES:
        df, compte_rendu = regle(df)
        journal.append(compte_rendu)
    return df, journal
