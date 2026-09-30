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


# ---------------------------------------------------------------------------
# 1. Distributions par rayon
# ---------------------------------------------------------------------------

def test_resume_univarie_valeurs_connues():
    resume = eda_lib.resume_univarie(pd.Series([1.0, 2.0, 3.0, 4.0, 100.0, None]))
    assert resume["n"] == 5
    assert resume["manquants"] == 1
    assert resume["moyenne"] == 22.0
    assert resume["mediane"] == 3.0          # la médiane ignore le 100, pas la moyenne
    assert resume["IQR"] == 2.0              # Q3 = 4, Q1 = 2
    assert resume["MAD"] == 1.0              # écarts à 3 : 2, 1, 0, 1, 97 -> médiane 1
    assert resume["min"] == 1.0 and resume["max"] == 100.0


@pytest.fixture
def deux_rayons() -> pd.DataFrame:
    """40 boissons (sucres 0 à 39), 40 snacks (sucres 50 à 89), 5 produits d'un petit rayon."""
    return pd.DataFrame({
        "pnns_groups_1": ["Beverages"] * 40 + ["Sugary snacks"] * 40 + ["Baby foods"] * 5,
        "sugars_100g": [float(i) for i in range(40)] + [float(i) for i in range(50, 90)] + [10.0] * 5,
        "nutriscore_grade": ["a"] * 40 + ["e"] * 40 + ["unknown"] * 5,
    })


def test_profil_par_rayon_valeurs_connues(deux_rayons):
    profil = eda_lib.profil_par_rayon(deux_rayons, ["sugars_100g"])
    boissons = profil.loc[("sugars_100g", "Beverages")]
    assert boissons["n"] == 40
    assert boissons["mediane"] == 19.5
    assert boissons["moyenne"] == 19.5
    assert profil.loc[("sugars_100g", "Sugary snacks"), "mediane"] == 69.5


def test_profil_par_rayon_ecarte_les_petits_groupes(deux_rayons):
    profil = eda_lib.profil_par_rayon(deux_rayons, ["sugars_100g"], min_n=30)
    assert "Baby foods" not in profil.index.get_level_values("rayon")
    ecartes = eda_lib.rayons_ecartes(deux_rayons, ["sugars_100g"], min_n=30)
    assert ecartes.to_dict("records") == [{"nutriment": "sugars_100g", "rayon": "Baby foods", "n": 5}]


def test_croisement_rayon_grade(deux_rayons):
    table = eda_lib.croisement_rayon_grade(deux_rayons)
    assert list(table.columns) == ["a", "b", "c", "d", "e"]
    assert "Baby foods" not in table.index          # aucun grade a–e : écarté
    parts = eda_lib.parts_par_ligne(table)
    assert parts.loc["Beverages", "a"] == 100.0
    assert parts.sum(axis=1).tolist() == [100.0, 100.0]


def test_v_cramer_bornes(deux_rayons):
    parfaite = eda_lib.croisement_rayon_grade(deux_rayons)       # chaque rayon a un seul grade
    assert eda_lib.v_cramer(parfaite) == pytest.approx(1.0)
    independante = pd.DataFrame({"a": [20, 40], "b": [10, 20]}, index=["r1", "r2"])
    assert eda_lib.v_cramer(independante) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# 2. Complétude et qualité
# ---------------------------------------------------------------------------

@pytest.fixture
def fiches() -> pd.DataFrame:
    """Marque A : 4 produits dont 3 avec sucres, 2 avec sel, 2 complets, 1 score. Marque B : 1 produit."""
    return pd.DataFrame({
        "brands": ["A", "A", "A", "A", "B", None],
        "sugars_100g": [1.0, 2.0, 3.0, None, 5.0, 6.0],
        "salt_100g": [0.1, 0.2, None, None, 0.5, 0.6],
        "nutriscore_score": [3, None, None, None, 10, 1],
    })


def test_completude_par_groupe_taux_exacts(fiches):
    table = eda_lib.completude_par_groupe(fiches, "brands", ["sugars_100g", "salt_100g"], min_n=1)
    a = table.loc["A"]
    assert a["n"] == 4
    assert a["sugars_100g"] == 75.0
    assert a["salt_100g"] == 50.0
    assert a["fiches_completes"] == 50.0
    assert a["score_present"] == 25.0
    assert table.index.tolist() == ["B", "A"]        # tri par fiches complètes ; marque manquante ignorée


def test_completude_par_groupe_ecarte_les_petits_groupes(fiches):
    table = eda_lib.completude_par_groupe(fiches, "brands", ["sugars_100g", "salt_100g"], min_n=2)
    assert table.index.tolist() == ["A"]


@pytest.fixture
def incoherents() -> pd.DataFrame:
    """Une ligne saine, une ligne par incohérence, une ligne vide."""
    return pd.DataFrame({
        "energy-kcal_100g":   [170.0, 170.0, 170.0, 170.0, 500.0, 0.0, None],
        "carbohydrates_100g": [20.0, 20.0, 20.0, 20.0, 20.0, 20.0, None],
        "proteins_100g":      [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, None],
        "fat_100g":           [10.0, 10.0, 10.0, 10.0, 10.0, 0.0, None],
        "sugars_100g":        [20.5, 21.0, 5.0, 5.0, 5.0, 5.0, None],     # 20,5 : dans la tolérance
        "saturated-fat_100g": [3.0, 3.0, 11.0, 3.0, 3.0, 0.0, None],
        "salt_100g":          [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, None],
        "sodium_100g":        [0.4, 0.4, 0.4, 0.8, 0.4, 0.4, None],
    })


def test_incoherences_metier_un_drapeau_par_ligne(incoherents):
    drapeaux = eda_lib.incoherences_metier(incoherents)
    assert not drapeaux.loc[0].any()                                  # ligne saine, sucres à la tolérance
    assert drapeaux.loc[1].to_dict() == {"sucres_sup_glucides": True, "satures_sup_lipides": False,
                                         "sel_different_sodium": False, "energie_ecart_449": False,
                                         "energie_nulle_macros": False}
    assert drapeaux.loc[2, "satures_sup_lipides"]
    assert drapeaux.loc[3, "sel_different_sodium"]                    # 1,0 g de sel pour 0,8 g de sodium
    assert drapeaux.loc[4, "energie_ecart_449"]                       # 500 kcal déclarées, 170 calculées
    assert drapeaux.loc[5, "energie_nulle_macros"]
    assert drapeaux.sum().tolist() == [1, 1, 1, 1, 1]


def test_incoherences_metier_ignore_les_manquants(incoherents):
    drapeaux = eda_lib.incoherences_metier(incoherents)
    assert not drapeaux.loc[6].any()
    assert drapeaux.dtypes.eq(bool).all()


def test_energie_calculee():
    df = pd.DataFrame({"carbohydrates_100g": [50.0, 1.0], "proteins_100g": [20.0, 1.0], "fat_100g": [10.0, None]})
    assert eda_lib.energie_calculee(df).iloc[0] == 370.0
    assert pd.isna(eda_lib.energie_calculee(df).iloc[1])
