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

# nutriments bornés à 0–100 g pour 100 g (le sodium a sa propre borne)
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
# Contrat commun des comptes rendus
# ============================================================

@dataclass
class CompteRendu:
    """Résumé des transformations effectuées par une règle."""

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
    """Construit un compte rendu à partir des masques de modifications."""

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
    """Indique les lignes dont la valeur a réellement changé."""

    identiques = (
        (avant == apres).fillna(False)
        | (avant.isna() & apres.isna())
    )

    return ~identiques.astype(bool)


# ============================================================
# Règle 1 - typer_colonnes
# ============================================================

def typer_colonnes(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, CompteRendu]:
    """Convertit les colonnes vers les types attendus.

    - `code` est conservé en texte ;
    - les colonnes nutritionnelles et réelles sont converties en float ;
    - les compteurs sont convertis en entiers nullable ;
    - les valeurs numériques illisibles deviennent NA.
    """

    res = df.copy()

    res["code"] = res["code"].astype("string")

    valeurs_non_numeriques = pd.Series(
        False,
        index=res.index,
    )

    for colonne in COLONNES_REELS:
        if colonne not in res.columns:
            continue

        avant = res[colonne]
        apres = pd.to_numeric(
            avant,
            errors="coerce",
        ).astype("float64")

        valeurs_non_numeriques |= (
            avant.notna()
            & apres.isna()
        )

        res[colonne] = apres

    for colonne in COLONNES_COMPTEURS:
        if colonne not in res.columns:
            continue

        avant = pd.to_numeric(
            res[colonne],
            errors="coerce",
        )

        valeurs_non_numeriques |= (
            res[colonne].notna()
            & avant.isna()
        )

        valeurs_non_entieres = (
            avant.notna()
            & (avant % 1 != 0)
        )

        valeurs_non_numeriques |= valeurs_non_entieres

        res[colonne] = avant.where(
            ~valeurs_non_entieres
        ).astype("Int64")

    return res, _compte_rendu(
        "typer_colonnes",
        df,
        res,
        {
            "valeurs_non_numeriques": valeurs_non_numeriques,
        },
    )


# ============================================================
# Règle 2 - dedupliquer_codes
# ============================================================

def dedupliquer_codes(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, CompteRendu]:
    """Supprime les lignes sans code et les doublons de codes.

    Pour les codes en double, conserve la ligne ayant la meilleure
    complétude. En cas d'égalité, conserve la ligne la plus récemment
    modifiée lorsque `last_modified_t` est disponible.
    """

    res = df.copy()

    codes_absents = res["code"].isna()

    res = res.loc[~codes_absents].copy()

    sort_columns = ["code"]

    if "completeness" in res.columns:
        sort_columns.append("completeness")

    if "last_modified_t" in res.columns:
        sort_columns.append("last_modified_t")

    ascending = [True] + [False] * (
        len(sort_columns) - 1
    )

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

    lignes_supprimees = ~df.index.isin(
        res.index
    )

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
# Règle 3 - normaliser_unites
# ============================================================

def normaliser_unites(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, CompteRendu]:
    """Aligne les unités kcal/kJ et sel/sodium.

    Énergie :
    - si les kcal sont absentes et les kJ présents, les kcal sont
      calculées à partir des kJ ;
    - si le rapport kJ/kcal est hors de l'intervalle attendu,
      les kcal sont recalculées à partir des kJ ;
    - les kJ nuls ou négatifs ne servent pas de référence.

    Sel / sodium :
    - le sel absent est dérivé du sodium ;
    - le sodium absent est dérivé du sel ;
    - en cas d'incohérence, le sodium est recalculé à partir du sel.

    Les valeurs ne sont pas bornées ici : cette opération est réalisée
    par `borner_nutriments`.
    """

    res = df.copy()

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
        (sel - sodium * SEL_PAR_SODIUM).abs()
        > TOLERANCE_SEL_SODIUM
    )

    nouveau_sodium = sodium.mask(
        incoherent,
        sel / SEL_PAR_SODIUM,
    )

    sodium_recalcule = (
        incoherent
        & _a_change(
            sodium,
            nouveau_sodium,
        )
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
# Règle 4 - borner_nutriments
# ============================================================

def borner_nutriments(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, CompteRendu]:
    """Remplace les valeurs nutritionnelles incohérentes par NA.

    Règles :
    - nutriments en g/100 g négatifs ou supérieurs à 100 → NA ;
    - sodium supérieur à 40 g/100 g → NA ;
    - sucres supérieurs aux glucides + tolérance → NA ;
    - acides gras saturés supérieurs aux lipides + tolérance → NA.
    """

    res = df.copy()
    masques = {}

    bornes = {
        colonne: NUTRIMENT_MAX_G
        for colonne in COLONNES_0_100
    }

    bornes["sodium_100g"] = SODIUM_MAX_G

    for colonne, borne in bornes.items():
        if colonne not in res.columns:
            continue

        negatif = res[colonne] < 0
        sup_borne = res[colonne] > borne

        res[colonne] = res[colonne].mask(
            negatif | sup_borne
        )

        masques[f"{colonne}_negatifs"] = negatif
        masques[f"{colonne}_sup_borne"] = sup_borne

    sucres_sup = (
        res["sugars_100g"]
        > res["carbohydrates_100g"]
        + TOLERANCE_SOUS_TOTAL_G
    )

    res["sugars_100g"] = res[
        "sugars_100g"
    ].mask(sucres_sup)

    satures_sup = (
        res["saturated-fat_100g"]
        > res["fat_100g"]
        + TOLERANCE_SOUS_TOTAL_G
    )

    res["saturated-fat_100g"] = res[
        "saturated-fat_100g"
    ].mask(satures_sup)

    masques["sucres_sup_glucides"] = sucres_sup
    masques["satures_sup_lipides"] = satures_sup

    return res, _compte_rendu(
        "borner_nutriments",
        df,
        res,
        masques,
    )


# ============================================================
# Règle 5 - corriger_energie
# ============================================================

def calcul_energie_449(
    df: pd.DataFrame,
) -> pd.Series:
    """Calcule l'énergie théorique selon la formule 4/4/9."""

    return (
        KCAL_PAR_G_GLUCIDES
        * df["carbohydrates_100g"]
        + KCAL_PAR_G_PROTEINES
        * df["proteins_100g"]
        + KCAL_PAR_G_LIPIDES
        * df["fat_100g"]
    )


def corriger_energie(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, CompteRendu]:
    """Corrige ou invalide les valeurs énergétiques incohérentes.

    Une énergie est corrigée lorsqu'elle est nulle, négative, supérieure
    à 900 kcal ou incohérente de plus de 50 % avec le calcul 4/4/9.

    Le recalcul n'est effectué que lorsque le calcul théorique est valide
    et supérieur ou égal à 50 kcal.

    Les boissons alcoolisées sont exclues de la règle d'incohérence 4/4/9.
    """

    res = df.copy()

    kcal = res["energy-kcal_100g"]
    calcul = calcul_energie_449(res)

    calcul_valide = (
        calcul.notna()
        & calcul.between(
            0,
            KCAL_MAX,
        )
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

    ecart = (
        (kcal - calcul).abs()
        / calcul
    )

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

    res["energy_100g"] = res[
        "energy_100g"
    ].mask(
        a_corriger,
        nouvelles_kcal * KJ_PAR_KCAL,
    )

    masques = {}

    for nom, cas in [
        ("nulles", nulles),
        ("negatives", negatives),
        ("sup_900", sup_900),
        ("incoherentes", incoherentes),
    ]:
        masques[
            f"{nom}_recalculees"
        ] = cas & calcul_valide

        masques[
            f"{nom}_invalidees"
        ] = cas & ~calcul_valide

    return res, _compte_rendu(
        "corriger_energie",
        df,
        res,
        masques,
    )


# ============================================================
# Règle 6 - traiter_categories_vides
# ============================================================

def traiter_categories_vides(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, CompteRendu]:
    """Remplace les catégories vides par des valeurs manquantes."""

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
        {
            "categories_vides": categories_vides,
        },
    )


# ============================================================
# Règle 7 - strategie_manquants
# ============================================================

def strategie_manquants(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, CompteRendu]:
    """Applique la stratégie de gestion des valeurs manquantes.

    Les valeurs manquantes sont conservées à NA : aucune valeur inconnue
    n'est artificiellement imputée.

    Les produits ne sont pas supprimés ici. Les lignes sans code ont déjà
    été traitées par `dedupliquer_codes`.
    """

    res = df.copy()

    return res, _compte_rendu(
        "strategie_manquants",
        df,
        res,
        {},
    )


# ============================================================
# Lecture et pipeline complet
# ============================================================
# Ordre imposé : types, textes, doublons, unités, bornes, énergie,
# catégories, manquants. Chaque règle ajoutée se branche ici.

def lire_brut(
    chemin: str | Path,
) -> pd.DataFrame:
    """Lit un export CSV Open Food Facts en conservant `code` en texte."""

    return pd.read_csv(
        chemin,
        dtype={"code": "string"},
        low_memory=False,
    )


REGLES = [
    typer_colonnes,
    dedupliquer_codes,
    normaliser_unites,
    borner_nutriments,
    corriger_energie,
    traiter_categories_vides,
    strategie_manquants,
]


def nettoyer(
    brut: pd.DataFrame,
    regles=None,
) -> tuple[pd.DataFrame, list[CompteRendu]]:
    """Applique les règles dans l'ordre et retourne le résultat et le journal."""

    df = brut
    journal = []

    for regle in (
        regles if regles is not None else REGLES
    ):
        df, compte_rendu = regle(df)
        journal.append(compte_rendu)

    return df, journal