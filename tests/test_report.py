from datetime import date

import pandas as pd
import pytest

from src.cleaning import nettoyer
from src.report import diagnostiquer, generer_rapport


@pytest.fixture
def mini() -> pd.DataFrame:
    """Trois produits : un propre, un avec 74 000 g de sucres, un avec 24 000 kcal."""
    return pd.DataFrame({
        "code": ["001", "002", "003"],
        "product_name": ["Yaourt", "Biscuit", "Beurre"],
        "brands": ["A", None, "C"],
        "categories_tags": ["en:yogurts", "en:biscuits", None],
        "pnns_groups_1": ["Milk and dairy products", "Sugary snacks", "Fat and sauces"],
        "nutriscore_grade": ["a", "e", "e"],
        "energy-kcal_100g": [60.0, 450.0, 24000.0],
        "energy_100g": [251.0, 1883.0, None],
        "fat_100g": [3.0, 20.0, 82.0],
        "saturated-fat_100g": [2.0, 10.0, 50.0],
        "carbohydrates_100g": [5.0, 60.0, 1.0],
        "sugars_100g": [5.0, 74000.0, 1.0],
        "fiber_100g": [None, 2.0, None],
        "proteins_100g": [4.0, 6.0, 1.0],
        "salt_100g": [0.1, 0.5, 0.05],
        "sodium_100g": [0.04, 0.2, 0.02],
    })


def test_diagnostiquer_compte_les_lignes(mini):
    diag = diagnostiquer(mini)
    assert diag["nutriment hors 0–100 g"] == 1
    assert diag["énergie hors 0–900 kcal"] == 1
    assert diag["au moins une"] == 2


def test_generer_rapport_reproductible(mini, tmp_path):
    propre, journal = nettoyer(mini)
    premier = generer_rapport(mini, propre, journal, tmp_path / "r.md", jour=date(2026, 9, 24))
    second = generer_rapport(mini, propre, journal, tmp_path / "r.md", jour=date(2026, 9, 24))
    assert premier == second == (tmp_path / "r.md").read_text(encoding="utf-8")
    assert "© Open Food Facts contributors" in premier
    for regle in journal:
        assert f"`{regle.regle}`" in premier
