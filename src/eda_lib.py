"""Fonctions de calcul de l'EDA de référence (TP 10).

Aucun affichage ni tracé ici : le notebook `notebooks/eda_reference.ipynb`
appelle ces fonctions, trace et commente. Tout ce qui calcule est testé
dans `tests/test_eda_lib.py`.
"""

import numpy as np
import pandas as pd
from scipy import stats

if int(pd.__version__.split(".")[0]) < 3:
    pd.options.mode.copy_on_write = True  # déjà le comportement par défaut en pandas 3

GRAINE = 42

# les sept nutriments clés du module 3.3 (les fibres, à 59 % de manquants, n'en font pas partie)
NUTRIMENTS_CLES = [
    "energy-kcal_100g", "fat_100g", "saturated-fat_100g", "carbohydrates_100g",
    "sugars_100g", "proteins_100g", "salt_100g",
]
# toutes les colonnes en g pour 100 g (l'énergie a sa propre borne)
COLONNES_G_100G = [
    "fat_100g", "saturated-fat_100g", "carbohydrates_100g", "sugars_100g",
    "fiber_100g", "proteins_100g", "salt_100g", "sodium_100g",
    "fruits-vegetables-legumes_100g",
]
NUTRIMENT_MAX_G = 100.0
KCAL_MAX = 900.0
RAYON = "pnns_groups_1"
RAYON_INCONNU = "unknown"
GRADES = ["a", "b", "c", "d", "e"]


# ============================================================
# 0. Données
# ============================================================

def nettoyage_minimal(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoyage minimal du module 3.3, utilisé tant que le TP 9 n'est pas terminé.

    - doublons de codes-barres : première occurrence gardée ;
    - nutriment hors 0–100 g pour 100 g : ligne écartée ;
    - énergie hors 0–900 kcal pour 100 g : ligne écartée.

    Les manquants sont conservés. Sur l'échantillon partagé : 8 689 → 8 400
    produits, dont 6 674 dans un rayon connu (voir `rayons_connus`).
    À remplacer par `src.cleaning.nettoyer` quand le TP 9 sera livré.
    """
    res = df.drop_duplicates("code", keep="first")
    colonnes = [c for c in COLONNES_G_100G if c in res.columns]
    hors_bornes = ((res[colonnes] < 0) | (res[colonnes] > NUTRIMENT_MAX_G)).any(axis=1)
    res = res[~hors_bornes]
    kcal = res["energy-kcal_100g"]
    res = res[~((kcal < 0) | (kcal > KCAL_MAX))]
    return res.reset_index(drop=True)


def rayons_connus(df: pd.DataFrame) -> pd.DataFrame:
    """Écarte les produits sans rayon ou de rayon `unknown`, pour les comparaisons par rayon."""
    rayon = df[RAYON]
    return df[rayon.notna() & (rayon != RAYON_INCONNU)].reset_index(drop=True)


# ============================================================
# 1. Distributions par rayon
# ============================================================

def resume_univarie(s: pd.Series) -> pd.Series:
    """Résumé d'une variable numérique, calculé sur les valeurs présentes.

    Effectif (`n`), manquants, moyenne, médiane, écart-type, IQR, MAD
    (médiane des écarts absolus à la médiane), CV (écart-type / moyenne),
    asymétrie, aplatissement, quantiles 5 / 25 / 75 / 95 %, min et max.
    """
    x = s.dropna()
    p05, q1, mediane, q3, p95 = x.quantile([0.05, 0.25, 0.5, 0.75, 0.95])
    return pd.Series({
        "n": len(x), "manquants": int(s.isna().sum()),
        "moyenne": x.mean(), "mediane": mediane, "ecart_type": x.std(),
        "IQR": q3 - q1, "MAD": stats.median_abs_deviation(x),
        "CV": x.std() / x.mean(), "asymetrie": x.skew(), "aplatissement": x.kurt(),
        "p05": p05, "Q1": q1, "Q3": q3, "p95": p95, "min": x.min(), "max": x.max(),
    })


def _effectifs_par_rayon(df: pd.DataFrame, colonnes: list[str]) -> pd.DataFrame:
    """Nombre de valeurs présentes par (nutriment, rayon), en format long."""
    effectifs = df.groupby(RAYON, observed=True)[colonnes].count()
    effectifs = effectifs.rename_axis(columns="nutriment").T.stack().rename("n")
    return effectifs.reset_index()


def profil_par_rayon(df: pd.DataFrame, colonnes: list[str], min_n: int = 30) -> pd.DataFrame:
    """Effectif, quartiles, médiane et moyenne par nutriment et par rayon.

    Une ligne par (nutriment, rayon). Les groupes de moins de `min_n` valeurs
    présentes sont écartés : une médiane sur 12 produits ne se commente pas.
    Ils sont listés par `rayons_ecartes`.
    """
    lignes = []
    for colonne in colonnes:
        for rayon, x in df.groupby(RAYON, observed=True)[colonne]:
            x = x.dropna()
            if len(x) < min_n:
                continue
            q1, mediane, q3 = x.quantile([0.25, 0.5, 0.75])
            lignes.append({"nutriment": colonne, "rayon": rayon, "n": len(x),
                           "Q1": q1, "mediane": mediane, "Q3": q3, "moyenne": x.mean()})
    colonnes_sortie = ["nutriment", "rayon", "n", "Q1", "mediane", "Q3", "moyenne"]
    return pd.DataFrame(lignes, columns=colonnes_sortie).set_index(["nutriment", "rayon"])


def rayons_ecartes(df: pd.DataFrame, colonnes: list[str], min_n: int = 30) -> pd.DataFrame:
    """Les (nutriment, rayon) de moins de `min_n` valeurs présentes, avec leur effectif."""
    effectifs = _effectifs_par_rayon(df, colonnes)
    return effectifs[effectifs["n"] < min_n].rename(columns={RAYON: "rayon"}).reset_index(drop=True)


def croisement_rayon_grade(df: pd.DataFrame, min_n: int = 30) -> pd.DataFrame:
    """Effectifs rayon × grade Nutri-Score, limités aux grades a–e.

    Les grades `unknown` et `not-applicable` sont écartés : ce ne sont pas
    des notes. Les rayons de moins de `min_n` produits notés sont écartés
    aussi. Pour les parts par rayon, voir `parts_par_ligne`.
    """
    notes = df[df["nutriscore_grade"].isin(GRADES)]
    table = pd.crosstab(notes[RAYON], notes["nutriscore_grade"])
    table = table.reindex(columns=GRADES, fill_value=0)
    return table[table.sum(axis=1) >= min_n]


def parts_par_ligne(table: pd.DataFrame) -> pd.DataFrame:
    """Un tableau d'effectifs en % par ligne (chaque ligne somme à 100)."""
    return table.div(table.sum(axis=1), axis=0) * 100


def v_cramer(table: pd.DataFrame) -> float:
    """V de Cramér d'un tableau de contingence : 0 = indépendance, 1 = liaison parfaite.

    V = racine(khi² / (n × (min(lignes, colonnes) − 1))). Les lignes et colonnes
    vides sont retirées, sinon le khi² n'est pas défini.
    """
    table = table.loc[table.sum(axis=1) > 0, table.sum(axis=0) > 0]
    khi2 = stats.chi2_contingency(table, correction=False)[0]
    n = table.to_numpy().sum()
    return float(np.sqrt(khi2 / (n * (min(table.shape) - 1))))


# ============================================================
# 2. Complétude et qualité
# ============================================================

def completude_par_groupe(df: pd.DataFrame, groupe: str, colonnes: list[str], min_n: int = 20) -> pd.DataFrame:
    """Taux de présence par nutriment, taux de fiches complètes et présence du score, par groupe."""
    raise NotImplementedError


def incoherences_metier(df: pd.DataFrame) -> pd.DataFrame:
    """Un drapeau booléen par produit et par incohérence. On compte, on ne corrige pas."""
    raise NotImplementedError


# ============================================================
# 3. Corrélations
# ============================================================

def correlations_nutriscore(df: pd.DataFrame, colonnes: list[str], cible: str, min_n: int = 30) -> pd.DataFrame:
    """Pearson et Spearman de chaque nutriment avec la cible, effectifs, tri par |Spearman|."""
    raise NotImplementedError


def paires_redondantes(matrice: pd.DataFrame, seuil: float = 0.8) -> pd.DataFrame:
    """Paires de colonnes dont la corrélation dépasse `seuil` en valeur absolue."""
    raise NotImplementedError


def correlations_par_rayon(df: pd.DataFrame, colonne: str, cible: str, min_n: int = 30) -> pd.DataFrame:
    """Spearman entre `colonne` et `cible` dans chaque rayon d'au moins `min_n` paires."""
    raise NotImplementedError


# ============================================================
# 4. Extrêmes restants
# ============================================================

def zscore_robuste(s: pd.Series) -> pd.Series:
    """Écart à la médiane en nombre de MAD (0,6745 × (x − médiane) / MAD)."""
    raise NotImplementedError


def extremes_restants(df: pd.DataFrame, colonnes: list[str], seuil: float = 3.5) -> pd.DataFrame:
    """Valeurs à plus de `seuil` MAD de la médiane de leur rayon, en format long, triées par |z|."""
    raise NotImplementedError


# ============================================================
# 5. Hypothèses
# ============================================================

def comparer_deux_groupes(a: pd.Series, b: pd.Series) -> pd.Series:
    """Médianes, d de Cohen et test de Mann-Whitney entre deux groupes."""
    raise NotImplementedError
