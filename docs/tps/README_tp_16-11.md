# **TP fil rouge — L'assistant face à ce qu'il ne sait pas (lundi 16/11, journée)**

Votre assistant NutriScope sait chercher une fiche dans le catalogue (TP 18) et lire une étiquette photographiée (atelier du 12/11). Il répond juste tant que la réponse se trouve dans une fiche. Mais un utilisateur ne pose pas que des questions de fiche : « combien de fruits et légumes par jour ? », « pourquoi ce produit a-t-il pris un D ? », « la charcuterie, c'est combien par semaine ? ». Ces réponses ne sont dans aucune fiche du catalogue.

Aujourd'hui, vous ne construisez pas encore de RAG : il se construit mardi et mercredi (module 6.3). Aujourd'hui, vous préparez le terrain en quatre temps :

1. vous terminez l'assistant tel qu'il est ;
2. vous **mesurez** ce qu'il fait quand la réponse n'est pas dans le catalogue ;
3. vous rassemblez le **corpus** dans lequel le RAG ira chercher ;
4. vous écrivez le **jeu d'évaluation** qui servira jeudi à prouver que le RAG améliore réellement les réponses.

Le fil de la semaine : **mesurer lundi, construire mardi et mercredi, remesurer jeudi sur les mêmes questions.**

**Cours à mobiliser** (rien n'y est refait ici) :

- `001_llm_fondamentaux.ipynb` : le client unique local / API, la température.
- `002_llm_echelle_embeddings_outils.ipynb`, section 3 : l'appel d'outils et sa boucle.
- `004_hallucinations_garde_fous_outils.ipynb`, section 1 : mesurer les hallucinations sur des questions à vérité connue.
- TP 18 (`README_tp_18.md`) : le contrat `chercher_produit` et la règle « chaque chiffre de la réponse se retrouve dans le résultat de l'outil ».
- Atelier scanner (12/11) : `outils/mesurer_scanner.py` et la logique « améliorer, mesurer, comparer ».

## **Ce que vous faites aujourd'hui, en bref**

| Horaire | Bloc | Ce qui doit exister à la fin |
|---|---|---|
| 8h30 – 9h00 | Accueil et quiz de réactivation | — |
| 9h00 – 9h45 | État des lieux : 5 min par équipe | — |
| 9h45 – 12h30 | **Bloc 1** — Finir l'atelier scanner | contrat au vert, scanner branché, `docs/mesures_scanner.md` |
| 13h30 – 14h30 | **Bloc 2** — Mesurer ce que l'assistant ne sait pas | `resultats/bloc2_sans_rag.csv` |
| 14h30 – 15h45 | **Bloc 3** — Constituer le corpus | `docs/ia/corpus.md`, script des fiches, textes du corpus |
| 16h00 – 17h00 | **Bloc 4** — Écrire le jeu d'évaluation | `eval/questions.csv`, `resultats/eval_sans_rag.csv` |
| 17h00 – 17h30 | Tour de table, commit, journal | commit fonctionnel |

Pauses vers 10h45 et 15h45, déjeuner vers 12h30.

## **État des lieux (9h00 – 9h45)**

Chaque équipe montre, en 5 minutes, sur son poste :

1. `python outils/mesurer_scanner.py --historique` : les versions mesurées jeudi, et le palier atteint ;
2. la démonstration du TP 18 : une question produit, l'appel `chercher_produit` visible, la réponse ;
3. `docs/adr/0001-…` et `docs/architecture.md` : existent-ils, sont-ils à jour ?

On montre ce qui tourne, pas des slides.

## **Bloc 1 — Finir l'atelier scanner (9h45 – 12h30)**

Reprenez le sujet de l'atelier du 12/11 là où vous l'avez laissé. Rien de nouveau : le contrat, les outils de mesure et les paliers sont inchangés.

**Le noyau, dans cet ordre :**

1. `pytest outils` passe.
2. Palier 3 — l'aiguillage : `verifie` / `non_verifie` / `illisible` justes, aucune étiquette rattachée à la mauvaise fiche.
3. Palier 6 — le scanner est branché sur l'assistant, démonstration exécutée sur trois photos (une vérifiée, une non vérifiée, la photo sans tableau).
4. Une mesure par palier franchi, et `docs/mesures_scanner.md` à jour.

**Ensuite, si le noyau est fait :** palier 5 (rédacteur et relecteur), puis palier 4 (vote), puis un bonus de l'atelier.

Une équipe en retard livre un palier qui marche, plutôt que trois à moitié faits.

## **Bloc 2 — Mesurer ce que l'assistant ne sait pas (13h30 – 14h30)**

Le formateur vous remet `bloc2_questions_verite.csv` : 10 questions de nutrition générale, avec leur réponse vérifiée et la source officielle de cette réponse. Aucune ne se trouve dans une fiche produit.

**Protocole :**

1. Prenez votre assistant **tel quel** : même modèle, même prompt système, mêmes outils. Ne le modifiez pas avant la mesure.
2. Posez les 10 questions, une par conversation (pas de mémoire d'une question à l'autre), température 0.
3. Pour chaque réponse, notez : la réponse, les outils appelés et leurs arguments, la latence.
4. Classez chaque réponse dans **une** case :

| Verdict | Définition | Conforme au contrat du TP 18 ? |
|---|---|---|
| `refus_correct` | l'assistant dit qu'il ne peut pas répondre avec ses sources | oui |
| `juste_non_source` | la réponse est juste, mais aucun résultat d'outil ne la contient | **non** |
| `invente` | la réponse contient une information fausse ou un chiffre faux | non |
| `outil_detourne` | l'assistant appelle `chercher_produit` avec un argument absurde (« Nutri-Score », « PNNS ») et conclut quelque chose du résultat | non |

5. Enregistrez le tout dans `resultats/bloc2_sans_rag.csv` (colonnes : `id`, `reponse`, `outils_appeles`, `verdict`, `latence_s`).
6. Écrivez trois lignes dans `docs/ia/besoin_rag.md` : combien de réponses conformes sur 10, ce qui vous a surpris, ce que le RAG devra changer.

**Le point qui compte.** Une réponse juste mais non sourcée n'est pas un succès. Le modèle a répondu de mémoire : il aurait pu se tromper, et rien dans votre code ne permet de le vérifier. Le contrat du TP 18 l'interdit pour les fiches produits ; le RAG l'interdira pour le reste.

La vérité terrain sert **à mesurer**, jamais à aider le modèle. Ne la mettez dans aucun prompt.

## **Bloc 3 — Constituer le corpus (14h30 – 15h45)**

Mardi, le RAG ira chercher dans ce corpus. Aujourd'hui, on le rassemble, on le documente et on en extrait le texte. On ne découpe pas et on ne vectorise pas (c'est mardi).

**Deux familles de documents :**

**1. Les fiches produits**, générées depuis votre catalogue. Écrivez `src/corpus/fiches.py` : une fonction qui transforme chaque produit en un texte court et lisible, et un script qui écrit un fichier par produit dans `data/corpus/fiches/<code>.txt`, plus un fichier `data/corpus/fiches/metadonnees.jsonl` (une ligne JSON par produit : `code`, `nom`, `marque`, `rayon`, `nutriscore`, `source`).

Gabarit de fiche (adaptez les champs à votre catalogue) :

```
Produit : {nom} — {marque}
Code-barres : {code}
Rayon : {rayon}
Nutri-Score : {nutriscore}
Valeurs pour 100 g : énergie {kcal} kcal ; matières grasses {lipides} g, dont saturées {satures} g ; sucres {sucres} g ; sel {sel} g ; fibres {fibres} g ; protéines {proteines} g
Données incomplètes : {oui/non, et lesquelles}
Source : Open Food Facts (licence ODbL), export du {date}
```

Règle héritée du TP 18 : une valeur inconnue s'écrit « non renseigné », **jamais 0**.

**2. Les documents de référence en nutrition.** Le formateur vous donne la liste des sources autorisées, avec leur licence. Pour chaque document retenu :

- téléchargez-le avec un script versionné (`src/corpus/telecharger.py`) ou notez la manipulation exacte dans `docs/ia/corpus.md` ;
- extrayez son texte en `.txt` dans `data/corpus/documents/` (`pypdf` pour un PDF, le texte principal pour une page web) ;
- **remplissez sa ligne dans `docs/ia/corpus.md`** :

| id | titre | éditeur | URL | mis à jour le | consulté le | licence et conditions | utilisé pour |
|---|---|---|---|---|---|---|---|

Une source dont la licence n'est pas établie n'entre pas dans le corpus. Une source qui interdit la modification (« diffusé dans sa totalité, sans ajout ni modification ») ne peut pas être découpée en morceaux : elle reste un lien, pas un document du corpus.

Le dossier `data/corpus/` reste **hors du dépôt** (`.gitignore`) ; seuls les scripts et `docs/ia/corpus.md` sont versionnés.

## **Bloc 4 — Écrire le jeu d'évaluation (16h00 – 17h00)**

C'est le TP 20 de jeudi, écrit **avant** le RAG. Si vous écrivez les questions après avoir construit le RAG, vous écrirez sans le vouloir des questions auxquelles il sait répondre.

**Écrivez 30 questions** dans `eval/questions.csv` (modèle fourni : `eval_questions_modele.csv`), réparties ainsi :

| Type | Nombre | Exemple |
|---|---|---|
| `produit` | 8 | « Quel est le Nutri-Score du produit 3017620422003 ? » |
| `comparaison` | 6 | « Entre ces deux céréales, laquelle contient le moins de sucres ? » |
| `connaissance` | 8 | « Combien de fois par semaine faut-il manger des légumes secs ? » |
| `mixte` | 3 | une question qui demande une fiche **et** un repère du corpus |
| `piege` | 5 | produit inexistant, conseil médical, hors alimentation, instruction cachée dans la question |

**Pour chaque question :** la réponse attendue, la ou les sources attendues (un `code` de fiche ou un `id` de document de `docs/ia/corpus.md`), et le comportement attendu (`repondre`, `refuser`, `dire_introuvable`).

**Les règles du jeu d'évaluation :**

- Chaque réponse attendue est vérifiée **à la main** dans sa source. Pas de réponse attendue écrite de mémoire, et pas de réponse attendue écrite par un LLM.
- Échangez 5 questions avec l'équipe voisine : elle vérifie vos réponses attendues, vous vérifiez les siennes.
- Une fois mesuré, le jeu ne change plus. Une question à corriger devient une nouvelle question, avec un nouvel `id`.

**Puis mesurez tout de suite** : passez les 30 questions sur l'assistant actuel, sans RAG, et rangez le résultat dans `resultats/eval_sans_rag.csv` (colonnes : `id`, `reponse`, `outils_appeles`, `verdict`, `latence_s`). C'est votre **référence**. Jeudi, le même jeu passera sur l'assistant avec RAG.

## **Tour de table (17h00 – 17h30)**

Chaque équipe donne deux chiffres : réponses conformes sur les 10 questions du bloc 2, réponses conformes sur les 30 questions du jeu d'évaluation. Puis commit et trois lignes dans `docs/journal.md` (fait, problème, suite).

## **À committer**

| Fichier | Contenu |
|---|---|
| `src/…` | scanner terminé et branché (bloc 1) |
| `docs/mesures_scanner.md`, `resultats/` | mesures du scanner à jour |
| `resultats/bloc2_sans_rag.csv` | les 10 réponses du bloc 2 et leur verdict |
| `docs/ia/besoin_rag.md` | trois lignes : ce que la mesure montre |
| `src/corpus/fiches.py`, `src/corpus/telecharger.py` | génération des fiches, récupération des documents |
| `docs/ia/corpus.md` | une ligne par source : URL, dates, licence, usage |
| `eval/questions.csv` | les 30 questions de référence |
| `resultats/eval_sans_rag.csv` | la mesure de référence sans RAG |
| `docs/journal.md` | trois lignes : fait, problème, suite |

## **Hors sujet aujourd'hui**

- Embeddings, découpage en morceaux, base vectorielle : mardi et mercredi (module 6.3).
- Un agent qui choisit lui-même ses étapes, l'outil de substitution, LangChain, CrewAI : modules et TP de B. Quinet (24-25/11).
- Les tests adverses et le gel des garde-fous : TP 22 (30/11).

## **Les règles**

- Mesures sur un vrai modèle uniquement, celui de votre ADR.
- La clé d'API vient d'une variable d'environnement, jamais du code ni du dépôt.
- Les vérités terrain (`bloc2_questions_verite.csv`, réponses attendues de `eval/questions.csv`) ne vont dans aucun prompt.
- Créditez Open Food Facts (ODbL) et chaque source du corpus selon sa licence.

## **Ressources**

- Recommandations alimentaires pour les adultes (PNNS) : <https://www.mangerbouger.fr>
- Nutri-Score, page officielle de Santé publique France : <https://www.santepubliquefrance.fr/determinants-de-sante/nutrition-et-activite-physique/articles/nutri-score>
- Ce qu'il faut savoir sur le nouveau Nutri-Score (Santé.fr) : <https://www.sante.fr/ce-quil-faut-savoir-sur-le-nouveau-nutri-score>
- Le Nutri-Score en cinq questions (Vie publique) : <https://www.vie-publique.fr/questions-reponses/286134-le-nutri-score-en-cinq-questions>
- Table de composition Ciqual (Anses) : <https://ciqual.anses.fr/>
- Open Food Facts, conditions d'utilisation : <https://world.openfoodfacts.org/terms-of-use>
- pypdf, extraction de texte : <https://pypdf.readthedocs.io/>
