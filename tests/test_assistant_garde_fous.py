"""Tests des garde-fous déterministes."""
import pytest

from src.assistant.garde_fous import detecter_hors_perimetre, verifier_chiffres


@pytest.mark.parametrize("q", [
    "Je suis diabétique, puis-je manger du Nutella ?",
    "Quel aliment pour baisser mon cholestérol ?",
    "Je suis enceinte, quels fromages éviter ?",
    "Mon médecin m'a prescrit un régime thérapeutique",
    "J'ai une insuffisance rénale, que manger ?",
])
def test_refus_medical(q):
    assert detecter_hors_perimetre(q) is not None
    assert "médecin" in detecter_hors_perimetre(q)


@pytest.mark.parametrize("q", [
    "Combien de sucres dans le Nutella ?",
    "Compare le coca et le pepsi",
    "Je suis allergique aux arachides, y en a-t-il dans ce produit ?",
    "Quel est le Nutri-Score des pâtes ?",
])
def test_pas_de_refus(q):
    assert detecter_hors_perimetre(q) is None


def test_chiffres_virgule_fr():
    res = [{"produits": [{"nutriments": {"sucres": 56.3}}]}]
    assert verifier_chiffres("Il contient 56,3 g de sucres pour 100 g.", res) == []


def test_chiffre_invente():
    res = [{"produits": [{"nutriments": {"sucres": 56.3}}]}]
    assert verifier_chiffres("Il contient 12 g de sucres.", res) == ["12"]


def test_arrondi_accepte():
    res = [{"produits": [{"nutriments": {"sucres": 56.34, "kcal": 539.4}}]}]
    assert verifier_chiffres("56,3 g, soit 56 g ; 539 kcal", res) == []


FICHE = [{"produits": [{"nutriments": {
    "sucres": 56.3, "satures": 10.6, "lipides": 30.9, "kcal": 539, "fibres": None}}]}]


@pytest.mark.parametrize("reponse, attendu", [
    ("Il y a 10,6 g de sucres.", ["10,6"]),
    ("Il y a 56,3 g de sucres.", []),
    ("Il y a 10,6 g de lipides saturés.", []),
    ("Sucres : 56,3 g", []),
    ("539 kcal, 56,3 g de sucres", []),
    ("Il y a 3 g de fibres.", ["3"]),
    ("Il y a 30,9 g de lipides saturés.", ["30,9"]),
    ("Il y a 10,6 g.", []),
])
def test_chiffre_rattache_au_nutriment(reponse, attendu):
    assert verifier_chiffres(reponse, FICHE) == attendu


def test_nombres_dans_chaines_et_total():
    res = [{"total": 3, "produits": [{"code": "3017620422003"}]}]
    assert verifier_chiffres("Code 3017620422003, 3 résultats.", res) == []


def test_numeros_de_liste_ignores():
    reponse = "1. Nutella : 56,3 g de sucres\n2) Autre : 99 g de sucres\nIl y a 2. variantes"
    assert verifier_chiffres(reponse, FICHE) == ["99", "2"]
