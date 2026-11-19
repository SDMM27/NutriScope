"""FAUX client LLM, pour les tests unitaires uniquement.

Il imite la forme des réponses de l'API compatible OpenAI (Ollama, OpenRouter) et rejoue un script
de réponses écrit à l'avance. Il ne remplace jamais le vrai modèle pour une mesure ou une démonstration.
"""

from __future__ import annotations

import json
from types import SimpleNamespace as NS
from typing import Any


def appel_outil(nom: str, arguments: dict[str, Any] | str, ident: str = "appel_1") -> NS:
    brut = arguments if isinstance(arguments, str) else json.dumps(arguments, ensure_ascii=False)
    return NS(id=ident, type="function", function=NS(name=nom, arguments=brut))


def reponse(texte: str | None = None, appels: list[NS] | None = None) -> NS:
    message = NS(content=texte, tool_calls=appels or None)
    return NS(choices=[NS(message=message)], usage=NS(prompt_tokens=100, completion_tokens=20))


class FauxClient:
    """Rejoue `script` dans l'ordre. Si `outils_en_boucle`, demande un outil tant qu'on lui en propose."""

    def __init__(self, script: list[NS] | None = None, outils_en_boucle: bool = False):
        self.script = list(script or [])
        self.outils_en_boucle = outils_en_boucle
        self.appels: list[dict[str, Any]] = []
        self.chat = NS(completions=NS(create=self._create))

    def _create(self, **kwargs: Any) -> NS:
        self.appels.append(kwargs)
        if self.outils_en_boucle:
            if "tools" in kwargs:
                return reponse(appels=[appel_outil("chercher_produit", {"nom": "nutella"}, f"a{len(self.appels)}")])
            return reponse("Réponse finale sans outil.")
        return self.script.pop(0)
