"""Fait passer un jeu de questions à l'assistant et enregistre ses réponses.

Usage :
    python -m outils.mesurer_assistant <questions.csv> <resultats.csv>

Même script pour le bloc 2, le bloc 4 et la remesure avec RAG : seul l'assistant doit changer
entre deux mesures, jamais le protocole.

Protocole :
- seules les colonnes `id` et `question` sont lues : la vérité terrain n'atteint jamais le prompt ;
- une conversation par question (pas d'historique), température 0 (défaut de ClientOllama) ;
- un appel de chauffe non enregistré, pour que la question 1 ne paie pas le chargement du modèle ;
- `verdict` reste vide : il est rempli à la main.
"""
import csv
import json
import sys
from pathlib import Path

from src.assistant.assistant import repondre
from src.assistant.catalogue import charger_catalogue
from src.assistant.client_ollama import ClientOllama

COLONNES_SORTIE = ["id", "reponse", "outils_appeles", "verdict", "latence_s"]
QUESTION_CHAUFFE = "Quel est le Nutri-Score du Nutella ?"


def lire_questions(chemin):
    """Ne garde que (id, question) : les autres colonnes ne quittent pas ce fichier."""
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        return [(ligne["id"], ligne["question"]) for ligne in csv.DictReader(f, delimiter=";")]


def resumer_appels(appels):
    """Outils appelés et leurs arguments, sans le résultat (trop long pour un CSV)."""
    return json.dumps([{"outil": a["outil"], "arguments": a["arguments"]} for a in appels], ensure_ascii=False)


def mesurer(questions, catalogue, client):
    lignes = []
    for i, (id_q, question) in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] {id_q} : {question}")
        try:
            r = repondre(question, catalogue, client)  # historique=None : une conversation par question
            ligne = {"reponse": r["reponse"], "outils_appeles": resumer_appels(r["appels"]),
                     "latence_s": round(r["latence_totale_s"], 2)}
        except Exception as e:  # une question en erreur ne doit pas arrêter toute la mesure
            ligne = {"reponse": f"ERREUR : {e}", "outils_appeles": "[]", "latence_s": ""}
        lignes.append({"id": id_q, "verdict": "", **ligne})
        print(f"    -> {ligne['latence_s']} s, outils : {ligne['outils_appeles']}")
    return lignes


def main():
    if len(sys.argv) != 3:
        sys.exit("Usage : python -m outils.mesurer_assistant <questions.csv> <resultats.csv>")
    entree, sortie = Path(sys.argv[1]), Path(sys.argv[2])

    questions = lire_questions(entree)
    catalogue = charger_catalogue()
    client = ClientOllama()  # modèle de l'ADR 0001 : qwen3:8b, think false, température 0

    print("Appel de chauffe (non enregistré)...")
    repondre(QUESTION_CHAUFFE, catalogue, client)

    lignes = mesurer(questions, catalogue, client)

    sortie.parent.mkdir(parents=True, exist_ok=True)
    with open(sortie, "w", encoding="utf-8-sig", newline="") as f:  # utf-8-sig : accents lisibles dans Excel
        ecrivain = csv.DictWriter(f, fieldnames=COLONNES_SORTIE, delimiter=";")
        ecrivain.writeheader()
        ecrivain.writerows(lignes)
    print(f"{len(lignes)} réponses écrites dans {sortie}. Remplissez la colonne verdict à la main.")


if __name__ == "__main__":
    main()
