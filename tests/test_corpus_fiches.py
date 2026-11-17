from src.corpus.fiches import fiche_en_texte


def _fiche(**nutriments):
    base = {"kcal": 500.0, "lipides": 20.0, "satures": 5.5, "sucres": 10.0,
            "sel": 0.0, "fibres": 3.0, "proteines": 7.0}
    base.update(nutriments)
    return {"code": "123", "nom": "Biscuit", "marque": "Marque", "nutriscore": "C",
            "nutriments": base, "donnees_incompletes": False}


def _ligne(texte, debut):
    return next(l for l in texte.splitlines() if l.startswith(debut))


def test_valeur_inconnue_non_renseignee():
    texte = fiche_en_texte(_fiche(fibres=None), "biscuits", "2026-01-01")
    assert "fibres non renseigné" in texte
    assert "fibres 0" not in texte
    assert _ligne(texte, "Données incomplètes") == "Données incomplètes : oui (fibres)"


def test_vrai_zero_reste_zero():
    texte = fiche_en_texte(_fiche(sel=0.0), "biscuits", "2026-01-01")
    assert "sel 0 g" in texte
    assert _ligne(texte, "Données incomplètes") == "Données incomplètes : non"


def test_rayon_absent():
    texte = fiche_en_texte(_fiche(), None, "2026-01-01")
    assert "Rayon : non renseigné" in texte
    assert "Source : Open Food Facts (licence ODbL), export du 2026-01-01" in texte
