"""Tests unitaires des fonctions de visualisation du TP11."""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from src import eda_lib, viz


# ---------------------------------------------------------------------
# Fixtures et données synthétiques
# ---------------------------------------------------------------------

@pytest.fixture(autouse=True)
def fermer_figures():
    """Ferme les figures après chaque test."""
    yield
    plt.close("all")


@pytest.fixture
def profil_sucres():
    """Profil de sucres par rayon."""
    return pd.DataFrame(
        {
            "mediane": [12.0, 35.0, 5.0],
            "n": [100, 80, 120],
        },
        index=["Boissons", "Snacks sucrés", "Fruits"],
    )


@pytest.fixture
def produits_nutriscore():
    """Produits avec des grades Nutri-Score exploitables."""
    return pd.DataFrame(
        {
            "pnns_groups_1": [
                "Sugary snacks",
                "Sugary snacks",
                "Sugary snacks",
                "Fruits and vegetables",
                "Fruits and vegetables",
                "Fruits and vegetables",
                "Sugary snacks",
                "Fruits and vegetables",
            ],
            "nutriscore_grade": [
                "a", "d", "e", "a", "b", "c", "unknown", None,
            ],
        }
    )


@pytest.fixture
def produits_rayons():
    """Produits avec des rayons connus, inconnus et absents."""
    return pd.DataFrame(
        {
            eda_lib.RAYON: [
                "Sugary snacks",
                "Fruits and vegetables",
                eda_lib.RAYON_INCONNU,
                None,
                "Beverages",
            ]
        }
    )


@pytest.fixture
def completude():
    """Résultat synthétique de complétude par rayon."""
    return pd.DataFrame(
        {
            "n": [100, 50],
            "fiches_completes": [80.0, 60.0],
            "score_present": [90.0, 70.0],
        },
        index=["Fruits and vegetables", "Sugary snacks"],
    )


@pytest.fixture
def comparables():
    """Produits comparables pour le contrôle énergétique."""
    return pd.DataFrame(
        {
            "product_name": [
                "Produit A",
                "Produit B",
                "Produit C",
                "Produit D",
            ],
            "ecart_energie": [10.0, -100.0, 30.0, np.nan],
        }
    )


@pytest.fixture
def donnees_extremes():
    """Valeurs extrêmes synthétiques."""
    return pd.DataFrame(
        {
            "code": ["001", "002", "002", "003"],
            "product_name": [
                "Produit A",
                "Produit B",
                "Produit B",
                "Produit C",
            ],
            "rayon": [
                "Snacks",
                "Snacks",
                "Snacks",
                "Boissons",
            ],
            "nutriment": [
                "sugars_100g",
                "sugars_100g",
                "fat_100g",
                "salt_100g",
            ],
            "valeur": [95.0, 90.0, 80.0, 25.0],
            "z": [5.0, 4.0, 3.0, 6.0],
        }
    )


@pytest.fixture
def par_rayon():
    """Produits du rayon utilisé pour illustrer un cas extrême."""
    return pd.DataFrame(
        {
            "code": [
                "3760159010608",
                "001",
                "002",
                "003",
                "004",
            ],
            "product_name": [
                "Noix De Coco Râpée",
                "Produit A",
                "Produit B",
                "Produit C",
                "Produit D",
            ],
            eda_lib.RAYON: [
                "Fruits and vegetables",
                "Fruits and vegetables",
                "Fruits and vegetables",
                "Fruits and vegetables",
                "Fruits and vegetables",
            ],
            "saturated-fat_100g": [57.2, 0.2, 1.0, 0.5, 0.8],
        }
    )


@pytest.fixture
def perimetre():
    """Périmètre minimal pour la synthèse qualité."""
    return pd.DataFrame(
        {
            eda_lib.RAYON: [
                "Fruits and vegetables",
                "Sugary snacks",
                "Beverages",
                eda_lib.RAYON_INCONNU,
                None,
            ],
            **{
                nutriment: [1.0, 2.0, np.nan, 3.0, 4.0]
                for nutriment in eda_lib.NUTRIMENTS_CLES
            },
        }
    )


# ---------------------------------------------------------------------
# 1. Médianes de sucres par rayon
# ---------------------------------------------------------------------

def test_tracer_medianes_sucres_retourne_figure_et_axes(profil_sucres):
    fig, ax = viz.tracer_medianes_sucres(profil_sucres)

    assert isinstance(fig, matplotlib.figure.Figure)
    assert isinstance(ax, matplotlib.axes.Axes)
    assert len(ax.patches) == 3


def test_tracer_medianes_sucres_trie_les_valeurs(profil_sucres):
    _, ax = viz.tracer_medianes_sucres(profil_sucres)

    valeurs = [barre.get_width() for barre in ax.patches]

    assert valeurs == sorted(valeurs, reverse=True)


def test_tracer_medianes_sucres_exclut_medianes_manquantes():
    profil = pd.DataFrame(
        {"mediane": [10.0, np.nan], "n": [20, 30]},
        index=["Rayon A", "Rayon B"],
    )

    _, ax = viz.tracer_medianes_sucres(profil)

    assert len(ax.patches) == 1


def test_tracer_medianes_sucres_refuse_donnees_vides():
    profil = pd.DataFrame(
        {"mediane": [np.nan], "n": [0]},
        index=["Rayon A"],
    )

    with pytest.raises(ValueError, match="Aucune médiane"):
        viz.tracer_medianes_sucres(profil)


def test_tracer_medianes_sucres_refuse_colonne_manquante():
    profil = pd.DataFrame({"mediane": [10.0]})

    with pytest.raises(ValueError, match="colonnes manquantes"):
        viz.tracer_medianes_sucres(profil)


# ---------------------------------------------------------------------
# 2. Grades Nutri-Score mis en avant
# ---------------------------------------------------------------------

def test_tracer_grades_mis_en_avant_retourne_figure_et_axes(
    produits_nutriscore,
):
    fig, ax = viz.tracer_grades_mis_en_avant(produits_nutriscore)

    assert isinstance(fig, matplotlib.figure.Figure)
    assert isinstance(ax, matplotlib.axes.Axes)
    assert len(ax.containers) == 5


def test_tracer_grades_mis_en_avant_normalise_les_proportions(
    produits_nutriscore,
):
    _, ax = viz.tracer_grades_mis_en_avant(produits_nutriscore)

    for conteneur in ax.containers:
        assert len(conteneur) == 2

    for position in range(2):
        total = sum(
            conteneur[position].get_width()
            for conteneur in ax.containers
        )
        assert total == pytest.approx(100.0)


def test_tracer_grades_mis_en_avant_exclut_grades_invalides(
    produits_nutriscore,
):
    _, ax = viz.tracer_grades_mis_en_avant(produits_nutriscore)

    assert ax.get_xlim() == (0.0, 100.0)


def test_tracer_grades_mis_en_avant_refuse_rayon_sans_grade():
    produits = pd.DataFrame(
        {
            "pnns_groups_1": [
                "Sugary snacks",
                "Fruits and vegetables",
            ],
            "nutriscore_grade": ["a", "unknown"],
        }
    )

    with pytest.raises(ValueError, match="Aucun produit"):
        viz.tracer_grades_mis_en_avant(produits)


def test_tracer_grades_mis_en_avant_refuse_colonne_manquante():
    produits = pd.DataFrame({"pnns_groups_1": ["Sugary snacks"]})

    with pytest.raises(ValueError, match="colonnes manquantes"):
        viz.tracer_grades_mis_en_avant(produits)


# ---------------------------------------------------------------------
# 3. Couverture des rayons
# ---------------------------------------------------------------------

def test_tracer_couverture_rayons_retourne_figure_et_axes(
    produits_rayons,
):
    fig, ax = viz.tracer_couverture_rayons(produits_rayons)

    assert isinstance(fig, matplotlib.figure.Figure)
    assert isinstance(ax, matplotlib.axes.Axes)
    assert len(ax.patches) == 2


def test_tracer_couverture_rayons_compte_les_categories(
    produits_rayons,
):
    _, ax = viz.tracer_couverture_rayons(produits_rayons)

    barres = ax.patches

    assert barres[0].get_width() == pytest.approx(60.0)
    assert barres[1].get_width() == pytest.approx(40.0)


def test_tracer_couverture_rayons_refuse_echantillon_vide():
    produits = pd.DataFrame({eda_lib.RAYON: []})

    with pytest.raises(ValueError, match="échantillon vide"):
        viz.tracer_couverture_rayons(produits)


def test_tracer_couverture_rayons_refuse_colonne_manquante():
    produits = pd.DataFrame({"autre_colonne": [1, 2]})

    with pytest.raises(ValueError, match="colonnes manquantes"):
        viz.tracer_couverture_rayons(produits)


# ---------------------------------------------------------------------
# 4. Complétude nutritionnelle par rayon
# ---------------------------------------------------------------------

def test_tracer_completude_rayons_retourne_figure_et_axes(completude):
    fig, ax = viz.tracer_completude_rayons(completude)

    assert isinstance(fig, matplotlib.figure.Figure)
    assert isinstance(ax, matplotlib.axes.Axes)
    assert len(ax.patches) == 6


def test_tracer_completude_rayons_estime_effectifs(completude):
    _, ax = viz.tracer_completude_rayons(completude)

    # Matplotlib stocke les barres par série :
    # 1. Effectifs totaux : 50, 100
    # 2. Produits avec Nutri-Score : 35, 90
    # 3. Fiches complètes : 30, 80
    largeurs = [barre.get_width() for barre in ax.patches]

    assert largeurs == pytest.approx(
        [50, 100, 35, 90, 30, 80]
    )


def test_tracer_completude_rayons_refuse_donnees_vides():
    donnees = pd.DataFrame(
        columns=["n", "fiches_completes", "score_present"]
    )

    with pytest.raises(ValueError, match="Aucune donnée"):
        viz.tracer_completude_rayons(donnees)


def test_tracer_completude_rayons_refuse_taux_hors_limites():
    donnees = pd.DataFrame(
        {
            "n": [100],
            "fiches_completes": [120.0],
            "score_present": [80.0],
        },
        index=["Rayon A"],
    )

    with pytest.raises(ValueError, match="hors limites"):
        viz.tracer_completude_rayons(donnees)


def test_tracer_completude_rayons_refuse_colonne_manquante():
    donnees = pd.DataFrame({"n": [100]})

    with pytest.raises(ValueError, match="colonnes manquantes"):
        viz.tracer_completude_rayons(donnees)


# ---------------------------------------------------------------------
# 5. Écarts énergétiques
# ---------------------------------------------------------------------

def test_tracer_ecarts_energetiques_retourne_figure_et_axes(comparables):
    fig, ax = viz.tracer_ecarts_energetiques(comparables)

    assert isinstance(fig, matplotlib.figure.Figure)
    assert isinstance(ax, matplotlib.axes.Axes)
    assert len(ax.patches) == 3


def test_tracer_ecarts_energetiques_conserve_les_plus_grands_ecarts(
    comparables,
):
    _, ax = viz.tracer_ecarts_energetiques(comparables)

    valeurs = [barre.get_width() for barre in ax.patches]

    assert sorted(valeurs) == pytest.approx([-100.0, 10.0, 30.0])


def test_tracer_ecarts_energetiques_refuse_aucun_ecart():
    donnees = pd.DataFrame(
        {
            "product_name": ["Produit A"],
            "ecart_energie": [np.nan],
        }
    )

    with pytest.raises(ValueError, match="Aucun écart"):
        viz.tracer_ecarts_energetiques(donnees)


def test_tracer_ecarts_energetiques_refuse_colonne_manquante():
    donnees = pd.DataFrame(
        {"product_name": ["Produit A"]}
    )

    with pytest.raises(ValueError, match="colonnes manquantes"):
        viz.tracer_ecarts_energetiques(donnees)


# ---------------------------------------------------------------------
# 6. Bilan des valeurs extrêmes
# ---------------------------------------------------------------------

def test_tracer_bilan_valeurs_extremes_retourne_figure_et_axes(
    donnees_extremes,
    par_rayon,
):
    fig, axes = viz.tracer_bilan_valeurs_extremes(
        donnees_extremes,
        total_rayons_connus=100,
        par_rayon=par_rayon,
    )

    assert isinstance(fig, matplotlib.figure.Figure)
    assert len(axes) == 2
    assert all(isinstance(ax, matplotlib.axes.Axes) for ax in axes)


def test_tracer_bilan_valeurs_extremes_compte_les_produits_uniques(
    donnees_extremes,
    par_rayon,
):
    fig, _ = viz.tracer_bilan_valeurs_extremes(
        donnees_extremes,
        total_rayons_connus=100,
        par_rayon=par_rayon,
    )

    # Trois codes distincts, même si le code 002 apparaît deux fois.
    assert "3 produits sur 100" in fig._suptitle.get_text()


def test_tracer_bilan_valeurs_extremes_refuse_un_total_nul(
    donnees_extremes,
    par_rayon,
):
    with pytest.raises(ValueError, match="doit être positif"):
        viz.tracer_bilan_valeurs_extremes(
            donnees_extremes,
            total_rayons_connus=0,
            par_rayon=par_rayon,
        )


def test_tracer_bilan_valeurs_extremes_refuse_cible_absente(
    donnees_extremes,
):
    donnees = pd.DataFrame(
        {
            "code": ["001"],
            "product_name": ["Produit A"],
            eda_lib.RAYON: ["Fruits and vegetables"],
            "saturated-fat_100g": [0.2],
        }
    )

    with pytest.raises(ValueError, match="absent du rayon"):
        viz.tracer_bilan_valeurs_extremes(
            donnees_extremes,
            total_rayons_connus=100,
            par_rayon=donnees,
        )


def test_tracer_bilan_valeurs_extremes_refuse_rayons_vides(
    donnees_extremes,
):
    donnees = pd.DataFrame(
        {
            "code": ["001"],
            "product_name": ["Produit A"],
            eda_lib.RAYON: ["Snacks"],
            "saturated-fat_100g": [0.2],
        }
    )

    with pytest.raises(ValueError, match="Aucun produit"):
        viz.tracer_bilan_valeurs_extremes(
            donnees_extremes,
            total_rayons_connus=100,
            par_rayon=donnees,
        )


# ---------------------------------------------------------------------
# 7. Synthèse de la qualité
# ---------------------------------------------------------------------

def test_tracer_synthese_qualite_retourne_figure_et_axes(
    perimetre,
    comparables,
    donnees_extremes,
):
    fig, axes = viz.tracer_synthese_qualite(
        perimetre,
        comparables,
        donnees_extremes,
    )

    assert isinstance(fig, matplotlib.figure.Figure)
    assert set(axes) == {
        "couverture",
        "completude",
        "energie",
        "extremes",
    }


def test_tracer_synthese_qualite_calculs_de_couverture(
    perimetre,
    comparables,
    donnees_extremes,
):
    _, axes = viz.tracer_synthese_qualite(
        perimetre,
        comparables,
        donnees_extremes,
    )

    textes = [texte.get_text() for texte in axes["couverture"].texts]

    assert "5" in textes
    assert "3" in textes
    assert any("60.0 %" in texte for texte in textes)


def test_tracer_synthese_qualite_refuse_colonne_manquante(
    perimetre,
    comparables,
    donnees_extremes,
):
    donnees_incompletes = perimetre.drop(
        columns=[eda_lib.NUTRIMENTS_CLES[0]]
    )

    with pytest.raises(ValueError, match="colonnes manquantes"):
        viz.tracer_synthese_qualite(
            donnees_incompletes,
            comparables,
            donnees_extremes,
        )


def test_tracer_synthese_qualite_refuse_ecart_energie_absent(
    perimetre,
    donnees_extremes,
):
    comparables_incomplets = pd.DataFrame(
        {"autre_colonne": [1, 2]}
    )

    with pytest.raises(ValueError, match="colonnes manquantes"):
        viz.tracer_synthese_qualite(
            perimetre,
            comparables_incomplets,
            donnees_extremes,
        )


def test_tracer_synthese_qualite_refuse_code_absent(
    perimetre,
    comparables,
):
    extremes_incomplets = pd.DataFrame(
        {"autre_colonne": [1, 2]}
    )

    with pytest.raises(ValueError, match="colonnes manquantes"):
        viz.tracer_synthese_qualite(
            perimetre,
            comparables,
            extremes_incomplets,
        )