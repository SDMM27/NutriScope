import pandas as pd
import pytest

from src.cleaning import (
    REGLES,
    CompteRendu,
    nettoyer,
    typer_colonnes,
    borner_nutriments,
    corriger_energie,
    KJ_PAR_KCAL,
)


@pytest.fixture
def brut() -> pd.DataFrame:
    """Quelques lignes telles qu'elles sortent d'un CSV lu sans précaution."""
    return pd.DataFrame({
        "code": ["0000356470029", "00004206", "3017620422003"],
        "nova_group": [2.0, None, "4"],
        "nutriscore_score": ["12", "abc", 3.5],     # "abc" illisible, 3.5 non entier
        "fat_100g": ["25.0", 12, None],
        "completeness": [0.3, 0.275, 0.9],
    })


def test_typer_colonnes_types(brut):
    df, cr = typer_colonnes(brut)
    assert df["code"].dtype == "string"
    assert df["code"].iloc[0] == "0000356470029"     # zéros de tête conservés
    assert df["nova_group"].dtype == "Int64"
    assert df["nutriscore_score"].dtype == "Int64"
    assert df["fat_100g"].dtype == "float64"
    assert df["completeness"].dtype == "float64"
    assert df["nova_group"].tolist()[2] == 4
    assert isinstance(cr, CompteRendu) and cr.regle == "typer_colonnes"


def test_typer_colonnes_valeurs_illisibles(brut):
    df, cr = typer_colonnes(brut)
    assert df["nutriscore_score"].iloc[0] == 12
    assert pd.isna(df["nutriscore_score"].iloc[1])   # "abc"
    assert pd.isna(df["nutriscore_score"].iloc[2])   # 3.5
    assert cr.details == {"valeurs_non_numeriques": 2}
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


def test_nettoyer_enchaine_les_regles(brut):
    df, journal = nettoyer(brut, [typer_colonnes])
    assert [cr.regle for cr in journal] == ["typer_colonnes"]
    assert df["code"].dtype == "string"


def test_pipeline_commence_par_typer_colonnes():
    assert REGLES[0] is typer_colonnes
    assert all(callable(regle) for regle in REGLES)


@pytest.fixture
def nutriments_invalides() -> pd.DataFrame:
    return pd.DataFrame({
        "fat_100g": [25.0, -1.0, 101.0],
        "sugars_100g": [25.0, -1.0, 101.0],
        "carbohydrates_100g": [25.0, -1.0, 101.0],
        "sodium_100g": [25.0, -1.0, 40.1], #sel +/- sodium * 2.5
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

@pytest.fixture
def energie_invalide() -> pd.DataFrame:
    return pd.DataFrame({
        "energy-kcal_100g": [
            0.0,
            -1.0,
            901.0,
            100.0,
            370.0,
            100.0,
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