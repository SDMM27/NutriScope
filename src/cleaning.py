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

# rapport kJ / kcal toléré avant de recalculer les kcal (4,184 théorique)
RAPPORT_KJ_KCAL_MIN = 3.9
RAPPORT_KJ_KCAL_MAX = 4.5
# écart toléré entre sel et sodium × 2,5 (arrondis de saisie)
TOLERANCE_SEL_SODIUM = 0.1

NUTRIMENT_MAX_G = 100.0        # g pour 100 g
SODIUM_MAX_G = NUTRIMENT_MAX_G / SEL_PAR_SODIUM   # 40 g : sel ≤ 100 g
TOLERANCE_SOUS_TOTAL_G = 0.5   # sucres ≤ glucides + 0,5 ; saturés ≤ lipides + 0,5

KCAL_MAX = 900.0               # 100 g de lipides purs
KCAL_PAR_G_GLUCIDES = 4.0
KCAL_PAR_G_PROTEINES = 4.0
KCAL_PAR_G_LIPIDES = 9.0
ECART_ENERGIE_MAX = 0.5        # écart relatif toléré avec le calcul 4 / 4 / 9
CALCUL_ENERGIE_MIN = 50.0      # sous 50 kcal calculées, l'écart relatif n'est pas fiable
RAYON_ALCOOL = "Alcoholic beverages"

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
# nutriments bornés à 0–100 g pour 100 g (le sodium a sa propre borne)
COLONNES_0_100 = [
    "fat_100g", "saturated-fat_100g", "carbohydrates_100g", "sugars_100g",
    "fiber_100g", "proteins_100g", "salt_100g",
]


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


# ------------------------------------------------------------
# Règles nutriments (Sacha)
# ------------------------------------------------------------

def normaliser_unites(df: pd.DataFrame) -> tuple[pd.DataFrame, CompteRendu]:
    """Aligne kcal sur kJ et sel sur sodium.

    Énergie (`energy_100g` en kJ, `energy-kcal_100g` en kcal) :
    - kcal absentes et kJ présents → kcal = kJ / KJ_PAR_KCAL (`kcal_derivees`) ;
    - kJ > 0 et rapport kJ / kcal hors [RAPPORT_KJ_KCAL_MIN ; RAPPORT_KJ_KCAL_MAX]
      → kcal = kJ / KJ_PAR_KCAL (`kcal_recalculees`). On fait confiance aux kJ,
      l'unité légale ; des kJ nuls ou négatifs ne servent pas de référence.

    Sel / sodium (sel = sodium × SEL_PAR_SODIUM) :
    - sel absent → dérivé du sodium (`sel_derive`) ;
    - sodium absent → dérivé du sel (`sodium_derive`) ;
    - les deux présents mais écart > TOLERANCE_SEL_SODIUM → sodium recalculé
      depuis le sel (`sodium_recalcule`).

    Aucune valeur n'est bornée ici : un sel dérivé aberrant sera traité par
    `borner_nutriments`, qui passe après.
    """
    res = df.copy()
    kcal, kj = res["energy-kcal_100g"], res["energy_100g"]
    depuis_kj = kj / KJ_PAR_KCAL

    kcal_derivees = kcal.isna() & kj.notna()
    rapport = kj / kcal
    hors_rapport = (kj > 0) & kcal.notna() & ~rapport.between(RAPPORT_KJ_KCAL_MIN, RAPPORT_KJ_KCAL_MAX)
    nouvelles_kcal = kcal.mask(kcal_derivees | hors_rapport, depuis_kj)
    kcal_recalculees = hors_rapport & _a_change(kcal, nouvelles_kcal)
    res["energy-kcal_100g"] = nouvelles_kcal

    sel, sodium = res["salt_100g"], res["sodium_100g"]
    sel_derive = sel.isna() & sodium.notna()
    sodium_derive = sodium.isna() & sel.notna()
    sel = sel.mask(sel_derive, sodium * SEL_PAR_SODIUM)
    sodium = sodium.mask(sodium_derive, sel / SEL_PAR_SODIUM)
    incoherent = (sel - sodium * SEL_PAR_SODIUM).abs() > TOLERANCE_SEL_SODIUM
    nouveau_sodium = sodium.mask(incoherent, sel / SEL_PAR_SODIUM)
    sodium_recalcule = incoherent & _a_change(sodium, nouveau_sodium)
    res["salt_100g"] = sel
    res["sodium_100g"] = nouveau_sodium

    return res, _compte_rendu("normaliser_unites", df, res, {
        "kcal_derivees": kcal_derivees,
        "kcal_recalculees": kcal_recalculees,
        "sel_derive": sel_derive,
        "sodium_derive": sodium_derive,
        "sodium_recalcule": sodium_recalcule,
    })


def borner_nutriments(df: pd.DataFrame) -> tuple[pd.DataFrame, CompteRendu]:
    """Passe à NA les valeurs physiquement impossibles.

    - `COLONNES_0_100` : négatif ou > NUTRIMENT_MAX_G (100 g pour 100 g) → NA ;
    - `sodium_100g` : négatif ou > SODIUM_MAX_G (40 g, soit 100 g de sel) → NA ;
    - sucres > glucides + TOLERANCE_SOUS_TOTAL_G → sucres NA ;
    - saturés > lipides + TOLERANCE_SOUS_TOTAL_G → saturés NA.

    Une valeur impossible n'est jamais tronquée (74 000 g de sucres ne veut
    pas dire 100 g) : on la retire. Les cohérences sucres / saturés sont
    testées après les bornes, sur des glucides et lipides déjà plausibles ;
    c'est le sous-total qu'on retire, le total étant le plus souvent saisi
    correctement.

    Détails : `<colonne>_negatifs`, `<colonne>_sup_borne`, `sucres_sup_glucides`,
    `satures_sup_lipides`.
    """
    res = df.copy()
    masques = {}
    bornes = {col: NUTRIMENT_MAX_G for col in COLONNES_0_100} | {"sodium_100g": SODIUM_MAX_G}

    for col, borne in bornes.items():
        if col not in res.columns:
            continue
        negatif = res[col] < 0
        sup_borne = res[col] > borne
        res[col] = res[col].mask(negatif | sup_borne)
        masques[f"{col}_negatifs"] = negatif
        masques[f"{col}_sup_borne"] = sup_borne

    sucres_sup = res["sugars_100g"] > res["carbohydrates_100g"] + TOLERANCE_SOUS_TOTAL_G
    res["sugars_100g"] = res["sugars_100g"].mask(sucres_sup)
    satures_sup = res["saturated-fat_100g"] > res["fat_100g"] + TOLERANCE_SOUS_TOTAL_G
    res["saturated-fat_100g"] = res["saturated-fat_100g"].mask(satures_sup)
    masques["sucres_sup_glucides"] = sucres_sup
    masques["satures_sup_lipides"] = satures_sup

    return res, _compte_rendu("borner_nutriments", df, res, masques)


def calcul_energie_449(df: pd.DataFrame) -> pd.Series:
    """kcal attendues d'après les macronutriments : 4 × glucides + 4 × protéines + 9 × lipides.

    NA si l'un des trois manque.
    """
    return (KCAL_PAR_G_GLUCIDES * df["carbohydrates_100g"]
            + KCAL_PAR_G_PROTEINES * df["proteins_100g"]
            + KCAL_PAR_G_LIPIDES * df["fat_100g"])


def corriger_energie(df: pd.DataFrame) -> tuple[pd.DataFrame, CompteRendu]:
    """Corrige les kcal impossibles ou incohérentes avec le calcul 4 / 4 / 9.

    Trois cas, exclusifs, testés sur les kcal d'entrée :
    - kcal nulles alors qu'au moins un macronutriment est > 0 (`nulles_...`) ;
    - kcal hors [0 ; KCAL_MAX] (`negatives_...`, `sup_900_...`) ;
    - kcal à plus de ECART_ENERGIE_MAX (50 %) du calcul 4 / 4 / 9, quand le
      calcul vaut au moins CALCUL_ENERGIE_MIN (`incoherentes_...`).
      Exception : le rayon RAYON_ALCOOL, dont l'alcool (7 kcal/g) n'est pas
      compté par les macronutriments ; ses kcal ne sont jamais jugées
      incohérentes (elles restent soumises à la borne 0–900).

    Dans chaque cas, les kcal sont remplacées par le calcul 4 / 4 / 9 s'il est
    disponible et dans [0 ; KCAL_MAX] (`..._recalculees`), sinon passées à NA
    (`..._invalidees`). Les kJ des lignes corrigées sont réalignés
    (kcal × KJ_PAR_KCAL, ou NA).

    À appliquer après `borner_nutriments` : le calcul s'appuie sur des
    macronutriments déjà plausibles.
    """
    res = df.copy()
    kcal = res["energy-kcal_100g"]
    calcul = calcul_energie_449(res)
    calcul_valide = calcul.notna() & calcul.between(0, KCAL_MAX)
    alcool = res["pnns_groups_1"].eq(RAYON_ALCOOL).fillna(False).astype(bool)

    macro_positif = (res[["carbohydrates_100g", "proteins_100g", "fat_100g"]] > 0).any(axis=1)
    nulles = (kcal == 0) & macro_positif
    negatives = kcal < 0
    sup_900 = kcal > KCAL_MAX
    ecart = (kcal - calcul).abs() / calcul
    incoherentes = (~nulles & ~negatives & ~sup_900 & ~alcool
                    & (calcul >= CALCUL_ENERGIE_MIN) & (ecart > ECART_ENERGIE_MAX))

    a_corriger = nulles | negatives | sup_900 | incoherentes
    nouvelles_kcal = kcal.mask(a_corriger & calcul_valide, calcul).mask(a_corriger & ~calcul_valide)
    res["energy-kcal_100g"] = nouvelles_kcal
    res["energy_100g"] = res["energy_100g"].mask(a_corriger, nouvelles_kcal * KJ_PAR_KCAL)

    masques = {}
    for nom, cas in [("nulles", nulles), ("negatives", negatives),
                     ("sup_900", sup_900), ("incoherentes", incoherentes)]:
        masques[f"{nom}_recalculees"] = cas & calcul_valide
        masques[f"{nom}_invalidees"] = cas & ~calcul_valide
    return res, _compte_rendu("corriger_energie", df, res, masques)


# ============================================================
# Pipeline
# ============================================================

# Ordre imposé : types, textes, doublons, unités, bornes, énergie,
# catégories, manquants. Chaque règle ajoutée se branche ici.
REGLES = [
    typer_colonnes,
    normaliser_unites,
    borner_nutriments,
    corriger_energie,
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
