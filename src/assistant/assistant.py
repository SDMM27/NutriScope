"""Boucle de dialogue : question (+ historique) -> appels d'outils -> réponse vérifiée."""
import json
import time
import uuid

from src.assistant.garde_fous import PROMPT_SYSTEME, detecter_hors_perimetre, verifier_chiffres
from src.assistant.outils import SCHEMA_CHERCHER_PRODUIT, executer_outil

MESSAGE_ECHEC = (
    "Désolé, je n'ai pas réussi à répondre à cette question (trop d'appels d'outils sans réponse finale)."
)

# Mémoire de conversation : nombre d'échanges précédents renvoyés au modèle.
# Un échange = une question utilisateur + tout ce qui suit (appels d'outils, résultats, réponse).
# Borné car tout l'historique est renvoyé à chaque tour : plus de tokens = plus de latence (et de coût via API).
MAX_ECHANGES = 3


def _tronquer(historique, max_echanges=MAX_ECHANGES):
    """Garde le message system + les `max_echanges` derniers échanges COMPLETS.

    On coupe toujours juste avant un message "user" : un résultat d'outil ne doit
    jamais se retrouver sans l'appel qui l'a demandé.
    """
    debuts = [i for i, m in enumerate(historique) if m.get("role") == "user"]
    if len(debuts) <= max_echanges:
        return list(historique)
    return [historique[0]] + historique[debuts[-max_echanges]:]


def _resultats_outils(messages):
    """Résultats d'outils présents dans l'historique (le modèle peut citer un tour précédent)."""
    resultats = []
    for m in messages:
        if m.get("role") == "tool":
            try:
                resultats.append(json.loads(m["content"]))
            except (ValueError, KeyError, TypeError):
                pass
    return resultats


def repondre(question, catalogue, client, max_tours=4, historique=None) -> dict:
    """Répond à une question en tenant compte de l'historique de conversation.

    `historique` : liste de messages renvoyée par l'appel précédent (clé "historique"),
    ou None pour démarrer une conversation. La fonction ne garde aucun état : c'est
    l'appelant qui conserve l'historique (notebook aujourd'hui, API au TP 23).
    """
    debut = time.perf_counter()
    if historique:
        messages = _tronquer(historique)  # nouvelle liste : celle de l'appelant n'est pas modifiée
    else:
        messages = [{"role": "system", "content": PROMPT_SYSTEME}]
    messages.append({"role": "user", "content": question})

    refus = detecter_hors_perimetre(question)
    if refus:
        # Le refus est gardé en mémoire : le modèle sait qu'il a déjà décliné cette demande.
        messages.append({"role": "assistant", "content": refus})
        return {
            "question": question, "reponse": refus, "appels": [], "tours": 0,
            "latence_totale_s": time.perf_counter() - debut,
            "chiffres_non_verifies": [], "refus": "filtre", "historique": messages, "mesures_appels": [],
        }

    appels, reponse, arret, tours = [], None, None, 0
    mesures_appels = []
    while tours < max_tours:
        tours += 1
        message = client.discuter(messages, [SCHEMA_CHERCHER_PRODUIT])
        mesures_appels.append({"latence_s": message.get("_latence_s"), "tokens": message.get("_tokens")})
        appels_demandes = message.get("tool_calls")
        if not appels_demandes:
            reponse = message.get("content") or ""
            break
        message_historique = {k: v for k, v in message.items() if not k.startswith("_")}
        for appel in appels_demandes:
            if not appel.get("id"):
                appel["id"] = f"call_{uuid.uuid4().hex}"
        messages.append(message_historique)
        for appel in appels_demandes:
            fonction = appel.get("function", {})
            nom, arguments = fonction.get("name"), fonction.get("arguments")
            resultat = executer_outil(nom, arguments, catalogue)
            appels.append({"outil": nom, "arguments": arguments, "resultat": resultat})
            messages.append({
                "role": "tool", "tool_name": nom, "name": nom,
                "tool_call_id": appel["id"],
                "content": json.dumps(resultat, ensure_ascii=False),
            })
    if reponse is None:
        reponse, arret = MESSAGE_ECHEC, "max_tours"
    messages.append({"role": "assistant", "content": reponse})

    resultat_final = {
        "question": question, "reponse": reponse, "appels": appels, "tours": tours,
        "latence_totale_s": time.perf_counter() - debut,
        "chiffres_non_verifies": verifier_chiffres(reponse, _resultats_outils(messages)),
        "refus": None, "historique": messages, "mesures_appels": mesures_appels,
    }
    if arret:
        resultat_final["arret"] = arret
    return resultat_final
