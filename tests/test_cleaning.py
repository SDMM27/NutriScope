import pandas as pd
import pytest

from src.cleaning import (
    KJ_PAR_KCAL,
    REGLES,
    CompteRendu,
    borner_nutriments,
    corriger_energie,
    dedupliquer_codes,
    nettoyer,
    normaliser_unites,
    strategie_manquants,
    traiter_categories_vides,
    typer_colonnes,
)


# ---------------------------------------------------------------------------
# Règle 1 - typer_colonnes
# ---------------------------------------------------------------------------

@pytest.fixture
def brut() -> pd.DataFrame:
    """Jeu de données représentant des lignes issues du CSV brut."""
    return pd.DataFrame({
        "code": [
            "0000356470029",
            "00004206",
            "3017620422003",
        ],
        "nova_group": [
            2.0,
            None,
            "4",
        ],
        "nutriscore_score": [
            "12",
            "abc",
            3.5,
        ],
        "fat_100g": [
            "25.0",
            12,
            None,
        ],
        "completeness": [
            0.3,
            0.275,
            0.9,
        ],
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

    pd.testing.assert_frame_equal(
        une_fois,
        deux_fois,
    )

    assert cr.lignes_touchees == 0


# ---------------------------------------------------------------------------
# Règle 2 - dedupliquer_codes
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
        "completeness": [
            50.0,
            80.0,
            90.0,
            70.0,
            60.0,
            75.0,
        ],
        "last_modified_t": [
            1000,
            1000,
            900,
            1000,
            2000,
            1000,
        ],
    })


def test_dedupliquer_codes(codes_dupliques):
    resultat, cr = dedupliquer_codes(codes_dupliques)

    assert resultat["code"].tolist() == [
        "000001",
        "000002",
        "000003",
    ]

    # Le doublon ayant la meilleure complétude est conservé.
    assert resultat.loc[
        resultat["code"] == "000001",
        "name",
    ].iloc[0] == "Produit A doublon"

    assert len(resultat) == 3

    assert isinstance(cr, CompteRendu)
    assert cr.regle == "dedupliquer_codes"
    assert cr.lignes_avant == 6
    assert cr.lignes_apres == 3
    assert cr.lignes_touchees == 3

    assert cr.details == {
        "codes_absents": 2,
        "doublons_supprimes": 1,
    }


def test_dedupliquer_codes_garde_le_plus_recent_en_cas_degalite():
    donnees = pd.DataFrame({
        "code": [
            "000001",
            "000001",
        ],
        "name": [
            "Ancienne version",
            "Nouvelle version",
        ],
        "completeness": [
            90.0,
            90.0,
        ],
        "last_modified_t": [
            1000,
            2000,
        ],
    })

    resultat, _ = dedupliquer_codes(donnees)

    assert len(resultat) == 1
    assert resultat.iloc[0]["name"] == "Nouvelle version"


def test_dedupliquer_codes_ne_modifie_pas_l_entree(codes_dupliques):
    copie = codes_dupliques.copy()

    dedupliquer_codes(codes_dupliques)

    pd.testing.assert_frame_equal(
        codes_dupliques,
        copie,
    )


def test_dedupliquer_codes_idempotente(codes_dupliques):
    une_fois, _ = dedupliquer_codes(codes_dupliques)
    deux_fois, cr = dedupliquer_codes(une_fois)

    pd.testing.assert_frame_equal(
        une_fois,
        deux_fois,
    )

    assert cr.lignes_touchees == 0


# ---------------------------------------------------------------------------
# Règle 3 - normaliser_unites
# ---------------------------------------------------------------------------

@pytest.fixture
def donnees_unites():
    return pd.DataFrame({
        "energy-kcal_100g": [
            None,
            100.0,
            100.0,
        ],
        "energy_100g": [
            418.4,
            418.4,
            1000.0,
        ],
        "salt_100g": [
            None,
            2.5,
            5.0,
        ],
        "sodium_100g": [
            1.0,
            1.0,
            1.0,
        ],
    })


def test_normaliser_unites(donnees_unites):
    resultat, cr = normaliser_unites(donnees_unites)

    assert resultat.loc[0, "energy-kcal_100g"] == pytest.approx(100.0)

    assert resultat.loc[
        2,
        "energy-kcal_100g",
    ] == pytest.approx(
        1000.0 / KJ_PAR_KCAL
    )

    assert resultat.loc[
        0,
        "salt_100g",
    ] == pytest.approx(2.5)

    assert resultat.loc[
        0,
        "sodium_100g",
    ] == pytest.approx(1.0)

    assert resultat.loc[
        1,
        "salt_100g",
    ] == pytest.approx(2.5)

    assert resultat.loc[
        1,
        "sodium_100g",
    ] == pytest.approx(1.0)

    assert resultat.loc[
        2,
        "salt_100g",
    ] == pytest.approx(5.0)

    assert resultat.loc[
        2,
        "sodium_100g",
    ] == pytest.approx(2.0)

    assert cr.lignes_touchees == 2
    assert cr.details["kcal_derivees"] == 1
    assert cr.details["kcal_recalculees"] == 1
    assert cr.details["sel_derive"] == 1
    assert cr.details["sodium_recalcule"] == 1


def test_normaliser_unites_ne_modifie_pas_l_entree(donnees_unites):
    copie = donnees_unites.copy()

    normaliser_unites(donnees_unites)

    pd.testing.assert_frame_equal(
        donnees_unites,
        copie,
    )


def test_normaliser_unites_idempotente(donnees_unites):
    une_fois, _ = normaliser_unites(donnees_unites)
    deux_fois, cr = normaliser_unites(une_fois)

    pd.testing.assert_frame_equal(
        une_fois,
        deux_fois,
    )

    assert cr.lignes_touchees == 0


def test_normaliser_unites_kj_nuls_ne_recalculent_pas():
    donnees = pd.DataFrame({
        "energy-kcal_100g": [
            100.0,
            200.0,
        ],
        "energy_100g": [
            0.0,
            -100.0,
        ],
        "salt_100g": [
            1.0,
            1.0,
        ],
        "sodium_100g": [
            0.4,
            0.4,
        ],
    })

    resultat, cr = normaliser_unites(donnees)

    assert resultat["energy-kcal_100g"].tolist() == [
        100.0,
        200.0,
    ]

    assert cr.details["kcal_recalculees"] == 0


# ---------------------------------------------------------------------------
# Règle 4 - borner_nutriments
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
    df, _ = borner_nutriments(nutriments_invalides)

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
        "carbohydrates_100g": [
            50.0,
            50.0,
            50.0,
        ],
        "sugars_100g": [
            50.0,
            50.4,
            51.0,
        ],
        "fat_100g": [
            20.0,
            20.0,
            20.0,
        ],
        "saturated-fat_100g": [
            20.0,
            20.4,
            21.0,
        ],
    })

    resultat, _ = borner_nutriments(df)

    assert not pd.isna(
        resultat["sugars_100g"].iloc[0]
    )

    assert not pd.isna(
        resultat["sugars_100g"].iloc[1]
    )

    assert pd.isna(
        resultat["sugars_100g"].iloc[2]
    )

    assert not pd.isna(
        resultat["saturated-fat_100g"].iloc[0]
    )

    assert not pd.isna(
        resultat["saturated-fat_100g"].iloc[1]
    )

    assert pd.isna(
        resultat["saturated-fat_100g"].iloc[2]
    )


# ---------------------------------------------------------------------------
# Règle 5 - corriger_energie
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Règle 6 - traiter_categories_vides
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
    resultat, cr = traiter_categories_vides(
        categories_vides
    )

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


def test_traiter_categories_vides_ne_modifie_pas_l_entree(
    categories_vides,
):
    copie = categories_vides.copy()

    traiter_categories_vides(categories_vides)

    pd.testing.assert_frame_equal(
        categories_vides,
        copie,
    )


def test_traiter_categories_vides_idempotente(
    categories_vides,
):
    une_fois, _ = traiter_categories_vides(
        categories_vides
    )

    deux_fois, cr = traiter_categories_vides(
        une_fois
    )

    pd.testing.assert_frame_equal(
        une_fois,
        deux_fois,
    )

    assert cr.lignes_touchees == 0


# ---------------------------------------------------------------------------
# Règle 7 - strategie_manquants
# ---------------------------------------------------------------------------

@pytest.fixture
def donnees_manquants() -> pd.DataFrame:
    return pd.DataFrame({
        "code": [
            "000001",
            "000002",
            "000003",
        ],
        "name": [
            "Produit A",
            None,
            "Produit C",
        ],
        "completeness": [
            80.0,
            None,
            90.0,
        ],
        "brand_id": [
            1,
            None,
            3,
        ],
        "nutriscore_grade": [
            "a",
            None,
            "c",
        ],
        "nutriscore_score": [
            1,
            None,
            10,
        ],
        "proteins_100g": [
            5.0,
            None,
            10.0,
        ],
        "sugars_100g": [
            2.0,
            None,
            5.0,
        ],
        "salt_100g": [
            0.5,
            None,
            1.0,
        ],
    })


def test_strategie_manquants_conserve_les_na(
    donnees_manquants,
):
    resultat, cr = strategie_manquants(
        donnees_manquants
    )

    pd.testing.assert_frame_equal(
        resultat,
        donnees_manquants,
    )

    assert isinstance(cr, CompteRendu)
    assert cr.regle == "strategie_manquants"
    assert cr.lignes_avant == 3
    assert cr.lignes_apres == 3
    assert cr.lignes_touchees == 0


def test_strategie_manquants_ne_modifie_pas_l_entree(
    donnees_manquants,
):
    copie = donnees_manquants.copy()

    strategie_manquants(donnees_manquants)

    pd.testing.assert_frame_equal(
        donnees_manquants,
        copie,
    )


def test_strategie_manquants_idempotente(
    donnees_manquants,
):
    une_fois, _ = strategie_manquants(
        donnees_manquants
    )

    deux_fois, cr = strategie_manquants(
        une_fois
    )

    pd.testing.assert_frame_equal(
        une_fois,
        deux_fois,
    )

    assert cr.lignes_touchees == 0


# ---------------------------------------------------------------------------
# Pipeline complet - nettoyer
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


def test_nettoyer_enchaine_toutes_les_regles(
    donnees_pipeline,
):
    resultat, journal = nettoyer(
        donnees_pipeline,
        REGLES,
    )

    assert [
        cr.regle
        for cr in journal
    ] == [
        "typer_colonnes",
        "dedupliquer_codes",
        "normaliser_unites",
        "borner_nutriments",
        "corriger_energie",
        "traiter_categories_vides",
        "strategie_manquants",
    ]

    assert len(journal) == len(REGLES)
    assert isinstance(resultat, pd.DataFrame)


def test_nettoyer_applique_les_transformations(
    donnees_pipeline,
):
    resultat, _ = nettoyer(
        donnees_pipeline,
        REGLES,
    )

    assert len(resultat) == 3

    assert resultat["code"].tolist() == [
        "000001",
        "000002",
        "000003",
    ]

    assert resultat["categories"].iloc[0] == "Snacks"
    assert pd.isna(
        resultat["categories"].iloc[1]
    )
    assert resultat["categories"].iloc[2] == "Beverages"


def test_nettoyer_ne_modifie_pas_l_entree(
    donnees_pipeline,
):
    copie = donnees_pipeline.copy()

    nettoyer(
        donnees_pipeline,
        REGLES,
    )

    pd.testing.assert_frame_equal(
        donnees_pipeline,
        copie,
    )