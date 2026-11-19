"""Le contrat de chercher_produit (TP 18), règle par règle."""

import pytest

from src.assistant.catalogue import charger_catalogue
from src.assistant.outils import chercher_produit

CAT = charger_catalogue()


def test_par_code_ok():
    r = chercher_produit({"code": "3017620422003"}, CAT)
    assert r["statut"] == "ok" and r["total"] == 1
    fiche = r["produits"][0]
    assert fiche["nom"] == "Nutella" and fiche["nutriscore"] == "E"
    assert set(fiche["nutriments"]) == {"kcal", "lipides", "satures", "sucres", "fibres", "proteines", "sel"}


def test_code_prime_sur_nom():
    r = chercher_produit({"code": "87157215", "nom": "nutella"}, CAT)
    assert r["statut"] == "ok" and r["produits"][0]["nom"] == "Tomato Ketchup"


def test_nom_sans_casse_ni_accents():
    r = chercher_produit({"nom": "PATE A TARTINER"}, CAT)
    assert r["statut"] == "ok" and r["produits"][0]["marque"] == "Bonne Maman"


def test_repli_sur_la_marque():
    r = chercher_produit({"nom": "herta"}, CAT)
    assert r["statut"] == "ok" and r["produits"][0]["code"] == "3154230810131"


def test_ambigu_et_limite():
    r = chercher_produit({"nom": "e", "limite": 2}, CAT)
    assert r["statut"] == "ambigu" and r["total"] > 2 and len(r["produits"]) == 2


def test_introuvable():
    assert chercher_produit({"code": "0000000000000"}, CAT) == {"statut": "introuvable", "total": 0, "produits": []}
    assert chercher_produit({"nom": "oreo"}, CAT)["statut"] == "introuvable"


def test_valeur_inconnue_vaut_null_jamais_0():
    coca = chercher_produit({"code": "5449000214911"}, CAT)["produits"][0]
    assert coca["nutriments"]["fibres"] is None
    assert coca["donnees_incompletes"] is True
    assert coca["base"] == "100 ml"


@pytest.mark.parametrize("arguments", [
    "{pas du json",
    {"nom": "nutella", "rayon": "petit-déjeuner"},
    {"nom": "nutella", "limite": 0},
    {"nom": "nutella", "limite": 6},
    {"nom": "nutella", "limite": True},
    {"nom": "nutella", "limite": "3"},
    {},
    {"nom": "   "},
    {"code": 3017620422003},
    ["nutella"],
])
def test_arguments_invalides_rendent_une_erreur_sans_exception(arguments):
    r = chercher_produit(arguments, CAT)
    assert set(r) == {"erreur"} and r["erreur"]


def test_arguments_en_texte_json():
    assert chercher_produit('{"nom": "skyr"}', CAT)["statut"] == "ok"
