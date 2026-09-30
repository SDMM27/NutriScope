import pandas as pd
import pytest

from src import eda_lib


@pytest.fixture
def produits() -> pd.DataFrame:
    """Six produits : un doublon, un sucre impossible, une énergie impossible, deux sans rayon connu."""
    return pd.DataFrame({
        "code": ["001", "001", "002", "003", "004", "005"],
        "pnns_groups_1": ["Beverages", "Beverages", "Sugary snacks", "Fat and sauces", "unknown", None],
        "energy-kcal_100g": [40.0, 45.0, 400.0, 24000.0, 100.0, None],
        "sugars_100g": [10.0, 11.0, 74000.0, 0.0, 5.0, None],
        "salt_100g": [0.0, 0.0, 0.5, 0.1, None, 1.0],
        "sodium_100g": [0.0, 0.0, 0.2, 0.04, None, 0.4],
    })


def test_module_importable():
    assert eda_lib.GRAINE == 42
    assert "sugars_100g" in eda_lib.NUTRIMENTS_CLES


def test_nettoyage_minimal(produits):
    propre = eda_lib.nettoyage_minimal(produits)
    assert propre["code"].tolist() == ["001", "004", "005"]      # doublon, 74 000 g et 24 000 kcal écartés
    assert propre.loc[0, "energy-kcal_100g"] == 40.0             # première occurrence gardée
    assert propre["salt_100g"].isna().sum() == 1                 # les manquants restent
    assert len(produits) == 6                                    # entrée intacte


def test_rayons_connus(produits):
    connus = eda_lib.rayons_connus(produits)
    assert set(connus["pnns_groups_1"]) == {"Beverages", "Sugary snacks", "Fat and sauces"}
