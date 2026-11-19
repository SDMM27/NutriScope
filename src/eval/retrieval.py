"""Mesure de 16h45 : la bonne fiche est-elle dans le top k ? (TP 19, étape 1). Fourni complet.

Pour chaque question `produit` et `comparaison` de eval/questions.csv :
  - attendus : les fiche:<code> de sources_attendues (séparés par |) ;
  - trouves  : les ids rendus par rechercher(question, k) ;
  - rang     : position de la première fiche attendue trouvée, vide si aucune (servira au MRR de jeudi) ;
  - hit      : 1 si TOUTES les fiches attendues sont dans le top k, sinon 0.

Usage : python -m src.eval.retrieval [--k 5] [--sortie resultats/retrieval_fiches.csv]
                                     [--moteur chroma|numpy] [--sans-consigne]
"""

from __future__ import annotations

import argparse
import csv
from collections.abc import Callable
from pathlib import Path
from typing import Any

RACINE = Path(__file__).resolve().parents[2]
TYPES = ("produit", "comparaison")
COLONNES = ["id", "type", "attendus", "trouves", "rang", "hit"]


def lire_questions(chemin: str | Path) -> list[dict[str, str]]:
    with open(chemin, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def attendus_fiches(sources: str | None) -> list[str]:
    return [s.strip() for s in (sources or "").split("|") if s.strip().startswith("fiche:")]


def mesurer(questions: list[dict[str, str]], rechercher: Callable[..., list[dict[str, Any]]],
            k: int = 5, types: tuple[str, ...] = TYPES) -> list[dict[str, Any]]:
    lignes = []
    for q in questions:
        attendus = attendus_fiches(q.get("sources_attendues"))
        if q.get("type") not in types or not attendus:
            continue
        trouves = [r["id"] for r in rechercher(q["question"], k=k)]
        rangs = sorted(trouves.index(a) + 1 for a in attendus if a in trouves)
        lignes.append({
            "id": q["id"], "type": q["type"],
            "attendus": "|".join(attendus), "trouves": "|".join(trouves),
            "rang": rangs[0] if rangs else "", "hit": int(len(rangs) == len(attendus)),
        })
    return lignes


def ecrire(lignes: list[dict[str, Any]], chemin: str | Path) -> None:
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLONNES, delimiter=";")
        w.writeheader()
        w.writerows(lignes)


def synthese(lignes: list[dict[str, Any]]) -> dict[str, Any]:
    par_type: dict[str, list[int]] = {}
    for l in lignes:
        h, n = par_type.setdefault(l["type"], [0, 0])
        par_type[l["type"]] = [h + l["hit"], n + 1]
    return {"hits": sum(l["hit"] for l in lignes), "total": len(lignes), "par_type": par_type}


def main() -> None:
    parser = argparse.ArgumentParser(description="Hit@k des fiches sur les questions produit et comparaison.")
    parser.add_argument("--questions", default=str(RACINE / "eval" / "questions.csv"))
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--sortie", default=str(RACINE / "resultats" / "retrieval_fiches.csv"))
    parser.add_argument("--moteur", choices=["chroma", "numpy"], default="chroma")
    parser.add_argument("--sans-consigne", action="store_true")
    args = parser.parse_args()

    if args.moteur == "numpy":
        from src.rag.index_numpy import rechercher as moteur
    else:
        from src.rag.recherche import rechercher as moteur

    def chercher(question: str, k: int) -> list[dict[str, Any]]:
        return moteur(question, k=k, consigne=not args.sans_consigne)

    questions = lire_questions(args.questions)
    lignes = mesurer(questions, chercher, k=args.k)
    ecrire(lignes, args.sortie)

    s = synthese(lignes)
    print(f"hit@{args.k} : {s['hits']} / {s['total']}")
    for t, (h, n) in s["par_type"].items():
        print(f"  {t:<12} {h} / {n}")
    textes = {q["id"]: q["question"] for q in questions}
    echecs = [l for l in lignes if not l["hit"]]
    if echecs:
        print("\nÉchecs (à classer : code-barres seul, nom, marque, comparaison) :")
        for l in echecs:
            print(f"  {l['id']}  rang {l['rang'] or '—'}  {textes[l['id']]}")
    print(f"\nRésultats dans {args.sortie}")


if __name__ == "__main__":
    main()
