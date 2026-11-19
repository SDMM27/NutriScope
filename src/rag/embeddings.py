"""Vectorisation des textes avec le modèle d'embeddings (TP 19). Fourni complet..

Le modèle d'embeddings tourne en local (Ollama, API compatible OpenAI), même si le LLM passe par
OpenRouter : un index n'a de sens qu'avec le modèle qui l'a construit. Changer de modèle, c'est
réindexer tout le corpus.

Variables d'environnement (facultatives, valeurs par défaut ci-dessous) :
  NUTRISCOPE_EMBED_BASE_URL      http://localhost:11434/v1
  NUTRISCOPE_EMBED_API_KEY       ollama
  NUTRISCOPE_MODELE_EMBEDDINGS   qwen3-embedding:0.6b
"""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from typing import Any

try:  # lit .env s'il existe, comme l'assistant de lundi
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

MODELE = os.environ.get("NUTRISCOPE_MODELE_EMBEDDINGS", "qwen3-embedding:0.6b")
DIMENSION = 1024  # qwen3-embedding:0.6b
TAILLE_LOT = 64  # textes par appel d'API

# qwen3-embedding attend une consigne devant la question, rien devant les documents.
# La fiche du modèle conseille de l'écrire en anglais, même pour des questions en français.
CONSIGNE = "Given a question about food products or nutrition, retrieve the passage that answers it"

Vectoriseur = Callable[[Sequence[str]], list[list[float]]]

_client: Any = None


def creer_client_embeddings() -> Any:
    """Même client OpenAI que l'assistant (cours 002), mais pointé sur le serveur d'embeddings."""
    from openai import OpenAI

    return OpenAI(
        base_url=os.environ.get("NUTRISCOPE_EMBED_BASE_URL", "http://localhost:11434/v1"),
        api_key=os.environ.get("NUTRISCOPE_EMBED_API_KEY", "ollama"),
    )


def _client_par_defaut() -> Any:
    global _client
    if _client is None:
        _client = creer_client_embeddings()
    return _client


def embed_documents(textes: Sequence[str], client: Any = None) -> list[list[float]]:
    """Un vecteur par texte, dans l'ordre des textes, par lots de TAILLE_LOT. Sans consigne."""
    client = client or _client_par_defaut()
    textes = list(textes)
    vecteurs: list[list[float]] = []
    for debut in range(0, len(textes), TAILLE_LOT):
        lot = textes[debut:debut + TAILLE_LOT]
        reponse = client.embeddings.create(model=MODELE, input=lot)
        donnees = sorted(reponse.data, key=lambda d: d.index)
        vecteurs.extend(list(d.embedding) for d in donnees)
    return vecteurs


def formater_question(question: str, consigne: bool = True) -> str:
    """Le texte réellement vectorisé pour une question."""
    return f"Instruct: {CONSIGNE}\nQuery:{question}" if consigne else question


def embed_question(question: str, consigne: bool = True, client: Any = None) -> list[float]:
    return embed_documents([formater_question(question, consigne)], client=client)[0]
