"""Cleaning rules for NutriScope (TP 9).

Contract shared by all cleaning rules:
`rule(df) -> (DataFrame, CompteRendu)`.

Each rule works on a copy and never modifies its input. Business thresholds
are defined as named constants below.

`lignes_touchees` counts rows where a value actually changed or where the row
was removed. A row affected by several sub-rules is counted once in
`lignes_touchees`, but once per sub-rule in `details`.
"""

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


if int(pd.__version__.split(".")[0]) < 3:
    pd.options.mode.copy_on_write = True


# ============================================================
# Business constants
# ============================================================

KJ_PAR_KCAL = 4.184
SEL_PAR_SODIUM = 2.5

RAPPORT_KJ_KCAL_MIN = 3.9
RAPPORT_KJ_KCAL_MAX = 4.5

TOLERANCE_SEL_SODIUM = 0.1

NUTRIMENT_MAX_G = 100.0
SODIUM_MAX_G = NUTRIMENT_MAX_G / SEL_PAR_SODIUM
TOLERANCE_SOUS_TOTAL_G = 0.5

KCAL_MAX = 900.0
KCAL_PAR_G_GLUCIDES = 4.0
KCAL_PAR_G_PROTEINES = 4.0
KCAL_PAR_G_LIPIDES = 9.0
ECART_ENERGIE_MAX = 0.5
CALCUL_ENERGIE_MIN = 50.0

RAYON_ALCOOL = "Alcoholic beverages"


# ============================================================
# Column groups
# ============================================================

COLONNES_NUTRIMENTS = [
    "energy-kcal_100g",
    "energy_100g",
    "fat_100g",
    "saturated-fat_100g",
    "carbohydrates_100g",
    "sugars_100g",
    "fiber_100g",
    "proteins_100g",
    "salt_100g",
    "sodium_100g",
    "fruits-vegetables-legumes_100g",
]

COLONNES_REELS = COLONNES_NUTRIMENTS + [
    "completeness",
    "created_t",
    "last_modified_t",
]

COLONNES_COMPTEURS = [
    "additives_n",
    "nova_group",
    "nutriscore_score",
]

COLONNES_0_100 = [
    "fat_100g",
    "saturated-fat_100g",
    "carbohydrates_100g",
    "sugars_100g",
    "fiber_100g",
    "proteins_100g",
    "salt_100g",
]


# ============================================================
# Common report contract
# ============================================================

@dataclass
class CompteRendu:
    """Summary of the changes performed by one cleaning rule."""

    regle: str
    lignes_avant: int
    lignes_apres: int
    lignes_touchees: int
    details: dict[str, int] = field(default_factory=dict)


def _compte_rendu(
    regle: str,
    avant: pd.DataFrame,
    apres: pd.DataFrame,
    masques: dict[str, pd.Series],
) -> CompteRendu:
    """Build a report from one boolean mask per sub-rule."""
    touchees = pd.Series(False, index=avant.index)

    for masque in masques.values():
        touchees = touchees | masque.reindex(
            avant.index,
            fill_value=False,
        )

    return CompteRendu(
        regle=regle,
        lignes_avant=len(avant),
        lignes_apres=len(apres),
        lignes_touchees=int(touchees.sum()),
        details={
            nom: int(masque.sum())
            for nom, masque in masques.items()
        },
    )


def _a_change(
    avant: pd.Series,
    apres: pd.Series,
) -> pd.Series:
    """Return True where a value changed, excluding NA -> NA."""
    identiques = (
        (avant == apres).fillna(False)
        | (avant.isna() & apres.isna())
    )

    return ~identiques.astype(bool)


# ============================================================
# Rule 1 - Column typing
# ============================================================

def typer_colonnes(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, CompteRendu]:
    """Set expected pandas types for codes, numeric columns and counters.

    - `code` is converted to pandas `string`.
    - Counters use nullable `Int64`.
    - Nutrients, completeness and timestamps use `float64`.
    - Invalid numeric values are converted to NA.
    """
    res = df.copy()
    illisibles = pd.Series(False, index=df.index)

    if "code" in res.columns:
        res["code"] = res["code"].astype("string")

    for col in [c for c in COLONNES_REELS if c in res.columns]:
        valeurs = pd.to_numeric(
            res[col],
            errors="coerce",
        ).astype("float64")

        illisibles |= res[col].notna() & valeurs.isna()
        res[col] = valeurs

    for col in [c for c in COLONNES_COMPTEURS if c in res.columns]:
        valeurs = pd.to_numeric(
            res[col],
            errors="coerce",
        ).astype("float64")

        valeurs = valeurs.where(
            valeurs.round() == valeurs
        )

        illisibles |= res[col].notna() & valeurs.isna()
        res[col] = valeurs.astype("Int64")

    return res, _compte_rendu(
        "typer_colonnes",
        df,
        res,
        {"valeurs_non_numeriques": illisibles},
    )


# ============================================================
# Rule 2 - Code deduplication
# ============================================================

def dedupliquer_codes(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, CompteRendu]:
    """Remove rows without a code and duplicate product codes.

    For duplicate codes, keep the row with the highest completeness.
    If completeness is equal, keep the most recently modified row.
    """
    res = df.copy()

    codes_absents = res["code"].isna()

    # Products without a code cannot be reliably identified.
    res = res.loc[~codes_absents].copy()

    sort_columns = ["code"]

    if "completeness" in res.columns:
        sort_columns.append("completeness")

    if "last_modified_t" in res.columns:
        sort_columns.append("last_modified_t")

    ascending = [True] + [False] * (len(sort_columns) - 1)

    res = (
        res.sort_values(
            sort_columns,
            ascending=ascending,
            na_position="last",
        )
        .drop_duplicates(
            subset="code",
            keep="first",
        )
    )

    lignes_supprimees = ~df.index.isin(res.index)

    doublons_supprimes = (
        lignes_supprimees
        & df["code"].notna()
    )

    return res, _compte_rendu(
        "dedupliquer_codes",
        df,
        res,
        {
            "codes_absents": codes_absents,
            "doublons_supprimes": doublons_supprimes,
        },
    )


# ============================================================
# Rule 3 - Unit normalization
# ============================================================

def normaliser_unites(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, CompteRendu]:
    """Align kcal with kJ and salt with sodium."""
    res = df.copy()

    # --------------------------------------------------------
    # Energy
    # --------------------------------------------------------

    kcal = res["energy-kcal_100g"]
    kj = res["energy_100g"]

    depuis_kj = kj / KJ_PAR_KCAL

    kcal_derivees = (
        kcal.isna()
        & kj.notna()
    )

    rapport = kj / kcal

    hors_rapport = (
        (kj > 0)
        & kcal.notna()
        & ~rapport.between(
            RAPPORT_KJ_KCAL_MIN,
            RAPPORT_KJ_KCAL_MAX,
        )
    )

    nouvelles_kcal = kcal.mask(
        kcal_derivees | hors_rapport,
        depuis_kj,
    )

    kcal_recalculees = (
        hors_rapport
        & _a_change(kcal, nouvelles_kcal)
    )

    res["energy-kcal_100g"] = nouvelles_kcal

    # --------------------------------------------------------
    # Salt / sodium
    # --------------------------------------------------------

    sel = res["salt_100g"]
    sodium = res["sodium_100g"]

    sel_derive = (
        sel.isna()
        & sodium.notna()
    )

    sodium_derive = (
        sodium.isna()
        & sel.notna()
    )

    sel = sel.mask(
        sel_derive,
        sodium * SEL_PAR_SODIUM,
    )

    sodium = sodium.mask(
        sodium_derive,
        sel / SEL_PAR_SODIUM,
    )

    incoherent = (
        sel - sodium * SEL_PAR_SODIUM
    ).abs() > TOLERANCE_SEL_SODIUM

    nouveau_sodium = sodium.mask(
        incoherent,
        sel / SEL_PAR_SODIUM,
    )

    sodium_recalcule = (
        incoherent
        & _a_change(sodium, nouveau_sodium)
    )

    res["salt_100g"] = sel
    res["sodium_100g"] = nouveau_sodium

    return res, _compte_rendu(
        "normaliser_unites",
        df,
        res,
        {
            "kcal_derivees": kcal_derivees,
            "kcal_recalculees": kcal_recalculees,
            "sel_derive": sel_derive,
            "sodium_derive": sodium_derive,
            "sodium_recalcule": sodium_recalcule,
        },
    )


# ============================================================
# Rule 4 - Nutrient bounds
# ============================================================

def borner_nutriments(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, CompteRendu]:
    """Set physically impossible nutrient values to NA."""
    res = df.copy()
    masques = {}

    bornes = {
        col: NUTRIMENT_MAX_G
        for col in COLONNES_0_100
    } | {
        "sodium_100g": SODIUM_MAX_G,
    }

    for col, borne in bornes.items():
        if col not in res.columns:
            continue

        negatif = res[col] < 0
        sup_borne = res[col] > borne

        res[col] = res[col].mask(
            negatif | sup_borne
        )

        masques[f"{col}_negatifs"] = negatif
        masques[f"{col}_sup_borne"] = sup_borne

    sucres_sup = (
        res["sugars_100g"]
        > res["carbohydrates_100g"] + TOLERANCE_SOUS_TOTAL_G
    )

    res["sugars_100g"] = res["sugars_100g"].mask(
        sucres_sup
    )

    satures_sup = (
        res["saturated-fat_100g"]
        > res["fat_100g"] + TOLERANCE_SOUS_TOTAL_G
    )

    res["saturated-fat_100g"] = res["saturated-fat_100g"].mask(
        satures_sup
    )

    masques["sucres_sup_glucides"] = sucres_sup
    masques["satures_sup_lipides"] = satures_sup

    return res, _compte_rendu(
        "borner_nutriments",
        df,
        res,
        masques,
    )


# ============================================================
# Rule 5 - Energy correction
# ============================================================

def calcul_energie_449(
    df: pd.DataFrame,
) -> pd.Series:
    """Calculate expected kcal using the 4 / 4 / 9 formula."""
    return (
        KCAL_PAR_G_GLUCIDES * df["carbohydrates_100g"]
        + KCAL_PAR_G_PROTEINES * df["proteins_100g"]
        + KCAL_PAR_G_LIPIDES * df["fat_100g"]
    )


def corriger_energie(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, CompteRendu]:
    """Correct impossible or inconsistent energy values."""
    res = df.copy()

    kcal = res["energy-kcal_100g"]
    calcul = calcul_energie_449(res)

    calcul_valide = (
        calcul.notna()
        & calcul.between(0, KCAL_MAX)
    )

    alcool = (
        res["pnns_groups_1"]
        .eq(RAYON_ALCOOL)
        .fillna(False)
        .astype(bool)
    )

    macro_positif = (
        res[
            [
                "carbohydrates_100g",
                "proteins_100g",
                "fat_100g",
            ]
        ] > 0
    ).any(axis=1)

    nulles = (
        (kcal == 0)
        & macro_positif
    )

    negatives = kcal < 0
    sup_900 = kcal > KCAL_MAX

    ecart = (kcal - calcul).abs() / calcul

    incoherentes = (
        ~nulles
        & ~negatives
        & ~sup_900
        & ~alcool
        & (calcul >= CALCUL_ENERGIE_MIN)
        & (ecart > ECART_ENERGIE_MAX)
    )

    a_corriger = (
        nulles
        | negatives
        | sup_900
        | incoherentes
    )

    nouvelles_kcal = (
        kcal
        .mask(
            a_corriger & calcul_valide,
            calcul,
        )
        .mask(
            a_corriger & ~calcul_valide,
        )
    )

    res["energy-kcal_100g"] = nouvelles_kcal

    res["energy_100g"] = (
        res["energy_100g"]
        .mask(
            a_corriger,
            nouvelles_kcal * KJ_PAR_KCAL,
        )
    )

    masques = {}

    for nom, cas in [
        ("nulles", nulles),
        ("negatives", negatives),
        ("sup_900", sup_900),
        ("incoherentes", incoherentes),
    ]:
        masques[f"{nom}_recalculees"] = (
            cas & calcul_valide
        )
        masques[f"{nom}_invalidees"] = (
            cas & ~calcul_valide
        )

    return res, _compte_rendu(
        "corriger_energie",
        df,
        res,
        masques,
    )


# ============================================================
# Rule 6 - Empty categories
# ============================================================

def traiter_categories_vides(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, CompteRendu]:
    """Replace empty category strings with missing values."""
    res = df.copy()

    categories_vides = (
        res["categories"].notna()
        & res["categories"]
        .astype("string")
        .str.strip()
        .eq("")
    )

    res.loc[
        categories_vides,
        "categories",
    ] = pd.NA

    return res, _compte_rendu(
        "traiter_categories_vides",
        df,
        res,
        {"categories_vides": categories_vides},
    )


# ============================================================
# Rule 7 - Missing values strategy
# ============================================================

def strategie_manquants(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, CompteRendu]:
    """Preserve missing values without artificial imputation.

    Missing values remain NA. Rows without a product code have already been
    removed by `dedupliquer_codes`.
    """
    res = df.copy()

    return res, _compte_rendu(
        "strategie_manquants",
        df,
        res,
        {},
    )


# ============================================================
# Input and pipeline
# ============================================================

def lire_brut(
    chemin: str | Path,
) -> pd.DataFrame:
    """Read an Open Food Facts CSV while preserving product codes as strings."""
    return pd.read_csv(
        chemin,
        dtype={"code": "string"},
        low_memory=False,
    )


def nettoyer(
    brut: pd.DataFrame,
    regles=None,
) -> tuple[pd.DataFrame, list[CompteRendu]]:
    """Apply the cleaning rules in order."""
    df = brut
    journal = []

    for regle in regles if regles is not None else REGLES:
        df, compte_rendu = regle(df)
        journal.append(compte_rendu)

    return df, journal


# Order defined by TP9.
# `normaliser_textes` is optional and is intentionally deferred.
REGLES = [
    typer_colonnes,
    dedupliquer_codes,
    normaliser_unites,
    borner_nutriments,
    corriger_energie,
    traiter_categories_vides,
    strategie_manquants,
]