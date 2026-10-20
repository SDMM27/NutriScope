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
# seuils des incohérences métier (les trois premiers sont ceux de src/cleaning.py)
TOLERANCE_SOUS_TOTAL_G = 0.5   # sucres ≤ glucides + 0,5 ; saturés ≤ lipides + 0,5
SEL_PAR_SODIUM = 2.5
TOLERANCE_SEL_SODIUM = 0.1
ECART_ENERGIE_KCAL = 150.0     # écart toléré entre énergie déclarée et calculée
CIBLE = "nutriscore_score"
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
    """Complétude par groupe (rayon, marque…), en %, avec l'effectif `n`.

    Pour chaque groupe d'au moins `min_n` produits : taux de présence de
    chaque colonne, `fiches_completes` (toutes les colonnes présentes) et
    `score_present` (`nutriscore_score` renseigné). Les produits sans valeur
    de `groupe` sont ignorés. Tri par `fiches_completes` décroissant.
    """
    presence = df[colonnes].notna()
    presence["fiches_completes"] = presence.all(axis=1)
    presence["score_present"] = df[CIBLE].notna()
    groupes = presence.groupby(df[groupe], observed=True)
    table = groupes.mean() * 100
    table.insert(0, "n", groupes.size())
    table = table[table["n"] >= min_n]
    return table.sort_values(["fiches_completes", "n"], ascending=False, kind="stable")


def incoherences_metier(df: pd.DataFrame) -> pd.DataFrame:
    """Un drapeau booléen par produit et par incohérence. On compte, on ne corrige pas.

    - `sucres_sup_glucides` : sucres > glucides + TOLERANCE_SOUS_TOTAL_G ;
    - `satures_sup_lipides` : saturés > lipides + TOLERANCE_SOUS_TOTAL_G ;
    - `sel_different_sodium` : |sel − 2,5 × sodium| > TOLERANCE_SEL_SODIUM ;
    - `energie_ecart_449` : énergie déclarée à plus de ECART_ENERGIE_KCAL (150 kcal)
      de l'énergie calculée 4 × glucides + 4 × protéines + 9 × lipides ;
    - `energie_nulle_macros` : 0 kcal alors qu'un macronutriment est > 0.

    Une valeur manquante ne lève aucun drapeau.
    """
    kcal = df["energy-kcal_100g"]
    macro_positif = (df[["carbohydrates_100g", "proteins_100g", "fat_100g"]] > 0).any(axis=1)
    return pd.DataFrame({
        "sucres_sup_glucides": df["sugars_100g"] > df["carbohydrates_100g"] + TOLERANCE_SOUS_TOTAL_G,
        "satures_sup_lipides": df["saturated-fat_100g"] > df["fat_100g"] + TOLERANCE_SOUS_TOTAL_G,
        "sel_different_sodium": (df["salt_100g"] - SEL_PAR_SODIUM * df["sodium_100g"]).abs() > TOLERANCE_SEL_SODIUM,
        "energie_ecart_449": (kcal - energie_calculee(df)).abs() > ECART_ENERGIE_KCAL,
        "energie_nulle_macros": (kcal == 0) & macro_positif,
    })


def energie_calculee(df: pd.DataFrame) -> pd.Series:
    """kcal attendues : 4 × glucides + 4 × protéines + 9 × lipides (NA si l'un des trois manque)."""
    return 4 * df["carbohydrates_100g"] + 4 * df["proteins_100g"] + 9 * df["fat_100g"]


# ============================================================
# 3. Corrélations
# ============================================================

def _pearson_spearman(x: pd.Series, y: pd.Series) -> tuple[float, float]:
    """(Pearson, Spearman) de deux séries sans manquants ; NaN si l'une est constante."""
    if x.nunique() < 2 or y.nunique() < 2:
        return np.nan, np.nan   # corrélation non définie : scipy renverrait NaN avec un avertissement
    return float(stats.pearsonr(x, y)[0]), float(stats.spearmanr(x, y)[0])


def correlations_nutriscore(df: pd.DataFrame, colonnes: list[str], cible: str, min_n: int = 30) -> pd.DataFrame:
    """Pearson et Spearman de chaque nutriment avec la cible, effectifs, tri par |Spearman|.

    Pour chaque colonne, seuls les produits qui ont à la fois la colonne et la cible
    comptent (`n` = nombre de paires complètes) ; la corrélation de deux colonnes
    n'est donc pas calculée sur les mêmes produits. Sous `min_n` paires, le nutriment
    est écarté.

    - Pearson mesure la liaison linéaire, sensible aux valeurs extrêmes ;
    - Spearman mesure la liaison monotone (corrélation des rangs), robuste aux extrêmes.
    Spearman est le défaut, Pearson sert de comparaison : un grand écart entre les
    deux signale une relation courbe ou tirée par quelques extrêmes.
    """
    lignes = []
    for colonne in colonnes:
        paires = df[[colonne, cible]].dropna()
        if len(paires) < min_n:
            continue
        pearson, spearman = _pearson_spearman(paires[colonne], paires[cible])
        lignes.append({"nutriment": colonne, "n": len(paires), "pearson": pearson, "spearman": spearman})
    table = pd.DataFrame(lignes, columns=["nutriment", "n", "pearson", "spearman"]).set_index("nutriment")
    return table.reindex(table["spearman"].abs().sort_values(ascending=False).index)


def paires_redondantes(matrice: pd.DataFrame, seuil: float = 0.8) -> pd.DataFrame:
    """Paires de colonnes dont la corrélation dépasse `seuil` en valeur absolue.

    On ne lit que le triangle supérieur de la matrice (`k=1` exclut la diagonale,
    qui vaut toujours 1) : chaque paire apparaît une seule fois. Tri par |corrélation|.
    """
    haut = np.triu(np.ones(matrice.shape, dtype=bool), k=1)
    paires = matrice.where(haut).stack().rename("correlation").reset_index()
    paires.columns = ["a", "b", "correlation"]
    paires = paires[paires["correlation"].abs() >= seuil]
    ordre = paires["correlation"].abs().sort_values(ascending=False).index
    return paires.loc[ordre].reset_index(drop=True)


def correlations_par_rayon(df: pd.DataFrame, colonne: str, cible: str, min_n: int = 30) -> pd.DataFrame:
    """Spearman entre `colonne` et `cible` dans chaque rayon d'au moins `min_n` paires.

    Un rayon avec moins de `min_n` paires complètes est absent du résultat : c'est
    voulu, on ne baisse pas le seuil. Sert à comparer à la corrélation globale :
    si elle change de signe ou d'ampleur d'un rayon à l'autre, la valeur globale
    mélange des populations différentes (paradoxe de Simpson). Tri par Spearman décroissant.
    """
    lignes = []
    for rayon, groupe in df.groupby(RAYON, observed=True):
        paires = groupe[[colonne, cible]].dropna()
        if len(paires) < min_n:
            continue
        lignes.append({"rayon": rayon, "n": len(paires),
                       "spearman": _pearson_spearman(paires[colonne], paires[cible])[1]})
    table = pd.DataFrame(lignes, columns=["rayon", "n", "spearman"]).set_index("rayon")
    return table.sort_values("spearman", ascending=False)


# ============================================================
# 4. Extrêmes restants
# ============================================================

def zscore_robuste(s: pd.Series) -> pd.Series:
    """Écart à la médiane en nombre de MAD (0,6745 × (x − médiane) / MAD).

    Médiane et MAD (médiane des écarts absolus à la médiane) ne sont pas tirées
    par les extrêmes, contrairement à la moyenne et à l'écart-type du z-score
    classique. Le facteur 0,6745 met l'échelle en équivalent d'écarts-types pour
    une loi normale, d'où le seuil usuel de 3,5.
    Les manquants restent manquants. Si la MAD vaut 0 (plus de la moitié des
    valeurs sont identiques, par exemple 0 g de lipides dans les boissons), le
    z-score n'est pas défini : on renvoie NaN, pas une valeur infinie.
    """
    x = s.astype("float64")
    mad = stats.median_abs_deviation(x.dropna())
    if not mad > 0:   # MAD nulle ou série vide (comparaison fausse avec NaN aussi)
        return pd.Series(np.nan, index=s.index)
    return 0.6745 * (x - x.median()) / mad


def extremes_restants(df: pd.DataFrame, colonnes: list[str], seuil: float = 3.5) -> pd.DataFrame:
    """Valeurs à plus de `seuil` MAD de la médiane de leur rayon, en format long, triées par |z|.

    Une ligne par (produit, nutriment) extrême : code, nom, rayon, nutriment, valeur,
    médiane du rayon et `z`. On compare un produit à son rayon, pas à tout le
    périmètre : 60 g de sucres est banal dans les snacks sucrés, extrême dans les
    viandes. Les groupes à MAD nulle ne sont pas jugés (voir `zscore_robuste`).
    Aucun extrême : un tableau vide, avec les mêmes colonnes.
    """
    colonnes_sortie = ["code", "product_name", "rayon", "nutriment", "valeur", "mediane_rayon", "z"]
    morceaux = []
    for colonne in colonnes:
        par_rayon = df.groupby(RAYON, observed=True)[colonne]
        z = par_rayon.transform(zscore_robuste)
        mediane = par_rayon.transform("median")
        extremes = z.abs() > seuil          # False pour les NaN : manquants et groupes à MAD nulle
        morceaux.append(pd.DataFrame({
            "code": df.loc[extremes, "code"], "product_name": df.loc[extremes, "product_name"],
            "rayon": df.loc[extremes, RAYON], "nutriment": colonne, "valeur": df.loc[extremes, colonne],
            "mediane_rayon": mediane[extremes], "z": z[extremes],
        }))
    resultat = pd.concat(morceaux, ignore_index=True).reindex(columns=colonnes_sortie)
    return resultat.sort_values("z", key=abs, ascending=False, kind="stable").reset_index(drop=True)


# ============================================================
# 5. Hypothèses
# ============================================================

def comparer_deux_groupes(a: pd.Series, b: pd.Series) -> pd.Series:
    """Compare une variable numérique entre deux groupes : médianes, d de Cohen, Mann-Whitney.

    Trois mesures complémentaires, calculées sur les valeurs présentes :

    - `diff_medianes` (médiane de `a` − médiane de `b`) : l'écart réel, dans l'unité
      de la variable, robuste aux extrêmes ;
    - `d_cohen` : l'écart des moyennes rapporté à l'écart-type regroupé des deux
      groupes. Taille d'effet sans unité (≈ 0,2 petit, 0,5 moyen, 0,8 grand),
      qui ne gonfle pas avec l'effectif ;
    - `U` et `p_value` : test de Mann-Whitney bilatéral, non paramétrique (sur les
      rangs), adapté aux distributions asymétriques des nutriments. La p-value
      devient minuscule dès que `n` est grand : on la lit toujours à côté du d.

    Un groupe vide, ou un écart-type regroupé nul (les deux groupes constants),
    donne `d_cohen` et le test à NaN plutôt qu'une division par zéro ou une erreur.
    Test exploratoire : la rigueur inférentielle (corrections, hypothèses) est vue au 3.4.
    """
    a, b = a.dropna(), b.dropna()
    na, nb = len(a), len(b)
    if na == 0 or nb == 0:
        return pd.Series({"n_a": na, "n_b": nb, "mediane_a": np.nan, "mediane_b": np.nan,
                          "diff_medianes": np.nan, "d_cohen": np.nan, "U": np.nan, "p_value": np.nan})
    if na + nb > 2:
        var_regroupee = ((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2)
        ecart_type = np.sqrt(var_regroupee)
    else:
        ecart_type = 0.0
    d = float((a.mean() - b.mean()) / ecart_type) if ecart_type > 0 else np.nan
    if a.nunique() < 2 and b.nunique() < 2 and a.iloc[0] == b.iloc[0]:
        u, p = np.nan, np.nan        # deux groupes constants et identiques : rien à départager
    else:
        u, p = stats.mannwhitneyu(a, b, alternative="two-sided", method="asymptotic")
    return pd.Series({
        "n_a": na, "n_b": nb,
        "mediane_a": a.median(), "mediane_b": b.median(), "diff_medianes": a.median() - b.median(),
        "d_cohen": d, "U": float(u), "p_value": float(p),
    })
