"""rechercher() : la recherche sémantique dans les fiches (TP 19, étape 1).

Contrat. C'est la fonction que B. Quinet emballera dans l'outil repondre_source (TP 21, 25/11).

    rechercher(question, k=5, filtres=None) -> list[dict]

- Rend au plus k résultats (1 <= k <= 20), triés par score décroissant : le plus proche d'abord.
- Chaque résultat : {"id": "fiche:<code>", "score": float, "texte": str, "metadonnees": dict}.
- "id" a le format de sources_attendues dans eval/questions.csv.
- "score" = 1 - distance cosinus. 1 : même direction. Plus haut = plus proche.
- "metadonnees" : une clé absente = valeur inconnue. Jamais 0, jamais chaîne vide.
- "filtres" : un filtre `where` de Chroma, par exemple {"rayon": "Boissons"}. None = aucun filtre.
- Question vide ou k hors limites : ValueError. Index vide : liste vide.
- Aucune génération ici : on rend des extraits, pas une réponse.

Usage : python -m src.rag.recherche "Combien de sucres dans le skyr nature ?" [-k 5] [--rayon Boissons]
        [--sans-consigne]

Fourni : les vérifications d'entrée, la ligne de commande. À écrire : TODO 3 à 5.
"""

from __future__ import annotations

import argparse
from typing import Any

from src.rag.embeddings import Vectoriseur, embed_documents, formater_question
from src.rag.indexer import collection_fiches

K_MAX = 20

_collection: Any = None


def _collection_par_defaut() -> Any:
    global _collection
    if _collection is None:
        _collection = collection_fiches()
    return _collection


def rechercher(question: str, k: int = 5, filtres: dict[str, Any] | None = None, *,
               collection: Any = None, vectoriser: Vectoriseur | None = None,
               consigne: bool = True) -> list[dict[str, Any]]:
    """Voir le contrat en tête de module. Les arguments nommés servent aux tests et aux mesures."""
    if not question or not question.strip():
        raise ValueError("question vide")
    if not 1 <= k <= K_MAX:
        raise ValueError(f"k doit être compris entre 1 et {K_MAX}")

    collection = collection if collection is not None else _collection_par_defaut()
    if collection.count() == 0:
        return []

    vectoriser = vectoriser or embed_documents

    # TODO 3 : préparer puis vectoriser la question.
    texte_prepare = formater_question(question, consigne)
    vecteur = vectoriser([texte_prepare])[0]

    # TODO 4 : interroger Chroma.
    # Pour les embeddings déjà calculés, utilise query_embeddings, pas query_texts.
    reponse = collection.query(
        query_embeddings=[vecteur],
        n_results=k,
        where=filtres,
        include=["documents", "metadatas", "distances"],
    )

    # TODO 5 : reconstruire la liste demandée par le contrat.
    resultats: list[dict[str, Any]] = []

    ids = reponse["ids"][0]
    documents = reponse["documents"][0]
    metadonnees = reponse["metadatas"][0]
    distances = reponse["distances"][0]

    # zip parcourt ensemble les quatre listes alignées.
    for identifiant, texte, metadata, distance in zip(
        ids, documents, metadonnees, distances
    ):
        # Une métadonnée retournée à null devient {}.
        if metadata is None:
            metadata = {}

        resultats.append({
            "id": identifiant,
            "score": round(1 - distance, 4),
            "texte": texte,
            "metadonnees": metadata,
        })

    return resultats

    




def main() -> None:
    parser = argparse.ArgumentParser(description="Cherche les fiches les plus proches d'une question.")
    parser.add_argument("question")
    parser.add_argument("-k", type=int, default=5)
    parser.add_argument("--rayon", default=None, help="filtre sur la métadonnée rayon")
    parser.add_argument("--sans-consigne", action="store_true", help="vectorise la question sans consigne")
    args = parser.parse_args()
    filtres = {"rayon": args.rayon} if args.rayon else None
    resultats = rechercher(args.question, k=args.k, filtres=filtres, consigne=not args.sans_consigne)
    for rang, r in enumerate(resultats, 1):
        m = r["metadonnees"]
        print(f"{rang}. {r['score']:.3f}  {r['id']:<22}  {m.get('nom', '?')} — {m.get('marque') or 'marque non renseignée'}")
    if not resultats:
        print("Aucun résultat : l'index est vide, ou le filtre ne retient aucune fiche.")


if __name__ == "__main__":
    main()
