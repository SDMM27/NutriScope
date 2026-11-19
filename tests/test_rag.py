"""TP 19, étape 1 : tests fournis. Ils passent au vert quand les TODO 1 à 5 sont écrits.

Lancement, à la racine du dépôt :  python -m pytest tests/test_rag.py -v

Ils tournent sans Ollama : le faux modèle de tests/faux_embeddings.py remplace qwen3-embedding.
Les quatre fiches ci-dessous sont des données de test inventées, pas des produits réels.
"""

import json

import pytest

from src.rag import indexer as I
from src.rag import recherche as R
from tests.faux_embeddings import FauxEmbeddings

FAUX = FauxEmbeddings()

FICHES_TEST = [
    ("2000000000101", "Skyr nature", "Marque test A", "Produits laitiers", "A"),
    ("2000000000102", "Soda cola", "Marque test B", "Boissons", "E"),
    ("2000000000103", "Eau minérale gazeuse", "Marque test C", "Boissons", ""),
    ("2000000000104", "Biscuits sablés", "Marque test D", "Biscuits", "D"),
]


@pytest.fixture
def dossier_fiches(tmp_path):
    dossier = tmp_path / "fiches"
    dossier.mkdir()
    with open(dossier / "metadonnees.jsonl", "w", encoding="utf-8") as meta:
        for code, nom, marque, rayon, ns in FICHES_TEST:
            (dossier / f"{code}.txt").write_text(
                f"Produit : {nom} — {marque}\nCode-barres : {code}\nRayon : {rayon}\n"
                f"Nutri-Score : {ns or 'non renseigné'}\nSource : données de test\n", encoding="utf-8")
            meta.write(json.dumps({"id": f"fiche:{code}", "code": code, "nom": nom, "marque": marque,
                                   "rayon": rayon, "nutriscore": ns, "source": "test"}, ensure_ascii=False) + "\n")
    return dossier


@pytest.fixture
def fiches(dossier_fiches):
    return I.lire_fiches(dossier_fiches)


@pytest.fixture
def collection(tmp_path, fiches):
    col = I.collection_fiches(tmp_path / "index")
    I.indexer(fiches, col, vectoriser=FAUX.embed_documents)
    return col


def chercher(question, collection, **kwargs):
    return R.rechercher(question, collection=collection, vectoriser=FAUX.embed_documents, **kwargs)


# --- TODO 1 ---

def test_todo1_valeur_inconnue_devient_none():
    meta = {"code": " 2000000000103 ", "nom": "Eau", "marque": "", "nutriscore": None, "source": "test",
            "extrait_le": "2026-11-16"}
    assert I.metadonnees_de(meta) == {"code": "2000000000103", "nom": "Eau", "marque": None,
                                      "rayon": None, "nutriscore": None, "source": "test"}


# --- TODO 2 ---

def test_todo2_relancer_l_indexation_ne_change_pas_le_compte(fiches, collection):
    assert collection.count() == len(fiches) == 4
    I.indexer(fiches, collection, vectoriser=FAUX.embed_documents)
    assert collection.count() == 4


def test_todo2_une_fiche_modifiee_remplace_l_ancienne(fiches, collection):
    fiche = {**fiches[0], "texte": fiches[0]["texte"] + "Note : fiche corrigée\n"}
    I.indexer([fiche], collection, vectoriser=FAUX.embed_documents)
    assert collection.get(ids=[fiche["id"]])["documents"][0] == fiche["texte"]


def test_todo2_une_valeur_devenue_inconnue_disparait_de_l_index(fiches, collection):
    fiche = {**fiches[0], "metadonnees": {**fiches[0]["metadonnees"], "nutriscore": None}}
    I.indexer([fiche], collection, vectoriser=FAUX.embed_documents)
    assert "nutriscore" not in collection.get(ids=[fiche["id"]])["metadatas"][0]


# --- TODO 3 à 5 ---

def test_todo3a5_le_contrat_de_rechercher(collection):
    resultats = chercher("une boisson gazeuse", collection, k=3)
    assert len(resultats) == 3
    assert all(set(r) == {"id", "score", "texte", "metadonnees"} for r in resultats)
    assert all(r["id"].startswith("fiche:") for r in resultats)
    scores = [r["score"] for r in resultats]
    assert scores == sorted(scores, reverse=True), "le plus proche d'abord : score = 1 - distance"


def test_todo3a5_une_fiche_passee_telle_quelle_revient_en_tete(fiches, collection):
    for fiche in fiches:
        premier = chercher(fiche["texte"], collection, k=1, consigne=False)[0]
        assert premier["id"] == fiche["id"]
        assert premier["score"] > 0.99


def test_todo3a5_le_filtre_sur_le_rayon(collection):
    resultats = chercher("un produit", collection, k=5, filtres={"rayon": "Boissons"})
    assert {r["metadonnees"]["rayon"] for r in resultats} == {"Boissons"} and len(resultats) == 2


def test_fourni_question_vide_et_index_vide(tmp_path, collection):
    with pytest.raises(ValueError):
        chercher("   ", collection)
    assert chercher("skyr", I.collection_fiches(tmp_path / "vide")) == []
