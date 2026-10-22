
"""Fonctions de visualisation réutilisables pour le TP11.

Les fonctions de ce module construisent les figures à partir de données ou
de résultats déjà calculés par l'EDA. Elles renvoient (fig, ax) afin que
l'appelant puisse afficher ou exporter la figure.
"""

from collections.abc import Mapping

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from src import eda_lib


# Palette reprise des prototypes du notebook TP11.
BLEU = "#2a78d6"
GRIS = "#c3c2b7"
VERT = "#4a8f55"
ROUGE = "#c94c4c"
ORANGE = "#e5a142"
ENCRE = "#0b0b0b"


def _verifier_colonnes(
    df: pd.DataFrame,
    colonnes: set[str],
    nom: str,
) -> None:
    """Vérifie la présence des colonnes nécessaires."""
    manquantes = colonnes - set(df.columns)
    if manquantes:
        raise ValueError(
            f"{nom} : colonnes manquantes : {sorted(manquantes)}"
        )

# 1. Les snacks sucrés sont plus concentrés en sucres que les boissons
def tracer_medianes_sucres(
    profil_sucres: pd.DataFrame,
) -> tuple[Figure, Axes]:
    """Trace les médianes de sucres par rayon avec leurs effectifs.

    `profil_sucres` est indexé par rayon et contient `mediane` et `n`.
    """
    _verifier_colonnes(profil_sucres, {"mediane", "n"}, "profil_sucres")

    donnees = profil_sucres.dropna(subset=["mediane"]).copy()
    if donnees.empty:
        raise ValueError("Aucune médiane de sucres exploitable.")

    donnees = donnees.sort_values("mediane")
    donnees = donnees.iloc[::-1]

    fig, ax = plt.subplots(figsize=(10, max(4, 0.45 * len(donnees))))
    positions = np.arange(len(donnees))

    barres = ax.barh(
        positions,
        donnees["mediane"],
        color=BLEU,
        height=0.65,
    )

    ax.set_yticks(positions, labels=donnees.index.astype(str))
    ax.set_xlabel("Médiane des sucres (g / 100 g)")
    ax.set_ylabel("Rayon")
    ax.set_title("La teneur médiane en sucres varie selon les rayons")
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)

    decalage = max(float(donnees["mediane"].max()) * 0.015, 0.1)
    for barre, (_, ligne) in zip(barres, donnees.iterrows()):
        ax.text(
            barre.get_width() + decalage,
            barre.get_y() + barre.get_height() / 2,
            f"{barre.get_width():.1f}".replace(".", ",")
            + f"  (n={int(ligne['n'])})",
            va="center",
            fontsize=9,
        )

    ax.set_xlim(left=0)
    fig.tight_layout()
    return fig, ax

# 2. Les snacks sucrés présentent fréquemment un Nutri-Score E, contrairement aux fruits et légumes
def tracer_grades_mis_en_avant(
    produits: pd.DataFrame,
) -> tuple[Figure, Axes]:
    """Compare les grades Nutri-Score des snacks sucrés et des fruits et légumes.

    Les proportions sont calculées parmi les produits ayant un grade A à E.
    Les valeurs unknown, not-applicable et manquantes sont exclues.
    """
    _verifier_colonnes(
        produits,
        {"pnns_groups_1", "nutriscore_grade"},
        "produits",
    )

    rayons = ["Sugary snacks", "Fruits and vegetables"]
    traductions = {
        "Sugary snacks": "Snacks sucrés",
        "Fruits and vegetables": "Fruits et légumes",
    }
    grades = ["a", "b", "c", "d", "e"]

    couleurs_grades = {
        "a": "#038141",
        "b": "#85BB2F",
        "c": "#FECB02",
        "d": "#EE8100",
        "e": "#E63E11",
    }

    donnees = produits.loc[
        produits["pnns_groups_1"].isin(rayons),
        ["pnns_groups_1", "nutriscore_grade"],
    ].copy()

    donnees["nutriscore_grade"] = (
        donnees["nutriscore_grade"]
        .astype("string")
        .str.strip()
        .str.lower()
    )
    donnees = donnees.loc[donnees["nutriscore_grade"].isin(grades)]

    effectifs = pd.crosstab(
        donnees["pnns_groups_1"],
        donnees["nutriscore_grade"],
    ).reindex(index=rayons, columns=grades, fill_value=0)

    totaux = effectifs.sum(axis=1)
    if (totaux == 0).any():
        absents = [
            traductions[rayon]
            for rayon in totaux.index[totaux == 0]
        ]
        raise ValueError(
            f"Aucun produit avec un grade A à E pour : {absents}"
        )

    proportions = effectifs.div(totaux, axis=0) * 100
    proportions.index = proportions.index.map(traductions)
    proportions.columns = [grade.upper() for grade in proportions.columns]

    fig, ax = plt.subplots(figsize=(10, 4.5))

    proportions.plot(
        kind="barh",
        stacked=True,
        ax=ax,
        color=[couleurs_grades[grade] for grade in grades],
        width=0.58,
    )

    # Annoter chaque segment avec son pourcentage.
    for i, rayon in enumerate(proportions.index):
        position_gauche = 0.0

        for grade in [g.upper() for g in grades]:
            pourcentage = proportions.loc[rayon, grade]

            if pourcentage >= 5:
                couleur_texte = (
                    "white" if grade in {"A", "D", "E"} else ENCRE
                )
                ax.text(
                    position_gauche + pourcentage / 2,
                    i,
                    f"{pourcentage:.1f} %".replace(".", ","),
                    ha="center",
                    va="center",
                    fontsize=9,
                    fontweight="bold",
                    color=couleur_texte,
                )

            position_gauche += pourcentage

    ax.set_xlabel("Part des produits notés (%)")
    ax.set_ylabel("")
    ax.set_title(
        "Les snacks sucrés et les fruits et légumes "
        "présentent des grades Nutri-Score très différents"
    )
    ax.set_xlim(0, 100)
    ax.legend(
        title="Nutri-Score",
        labels=["A", "B", "C", "D", "E"],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=5,
        frameon=False,
    )
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)

    fig.text(
        0.01,
        0.01,
        "Source : Open Food Facts, échantillon français après nettoyage minimal. "
        "Les produits sans grade exploitable sont exclus ; les parts sont "
        "calculées séparément dans chaque rayon.",
        ha="left",
        fontsize=8,
        color="#52514e",
    )

    fig.tight_layout(rect=(0, 0.12, 1, 1))
    return fig, ax
 
# 3. Un produit sur cinq ne possède pas de rayon exploitable
def tracer_couverture_rayons(produits):
    """Compare la couverture des rayons sur l'ensemble des produits."""
    colonne_rayon = eda_lib.RAYON

    _verifier_colonnes(produits, {colonne_rayon}, "produits")

    total = len(produits)
    if total == 0:
        raise ValueError("Impossible de tracer un échantillon vide.")

    nombre_connus = len(eda_lib.rayons_connus(produits))
    nombre_unknown = int(
        produits[colonne_rayon].eq(eda_lib.RAYON_INCONNU).sum()
    )
    nombre_absents = int(produits[colonne_rayon].isna().sum())
    nombre_non_exploitables = total - nombre_connus

    if nombre_non_exploitables != nombre_unknown + nombre_absents:
        raise ValueError(
            "Les produits sans rayon exploitable ne correspondent pas "
            "à la somme des catégories unknown et des valeurs absentes."
        )

    part_connus = nombre_connus / total * 100
    part_non_exploitables = nombre_non_exploitables / total * 100

    fig, ax = plt.subplots(figsize=(9, 2.8))

    ax.barh(
        y=0,
        width=part_connus,
        color=BLEU,
        height=0.55,
    )
    ax.barh(
        y=0,
        width=part_non_exploitables,
        left=part_connus,
        color=GRIS,
        height=0.55,
    )

    ax.text(
        part_connus / 2,
        0,
        f"{part_connus:.1f} %\n{nombre_connus:,}".replace(",", " "),
        ha="center",
        va="center",
        color="white",
        fontweight="bold",
    )
    ax.text(
        part_connus + part_non_exploitables / 2,
        0,
        f"{part_non_exploitables:.1f} %\n"
        f"{nombre_non_exploitables:,}".replace(",", " "),
        ha="center",
        va="center",
        color=ENCRE,
        fontweight="bold",
    )

    ax.set_xlim(0, 100)
    ax.set_xticks(np.arange(0, 101, 20))
    ax.set_xlabel("Part des produits (%)")
    ax.set_yticks([0], labels=["Échantillon"])
    ax.set_title("Un produit sur cinq n’a pas de rayon exploitable")

    ax.text(
        0,
        -0.75,
        f"Sans rayon exploitable : {nombre_unknown:,} unknown et "
        f"{nombre_absents:,} valeur(s) manquante(s).".replace(",", " "),
        transform=ax.transData,
        ha="left",
        va="top",
        fontsize=9,
        color="#52514e",
    )

    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)
    fig.tight_layout()

    return fig, ax

# 4. La complétude nutritionnelle reste imparfaite
def tracer_completude_rayons(
    completude: pd.DataFrame,
) -> tuple[Figure, Axes]:
    """Compare les effectifs et la complétude des fiches par rayon.

    `completude` est le résultat de eda_lib.completude_par_groupe, avec
    les colonnes `n`, `fiches_completes` et `score_present`.
    """
    colonnes = {"n", "fiches_completes", "score_present"}
    _verifier_colonnes(completude, colonnes, "completude")

    if completude.empty:
        raise ValueError("Aucune donnée de complétude à représenter.")

    donnees = completude.copy()

    for colonne in ("n", "fiches_completes", "score_present"):
        donnees[colonne] = pd.to_numeric(
            donnees[colonne], errors="raise"
        )

    if (
        (donnees["n"] < 0).any()
        or (~donnees["fiches_completes"].between(0, 100)).any()
        or (~donnees["score_present"].between(0, 100)).any()
    ):
        raise ValueError("Effectifs ou taux de complétude hors limites.")

    # Estimations des effectifs à partir des taux EDA en pourcentage.
    donnees["avec_nutriscore"] = (
        donnees["n"] * donnees["score_present"] / 100
    ).round().astype(int)
    donnees["fiches_completes_n"] = (
        donnees["n"] * donnees["fiches_completes"] / 100
    ).round().astype(int)

    donnees = donnees.sort_values(
        ["fiches_completes", "n"], ascending=True, kind="stable"
    )

    positions = np.arange(len(donnees))
    hauteur = 0.24

    fig, ax = plt.subplots(
        figsize=(12, max(5, 0.55 * len(donnees)))
    )

    ax.barh(
        positions - hauteur,
        donnees["n"],
        height=hauteur,
        color=GRIS,
        label="Articles dans le rayon",
    )
    ax.barh(
        positions,
        donnees["avec_nutriscore"],
        height=hauteur,
        color=BLEU,
        label="Nutri-Score renseigné",
    )
    ax.barh(
        positions + hauteur,
        donnees["fiches_completes_n"],
        height=hauteur,
        color=VERT,
        label="Sept nutriments renseignés",
    )

    ax.set_yticks(positions, labels=donnees.index.astype(str))
    ax.set_xlabel("Nombre d'articles")
    ax.set_ylabel("Rayon")
    ax.set_title("La complétude des fiches varie selon les rayons")
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right")

    maximum = float(donnees["n"].max())
    position_taux = maximum * 1.08

    for position, (_, ligne) in zip(positions, donnees.iterrows()):
        ax.text(
            position_taux,
            position,
            f"{ligne['fiches_completes']:.1f} %".replace(".", ","),
            va="center",
            fontsize=9,
        )

    ax.text(
        position_taux,
        -0.8,
        "Complètes",
        ha="left",
        va="bottom",
        fontsize=9,
        fontweight="bold",
    )

    ax.set_xlim(0, maximum * 1.32)
    fig.text(
        0.01,
        0.01,
        "Une fiche complète contient les sept nutriments clés. "
        "Les effectifs dérivés des taux sont arrondis. "
        "Les rayons de moins de 20 articles sont exclus.",
        ha="left",
        fontsize=9,
        color="#52514e",
    )

    fig.tight_layout(rect=(0, 0.04, 1, 1))
    return fig, ax

# 5. Certains produits présentent un écart important entre deux estimations énergétiques
def tracer_ecarts_energetiques(comparables: pd.DataFrame):
    """Compare l'énergie calculée à l'énergie déclarée pour les cas les plus extrêmes."""
    colonnes = {"product_name", "ecart_energie"}
    _verifier_colonnes(comparables, colonnes, "comparables")

    # Conserver les écarts exploitables et identifier les 15 plus importants.
    ecarts = comparables.loc[
        comparables["ecart_energie"].notna(),
        ["product_name", "ecart_energie"],
    ].copy()

    ecarts = ecarts.sort_values(
        "ecart_energie",
        key=lambda serie: serie.abs(),
        ascending=False,
    ).head(15)

    if ecarts.empty:
        raise ValueError("Aucun écart énergétique exploitable.")

    # Préparer des libellés lisibles, y compris si le nom manque.
    noms = ecarts["product_name"].fillna("Produit sans nom").astype(str)
    ecarts["libelle"] = [
        f"{nom[:45]} ({i})" for i, nom in enumerate(noms, start=1)
    ]

    ecarts = ecarts.sort_values("ecart_energie")

    fig, ax = plt.subplots(figsize=(11, 7))

    couleurs = [
        BLEU if valeur >= 0 else GRIS
        for valeur in ecarts["ecart_energie"]
    ]

    barres = ax.barh(
        ecarts["libelle"],
        ecarts["ecart_energie"],
        color=couleurs,
    )

    ax.axvline(0, color=ENCRE, linewidth=0.8)
    ax.set_title("Les écarts énergétiques les plus importants")
    ax.set_xlabel(
        "Énergie calculée − énergie déclarée (kcal/100 g)"
    )
    ax.set_ylabel("")
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)

    # Afficher la valeur de chaque écart au bout de sa barre.
    for barre, valeur in zip(barres, ecarts["ecart_energie"]):
        decalage = 5 if valeur >= 0 else -5
        ax.annotate(
            f"{valeur:+.0f}",
            xy=(
                barre.get_width(),
                barre.get_y() + barre.get_height() / 2,
            ),
            xytext=(decalage, 0),
            textcoords="offset points",
            va="center",
            ha="left" if valeur >= 0 else "right",
            fontsize=8,
        )

    fig.tight_layout()
    return fig, ax

# 6. Les valeurs extrêmes ne sont pas toutes des erreurs
def tracer_bilan_valeurs_extremes(
    extremes: pd.DataFrame,
    total_rayons_connus: int,
    par_rayon: pd.DataFrame,
) -> tuple[Figure, np.ndarray]:
    """Illustre un cas extrême et présente le bilan de la revue manuelle."""

    colonnes_extremes = {
        "code", "product_name", "rayon", "nutriment", "valeur", "z"
    }
    _verifier_colonnes(extremes, colonnes_extremes, "extremes")

    nutriment = "saturated-fat_100g"
    rayon = "Fruits and vegetables"
    code_cible = "3760159010608"

    _verifier_colonnes(
        par_rayon,
        {"code", "product_name", eda_lib.RAYON, nutriment},
        "par_rayon",
    )

    if total_rayons_connus <= 0:
        raise ValueError("Le nombre de produits à rayon connu doit être positif.")

    # Fréquence globale : un produit est compté une seule fois.
    nb_produits_extremes = extremes["code"].nunique()
    taux_extremes = 100 * nb_produits_extremes / total_rayons_connus

    # Produits du rayon retenu pour l'exemple.
    produits = par_rayon.loc[
        par_rayon[eda_lib.RAYON].eq(rayon),
        ["code", "product_name", nutriment],
    ].dropna(subset=[nutriment]).copy()

    if produits.empty:
        raise ValueError(
            f"Aucun produit avec {nutriment} renseigné dans le rayon {rayon!r}."
        )

    produits[nutriment] = pd.to_numeric(
        produits[nutriment], errors="coerce"
    )
    produits = produits.dropna(subset=[nutriment]).reset_index(drop=True)

    cible = produits.loc[produits["code"].astype(str).eq(code_cible)]
    if cible.empty:
        raise ValueError(
            f"Le produit cible {code_cible} est absent du rayon {rayon!r}."
        )

    position_cible = int(cible.index[0])
    valeur_cible = float(cible[nutriment].iloc[0])
    mediane = float(produits[nutriment].median())

    # Bilan de la revue manuelle des 15 cas examinés.
    categories = [
        "Valeurs plausibles",
        "Valeurs résiduelles",
        "Plausible, mauvais rayon",
    ]
    effectifs = [9, 5, 1]
    couleurs = [BLEU, GRIS, ORANGE]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # Panneau gauche : distribution des graisses saturées.
    ax = axes[0]
    positions = np.arange(len(produits))

    ax.scatter(
        positions,
        produits[nutriment],
        color=BLEU,
        alpha=0.55,
        s=25,
        label="Autres produits",
        edgecolors="none",
    )

    ax.scatter(
        position_cible,
        valeur_cible,
        color=ROUGE,
        s=85,
        zorder=3,
        label="Noix de coco râpée",
        edgecolors="white",
        linewidths=0.8,
    )

    ax.axhline(
        mediane,
        color=ENCRE,
        linestyle="--",
        linewidth=1.2,
        label=f"Médiane du rayon : {mediane:.1f} g/100 g".replace(".", ","),
    )

    ax.annotate(
        f"Noix de coco râpée : {valeur_cible:.1f} g/100 g".replace(".", ","),
        xy=(position_cible, valeur_cible),
        xytext=(0.48, 0.83),
        textcoords="axes fraction",
        arrowprops={"arrowstyle": "->", "color": ROUGE},
        fontsize=9,
        color=ROUGE,
        ha="center",
    )

    ax.set_title("Un cas extrême dans les fruits et légumes")
    ax.set_xlabel("Produits du rayon (ordre arbitraire)")
    ax.set_ylabel("Graisses saturées (g / 100 g)")
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", fontsize=8)

    ax.text(
        0.02,
        0.97,
        f"{len(produits):,} produits avec une valeur renseignée".replace(",", " "),
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8,
        color="#52514e",
    )

    # Panneau droit : résultats de la revue manuelle.
    ax = axes[1]
    barres = ax.barh(categories, effectifs, color=couleurs, height=0.6)
    ax.invert_yaxis()
    ax.set_xlim(0, 10)
    ax.set_xlabel("Nombre de cas parmi les 15 examinés")
    ax.set_title("Revue manuelle des 15 cas les plus extrêmes")
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)

    for barre, effectif in zip(barres, effectifs):
        ax.text(
            effectif + 0.15,
            barre.get_y() + barre.get_height() / 2,
            str(effectif),
            va="center",
            fontsize=10,
        )

    fig.suptitle(
        "Une valeur extrême n'est pas nécessairement une erreur\n"
        f"{nb_produits_extremes:,} produits sur {total_rayons_connus:,} "
        f"({taux_extremes:.1f} %) présentent au moins une valeur extrême".replace(",", " ").replace(".", ","),
        fontsize=13,
        fontweight="bold",
    )

    fig.text(
        0.5,
        0.015,
        "La revue manuelle porte sur 15 cas sélectionnés parmi les plus extrêmes ; "
        "elle n'est pas représentative de l'ensemble des produits signalés.",
        ha="center",
        fontsize=8,
        color="#52514e",
    )

    fig.tight_layout(rect=(0, 0.06, 1, 0.86))
    return fig, axes

# 7. La qualité des données conditionne la fiabilité de NutriScope=
def tracer_synthese_qualite(
    perimetre: pd.DataFrame,
    comparables: pd.DataFrame,
    extremes: pd.DataFrame,
):
    """Présente la couverture, la complétude et les contrôles de qualité."""

    colonnes_nutriments = set(eda_lib.NUTRIMENTS_CLES)
    _verifier_colonnes(
        perimetre,
        {eda_lib.RAYON} | colonnes_nutriments,
        "perimetre",
    )
    _verifier_colonnes(comparables, {"ecart_energie"}, "comparables")
    _verifier_colonnes(extremes, {"code"}, "extremes")

    # ---------------------------------------------------------
    # 1. Calcul des indicateurs
    # ---------------------------------------------------------
    total = len(perimetre)
    rayons_connus = eda_lib.rayons_connus(perimetre)
    n_rayons_connus = len(rayons_connus)

    n_complets = int(
        rayons_connus[eda_lib.NUTRIMENTS_CLES]
        .notna()
        .all(axis=1)
        .sum()
    )

    taux_couverture = (
        100 * n_rayons_connus / total if total else 0
    )
    taux_completude = (
        100 * n_complets / n_rayons_connus
        if n_rayons_connus
        else 0
    )

    ecarts = comparables["ecart_energie"].dropna()
    n_evaluables = len(ecarts)
    n_ecarts_importants = int(
        (ecarts.abs() > eda_lib.ECART_ENERGIE_KCAL).sum()
    )
    taux_ecarts = (
        100 * n_ecarts_importants / n_evaluables
        if n_evaluables
        else 0
    )

    n_produits_extremes = (
        int(extremes["code"].nunique())
        if not extremes.empty
        else 0
    )
    taux_extremes = (
        100 * n_produits_extremes / n_rayons_connus
        if n_rayons_connus
        else 0
    )

    # ---------------------------------------------------------
    # 2. Mise en page générale
    # ---------------------------------------------------------
    fig = plt.figure(figsize=(14, 8), facecolor="white")

    fig.text(
        0.07, 0.94,
        "Synthèse de la qualité des données",
        fontsize=21,
        fontweight="bold",
        color=ENCRE,
        ha="left",
    )
    fig.text(
        0.07, 0.895,
        "Couverture du périmètre, disponibilité nutritionnelle et contrôles de cohérence",
        fontsize=10.5,
        color="#666666",
        ha="left",
    )

    # ---------------------------------------------------------
    # 3. Couverture : périmètre initial -> rayons connus
    # ---------------------------------------------------------
    ax_couverture = fig.add_axes([0.07, 0.70, 0.86, 0.13])
    ax_couverture.set_xlim(0, 1)
    ax_couverture.set_ylim(0, 1)
    ax_couverture.axis("off")

    ax_couverture.text(
        0.00, 0.90,
        "COUVERTURE DU PÉRIMÈTRE",
        fontsize=9,
        fontweight="bold",
        color="#666666",
        va="top",
    )

    ax_couverture.text(
        0.00, 0.48,
        f"{total:,}".replace(",", " "),
        fontsize=22,
        fontweight="bold",
        color=ENCRE,
        va="center",
    )
    ax_couverture.text(
        0.00, 0.12,
        "Produits initiaux",
        fontsize=10,
        color="#666666",
        va="center",
    )

    ax_couverture.text(
        0.30, 0.48,
        "→",
        fontsize=23,
        color="#999999",
        va="center",
        ha="center",
    )

    ax_couverture.text(
        0.39, 0.48,
        f"{n_rayons_connus:,}".replace(",", " "),
        fontsize=22,
        fontweight="bold",
        color=BLEU,
        va="center",
    )
    ax_couverture.text(
        0.39, 0.12,
        "Produits avec un rayon exploitable",
        fontsize=10,
        color="#666666",
        va="center",
    )

    ax_couverture.text(
        1.00, 0.48,
        f"{taux_couverture:.1f} %",
        fontsize=22,
        fontweight="bold",
        color=BLEU,
        va="center",
        ha="right",
    )
    ax_couverture.text(
        1.00, 0.12,
        "Taux de couverture",
        fontsize=10,
        color="#666666",
        va="center",
        ha="right",
    )

    # Barre de couverture
    ax_barre = fig.add_axes([0.07, 0.665, 0.86, 0.012])
    ax_barre.barh(
        0,
        1,
        height=1,
        color="#EAEAEA",
    )
    ax_barre.barh(
        0,
        taux_couverture / 100,
        height=1,
        color=BLEU,
    )
    ax_barre.set_xlim(0, 1)
    ax_barre.set_ylim(-0.6, 0.6)
    ax_barre.axis("off")

    # ---------------------------------------------------------
    # 4. Complétude nutritionnelle
    # ---------------------------------------------------------
    ax_completude = fig.add_axes([0.07, 0.46, 0.86, 0.15])
    ax_completude.set_xlim(0, 1)
    ax_completude.set_ylim(0, 1)
    ax_completude.axis("off")

    ax_completude.text(
        0.00, 0.95,
        "COMPLÉTUDE NUTRITIONNELLE",
        fontsize=9,
        fontweight="bold",
        color="#666666",
        va="top",
    )
    ax_completude.text(
        0.00, 0.48,
        f"{n_complets:,}".replace(",", " "),
        fontsize=22,
        fontweight="bold",
        color=ENCRE,
        va="center",
    )
    ax_completude.text(
        0.15, 0.48,
        f"produits avec les {len(eda_lib.NUTRIMENTS_CLES)} nutriments clés renseignés",
        fontsize=11,
        color="#555555",
        va="center",
    )
    ax_completude.text(
        1.00, 0.48,
        f"{taux_completude:.1f} %",
        fontsize=22,
        fontweight="bold",
        color=BLEU,
        va="center",
        ha="right",
    )
    ax_completude.text(
        1.00, 0.12,
        f"Sur {n_rayons_connus:,} produits avec rayon".replace(",", " "),
        fontsize=9,
        color="#666666",
        va="center",
        ha="right",
    )

    # Barre de complétude
    ax_barre_completude = fig.add_axes([0.07, 0.425, 0.86, 0.012])
    ax_barre_completude.barh(
        0, 1, height=1, color="#EAEAEA"
    )
    ax_barre_completude.barh(
        0,
        taux_completude / 100,
        height=1,
        color=BLEU,
    )
    ax_barre_completude.set_xlim(0, 1)
    ax_barre_completude.set_ylim(-0.6, 0.6)
    ax_barre_completude.axis("off")

    # ---------------------------------------------------------
    # 5. Deux diagnostics complémentaires
    # ---------------------------------------------------------
    fig.text(
        0.07, 0.355,
        "CONTRÔLES DE QUALITÉ",
        fontsize=9,
        fontweight="bold",
        color="#666666",
        ha="left",
    )

    # Séparateur central
    fig.add_artist(
        plt.Line2D(
            [0.50, 0.50],
            [0.10, 0.32],
            transform=fig.transFigure,
            color="#E5E5E5",
            linewidth=1,
        )
    )

    # Diagnostic 1 : incohérences énergétiques
    ax_energie = fig.add_axes([0.07, 0.12, 0.38, 0.20])
    ax_energie.set_xlim(0, 1)
    ax_energie.set_ylim(0, 1)
    ax_energie.axis("off")

    ax_energie.text(
        0.00, 0.95,
        "Incohérences énergétiques",
        fontsize=12,
        fontweight="bold",
        color=ENCRE,
        va="top",
    )
    ax_energie.text(
        0.00, 0.58,
        f"{n_ecarts_importants:,}".replace(",", " "),
        fontsize=25,
        fontweight="bold",
        color=ORANGE,
        va="center",
    )
    ax_energie.text(
        0.00, 0.30,
        f"sur {n_evaluables:,} produits évaluables".replace(",", " "),
        fontsize=10,
        color="#555555",
        va="center",
    )
    ax_energie.text(
        0.00, 0.08,
        f"{taux_ecarts:.1f} % avec un écart supérieur à "
        f"{eda_lib.ECART_ENERGIE_KCAL:.0f} kcal/100 g",
        fontsize=9,
        color="#666666",
        va="center",
    )

    # Diagnostic 2 : valeurs extrêmes
    ax_extremes = fig.add_axes([0.56, 0.12, 0.37, 0.20])
    ax_extremes.set_xlim(0, 1)
    ax_extremes.set_ylim(0, 1)
    ax_extremes.axis("off")

    ax_extremes.text(
        0.00, 0.95,
        "Produits avec valeurs extrêmes",
        fontsize=12,
        fontweight="bold",
        color=ENCRE,
        va="top",
    )
    ax_extremes.text(
        0.00, 0.58,
        f"{n_produits_extremes:,}".replace(",", " "),
        fontsize=25,
        fontweight="bold",
        color=GRIS,
        va="center",
    )
    ax_extremes.text(
        0.00, 0.30,
        f"sur {n_rayons_connus:,} produits avec rayon".replace(",", " "),
        fontsize=10,
        color="#555555",
        va="center",
    )
    ax_extremes.text(
        0.00, 0.08,
        f"{taux_extremes:.1f} % concernés — un signal n'est pas une preuve d'erreur",
        fontsize=9,
        color="#666666",
        va="center",
    )
     # ---------------------------------------------------------
    # Séparateurs entre les grandes sections
    # ---------------------------------------------------------
    for y in (0.635, 0.395):
        fig.add_artist(
            plt.Line2D(
                [0.07, 0.93],
                [y, y],
                transform=fig.transFigure,
                color="#D9D9D9",
                linewidth=0.9,
                solid_capstyle="round",
            )
        )

    fig.subplots_adjust(
        left=0.07,
        right=0.93,
        top=0.96,
        bottom=0.06,
    )

    return fig, {
        "couverture": ax_couverture,
        "completude": ax_completude,
        "energie": ax_energie,
        "extremes": ax_extremes,
    }