"""Contrat reconstitué du bloc 1 ; doubles réservés aux tests, pas aux mesures."""
import copy

import pytest

from src.scanner.scanner import aiguiller, analyser_texte, ean_valide, scanner_photo
from src.assistant.scanner import repondre_photo

TEXTE = "Nutella\n3017620422003\nPour 100 g\nEnergie 539 kcal\nLipides 30,9 g\nSucres 56,3 g\nSel 0,107 g"
EXTRACTION = {"base": "100 g", "preuve_base": "Pour 100 g", "nutriments": {
    "kcal": {"valeur": 539, "preuve": "Energie 539 kcal"},
    "lipides": {"valeur": 30.9, "preuve": "Lipides 30,9 g"},
    "sucres": {"valeur": 56.3, "preuve": "Sucres 56,3 g"},
    "sel": {"valeur": 0.107, "preuve": "Sel 0,107 g"}}}
CATALOGUE = [{"code": "3017620422003", "name": "Nutella", "brand_name": "xx:nutella",
              "nutriscore_grade": "e", "energy_kcal": 539.0, "fat": 30.9,
              "sugars": 56.3, "salt": 0.107}]


def test_verifie_et_absent_reste_null():
    r = aiguiller(TEXTE, EXTRACTION, CATALOGUE)
    assert r["statut"] == "verifie"
    assert r["produit"]["nutriscore"] == "E"
    assert r["nutriments"]["fibres"] is None


@pytest.mark.parametrize("texte,catalogue,raison", [
    (TEXTE.replace("3017620422003", ""), CATALOGUE, "identite_non_confirmee"),
    (TEXTE.replace("3017620422003", "3017620422004"), CATALOGUE, "identite_non_confirmee"),
    (TEXTE.replace("Nutella", "Autre produit"), CATALOGUE, "identite_non_confirmee"),
    (TEXTE, [], "code_absent_ou_ambigu"),
    (TEXTE, CATALOGUE * 2, "code_absent_ou_ambigu"),
    (TEXTE + "\n5449000000996", CATALOGUE, "identite_non_confirmee"),
])
def test_pas_de_mauvais_rattachement(texte, catalogue, raison):
    r = aiguiller(texte, EXTRACTION, catalogue)
    assert r["statut"] == "non_verifie"
    assert r["produit"] is None
    assert r["raison"] == raison


def test_divergence_refuse_la_fiche():
    catalogue = copy.deepcopy(CATALOGUE)
    catalogue[0]["sugars"] = 10
    assert aiguiller(TEXTE, EXTRACTION, catalogue)["raison"] == "divergence_nutritionnelle"


def test_sans_tableau():
    assert aiguiller("Un paysage", {}, CATALOGUE)["statut"] == "illisible"


@pytest.mark.parametrize("valeur", [None, True, -1, float("nan"), float("inf"), 101, "56.3"])
def test_valeur_invalide_non_utilisee(valeur):
    extraction = copy.deepcopy(EXTRACTION)
    extraction["nutriments"]["sucres"]["valeur"] = valeur
    assert aiguiller(TEXTE, extraction, CATALOGUE)["nutriments"]["sucres"] is None


@pytest.mark.parametrize("preuve", ["Sucres 42 g", "Lipides 30,9 g", "", None])
def test_preuve_inventee_ou_mauvais_nutriment(preuve):
    extraction = copy.deepcopy(EXTRACTION)
    extraction["nutriments"]["sucres"] = {"valeur": 30.9, "preuve": preuve}
    assert aiguiller(TEXTE, extraction, CATALOGUE)["nutriments"]["sucres"] is None


def test_multi_colonnes_refus_et_base_ml_non_rattachee():
    assert aiguiller(TEXTE + "\nPar portion", EXTRACTION, CATALOGUE)["statut"] == "illisible"
    extraction = copy.deepcopy(EXTRACTION)
    extraction.update(base="100 ml", preuve_base="Pour 100 ml")
    r = aiguiller(TEXTE.replace("100 g", "100 ml"), extraction, CATALOGUE)
    assert r["statut"] == "non_verifie"


def test_extraction_ne_modifie_pas_entrees():
    original = copy.deepcopy(EXTRACTION)
    aiguiller(TEXTE, EXTRACTION, CATALOGUE)
    assert EXTRACTION == original


@pytest.mark.parametrize("base", [None, [], {}, 100, "portion"])
def test_base_invalide(base):
    extraction = copy.deepcopy(EXTRACTION)
    extraction["base"] = base
    assert aiguiller(TEXTE, extraction, CATALOGUE)["statut"] == "illisible"


@pytest.mark.parametrize("preuve", ["Sel < 0,5 g", "Sel 0,5 %", "Sel 0,5 mg", "Sel 0,5 g 1 g"])
def test_unite_seuil_ou_colonne_non_prouves(preuve):
    extraction = copy.deepcopy(EXTRACTION)
    extraction["nutriments"]["sel"] = {"valeur": 0.5, "preuve": preuve}
    assert aiguiller(TEXTE + "\n" + preuve, extraction, CATALOGUE)["nutriments"]["sel"] is None


def test_vrai_zero_conserve():
    extraction = copy.deepcopy(EXTRACTION)
    extraction["nutriments"]["sel"] = {"valeur": 0, "preuve": "Sel 0 g"}
    assert aiguiller(TEXTE + "\nSel 0 g", extraction, [])["nutriments"]["sel"] == 0


def test_non_verifie_assistant_ne_reutilise_pas_nutriscore():
    r = repondre_photo("photo.png", [], ClientTest(), ocr=lambda _: TEXTE)
    assert r["scanner"]["produit"] is None
    assert "Nutri-Score : E" not in r["reponse"]
    assert "non vérifiée" in r["reponse"]


@pytest.mark.parametrize("code,attendu", [("3017620422003", True), ("3017620422004", False),
                                        ("96385074", True), ("123", False)])
def test_cle_ean(code, attendu):
    assert ean_valide(code) == attendu


class ClientTest:
    def discuter(self, messages, outils):
        import json
        assert messages[-1]["content"] == TEXTE
        assert outils == []
        return {"content": json.dumps(EXTRACTION)}


def test_entree_photo_assistant_et_provenance():
    r = repondre_photo("photo.png", CATALOGUE, ClientTest(), ocr=lambda _: TEXTE)
    assert r["scanner"]["statut"] == "verifie"
    assert "Open Food Facts" in r["reponse"]
    assert "fibres : non renseigné" in r["reponse"]


def test_json_invalide_et_panne_ne_sont_pas_confondus():
    class MauvaisClient:
        def discuter(self, *_):
            return {"content": "pas JSON"}
    assert analyser_texte(TEXTE, CATALOGUE, MauvaisClient())["raison"] == "sortie_modele_invalide"
    def panne(_):
        raise RuntimeError("OCR indisponible")
    with pytest.raises(RuntimeError, match="OCR indisponible"):
        scanner_photo("photo.png", CATALOGUE, ClientTest(), ocr=panne)
