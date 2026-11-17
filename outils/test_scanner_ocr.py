"""Régressions géométrie : alignement des colonnes et caractères ambigus."""
import copy

import pytest

from src.scanner.ocr import reconstruire_texte
from src.scanner.scanner import aiguiller
from test_scanner_contrat import TEXTE, EXTRACTION, CATALOGUE


def mot(texte, x, y):
    return {"texte": texte, "x": x, "y": y, "largeur": 50, "hauteur": 20}


def document(*lignes):
    return {"lignes": [{"mots": ligne} for ligne in lignes]}


def test_valeurs_lues_en_colonne_sont_replacees_sur_leur_ligne():
    d = document([mot("Sucres", 10, 10)], [mot("Sel", 10, 60)],
                 [mot("10 g", 200, 11), mot("0,2 g", 200, 61)])
    assert reconstruire_texte(d) == "Sucres 10 g\nSel 0,2 g"


def test_plusieurs_colonnes_ne_sont_pas_fusionnees_en_une_valeur():
    texte = reconstruire_texte(document([mot("Sel", 10, 10)],
                                        [mot("0,2 g", 150, 10), mot("0,1 g", 250, 10)]))
    assert texte == "Sel 0,2 g 0,1 g"
    e = copy.deepcopy(EXTRACTION)
    e["nutriments"]["sel"] = {"valeur": 0.2, "preuve": texte}
    assert aiguiller(TEXTE + "\n" + texte, e, CATALOGUE)["nutriments"]["sel"] is None
    e["nutriments"]["sel"]["preuve"] = "Sel 0,2 g"
    assert aiguiller(TEXTE + "\n" + texte, e, CATALOGUE)["nutriments"]["sel"] is None


def test_correction_base_documentee_et_limitee_aux_entetes():
    t = reconstruire_texte(document([mot("Valor por 1 OOg:", 0, 0)],
                                    [mot("Sucres 1OOg", 0, 60)]))
    assert str(t) == "Valor por 100 g:\nSucres 1OOg"
    assert t.metadata["corrections"] == [{"avant": "1 OOg", "apres": "100 g", "regle": "base_100_ocr_O_zero"}]
    assert "1 OOg" in t.metadata["texte_avant_normalisation"]


@pytest.mark.parametrize("preuve", ["Sucres\n10 g", "Sucres 05 g", "Sucres 00 g"])
def test_preuve_ambigue_ou_sans_alignement_refusee(preuve):
    e = copy.deepcopy(EXTRACTION)
    e["nutriments"]["sucres"] = {"valeur": 5 if "05" in preuve else 0 if "00" in preuve else 10,
                                  "preuve": preuve}
    assert aiguiller(TEXTE + "\n" + preuve, e, CATALOGUE)["nutriments"]["sucres"] is None


def test_code_imprime_groupe_reconnu_sans_fusion_entre_lignes():
    assert aiguiller(TEXTE.replace("3017620422003", "3 017620 422003"), EXTRACTION, CATALOGUE)["statut"] == "verifie"
    assert aiguiller(TEXTE.replace("3017620422003", "3\n017620\n422003"), EXTRACTION, CATALOGUE)["statut"] == "non_verifie"


def test_deux_codes_groupes_restent_ambigus():
    r = aiguiller(TEXTE + "\n5 449000 000996", EXTRACTION, CATALOGUE)
    assert r["statut"] == "non_verifie"
    assert r["produit"] is None
