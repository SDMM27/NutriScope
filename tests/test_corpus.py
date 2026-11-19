"""Bloc 3 : fiches produits et extraction de texte."""

import json

from src.assistant.catalogue import charger_catalogue
from src.corpus import telecharger as T
from src.corpus.fiches import NON_RENSEIGNE, ecrire_fiches, fiche_texte

CAT = {p["code"]: p for p in charger_catalogue()}


def test_fiche_nutella():
    texte = fiche_texte(CAT["3017620422003"])
    assert "Produit : Nutella — Ferrero, Nutella" in texte
    assert "Nutri-Score : E" in texte
    assert "dont sucres 56.3 g" in texte
    assert "Source : Open Food Facts (licence ODbL), export du 2026-11-11" in texte


def test_valeur_inconnue_ecrite_non_renseigne_jamais_0():
    texte = fiche_texte(CAT["5449000214911"])  # Coca-Cola : fibres absentes
    assert f"fibres {NON_RENSEIGNE}" in texte
    assert "Valeurs pour 100 ml" in texte
    assert "Données incomplètes : oui (fibres)" in texte


def test_arrondi_lisible():
    assert "énergie 143.3 kcal" in fiche_texte(CAT["3302740087059"])


def test_ecriture_fiches_et_metadonnees(tmp_path):
    n = ecrire_fiches(list(CAT.values()), tmp_path)
    assert n == 22 and len(list(tmp_path.glob("*.txt"))) == 22
    meta = [json.loads(l) for l in (tmp_path / "metadonnees.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(meta) == 22 and meta[0]["id"].startswith("fiche:") and meta[0]["licence"] == "ODbL"


def test_extraction_html_garde_le_contenu_principal():
    html = ("<html><body><nav>Menu Accueil</nav><script>pister()</script>"
            "<main><h1>Le Nutri-Score</h1><p>Calculé pour 100 g.</p></main><footer>Mentions</footer></body></html>")
    texte = T.texte_html(html.encode())
    assert texte == "Le Nutri-Score\nCalculé pour 100 g.\n"


def test_seules_les_sources_autorisees_par_defaut():
    ids = {s["id"] for s in T.a_recuperer(inclure_a_verifier=False)}
    assert ids == {"viepub-ns"}
    tous = {s["id"] for s in T.a_recuperer(inclure_a_verifier=True)}
    assert "hcsp-2017" not in tous  # exclue dans tous les cas : modification interdite
