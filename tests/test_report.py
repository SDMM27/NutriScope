from datetime import date

import pandas as pd
import pytest

from src.cleaning import nettoyer, _compte_rendu
from src.report import diagnostiquer, generer_rapport


@pytest.fixture
def mini() -> pd.DataFrame:
    """Trois produits : un propre, un avec 74 000 g de sucres, un avec 24 000 kcal."""
    return pd.DataFrame({
        "code": ["001", "002", "003"],
        "product_name": ["Yaourt", "Biscuit", "Beurre"],
        "brands": ["A", None, "C"],
        "categories_tags": ["en:yogurts", "en:biscuits", None],
        "food_groups_tags": [["en:milk-and-dairy-products"], [], None],
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


def test_rapport_utilise_groupes_off_quand_pnns_indisponible(mini, tmp_path):
    mini["pnns_groups_1"] = pd.NA
    propre, journal = nettoyer(mini)

    rapport = generer_rapport(mini, propre, journal, tmp_path / "r.md")

    assert "La répartition ci-dessous utilise les groupes Open Food Facts" in rapport
    assert "Un produit pouvant avoir plusieurs groupes" in rapport
    assert "en:milk-and-dairy-products | 1 | 33.3 %" in rapport
    assert "(vide) | 3 | 100.0 %" not in rapport

def test_compte_rendu_gere_les_index_dupliques():
    avant = pd.DataFrame(
        {
            "a": [1, 2, 3],
            "b": [10, 20, 30],
        },
        index=[0, 0, 1],
    )

    apres = avant.copy()
    apres.iloc[0, 0] = 100
    apres.iloc[2, 1] = 300

    masques = {
        "correction_a": pd.Series(
            [True, False, False],
            index=avant.index,
        ),
        "correction_b": pd.Series(
            [False, False, True],
            index=avant.index,
        ),
    }

    rapport = _compte_rendu("test", avant, apres, masques)

    assert rapport.lignes_touchees == 2
    assert rapport.details == {
        "correction_a": 1,
        "correction_b": 1,
    }

def test_compte_rendu_agrege_les_masques_par_position():
    avant = pd.DataFrame(
        {
            "a": [1, 2, 3],
            "b": [10, 20, 30],
        },
        index=[10, 10, 20],
    )

    apres = avant.copy()

    masques = {
        "correction_a": pd.Series(
            [True, False, False],
            index=[100, 200, 300],
        ),
        "correction_b": pd.Series(
            [True, False, True],
            index=[400, 500, 600],
        ),
    }

    rapport = _compte_rendu("test", avant, apres, masques)

    assert rapport.lignes_touchees == 2
    assert rapport.details == {
        "correction_a": 1,
        "correction_b": 2,
    }
    
def test_compte_rendu_refuse_un_masque_de_mauvaise_longueur():
    avant = pd.DataFrame({"a": [1, 2, 3]})
    apres = avant.copy()

    masques = {
        "correction_a": pd.Series([True, False]),
    }

    with pytest.raises(ValueError, match="contient 2 éléments"):
        _compte_rendu("test", avant, apres, masques)
