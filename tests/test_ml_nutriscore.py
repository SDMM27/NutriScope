"""Tests d'acceptation de la préparation des jeux du TP14."""

import pandas as pd
import pytest

from src.ml_nutriscore import preparer_jeux_classification


FEATURES = [
    "energy-kcal_100g",
    "fat_100g",
    "saturated-fat_100g",
    "carbohydrates_100g",
    "sugars_100g",
    "proteins_100g",
    "salt_100g",
    "fiber_100g",
    "fruits-vegetables-legumes_100g",
    "nova_group",
    "additives_n",
    "pnns_groups_1",
    "pnns_groups_2",
]


@pytest.fixture
def donnees_ml():
    return pd.DataFrame(
        {
            "code": ["001", "002", "003", "004", "005"],
            "product_name": ["Boisson", "Yaourt", "Céréales", "Biscuit", "Sauce"],
            **{colonne: [1, 2, 3, 4, 5] for colonne in FEATURES[:7]},
            "fiber_100g": [None, 1.0, None, 2.0, None],
            "fruits-vegetables-legumes_100g": [None, 20.0, 10.0, None, 5.0],
            "nova_group": [None, 2, 3, None, 4],
            "additives_n": [None, 0, 2, 1, None],
            "pnns_groups_1": ["Beverages", "Dairy", "Cereals", "Snacks", "Sauces"],
            "pnns_groups_2": ["Water", "Yogurts", "Breakfast cereals", "Biscuits", "Dressings"],
            "nutriscore_grade": ["a", "b", "c", "d", "e"],
            "nutriscore_score": [-2, 4, 10, 18, 25],
            "split": ["train", "train", "train", "test", "test"],
        }
    )


def test_preparer_separe_train_test_et_exclut_les_fuites(donnees_ml):
    jeux = preparer_jeux_classification(donnees_ml)

    assert jeux["X_train"].columns.tolist() == FEATURES
    assert jeux["X_train"].index.tolist() == [0, 1, 2]
    assert jeux["y_train"].tolist() == ["a", "b", "c"]
    assert jeux["X_test"].index.tolist() == [3, 4]
    assert jeux["y_test"].tolist() == ["d", "e"]
    assert not {"nutriscore_score", "nutriscore_grade", "code", "product_name", "split"} & set(
        jeux["X_train"].columns
    )
    assert jeux["donnees_test"]["code"].tolist() == ["004", "005"]
    assert jeux["donnees_test"]["nutriscore_score"].tolist() == [18, 25]


def test_preparer_conserve_les_valeurs_manquantes_des_features_optionnelles(donnees_ml):
    jeux = preparer_jeux_classification(donnees_ml)

    assert jeux["X_train"]["fiber_100g"].isna().sum() == 2
    assert jeux["X_test"]["additives_n"].isna().sum() == 1


@pytest.mark.parametrize("colonne", ["nutriscore_grade", "split", "energy-kcal_100g"])
def test_preparer_signale_une_colonne_obligatoire_absente(donnees_ml, colonne):
    with pytest.raises(ValueError, match="colonne"):
        preparer_jeux_classification(donnees_ml.drop(columns=colonne))


@pytest.mark.parametrize(
    ("colonne", "valeur"),
    [("split", "validation"), ("nutriscore_grade", "unknown")],
)
def test_preparer_refuse_les_valeurs_de_controle_inattendues(donnees_ml, colonne, valeur):
    donnees_ml.loc[0, colonne] = valeur

    with pytest.raises(ValueError):
        preparer_jeux_classification(donnees_ml)


def test_preparer_refuse_un_jeu_train_ou_test_vide(donnees_ml):
    donnees_ml.loc[:, "split"] = "train"

    with pytest.raises(ValueError, match="train|test"):
        preparer_jeux_classification(donnees_ml)
