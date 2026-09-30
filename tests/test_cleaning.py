import pandas as pd
import pytest

from src.cleaning import (
    REGLES,
    CompteRendu,
    borner_nutriments,
    corriger_energie,
    dedupliquer_codes,
    nettoyer,
    traiter_categories_vides,
    typer_colonnes,
)


# ---------------------------------------------------------------------------
# typer_colonnes
# ---------------------------------------------------------------------------

@pytest.fixture
def brut() -> pd.DataFrame:
    """Quelques lignes telles qu'elles sortent d'un CSV lu sans précaution."""
    return pd.DataFrame({
        "code": ["0000356470029", "00004206", "3017620422003"],
        "nova_group": [2.0, None, "4"],
        "nutriscore_score": ["12", "abc", 3.5],
        "fat_100g": ["25.0", 12, None],
        "completeness": [0.3, 0.275, 0.9],
    })


def test_typer_colonnes_types(brut):
    df, cr = typer_colonnes(brut)

    assert df["code"].dtype == "string"
    assert df["code"].iloc[0] == "0000356470029"
    assert df["nova_group"].dtype == "Int64"
    assert df["nutriscore_score"].dtype == "Int64"
    assert df["fat_100g"].dtype == "float64"
    assert df["completeness"].dtype == "float64"
    assert df["nova_group"].tolist()[2] == 4
    assert isinstance(cr, CompteRendu)
    assert cr.regle == "typer_colonnes"


def test_typer_colonnes_valeurs_illisibles(brut):
    df, cr = typer_colonnes(brut)

    assert df["nutriscore_score"].iloc[0] == 12
    assert pd.isna(df["nutriscore_score"].iloc[1])
    assert pd.isna(df["nutriscore_score"].iloc[2])

    assert cr.details == {
        "valeurs_non_numeriques": 2,
    }
    assert cr.lignes_touchees == 2
    assert cr.lignes_avant == cr.lignes_apres == 3


def test_typer_colonnes_ne_modifie_pas_l_entree(brut):
    copie = brut.copy()

    typer_colonnes(brut)

    pd.testing.assert_frame_equal(brut, copie)


def test_typer_colonnes_idempotente(brut):
    une_fois, _ = typer_colonnes(brut)
    deux_fois, cr = typer_colonnes(une_fois)

    pd.testing.assert_frame_equal(une_fois, deux_fois)
    assert cr.lignes_touchees == 0


# ---------------------------------------------------------------------------
# traiter_categories_vides
# ---------------------------------------------------------------------------

@pytest.fixture
def categories_vides() -> pd.DataFrame:
    return pd.DataFrame({
        "code": [
            "000001",
            "000002",
            "000003",
            "000004",
        ],
        "categories": [
            "Snacks",
            "",
            "   ",
            None,
        ],
    })


def test_traiter_categories_vides(categories_vides):
    resultat, cr = traiter_categories_vides(categories_vides)

    assert resultat["categories"].iloc[0] == "Snacks"
    assert pd.isna(resultat["categories"].iloc[1])
    assert pd.isna(resultat["categories"].iloc[2])
    assert pd.isna(resultat["categories"].iloc[3])

    assert isinstance(cr, CompteRendu)
    assert cr.regle == "traiter_categories_vides"
    assert cr.lignes_avant == 4
    assert cr.lignes_apres == 4
    assert cr.lignes_touchees == 2
    assert cr.details == {
        "categories_vides": 2,
    }


def test_traiter_categories_vides_ne_modifie_pas_l_entree(categories_vides):
    copie = categories_vides.copy()

    traiter_categories_vides(categories_vides)

    pd.testing.assert_frame_equal(categories_vides, copie)


def test_traiter_categories_vides_idempotente(categories_vides):
    une_fois, _ = traiter_categories_vides(categories_vides)
    deux_fois, cr = traiter_categories_vides(une_fois)

    pd.testing.assert_frame_equal(une_fois, deux_fois)
    assert cr.lignes_touchees == 0


# ---------------------------------------------------------------------------
# dedupliquer_codes
# ---------------------------------------------------------------------------

@pytest.fixture
def codes_dupliques() -> pd.DataFrame:
    return pd.DataFrame({
        "code": [
            "000001",
            "000002",
            "000001",
            None,
            None,
            "000003",
        ],
        "name": [
            "Produit A",
            "Produit B",
            "Produit A doublon",
            "Produit sans code 1",
            "Produit sans code 2",
            "Produit C",
        ],
    })


def test_dedupliquer_codes(codes_dupliques):
    resultat, cr = dedupliquer_codes(codes_dupliques)

    assert resultat["code"].tolist()[:2] == [
        "000001",
        "000002",
    ]

    assert pd.isna(resultat["code"].iloc[2])
    assert pd.isna(resultat["code"].iloc[3])

    assert resultat["code"].iloc[4] == "000003"

    assert len(resultat) == 5

    assert isinstance(cr, CompteRendu)
    assert cr.regle == "dedupliquer_codes"
    assert cr.lignes_avant == 6
    assert cr.lignes_apres == 5
    assert cr.lignes_touchees == 1
    assert cr.details == {
        "doublons_supprimes": 1,
    }


def test_dedupliquer_codes_ne_modifie_pas_l_entree(codes_dupliques):
    copie = codes_dupliques.copy()

    dedupliquer_codes(codes_dupliques)

    pd.testing.assert_frame_equal(codes_dupliques, copie)


def test_dedupliquer_codes_idempotente(codes_dupliques):
    une_fois, _ = dedupliquer_codes(codes_dupliques)
    deux_fois, cr = dedupliquer_codes(une_fois)

    pd.testing.assert_frame_equal(une_fois, deux_fois)
    assert cr.lignes_touchees == 0


# ---------------------------------------------------------------------------
# borner_nutriments
# ---------------------------------------------------------------------------

@pytest.fixture
def nutriments_invalides() -> pd.DataFrame:
    return pd.DataFrame({
        "fat_100g": [25.0, -1.0, 101.0],
        "sugars_100g": [25.0, -1.0, 101.0],
        "carbohydrates_100g": [25.0, -1.0, 101.0],
        "sodium_100g": [25.0, -1.0, 40.1],
        "saturated-fat_100g": [25.0, -1.0, 101.0],
    })


def test_borner_nutriments_valeurs_invalides(nutriments_invalides):
    df, journal = borner_nutriments(nutriments_invalides)

    colonnes = [
        "fat_100g",
        "sugars_100g",
        "carbohydrates_100g",
        "sodium_100g",
        "saturated-fat_100g",
    ]

    for colonne in colonnes:
        assert not pd.isna(df[colonne].iloc[0])
        assert pd.isna(df[colonne].iloc[1])
        assert pd.isna(df[colonne].iloc[2])


def test_borner_nutriments_sous_totaux():
    df = pd.DataFrame({
        "carbohydrates_100g": [50.0, 50.0, 50.0],
        "sugars_100g": [50.0, 50.4, 51.0],
        "fat_100g": [20.0, 20.0, 20.0],
        "saturated-fat_100g": [20.0, 20.4, 21.0],
    })

    resultat, cr = borner_nutriments(df)

    assert not pd.isna(resultat["sugars_100g"].iloc[0])
    assert not pd.isna(resultat["sugars_100g"].iloc[1])
    assert pd.isna(resultat["sugars_100g"].iloc[2])

    assert not pd.isna(resultat["saturated-fat_100g"].iloc[0])
    assert not pd.isna(resultat["saturated-fat_100g"].iloc[1])
    assert pd.isna(resultat["saturated-fat_100g"].iloc[2])


# ---------------------------------------------------------------------------
# corriger_energie
# ---------------------------------------------------------------------------

@pytest.fixture
def energie_invalide() -> pd.DataFrame:
    return pd.DataFrame({
        "energy-kcal_100g": [
            0.0,      # kcal nulles avec macros > 0
            -1.0,     # kcal négatives
            901.0,    # kcal > 900
            100.0,    # kcal incohérentes avec le calcul 4/4/9
            370.0,    # kcal cohérentes avec le calcul 4/4/9
            100.0,    # alcool : incohérence ignorée
        ],
        "energy_100g": [
            0.0,
            -1.0,
            901.0,
            418.4,
            1548.08,
            418.4,
        ],
        "carbohydrates_100g": [50.0] * 6,
        "proteins_100g": [20.0] * 6,
        "fat_100g": [10.0] * 6,
        "pnns_groups_1": [
            None,
            None,
            None,
            None,
            None,
            "Alcoholic beverages",
        ],
    })


def test_corriger_energie(energie_invalide):
    resultat, cr = corriger_energie(energie_invalide)

    assert resultat["energy-kcal_100g"].tolist() == [
        370.0,
        370.0,
        370.0,
        370.0,
        370.0,
        100.0,
    ]

    assert isinstance(cr, CompteRendu)
    assert cr.regle == "corriger_energie"

    assert cr.details == {
        "nulles_recalculees": 1,
        "nulles_invalidees": 0,
        "negatives_recalculees": 1,
        "negatives_invalidees": 0,
        "sup_900_recalculees": 1,
        "sup_900_invalidees": 0,
        "incoherentes_recalculees": 1,
        "incoherentes_invalidees": 0,
    }


# ---------------------------------------------------------------------------
# Pipeline complet : nettoyer
# ---------------------------------------------------------------------------

@pytest.fixture
def donnees_pipeline() -> pd.DataFrame:
    return pd.DataFrame({
        "code": [
            "000001",
            "000002",
            "000001",
            "000003",
        ],
        "categories": [
            "Snacks",
            "",
            "   ",
            "Beverages",
        ],
        "nova_group": [
            2.0,
            3.0,
            None,
            4.0,
        ],
        "nutriscore_score": [
            10.0,
            5.0,
            8.0,
            3.0,
        ],
        "fat_100g": [
            10.0,
            20.0,
            30.0,
            5.0,
        ],
        "sugars_100g": [
            5.0,
            10.0,
            15.0,
            2.0,
        ],
        "carbohydrates_100g": [
            20.0,
            30.0,
            40.0,
            10.0,
        ],
        "proteins_100g": [
            5.0,
            10.0,
            10.0,
            2.0,
        ],
        "energy-kcal_100g": [
            150.0,
            200.0,
            250.0,
            100.0,
        ],
        "energy_100g": [
            627.6,
            836.8,
            1046.0,
            418.4,
        ],
        "sodium_100g": [
            0.5,
            0.8,
            1.0,
            0.2,
        ],
        "salt_100g": [
            1.25,
            2.0,
            2.5,
            0.5,
        ],
        "saturated-fat_100g": [
            2.0,
            4.0,
            5.0,
            1.0,
        ],
        "completeness": [
            0.9,
            0.8,
            0.7,
            1.0,
        ],
        "pnns_groups_1": [
            "Snacks",
            "Snacks",
            "Snacks",
            "Beverages",
        ],
    })


def test_nettoyer_enchaine_toutes_les_regles(donnees_pipeline):
    resultat, journal = nettoyer(donnees_pipeline, REGLES)

    assert [cr.regle for cr in journal] == [
        "typer_colonnes",
        "traiter_categories_vides",
        "dedupliquer_codes",
        "normaliser_unites",
        "borner_nutriments",
        "corriger_energie",
    ]

    assert len(journal) == len(REGLES)
    assert isinstance(resultat, pd.DataFrame)


def test_nettoyer_applique_les_transformations(donnees_pipeline):
    resultat, journal = nettoyer(donnees_pipeline, REGLES)

    assert len(resultat) == 3

    assert resultat["code"].tolist() == [
        "000001",
        "000002",
        "000003",
    ]

    assert resultat["categories"].iloc[0] == "Snacks"
    assert pd.isna(resultat["categories"].iloc[1])
    assert resultat["categories"].iloc[2] == "Beverages"


def test_nettoyer_ne_modifie_pas_l_entree(donnees_pipeline):
    copie = donnees_pipeline.copy()

    nettoyer(donnees_pipeline, REGLES)

    pd.testing.assert_frame_equal(donnees_pipeline, copie)