import pandas as pd
import pytest

from src.cleaning import CompteRendu, nettoyer, typer_colonnes


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
    df, journal = nettoyer(brut)
    assert [cr.regle for cr in journal] == ["typer_colonnes"]
    assert df["code"].dtype == "string"
