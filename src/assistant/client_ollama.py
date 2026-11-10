"""Client minimal pour l'API /api/chat d'Ollama (urllib, sans dépendance)."""
import json
import os
import time
import urllib.error
import urllib.request


class ClientOllama:
    """Appelle un modèle local via Ollama."""

    def __init__(self, modele="qwen3:8b", url="http://localhost:11434", temperature=0.0, timeout=180):
        self.modele = modele
        self.url = os.environ.get("OLLAMA_URL", url).rstrip("/")
        self.temperature = temperature
        self.timeout = timeout

    def discuter(self, messages, outils) -> dict:
        """Un tour de chat ; renvoie le message du modèle + _latence_s et _tokens."""
        corps = {
            "model": self.modele,
            "messages": messages,
            "tools": outils,
            "stream": False,
            "think": False,
            "options": {"temperature": self.temperature},
        }
        requete = urllib.request.Request(
            f"{self.url}/api/chat",
            data=json.dumps(corps).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        debut = time.perf_counter()
        try:
            with urllib.request.urlopen(requete, timeout=self.timeout) as r:
                donnees = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ollama a répondu une erreur HTTP {e.code} : {detail}") from e
        except (urllib.error.URLError, OSError) as e:
            raise ConnectionError(
                f"Ollama injoignable sur {self.url} (est-il lancé ? `ollama serve`) : {e}"
            ) from e
        message = dict(donnees.get("message", {}))
        message["_latence_s"] = time.perf_counter() - debut
        message["_tokens"] = {
            k: donnees[k] for k in ("prompt_eval_count", "eval_count") if k in donnees
        }
        return message
