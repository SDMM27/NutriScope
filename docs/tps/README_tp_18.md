# **TP 18 — Architecture de l'assistant (lundi 09/11, demi-journée)**

NutriScope veut un assistant conversationnel : l'utilisateur pose une question sur un produit, l'assistant répond **à partir du catalogue de l'équipe**, pas de mémoire. À vous de concevoir cet assistant et de réussir son premier appel outillé sur un vrai modèle de langage, avec ce que nous avons vu ce matin et la semaine dernière.

Aucun code n'est fourni et aucun découpage n'est imposé : l'architecture est la vôtre, et vous devrez la défendre.

**Cours à mobiliser :** `courses/llm/001_llm_fondamentaux.ipynb` (tokens, contexte, température, coût d'un appel) et `courses/llm/002_llm_echelle_embeddings_outils.ipynb`, **section 3 « L'Appel d'Outils »** (le modèle demande, votre code exécute ; la boucle complète).

## **Ce que l'assistant doit faire**

- **Répondre sur un produit** : Nutri-Score, valeurs nutritionnelles, à partir de la fiche du catalogue.
- **Comparer** deux produits.
- **Expliquer un score** : dire ce qui, dans la fiche, pèse sur le Nutri-Score d'un produit.
- **Recommander** : orienter vers une alternative plus saine (le moteur de substitution du TP 16 deviendra un outil au TP 21 ; aujourd'hui, à vous de dire ce que votre assistant sait déjà faire).

Et dans tous les cas : ne jamais inventer une valeur. Produit introuvable ou valeur absente, l'assistant le dit.

## **Ce qu'il doit refuser**

- **Le conseil médical** : pathologie, traitement, régime thérapeutique (« je suis diabétique, puis-je… »). Il refuse poliment et renvoie vers un professionnel de santé.
- **Tout ce qui sort de l'alimentation.**

Où se fait le refus, et avec quel mécanisme : c'est une décision d'architecture, à justifier.

## **Le seul contrat imposé : l'outil `chercher_produit`**

Toutes les équipes exposent au modèle un outil de ce nom, avec ces arguments et cette forme de résultat. Il servira tel quel au TP 21 (orchestration) et au TP 23 (API). Le reste (où il vit, comment il cherche, ce qui l'entoure) vous appartient.

**Arguments** (objet JSON écrit par le modèle) :

| Argument | Type | Rôle |
|---|---|---|
| `nom` | texte, facultatif | nom ou partie du nom ; casse et accents ignorés |
| `code` | texte, facultatif | code-barres exact ; **prime sur `nom`** si les deux sont donnés |
| `limite` | entier de 1 à 5, facultatif | nombre maximal de fiches renvoyées (3 par défaut) |

Au moins `nom` ou `code`. Aucun autre argument n'est accepté.

**Résultat** (ce que le modèle reçoit) :

```
{
  "statut": "ok" | "ambigu" | "introuvable",
  "total": <nombre de produits trouvés>,
  "produits": [<fiche>, ...]          au plus `limite` fiches
}
```

- `ok` : un seul produit ; `ambigu` : plusieurs (le modèle doit pouvoir faire préciser) ; `introuvable` : aucun (`total` vaut 0, `produits` est vide).
- Une **fiche** contient au moins :

```
{
  "code": <texte>,
  "nom": <texte>,
  "nutriscore": "A" à "E" (majuscule) ou null,
  "nutriments": {"kcal", "lipides", "satures", "sucres", "sel", "fibres", "proteines"} : valeur pour 100 g ou null,
  "donnees_incompletes": vrai si le Nutri-Score ou un nutriment manque
}
```

  Vous pouvez y ajouter d'autres clés (rayon, bio, marque…).
- Une valeur inconnue vaut `null`, **jamais 0**.
- Arguments invalides (JSON illisible, argument inconnu, `limite` hors bornes, ni nom ni code) : pas d'exception, mais un résultat `{"erreur": "<explication>"}` renvoyé au modèle.

## **Les données et le modèle**

- **Catalogue :** celui de votre équipe (TP 12 / TP 16), avec ses vraies valeurs Open Food Facts. La démonstration se fait dessus, sur des produits que vous choisissez.
- **Modèle :** un vrai modèle qui sait appeler des outils : `qwen3:8b` dans Ollama, comme ce matin, ou l'API retenue dans votre ADR. La clé d'une API vient d'une variable d'environnement, jamais du code ni du dépôt.
- **Équipe sans fichier de catalogue :** interrogez l'API publique Open Food Facts (lien plus bas) pour constituer un extrait réel. `data/catalogue_secours.csv` est un jeu **synthétique** (produits inventés) : il peut servir à développer hors ligne, **jamais** à la démonstration.

## **Ce qui est attendu**

1. **Une architecture conçue :** quels composants, quelles responsabilités, où passent les garde-fous, ce qui est branché aujourd'hui et ce qui viendra (RAG, substitution, API, application).
2. **Un choix de modèle et de mode d'accès argumenté :** API commerciale, API hébergée en Europe, modèle local… comparés sur le coût, la latence et la confidentialité (la qualité aussi), avec au moins une mesure faite par vous (latence d'un appel outillé, par exemple).
3. **Un prototype d'appel outillé** sur votre vrai modèle : le modèle demande `chercher_produit`, votre code vérifie la demande avant d'exécuter quoi que ce soit, renvoie le résultat, le modèle conclut. Une boucle qui ne peut pas tourner sans fin.
4. **Une démonstration** sur votre catalogue réel : au moins un produit connu, une comparaison ou une explication de score, un produit introuvable ou une valeur manquante, un refus. Chaque chiffre de la réponse doit se retrouver dans le résultat de l'outil, et vous devez pouvoir le montrer.

## **Rappel : qu'est-ce qu'une ADR ?**

Une **ADR** (*Architecture Decision Record*) est une courte fiche, une page au plus, qui trace **une** décision d'architecture : ce qui a été décidé, pourquoi, et ce qu'on accepte en échange. Elle sert à ce que l'équipe, ou celui qui reprendra le projet dans six mois, comprenne le choix sans avoir assisté à la discussion, et sache quand le remettre en cause. Une ADR ne se réécrit pas : si la décision change, on en écrit une nouvelle qui remplace l'ancienne.

Elle se range dans le dépôt, à côté du code, une fiche par décision et numérotée : ici `docs/adr/0001-modele-et-mode-d-acces.md`. Squelette des titres :

```
# ADR 0001 — <la décision, en une phrase>
Date, statut (proposée / acceptée / remplacée par …)
## Contexte        le problème et les contraintes
## Options         les solutions envisagées
## Critères        sur quoi on les compare, avec vos mesures
## Décision        l'option retenue et pourquoi
## Conséquences    positives et négatives (au moins une)
```

## **Les règles**

- Données réelles uniquement pour la démonstration ; pas de modèle simulé présenté comme un vrai.
- Tout ce que produit le modèle (nom d'outil, arguments) est une donnée non fiable : jamais exécuté sans contrôle, jamais d'`eval`.
- Pas de secret dans le dépôt.
- Créditez Open Food Facts (licence ODbL) dans vos livrables.

## **À committer**

| Fichier | Contenu |
|---|---|
| `src/…` (organisation libre) | le prototype, avec les tests que vous jugez utiles |
| `notebooks/tp18_demo.ipynb` (ou un script et sa sortie) | la démonstration **exécutée** : nom du modèle, questions, réponses, appels d'outil et résultats visibles |
| `docs/adr/0001-modele-et-mode-d-acces.md` | l'ADR : contexte, options, critères, décision, conséquences (dont au moins une négative) |
| `docs/architecture.md` | le schéma (Mermaid) et quelques lignes : rôle de chaque composant, branché / à venir |
| `docs/journal.md` | trois lignes : fait, problème, suite |

Critères : `grille_evaluation_tp18.md`.

## **Ressources**

- Ollama, appel d'outils : <https://docs.ollama.com/capabilities/tool-calling>
- OpenAI, *function calling* (même format côté client) : <https://platform.openai.com/docs/guides/function-calling>
- Les ADR (modèles de rédaction, dont celui de Michael Nygard) : <https://adr.github.io/>
- Mermaid, diagrammes de flux : <https://mermaid.js.org/syntax/flowchart.html>
- API Open Food Facts : <https://openfoodfacts.github.io/openfoodfacts-server/api/>
