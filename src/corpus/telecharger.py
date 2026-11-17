"""Télécharge les documents de référence du corpus et en extrait le texte.

Usage : python -m src.corpus.telecharger

pnns_adultes : la page n'est qu'un sommaire, le détail est dans ses sous-pages (une par
repère), téléchargées aussi et concaténées dans le même .txt.
nutriscore_viepublique : le site répond par un défi JavaScript (cookie de redirection) que
urllib ne passe pas ; le texte a été enregistré à la main depuis le navigateur
(contenu de l'article, sans le menu ni les liens « en ce moment »).
Les licences de chaque source sont décrites dans docs/ia/corpus.md.
"""
import io
import re
import urllib.request
from html.parser import HTMLParser

from src.assistant.catalogue import RACINE

SOURCES = [
    ("pnns_adultes", "https://www.mangerbouger.fr/l-essentiel/les-recommandations-sur-l-alimentation-l-activite-physique-et-la-sedentarite"),
    ("nutriscore_spf", "https://www.santepubliquefrance.fr/determinants-de-sante/nutrition-et-activite-physique/articles/nutri-score"),
    ("nutriscore_santefr", "https://www.sante.fr/ce-quil-faut-savoir-sur-le-nouveau-nutri-score"),
    ("nutriscore_viepublique", "https://www.vie-publique.fr/questions-reponses/286134-le-nutri-score-en-cinq-questions"),
]
DOSSIER = RACINE / "data" / "corpus" / "documents"
IGNORES = {"script", "style", "noscript", "svg", "nav", "header", "footer", "form", "button", "iframe"}
BLOCS = {"p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "br", "tr", "section", "article", "ul", "ol"}


class ExtracteurHtml(HTMLParser):
    """Texte de la page ; si <main> ou <article> existe, seul son contenu est gardé."""

    def __init__(self):
        super().__init__()
        self.tout, self.principal = [], []
        self.ignore = 0
        self.dans_principal = 0

    def handle_starttag(self, tag, attrs):
        if tag in IGNORES:
            self.ignore += 1
        elif tag in ("main", "article"):
            self.dans_principal += 1
        if tag in BLOCS:
            self._ajouter("\n")

    def handle_endtag(self, tag):
        if tag in IGNORES and self.ignore:
            self.ignore -= 1
        elif tag in ("main", "article") and self.dans_principal:
            self.dans_principal -= 1
        if tag in BLOCS:
            self._ajouter("\n")

    def handle_data(self, data):
        if not self.ignore:
            self._ajouter(data)

    def _ajouter(self, texte):
        self.tout.append(texte)
        if self.dans_principal:
            self.principal.append(texte)

    def texte(self) -> str:
        brut = "".join(self.principal) if "".join(self.principal).strip() else "".join(self.tout)
        lignes = [re.sub(r"[ \t\xa0]+", " ", l).strip() for l in brut.splitlines()]
        texte = re.sub(r"\n{3,}", "\n\n", "\n".join(lignes)).strip()
        # bandeau de maintenance de mangerbouger.fr, répété sur chaque page
        return re.sub(r"Plusieurs pages de notre site.*?Merci pour votre compréhension\.\s*", "", texte, flags=re.S)


def extraire_html(octets: bytes) -> str:
    parseur = ExtracteurHtml()
    parseur.feed(octets.decode("utf-8", errors="replace"))
    return parseur.texte()


def extraire_pdf(octets: bytes) -> str:
    from pypdf import PdfReader  # import local : pypdf n'est requis que pour les PDF
    return "\n\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(octets)).pages).strip()


def telecharger(url: str) -> tuple[bytes, str]:
    requete = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (projet etudiant NutriScope)"})
    with urllib.request.urlopen(requete, timeout=30) as reponse:
        return reponse.read(), reponse.headers.get("Content-Type", "")


def sous_pages(octets: bytes, url: str) -> list[str]:
    """Liens de détail de la page de recommandations (la page principale n'est qu'un sommaire)."""
    chemin = re.escape(url.removeprefix("https://www.mangerbouger.fr"))
    liens = re.findall(rf'href="({chemin}/[^"#?]+)"', octets.decode("utf-8", errors="replace"))
    return list(dict.fromkeys("https://www.mangerbouger.fr" + l for l in liens))


def extraire(url: str, octets: bytes, type_: str) -> str:
    if "pdf" in type_.lower() or url.lower().endswith(".pdf"):
        return extraire_pdf(octets)
    return extraire_html(octets)


def main():
    DOSSIER.mkdir(parents=True, exist_ok=True)
    for id_, url in SOURCES:
        try:
            octets, type_ = telecharger(url)
            texte = extraire(url, octets, type_)
            if id_ == "pnns_adultes":
                for sous_url in sous_pages(octets, url):
                    texte += "\n\n=====\n" + extraire(sous_url, *telecharger(sous_url))
        except Exception as e:  # une source en échec ne bloque pas les autres
            print(f"{id_} : ÉCHEC ({e})")
            continue
        if not texte:  # page vide (défi JavaScript) : on n'écrase pas un texte déjà enregistré à la main
            print(f"{id_} : page vide, fichier laissé tel quel")
            continue
        (DOSSIER / f"{id_}.txt").write_text(texte, encoding="utf-8")
        print(f"{id_} : {len(texte)} caractères")


if __name__ == "__main__":
    main()
