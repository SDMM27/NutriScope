"""Client minimal pour l'API Chat Completions d'OpenRouter (urllib, sans dépendance)."""
import json
import os
import time
import urllib.error
import urllib.request


URL_CHAT_COMPLETIONS = "https://openrouter.ai/api/v1/chat/completions"


class ClientOpenRouter:
    """Appelle un modèle distant via OpenRouter."""

    def __init__(self, modele=None, temperature=0.0, max_tokens=256, timeout=60):
        self.modele = modele or os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    def discuter(self, messages, outils) -> dict:
        """Un tour de chat ; renvoie le message du modèle + _latence_s et _tokens."""
        cle = os.environ.get("OPENROUTER_API_KEY")
        if not cle:
            raise RuntimeError("La variable OPENROUTER_API_KEY n'est pas définie.")

        corps = {
            "model": self.modele,
            "messages": [{k: v for k, v in m.items() if k != "tool_name"} for m in messages],
            "tools": outils,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        requete = urllib.request.Request(
            URL_CHAT_COMPLETIONS,
            data=json.dumps(corps).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {cle}",
                "Content-Type": "application/json",
            },
        )
        debut = time.perf_counter()
        try:
            with urllib.request.urlopen(requete, timeout=self.timeout) as r:
                donnees = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"OpenRouter a répondu une erreur HTTP {e.code}.") from e
        except (urllib.error.URLError, OSError) as e:
            detail = e.reason if isinstance(e, urllib.error.URLError) else e
            detail = str(detail).replace(cle, "[masquée]")
            raise ConnectionError(f"Impossible de joindre OpenRouter : {detail}") from e

        choix = donnees.get("choices", [{}])[0]
        message = dict(choix.get("message", {}))
        usage = donnees.get("usage", {})
        message["_latence_s"] = time.perf_counter() - debut
        message["_tokens"] = {
            k: usage[k]
            for k in ("prompt_tokens", "completion_tokens", "total_tokens", "cost", "cost_details")
            if k in usage
        }
        return message
