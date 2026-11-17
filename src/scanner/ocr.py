"""Reconstruit des lignes à partir des mots et de leur géométrie Windows OCR.

Pas de valeurs catalogue ici. Seule correction de caractères : O -> 0 dans
la base explicite « 1 OO g/ml ». Les nombres nutritionnels ne sont pas réparés.
"""
import re
from statistics import median


class TexteOCR(str):
    def __new__(cls, texte, metadata):
        obj = super().__new__(cls, texte)
        obj.metadata = metadata
        return obj


def reconstruire_texte(document):
    mots = [m for ligne in document["lignes"] for m in ligne["mots"]
            if any(c.isalnum() for c in m["texte"])]
    groupes = []
    for mot in sorted(mots, key=lambda m: (m["y"] + m["hauteur"] / 2, m["x"])):
        centre = mot["y"] + mot["hauteur"] / 2
        candidats = []
        for groupe in groupes:
            hauteur = median(m["hauteur"] for m in groupe)
            milieu = median(m["y"] + m["hauteur"] / 2 for m in groupe)
            distance = abs(centre - milieu)
            if distance <= 0.6 * min(hauteur, mot["hauteur"]):
                candidats.append((distance, groupe))
        if candidats:
            min(candidats, key=lambda c: c[0])[1].append(mot)
        else:
            groupes.append([mot])
    groupes.sort(key=lambda g: median(m["y"] + m["hauteur"] / 2 for m in g))
    lignes = [" ".join(m["texte"] for m in sorted(g, key=lambda m: m["x"])) for g in groupes]
    texte_brut = "\n".join(lignes)
    corrections = []

    def base(match):
        avant = match.group()
        apres = "100 " + match.group(1).lower()
        if avant != apres:
            corrections.append({"avant": avant, "apres": apres, "regle": "base_100_ocr_O_zero"})
        return apres

    # Cette correction ne s'applique ni aux valeurs, ni aux codes-barres.
    motif = r"\b1\s*[0Oo]\s*[0Oo]\s*(g|ml)\b"
    texte = "\n".join(
        re.sub(motif, base, ligne) if (
            re.search(r"\b(?:pour|par|por|per)\b", ligne, re.I)
            or re.fullmatch(motif + r"[:.]?", ligne.strip())
        ) else ligne for ligne in lignes
    )
    return TexteOCR(texte, {**document, "texte_avant_normalisation": texte_brut,
                           "corrections": corrections, "reconstruction": "lignes-geometriques-v1"})
