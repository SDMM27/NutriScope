"""Bloc 3 — famille 2 : récupérer les documents de référence et en extraire le texte.

Usage :
  python -m src.corpus.telecharger                       # sources au statut « autorise » seulement
  python -m src.corpus.telecharger --inclure-a-verifier  # après lecture des mentions légales par l'équipe

Écrit data/corpus/documents/<id>.txt (texte extrait) et data/corpus/documents/manifeste.jsonl
(id, url, date, empreinte sha256, taille). Les fichiers restent hors du dépôt ; ce script est versionné.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
from pathlib import Path
from typing import Any

# Une ligne par source, recopiée de docs/ia/corpus.md. Le statut décide de ce qui entre dans le corpus.
SOURCES: list[dict[str, Any]] = [
    {
        "id": "viepub-ns",
        "titre": "Le Nutri-Score en cinq questions",
        "editeur": "Vie publique (DILA)",
        "url": "https://www.vie-publique.fr/questions-reponses/286134-le-nutri-score-en-cinq-questions",
        "licence": "Licence Ouverte 2.0 — citer Vie publique et la date, ne pas modifier le contenu",
        "statut": "autorise",
    },
    {
        "id": "santefr-ns",
        "titre": "Ce qu'il faut savoir sur le nouveau Nutri-Score",
        "editeur": "Santé.fr",
        "url": "https://www.sante.fr/ce-quil-faut-savoir-sur-le-nouveau-nutri-score",
        "licence": "conditions de réutilisation à lire dans les CGU de Santé.fr",
        "statut": "a_verifier",
    },
    {
        "id": "spf-ns",
        "titre": "Nutri-Score",
        "editeur": "Santé publique France",
        "url": "https://www.santepubliquefrance.fr/determinants-de-sante/nutrition-et-activite-physique/articles/nutri-score",
        "licence": "mentions légales de santepubliquefrance.fr à lire",
        "statut": "a_verifier",
    },
    {
        "id": "pnns-adultes",
        "titre": "Recommandations relatives à l'alimentation, à l'activité physique et à la sédentarité pour les adultes",
        "editeur": "Santé publique France",
        "url": "https://santepubliquefrance.fr/content/download/197811/2365735",
        "licence": "mentions légales de santepubliquefrance.fr à lire",
        "statut": "a_verifier",
    },
    {
        "id": "hcsp-2017",
        "titre": "Avis relatif à la révision des repères alimentaires pour les adultes",
        "editeur": "Haut Conseil de la santé publique",
        "url": "https://www.hcsp.fr/",
        "licence": "« diffusé dans sa totalité, sans ajout ni modification »",
        "statut": "exclu",  # interdit le découpage : lien seulement, jamais dans le corpus
    },
]

DOSSIER = Path("data/corpus/documents")


def texte_html(octets: bytes) -> str:
    """Texte principal d'une page : <main> ou <article> s'ils existent, sans menus ni scripts."""
    from bs4 import BeautifulSoup

    soupe = BeautifulSoup(octets, "html.parser")
    for balise in soupe(["script", "style", "nav", "header", "footer", "aside", "form", "noscript"]):
        balise.decompose()
    zone = soupe.find("main") or soupe.find("article") or soupe.body or soupe
    lignes = (ligne.strip() for ligne in zone.get_text("\n").splitlines())
    return "\n".join(ligne for ligne in lignes if ligne) + "\n"


def texte_pdf(octets: bytes) -> str:
    from pypdf import PdfReader

    lecteur = PdfReader(io.BytesIO(octets))
    pages = [(page.extract_text() or "").strip() for page in lecteur.pages]
    return "\n\n".join(p for p in pages if p) + "\n"


def extraire_texte(octets: bytes, type_contenu: str) -> str:
    if "pdf" in type_contenu.lower() or octets[:5] == b"%PDF-":
        return texte_pdf(octets)
    return texte_html(octets)


def telecharger(source: dict[str, Any], dossier: Path = DOSSIER) -> dict[str, Any]:
    import requests

    reponse = requests.get(source["url"], timeout=60, headers={"User-Agent": "NutriScope-formation/1.0"})
    reponse.raise_for_status()
    octets = reponse.content
    texte = extraire_texte(octets, reponse.headers.get("Content-Type", ""))
    entete = (f"Source : {source['titre']} — {source['editeur']}\nURL : {source['url']}\n"
              f"Licence : {source['licence']}\nConsulté le : {dt.date.today().isoformat()}\n\n")
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / f"{source['id']}.txt").write_text(entete + texte, encoding="utf-8")
    return {
        "id": source["id"], "url": source["url"], "licence": source["licence"],
        "consulte_le": dt.date.today().isoformat(), "octets": len(octets),
        "sha256": hashlib.sha256(octets).hexdigest(), "caracteres_texte": len(texte),
    }


def a_recuperer(inclure_a_verifier: bool) -> list[dict[str, Any]]:
    statuts = {"autorise", "a_verifier"} if inclure_a_verifier else {"autorise"}
    return [s for s in SOURCES if s["statut"] in statuts]


def main() -> None:
    parser = argparse.ArgumentParser(description="Récupère les documents du corpus et extrait leur texte.")
    parser.add_argument("--inclure-a-verifier", action="store_true",
                        help="inclure les sources dont l'équipe a lu et accepté les mentions légales")
    parser.add_argument("--sortie", default=str(DOSSIER))
    args = parser.parse_args()
    dossier = Path(args.sortie)
    with open(_manifeste(dossier), "a", encoding="utf-8") as m:
        for source in a_recuperer(args.inclure_a_verifier):
            try:
                ligne = telecharger(source, dossier)
                m.write(json.dumps(ligne, ensure_ascii=False) + "\n")
                print(f"ok   {source['id']:<14} {ligne['caracteres_texte']:>7} caractères")
            except Exception as e:  # une source en panne ne bloque pas les autres
                print(f"ÉCHEC {source['id']:<13} {type(e).__name__}: {e}")
    for source in SOURCES:
        if source["statut"] == "exclu":
            print(f"exclu {source['id']:<13} {source['licence']}")


def _manifeste(dossier: Path) -> Path:
    dossier.mkdir(parents=True, exist_ok=True)
    return dossier / "manifeste.jsonl"


if __name__ == "__main__":
    main()
