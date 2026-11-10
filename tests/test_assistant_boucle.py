"""Tests de la boucle de l'assistant avec un faux client scénarisé."""
import json

import numpy as np
import pandas as pd

from src.assistant.assistant import repondre
from src.assistant.catalogue import COLONNES_NUTRIMENTS, normaliser


class FauxClient:
    """Renvoie les messages scénarisés dans l'ordre (le dernier se répète)."""

    def __init__(self, messages):
        self.messages = messages
        self.appels = 0
        self.recus = []

    def discuter(self, messages, outils):
        self.recus.append(list(messages))
        msg = self.messages[min(self.appels, len(self.messages) - 1)]
        self.appels += 1
        return msg


def appel(nom, arguments):
    return {"role": "assistant", "content": "",
            "tool_calls": [{"function": {"name": nom, "arguments": arguments}}]}


def catalogue():
    base = {c: np.nan for c in COLONNES_NUTRIMENTS.values()}
    df = pd.DataFrame([{**base, "code": "1", "name": "Nutella", "brand_name": "Ferrero",
                        "nutriscore_grade": "e", "completeness": 0.9, "sugars": 56.3}])
    df["nom_normalise"] = df["name"].map(normaliser)
    return df


def test_appel_outil_puis_reponse():
    c = FauxClient([appel("chercher_produit", {"nom": "nutella"}),
                    {"role": "assistant", "content": "Le Nutella contient 56,3 g de sucres."}])
    r = repondre("Sucres du Nutella ?", catalogue(), c)
    assert r["tours"] == 2 and r["refus"] is None
    assert r["appels"][0]["resultat"]["statut"] == "ok"
    assert r["chiffres_non_verifies"] == []
    msg_outil = c.recus[1][-1]
    assert msg_outil["role"] == "tool" and msg_outil["tool_name"] == "chercher_produit"
    assert json.loads(msg_outil["content"])["total"] == 1


def test_arguments_en_chaine():
    c = FauxClient([appel("chercher_produit", '{"code": "1"}'),
                    {"role": "assistant", "content": "ok"}])
    assert repondre("code 1", catalogue(), c)["appels"][0]["resultat"]["statut"] == "ok"


def test_outil_inconnu_renvoye_au_modele():
    c = FauxClient([appel("pirater", {}), {"role": "assistant", "content": "désolé"}])
    r = repondre("question", catalogue(), c)
    assert "outil inconnu" in r["appels"][0]["resultat"]["erreur"]
    assert r["reponse"] == "désolé"


def test_chiffre_invente_detecte():
    c = FauxClient([appel("chercher_produit", {"nom": "nutella"}),
                    {"role": "assistant", "content": "Il y a 99 g de sucres."}])
    assert repondre("q", catalogue(), c)["chiffres_non_verifies"] == ["99"]


def test_max_tours():
    c = FauxClient([appel("chercher_produit", {"nom": "nutella"})])
    r = repondre("q", catalogue(), c, max_tours=3)
    assert r["arret"] == "max_tours" and r["tours"] == 3 and c.appels == 3
    assert r["reponse"]


def test_refus_filtre_sans_llm():
    c = FauxClient([{"role": "assistant", "content": "ne doit pas servir"}])
    r = repondre("Je suis diabétique, puis-je manger du Nutella ?", catalogue(), c)
    assert r["refus"] == "filtre" and r["tours"] == 0 and r["appels"] == []
    assert c.appels == 0


# ---------- Mémoire de conversation ----------

def test_historique_transmis_au_tour_suivant():
    c = FauxClient([{"role": "assistant", "content": "Lequel ?"}])
    r1 = repondre("Nutri-Score du Nutella ?", catalogue(), c)
    repondre("le premier", catalogue(), c, historique=r1["historique"])
    contenus = [m["content"] for m in c.recus[-1]]
    assert contenus[0].startswith("Tu es") and "Nutri-Score du Nutella ?" in contenus
    assert "Lequel ?" in contenus and contenus[-1] == "le premier"


def test_historique_appelant_non_modifie():
    c = FauxClient([{"role": "assistant", "content": "ok"}])
    r1 = repondre("q1", catalogue(), c)
    taille = len(r1["historique"])
    repondre("q2", catalogue(), c, historique=r1["historique"])
    assert len(r1["historique"]) == taille


def test_fenetre_glissante_garde_system_et_trois_echanges():
    from src.assistant.assistant import MAX_ECHANGES
    c = FauxClient([{"role": "assistant", "content": "ok"}])
    hist = None
    for i in range(5):
        hist = repondre(f"question {i}", catalogue(), c, historique=hist)["historique"]
    envoye = c.recus[-1]
    assert envoye[0]["role"] == "system"
    users = [m["content"] for m in envoye if m["role"] == "user"]
    # 3 échanges précédents gardés + la question courante
    assert users == [f"question {i}" for i in range(5 - MAX_ECHANGES - 1, 5)]


def test_troncature_ne_coupe_pas_un_echange_outille():
    from src.assistant.assistant import _tronquer
    hist = [{"role": "system", "content": "s"},
            {"role": "user", "content": "a"}, {"role": "assistant", "content": "", "tool_calls": []},
            {"role": "tool", "content": "{}"}, {"role": "assistant", "content": "ra"},
            {"role": "user", "content": "b"}, {"role": "assistant", "content": "rb"}]
    garde = _tronquer(hist, max_echanges=1)
    assert [m["role"] for m in garde] == ["system", "user", "assistant"]
    assert garde[1]["content"] == "b"


def test_chiffre_d_un_tour_precedent_est_verifie():
    c = FauxClient([appel("chercher_produit", {"code": "1"}),
                    {"role": "assistant", "content": "Trouvé."},
                    {"role": "assistant", "content": "Il contient 56,3 g de sucres."}])
    r1 = repondre("Nutella ?", catalogue(), c)
    r2 = repondre("Et ses sucres ?", catalogue(), c, historique=r1["historique"])
    assert r2["appels"] == [] and r2["chiffres_non_verifies"] == []


def test_refus_filtre_garde_en_memoire():
    c = FauxClient([{"role": "assistant", "content": "ok"}])
    r = repondre("Je suis diabétique, puis-je manger du Nutella ?", catalogue(), c)
    assert c.appels == 0
    assert [m["role"] for m in r["historique"]] == ["system", "user", "assistant"]
