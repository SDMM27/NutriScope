"""La boucle de l'assistant, testée avec un FAUX client (aucun modèle n'est appelé ici)."""

import json

from src.assistant import assistant as A
from src.assistant.catalogue import charger_catalogue
from tests.faux_client import FauxClient, appel_outil, reponse

CAT = charger_catalogue()


def test_appel_outil_puis_conclusion():
    client = FauxClient([
        reponse(appels=[appel_outil("chercher_produit", {"code": "3329770077003"})]),
        reponse("Le Skyr nature 0% est noté A."),
    ])
    r = A.repondre("Nutri-Score du skyr ?", client=client, catalogue=CAT)
    assert r["reponse"] == "Le Skyr nature 0% est noté A."
    assert r["outils_appeles"] == [{"outil": "chercher_produit", "arguments": '{"code": "3329770077003"}', "statut": "ok"}]
    # Le résultat de l'outil a bien été renvoyé au modèle, avec la vraie fiche.
    message_outil = client.appels[1]["messages"][-1]
    assert message_outil["role"] == "tool"
    assert json.loads(message_outil["content"])["produits"][0]["nutriscore"] == "A"
    assert client.appels[0]["temperature"] == 0


def test_conversation_neuve_et_prompt_systeme():
    client = FauxClient([reponse("Je n'ai pas de source pour répondre.")])
    A.repondre("Combien de fruits par jour ?", client=client, catalogue=CAT)
    messages = client.appels[0]["messages"]
    assert [m["role"] for m in messages] == ["system", "user"]


def test_la_boucle_ne_tourne_pas_sans_fin():
    client = FauxClient(outils_en_boucle=True)
    r = A.repondre("Parle-moi du Nutella", client=client, catalogue=CAT)
    assert len(client.appels) == A.TOURS_MAX + 1
    assert "tools" not in client.appels[-1]  # dernier tour : plus d'outils proposés, le modèle doit conclure
    assert r["reponse"] == "Réponse finale sans outil."
    assert len(r["outils_appeles"]) == A.TOURS_MAX


def test_outil_inconnu_et_arguments_illisibles():
    client = FauxClient([
        reponse(appels=[appel_outil("supprimer_base", {}, "x1"), appel_outil("chercher_produit", "{mal formé", "x2")]),
        reponse("Je ne peux pas répondre."),
    ])
    r = A.repondre("…", client=client, catalogue=CAT)
    assert [t["statut"] for t in r["outils_appeles"]] == ["erreur", "erreur"]
    contenus = [json.loads(m["content"]) for m in client.appels[1]["messages"] if m["role"] == "tool"]
    assert "outil inconnu" in contenus[0]["erreur"] and "mal formé" in contenus[1]["erreur"]


def test_jetons_comptes():
    client = FauxClient([reponse(appels=[appel_outil("chercher_produit", {"nom": "skyr"})]), reponse("ok")])
    r = A.repondre("?", client=client, catalogue=CAT)
    assert (r["tokens_entree"], r["tokens_sortie"]) == (200, 40)
