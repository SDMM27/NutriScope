"""FAUX modèle d'embeddings, pour les tests unitaires uniquement.

Il découpe le texte en trigrammes de caractères et les hache dans un vecteur de 1 024 nombres, de norme 1.
Deux textes qui partagent des morceaux de mots se ressemblent : c'est assez pour tester l'indexation,
le contrat de rechercher() et la mesure. Il ne capte pas le sens : il ne remplace jamais qwen3-embedding
pour une mesure ou une démonstration.
"""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from collections.abc import Sequence

DIMENSION = 1024


def _normaliser(texte: str) -> str:
    sans_accents = unicodedata.normalize("NFKD", texte.lower())
    sans_accents = "".join(c for c in sans_accents if not unicodedata.combining(c))
    return " " + re.sub(r"\s+", " ", sans_accents).strip() + " "


def vecteur(texte: str, dimension: int = DIMENSION) -> list[float]:
    t = _normaliser(texte)
    v = [0.0] * dimension
    for i in range(len(t) - 2):
        empreinte = hashlib.md5(t[i:i + 3].encode("utf-8")).digest()
        v[int.from_bytes(empreinte[:4], "little") % dimension] += 1.0 if empreinte[4] & 1 else -1.0
    norme = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / norme for x in v]


class FauxEmbeddings:
    """Même signature que src.rag.embeddings.embed_documents : textes -> vecteurs."""

    def __init__(self, dimension: int = DIMENSION) -> None:
        self.dimension = dimension
        self.appels = 0

    def embed_documents(self, textes: Sequence[str]) -> list[list[float]]:
        self.appels += 1
        return [vecteur(t, self.dimension) for t in textes]
