"""Tests du client OpenRouter avec transport HTTP simulé."""
import json
import urllib.error

import pytest

from src.assistant.client_openrouter import ClientOpenRouter, URL_CHAT_COMPLETIONS


class FauxReponse:
    def __init__(self, donnees):
        self.donnees = json.dumps(donnees).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.donnees


def test_reponse_texte_et_parametres(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "cle-test")
    monkeypatch.setenv("OPENROUTER_MODEL", "fournisseur/modele-test")
    requetes = []

    def ouvrir(requete, timeout):
        requetes.append((requete, timeout))
        return FauxReponse({
            "choices": [{"message": {"role": "assistant", "content": "Bonjour", "tool_calls": None}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 4, "total_tokens": 16},
        })

    monkeypatch.setattr("urllib.request.urlopen", ouvrir)
    client = ClientOpenRouter(temperature=0.2, max_tokens=128, timeout=7)
    message = client.discuter([{"role": "user", "content": "Salut"}], [])

    requete, timeout = requetes[0]
    corps = json.loads(requete.data)
    assert requete.full_url == URL_CHAT_COMPLETIONS
    assert requete.get_header("Authorization") == "Bearer cle-test"
    assert timeout == 7
    assert corps["model"] == "fournisseur/modele-test"
    assert corps["temperature"] == 0.2 and corps["max_tokens"] == 128
    assert message["role"] == "assistant" and message["content"] == "Bonjour"
    assert message["_tokens"] == {"prompt_tokens": 12, "completion_tokens": 4, "total_tokens": 16}
    assert message["_latence_s"] >= 0


def test_appel_outil_preserve_id_et_format(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "cle-test")
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: FauxReponse({
        "choices": [{"message": {
            "role": "assistant", "content": None,
            "tool_calls": [{
                "id": "call_abc", "type": "function",
                "function": {"name": "chercher_produit", "arguments": "{\"nom\":\"avoine\"}"},
            }],
        }}],
        "usage": {"prompt_tokens": 20, "completion_tokens": 8},
    }))

    message = ClientOpenRouter().discuter([], [{"type": "function"}])
    assert message["tool_calls"][0] == {
        "id": "call_abc", "type": "function",
        "function": {"name": "chercher_produit", "arguments": '{"nom":"avoine"}'},
    }
    assert message["_tokens"] == {"prompt_tokens": 20, "completion_tokens": 8}


def test_erreur_http_est_lisible_sans_cle(monkeypatch):
    cle = "secret-ne-pas-afficher"
    monkeypatch.setenv("OPENROUTER_API_KEY", cle)

    def ouvrir(*args, **kwargs):
        raise urllib.error.HTTPError(URL_CHAT_COMPLETIONS, 429, "Limite atteinte", {}, None)

    monkeypatch.setattr("urllib.request.urlopen", ouvrir)
    with pytest.raises(RuntimeError, match="erreur HTTP 429") as erreur:
        ClientOpenRouter().discuter([], [])
    assert cle not in str(erreur.value)


def test_erreur_reseau_est_lisible_sans_cle(monkeypatch):
    cle = "secret-ne-pas-afficher"
    monkeypatch.setenv("OPENROUTER_API_KEY", cle)
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(
        urllib.error.URLError("connexion refusée")
    ))

    with pytest.raises(ConnectionError, match="Impossible de joindre OpenRouter") as erreur:
        ClientOpenRouter().discuter([], [])
    assert cle not in str(erreur.value)


def test_absence_de_cle(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        ClientOpenRouter().discuter([], [])
