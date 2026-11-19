"""Blocs 2 et 4 — passer un jeu de questions sur l'assistant et ranger les résultats.

Usage :
  python -m src.eval.mesurer --questions bloc2_questions_verite.csv --sortie resultats/bloc2_sans_rag.csv
  python -m src.eval.mesurer --questions eval/questions.csv          --sortie resultats/eval_sans_rag.csv
  python -m src.eval.synthese resultats/eval_sans_rag.csv

Chaque question part dans une conversation neuve (aucune mémoire d'une question à l'autre), température 0.
Le script propose un verdict (colonne verdict_suggere) ; le verdict final est posé À LA MAIN dans la
colonne verdict, en comparant la réponse à la réponse attendue. La réponse attendue n'est jamais
envoyée au modèle : seule la colonne question l'est.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
from pathlib import Path
from typing import Any, Callable

VERDICTS = {
    "juste": "réponse juste, fondée sur un résultat d'outil",
    "refus_correct": "refuse alors qu'il fallait refuser, ou dit ne pas avoir de source",
    "introuvable_correct": "dit que le produit n'est pas dans le catalogue, sans inventer",
    "juste_non_source": "réponse juste, mais aucun résultat d'outil ne la contient",
    "invente": "information fausse ou chiffre absent des résultats d'outils",
    "outil_detourne": "outil appelé avec un argument absurde, puis une conclusion",
    "refus_sans_source": "refuse une question de connaissance faute de source (sûr, mais inutile)",
    "refus_a_tort": "refuse alors que la réponse était dans ses sources",
}
# Conforme : le comportement attendu est obtenu. Sans erreur : rien d'inventé ni de non sourcé.
CONFORMES = {"juste", "refus_correct", "introuvable_correct"}
ERREURS = {"juste_non_source", "invente", "outil_detourne"}

MARQUEURS_REFUS = re.compile(
    r"pas de source|ne dispose pas|ne peux pas|je ne suis pas en mesure|pas en mesure de|"
    r"professionnel de santé|hors de mon périmètre|je ne réponds|ne peux répondre",
    re.IGNORECASE,
)
MARQUEURS_INTROUVABLE = re.compile(
    r"pas dans le catalogue|introuvable|n'est pas référencé|aucun produit|ne figure pas", re.IGNORECASE
)
CHIFFRE = re.compile(r"\d")

COLONNES = ["id", "question", "reponse", "outils_appeles", "verdict_suggere", "verdict",
            "latence_s", "tokens_entree", "tokens_sortie", "modele"]


def suggerer_verdict(resultat: dict[str, Any], comportement_attendu: str | None) -> str:
    """Pré-classement automatique : une aide au correcteur, jamais le verdict final."""
    texte = resultat["reponse"]
    traces = resultat["outils_appeles"]
    if texte.startswith("ERREUR TECHNIQUE"):
        return "a_relancer"
    if MARQUEURS_INTROUVABLE.search(texte) and comportement_attendu in (None, "", "dire_introuvable"):
        return "introuvable_correct" if comportement_attendu == "dire_introuvable" else "refus_correct"
    if MARQUEURS_REFUS.search(texte):
        if comportement_attendu in (None, "", "refuser", "dire_introuvable"):
            return "refus_correct"
        return "refus_sans_source|refus_a_tort"
    if not traces:
        return "juste_non_source|invente"
    if all(t["statut"] in ("introuvable", "erreur") for t in traces) and CHIFFRE.search(texte):
        return "outil_detourne|invente"
    return "juste|invente"


def lire_questions(chemin: Path) -> list[dict[str, str]]:
    with open(chemin, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def mesurer(questions: list[dict[str, str]], repondre: Callable[[str], dict[str, Any]],
            sortie: Path, ids: set[str] | None = None) -> list[dict[str, Any]]:
    lignes = []
    for q in questions:
        if ids and q["id"] not in ids:
            continue
        try:
            resultat = repondre(q["question"])
        except Exception as e:  # modèle injoignable, quota… : on le note et on continue
            resultat = {"reponse": f"ERREUR TECHNIQUE : {type(e).__name__}: {e}", "outils_appeles": [],
                        "latence_s": 0.0, "tokens_entree": 0, "tokens_sortie": 0}
        lignes.append({
            "id": q["id"],
            "question": q["question"],
            "reponse": resultat["reponse"],
            "outils_appeles": json.dumps(resultat["outils_appeles"], ensure_ascii=False),
            "verdict_suggere": suggerer_verdict(resultat, q.get("comportement_attendu")),
            "verdict": "",
            "latence_s": resultat["latence_s"],
            "tokens_entree": resultat["tokens_entree"],
            "tokens_sortie": resultat["tokens_sortie"],
            "modele": os.environ.get("NUTRISCOPE_MODELE", "qwen3:8b"),
        })
        print(f"{q['id']:<5} {resultat['latence_s']:>6.1f} s  {lignes[-1]['verdict_suggere']:<26} "
              f"{resultat['reponse'][:70]!r}")
    sortie.parent.mkdir(parents=True, exist_ok=True)
    with open(sortie, "w", encoding="utf-8", newline="") as f:
        ecrivain = csv.DictWriter(f, fieldnames=COLONNES, delimiter=";")
        ecrivain.writeheader()
        ecrivain.writerows(lignes)
    return lignes


def main() -> None:
    from src.assistant.assistant import creer_client, repondre
    from src.assistant.catalogue import charger_catalogue

    parser = argparse.ArgumentParser(description="Passe un jeu de questions sur l'assistant.")
    parser.add_argument("--questions", required=True)
    parser.add_argument("--sortie", required=True)
    parser.add_argument("--ids", nargs="*", help="ne passer que ces questions (ex. --ids Q01 Q05)")
    args = parser.parse_args()

    client, catalogue = creer_client(), charger_catalogue()
    mesurer(lire_questions(Path(args.questions)),
            lambda question: repondre(question, client=client, catalogue=catalogue),
            Path(args.sortie), set(args.ids) if args.ids else None)
    print(f"\nRésultats dans {args.sortie} : remplissez la colonne verdict à la main.")


if __name__ == "__main__":
    main()
