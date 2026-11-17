"""Garde-fous : filtre hors périmètre, prompt système, vérification des chiffres."""
import re

from src.assistant.catalogue import normaliser

# Motifs (sur texte normalisé) signalant un conseil médical.
_MOTIFS_MEDICAUX = [
    r"\bdiabet\w*", r"\bcholesterol\w*", r"\bhypertension\b", r"\bhypertendu\w*",
    r"\bmaladies?\b", r"\bpathologies?\b", r"\btraitements?\b", r"\bmedicaments?\b",
    r"\bordonnances?\b", r"\benceinte\b", r"\bgrossesse\b", r"\bcancer\w*",
    r"\bregimes? therapeutiques?\b", r"\bmon medecin\b", r"\binsuffisance renale\b",
    r"\binsuffisance cardiaque\b", r"\bsymptomes?\b", r"\bdiagnostic\b",
    r"\bmaladie coeliaque\b", r"\btriglycerides?\b",
]
_REGEX_MEDICAL = re.compile("|".join(_MOTIFS_MEDICAUX))

MESSAGE_REFUS = (
    "Je ne peux pas donner de conseil médical ou de santé personnalisé. "
    "Pour toute question liée à une maladie, un traitement ou une situation particulière, "
    "adressez-vous à un médecin ou à un diététicien. "
    "Je peux en revanche vous donner les valeurs nutritionnelles d'un produit du catalogue."
)


def detecter_hors_perimetre(question):
    """Renvoie un message de refus si la question est médicale, sinon None."""
    if _REGEX_MEDICAL.search(normaliser(question)):
        return MESSAGE_REFUS
    return None


PROMPT_SYSTEME = """Tu es l'assistant NutriScope, spécialisé dans les produits alimentaires.

Règles :
- Tu réponds UNIQUEMENT à partir des résultats de l'outil chercher_produit. Appelle toujours l'outil avant de citer une valeur.
- Ne jamais inventer ni estimer une valeur. Une valeur null signifie « valeur absente du catalogue » : dis-le explicitement.
- Si le statut est « ambigu » : liste les candidats (nom + code) et demande de préciser, ou choisis le plus pertinent en le disant clairement.
- Si le statut est « introuvable » : dis-le simplement.
- Refuse poliment tout ce qui sort de l'alimentation et tout conseil médical (renvoie vers un médecin ou un diététicien).
- Pour expliquer un Nutri-Score : cite les composantes défavorables (kcal, sucres, saturés, sel) et favorables (fibres, protéines) présentes dans la fiche, sans inventer de points.
- Recommandation : un bon Nutri-Score, c'est A ou B ; ne présente jamais un produit C, D ou E comme bon.
- L'outil cherche par nom et ne trie pas par Nutri-Score : tu ne peux pas parcourir le catalogue pour trouver le meilleur produit (moteur de substitution au TP 21). Tu peux citer les fiches A ou B renvoyées par une recherche, en précisant que ce n'est qu'un échantillon de cette recherche ; s'il n'y en a aucune, dis-le.
- Pour « une alternative à X », cherche le produit X lui-même (éventuellement sa catégorie), pas la phrase entière.
- Ne cite jamais deux fois le même code produit.
- Réponds en français, de façon concise, et cite les valeurs pour 100 g.
- Les données viennent d'Open Food Facts (licence ODbL).
"""

_NOMBRE = re.compile(r"\d+(?:[.,]\d+)?")


def _extraire_nombres(texte):
    return [float(m.replace(",", ".")) for m in _NOMBRE.findall(texte)]


def _nombres_source(obj):
    """Tous les nombres d'une structure (valeurs numériques et nombres dans les chaînes)."""
    if isinstance(obj, bool) or obj is None:
        return []
    if isinstance(obj, (int, float)):
        return [float(obj)]
    if isinstance(obj, str):
        return _extraire_nombres(obj)
    if isinstance(obj, dict):
        return [n for v in obj.values() for n in _nombres_source(v)]
    if isinstance(obj, (list, tuple)):
        return [n for v in obj for n in _nombres_source(v)]
    return []


# Mots-clés par nutriment (texte normalisé) ; « lipides » exclut « lipides saturés ».
_MOTS_NUTRIMENTS = {
    "satures": re.compile(r"satur|acides? gras"),
    "lipides": re.compile(r"lipides?\b(?!\s+satur)|matieres? grasses?\b(?!\s+satur)"),
    "sucres": re.compile(r"sucres?"),
    "sel": re.compile(r"\bsel\b"),
    "fibres": re.compile(r"fibres?"),
    "proteines": re.compile(r"proteines?"),
    "kcal": re.compile(r"kcal|calories?"),
}
_FENETRE = 30
_COUPURE_APRES = re.compile(r"[,;\n(]")
_COUPURE_AVANT = re.compile(r"[,;\n.]")
# numéro de liste en début de ligne (« 1. », « 2) ») : pas une valeur à vérifier
_NUMERO_LISTE = re.compile(r"^[ \t]*(\d+)[.)]\s", re.MULTILINE)


def _correspond(n, s):
    """Vrai si n égale s à 0,01 près, ou son arrondi à l'entier ou à 1 décimale."""
    return abs(n - s) <= 0.01 or n == float(round(s)) or abs(n - round(s, 1)) <= 1e-9


def _nutriment_associe(texte, debut, fin):
    """Clé du nutriment auquel se rapporte le nombre texte[debut:fin], ou None."""
    # d'abord après le nombre (« 10 g de sucres »), jusqu'à la première coupure
    apres = texte[fin:fin + _FENETRE]
    coupure = _COUPURE_APRES.search(apres)
    if coupure:
        apres = apres[:coupure.start()]
    trouves = [(m.start(), cle) for cle, rx in _MOTS_NUTRIMENTS.items() if (m := rx.search(apres))]
    if trouves:
        return min(trouves)[1]
    # sinon avant (« Sucres : 10 g »), dans le dernier segment, mot-clé le plus proche
    avant = texte[max(0, debut - _FENETRE):debut]
    coupures = list(_COUPURE_AVANT.finditer(avant))
    if coupures:
        avant = avant[coupures[-1].end():]
    trouves = [(m.start(), cle) for cle, rx in _MOTS_NUTRIMENTS.items() for m in rx.finditer(avant)]
    return max(trouves)[1] if trouves else None


def _valeurs_nutriment(resultats_outils, cle):
    """Valeurs (non None) du nutriment cle dans toutes les fiches des résultats."""
    valeurs = []
    for r in resultats_outils if isinstance(resultats_outils, (list, tuple)) else [resultats_outils]:
        produits = r.get("produits") if isinstance(r, dict) else None
        for p in produits if isinstance(produits, list) else []:
            v = p.get("nutriments", {}).get(cle) if isinstance(p, dict) else None
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                valeurs.append(float(v))
    return valeurs


def verifier_chiffres(reponse, resultats_outils):
    """Renvoie les nombres de la réponse non vérifiés par les résultats d'outil.

    Règle : on cherche le nutriment cité près du nombre (après, sinon avant). S'il
    est trouvé, le nombre doit égaler (à 0,01 près, ou arrondi à l'entier ou à 1
    décimale) la valeur de CE nutriment dans une fiche : « 10,6 g de sucres » est
    signalé si 10,6 est la valeur des saturés. Limite : sans nutriment proche, le
    nombre n'est vérifié qu'en présence (il existe quelque part dans les résultats).
    Sont ignorés : « 100 » (pour 100 g) et les numéros de liste (« 1. » en début de ligne).
    """
    sources = _nombres_source(resultats_outils)
    texte = normaliser(reponse or "")  # mêmes positions, chiffres inchangés
    numeros_liste = {l.start(1) for l in _NUMERO_LISTE.finditer(texte)}
    inconnus = []
    for m in _NOMBRE.finditer(texte):
        n = float(m.group().replace(",", "."))
        if n == 100 or m.start() in numeros_liste:
            continue
        cle = _nutriment_associe(texte, m.start(), m.end())
        candidats = _valeurs_nutriment(resultats_outils, cle) if cle else sources
        if not any(_correspond(n, s) for s in candidats):
            inconnus.append(m.group())
    return inconnus
