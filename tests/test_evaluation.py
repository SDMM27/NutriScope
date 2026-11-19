"""Bloc 4 : le jeu de 30 questions et la chaîne de mesure."""

import csv
from collections import Counter
from pathlib import Path

from src.assistant.catalogue import charger_catalogue
from src.corpus.telecharger import SOURCES
from src.eval.mesurer import lire_questions, mesurer, suggerer_verdict
from src.eval.synthese import synthese

RACINE = Path(__file__).resolve().parents[1]
QUESTIONS = lire_questions(RACINE / "eval" / "questions.csv")
CODES = {p["code"] for p in charger_catalogue()}
DOCS = {s["id"] for s in SOURCES if s["statut"] != "exclu"}


def test_repartition_des_30_questions():
    assert len(QUESTIONS) == 30
    assert len({q["id"] for q in QUESTIONS}) == 30
    assert Counter(q["type"] for q in QUESTIONS) == {
        "produit": 8, "comparaison": 6, "connaissance": 8, "mixte": 3, "piege": 5}


def test_sources_attendues_existent():
    for q in QUESTIONS:
        for source in filter(None, q["sources_attendues"].split("|")):
            genre, ident = source.split(":", 1)
            assert (genre == "fiche" and ident in CODES) or (genre == "doc" and ident in DOCS), (q["id"], source)


def test_comportements_attendus():
    for q in QUESTIONS:
        assert q["comportement_attendu"] in {"repondre", "refuser", "dire_introuvable"}
        if q["type"] != "piege":
            assert q["comportement_attendu"] == "repondre"


def test_reponses_attendues_produit_tirees_du_catalogue():
    cat = {p["code"]: p for p in charger_catalogue()}
    q = {x["id"]: x for x in QUESTIONS}
    assert q["Q01"]["reponse_attendue"].startswith(cat["3017620422003"]["nutriscore"])
    assert "56.3" in q["Q09"]["reponse_attendue"] and "51" in q["Q09"]["reponse_attendue"]
    assert cat["5449000214911"]["nutriments"]["fibres"] is None and "non renseignée" in q["Q05"]["reponse_attendue"]


def test_suggestions_de_verdict():
    base = {"outils_appeles": []}
    assert suggerer_verdict({**base, "reponse": "Je n'ai pas de source pour répondre."}, None) == "refus_correct"
    assert suggerer_verdict({**base, "reponse": "Au moins 5 par jour."}, None) == "juste_non_source|invente"
    assert suggerer_verdict({**base, "reponse": "Je ne peux pas répondre."}, "repondre") == "refus_sans_source|refus_a_tort"
    assert suggerer_verdict({**base, "reponse": "Ce produit n'est pas dans le catalogue."}, "dire_introuvable") == "introuvable_correct"
    detourne = {"reponse": "Il faut 5 portions.", "outils_appeles": [{"outil": "chercher_produit", "statut": "introuvable"}]}
    assert suggerer_verdict(detourne, None) == "outil_detourne|invente"


def test_mesure_puis_synthese(tmp_path):
    def faux_repondre(question):  # FAUX assistant, pour tester la chaîne de mesure seulement
        return {"reponse": "Je n'ai pas de source.", "outils_appeles": [], "latence_s": 1.5,
                "tokens_entree": 10, "tokens_sortie": 5}

    sortie = tmp_path / "eval_sans_rag.csv"
    lignes = mesurer(QUESTIONS, faux_repondre, sortie, ids={"Q01", "Q15", "Q26"})
    assert [l["id"] for l in lignes] == ["Q01", "Q15", "Q26"]
    # le correcteur pose les verdicts à la main ; on simule cette étape
    with open(sortie, encoding="utf-8") as f:
        rangs = list(csv.DictReader(f, delimiter=";"))
    for rang, verdict in zip(rangs, ["refus_a_tort", "refus_sans_source", "introuvable_correct"]):
        rang["verdict"] = verdict
    with open(sortie, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rangs[0].keys(), delimiter=";")
        w.writeheader(); w.writerows(rangs)
    s = synthese(sortie)
    assert (s["questions"], s["conformes"], s["erreurs"], s["non_poses"]) == (3, 1, 0, 0)
