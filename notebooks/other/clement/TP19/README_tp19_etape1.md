# TP 19 · étape 1 — indexer vos fiches, chercher, mesurer

Module 6.3 RAG · DEV IA 01 · mercredi 18/11, 13h30 – 17h30

**Objectif :** à 17h30, toutes vos fiches sont dans Chroma, derrière `rechercher(question, k)`, et vous savez combien de vos questions trouvent la bonne fiche dans le top 5.

Le TP 19 se fait en trois étapes, une par demi-journée : **indexer les fiches** (aujourd'hui), découper et indexer les documents (jeudi matin), répondre avec des sources (jeudi fin de matinée).

## L'après-midi

| Horaire | Quoi | Ce que vous produisez |
|---|---|---|
| 13h30 – 14h10 | Cours : bases vectorielles, Chroma | — |
| 14h10 – 14h40 | Installation, vérification | `verifier_rag.py` : six lignes `[OK]` |
| 14h40 – 16h45 | TP : TODO 1 à 5 (pause 15h30 – 15h45) | tests au vert, collection `fiches` complète |
| 16h45 – 17h15 | Mesure | `resultats/retrieval_fiches.csv` |
| 17h15 – 17h30 | Tour de table, commit | un chiffre, un échec expliqué |

## 1. Installer le kit (14h10)

À la racine de votre dépôt :

```bash
unzip -n kit_tp19_etape1.zip      # -n : n'écrase aucun fichier existant
pip install chromadb==1.5.9 pytest
python verifier_rag.py
```

Ajoutez `chromadb==1.5.9` à `requirements.txt` et `data/index*/` à `.gitignore`. **Les six lignes doivent être `[OK]` avant de coder.**

## 2. Ce que contient le kit

| Fichier | État | Rôle |
|---|---|---|
| `src/rag/embeddings.py` | fourni | `embed_documents(textes)`, `embed_question(question)` : même modèle des deux côtés |
| `src/rag/indexer.py` | **TODO 1 et 2** | lit vos fiches et les range dans Chroma, relançable sans doublons |
| `src/rag/recherche.py` | **TODO 3 à 5** | `rechercher(question, k=5, filtres=None)`, le contrat en tête du fichier |
| `src/eval/retrieval.py` | fourni | la mesure de 16h45 |
| `tests/test_rag.py` | fourni | huit tests : ils passent au vert quand vos TODO sont écrits |
| `verifier_rag.py` | fourni | les six contrôles de l'installation |

Chaque TODO lève `NotImplementedError` tant qu'il n'est pas écrit. Les consignes sont dans le code, juste au-dessus.

## 3. Les TODO, dans l'ordre (14h40 – 16h45)

**TODO 1 — `metadonnees_de()`.** Les six métadonnées d'une fiche : `code`, `nom`, `marque`, `rayon`, `nutriscore`, `source`. Une valeur absente ou vide devient `None` : jamais 0, jamais chaîne vide (la règle du TP 18).

**TODO 2 — `indexer()`.** Une boucle sur les lots, un appel à Chroma par lot. Relancer l'indexation ne doit créer aucun doublon, et une fiche corrigée doit remplacer l'ancienne : lisez la différence entre `add()` et `upsert()` dans la documentation de Chroma.

```bash
python -m pytest tests/test_rag.py -v -k "todo1 or todo2"
python -m src.rag.indexer           # puis relancez-le : le compte ne doit pas bouger
```

**TODO 3 à 5 — `rechercher()`.** Vectoriser la question (avec la consigne `Instruct:`, comme ce matin), interroger la collection, rendre la liste du contrat avec `score = 1 − distance`.

```bash
python -m pytest tests/test_rag.py -v
python -m src.rag.recherche "Une pâte à tartiner moins sucrée"
python -m src.rag.recherche "Une boisson sans sucres" --rayon Boissons
```

### Le contrat de `rechercher()`

- Au plus `k` résultats, du plus proche au moins proche.
- Chaque résultat : `{"id": "fiche:<code>", "score": ..., "texte": ..., "metadonnees": {...}}`.
- `id` a le format de `sources_attendues` dans `eval/questions.csv`.
- `score` = 1 − distance cosinus : plus haut = plus proche.
- Une valeur inconnue : la clé est absente. Jamais 0, jamais chaîne vide.
- Aucune génération : des extraits, pas une réponse. Le 25/11, l'outil `repondre_source` appellera cette fonction telle quelle.

## 4. Mesure — la bonne fiche est-elle dans le top 5 ? (16h45)

La mesure ne se coupe pas. Le script est fourni :

```bash
python -m src.eval.retrieval
```

Il pose vos questions `produit` et `comparaison` de `eval/questions.csv` à `rechercher()` et écrit `resultats/retrieval_fiches.csv` (colonnes `id;type;attendus;trouves;rang;hit`).

- `hit` = 1 si **toutes** les fiches attendues sont dans les 5 premiers résultats.
- `rang` = position de la première fiche attendue trouvée : il servira au MRR jeudi.

Lisez vos échecs et classez-les par forme de question : code-barres seul, nom du produit, marque, comparaison. Confrontez-les à votre prédiction de mardi.

## 5. Si ça bloque

| Situation | Repli |
|---|---|
| Pas de fiches générées | le formateur vous donne `src/corpus/fiches.py` : 5 minutes pour générer |
| Chroma ne s'installe pas | votre index NumPy de ce matin, derrière la même fonction `rechercher()` : demandez `index_numpy.py` au formateur |
| L'indexation complète est trop lente | `python -m src.rag.indexer --limite 500` : les fiches citées dans `eval/questions.csv` + 500 tirées au hasard. Score flatteur, index complet ce soir |
| Ollama ne tourne pas sur votre poste | le poste du formateur sert le modèle d'embeddings ; jamais un autre modèle |
| `TypeError: ... MetadataValue` à l'indexation | `add()` refuse les valeurs `None` ; relisez le TODO 2 |

## 6. À committer (17h30)

| Fichier | Contenu |
|---|---|
| `src/rag/`, `src/eval/retrieval.py`, `tests/` | le kit complété, tests au vert |
| `requirements.txt`, `.gitignore` | `chromadb==1.5.9` ; `data/index*/` |
| `resultats/retrieval_fiches.csv` | la mesure |
| `docs/journal.md` | trois lignes (fait, problème, suite) et votre hit@5 |
| `docs/adr/0002-base-vectorielle.md` | **ce soir, 5 lignes** : contexte, options (Chroma, Qdrant, FAISS), décision, ce que le choix vous fait perdre |

## Demain

Jeudi matin : découper les documents et les indexer dans la même collection, puis `repondre_source()`, une réponse qui cite ses sources. Jeudi après-midi : les 30 questions, hit rate et MRR, une amélioration mesurée.
