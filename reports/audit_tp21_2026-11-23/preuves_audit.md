# Preuves d’audit

## Références institutionnelles et Git

| Source | Observation | Portée |
|---|---|---|
| `docs/Cahier_TP_NutriScope.md:151–166,187–929` | Version v1 au 28/07, 31 TP et 7 jalons. Markdown `c1bef2b`, PDF `417428b` dans l’historique | Grille, échéances, livrables |
| `CONTRIBUTING.md` et `AGENTS.md` équipe au commit `baa60fc` | Règles de relecture et branches. AGENTS distant vide, absent sur checkout | TP3 |
| `git status --short --branch`, `git branch -avv --no-abbrev`, `git remote -v`, `git tag -n` | Checkout `23a21ff`, fork synchronisé, upstream local `5f212cd`, aucun tag local, aucun changement initial | Base de comparaison |
| `gh api repos/{owner}/NutriScope/{branches,pulls,issues,tags}` avec page 100 | Main équipe signalée non protégée. 5 branches équipe, 7 fork, équipe #65/#70/#71 ouvertes, #69/#72 fusionnées, aucun tag | TP3, 4, 8, 13, 14, 17–22 |
| `gh api repos/SDMM27/NutriScope/compare/5f212cd...baa60fc` | Équipe 12 commits en avance sur la référence locale | Écart remote/local |
| `gh api repos/{owner}/NutriScope/git/trees/{sha}?recursive=1` | `baa60fc`, `d35e6b0`, `167d785`, `8bd221a` inspectés par nom de fichier ; lecture ciblée de fichiers via connecteur | Absences bornées, détection des travaux distants |
| `git ls-tree -r --name-only`, `git grep`, `git log --all` | Branches locales, historiques, scanner local `59abadf`, fichiers absents ou secondaires | TP13–31 |

## Preuves techniques sélectionnées

| TP | Emplacement | Observation |
|---|---|---|
| 1–2 | `notebooks/tp1_load_and_display_food_data.ipynb`, `notebooks/tp2_profiling.ipynb`, `docs/cadrage/perimetre.md:138–199` | Profil et décisions vérifiables, restitutions hors dépôt |
| 3–4 | `sql/schema.sql`, `sql/controles.sql`, `src/load_database.py:51–68`, `src/database/cleanup.py:25–42` | DDL, SQL de contrôle et rechargement. TRUNCATE validé séparément des insertions |
| 5–8 | `docs/cadrage/parties_prenantes.md:120–169`, `personas.md`, `benchmark.md`, `kpi_roi.xlsx`, `note_hypotheses.md:5–24`, GitHub #30–32 | CR, persona modifié, benchmark, classeur inspecté en XML, état des issues. Finalisation du cadrage non démontrée |
| 9–10 | `docs/journal.md:326–413,435–438`, `src/cleaning.py`, `tests/test_cleaning.py`, `notebooks/eda_reference.ipynb` | [PR TP9 finale](https://github.com/SDMM27/NutriScope/pull/55), [PR TP10](https://github.com/SDMM27/NutriScope/pull/56). EDA de référence sur échantillon, 8 689 → 8 400 |
| 11–13 | `src/viz.py`, `docs/NutriScope_TP11_Etat_du_marche.pptx`, `docs/tps/tp-12-parquet-et-duckdb.md:48–137`, `src/storage/export_features.py` | Sept slides, SQLite autorisé au benchmark TP12, split intégré. [Issue TP13](https://github.com/SDMM27/NutriScope/issues/67) et [branche du notebook](https://github.com/clement-welsch/NutriScope/tree/8bd221a3e70dbd4d9345d6d27f7fb7f33ab6acfb) |
| 14–16 | `tests/test_ml_nutriscore.py` à `9320531`, cahier 503–573, `docs/tps/tp16_segmentation_substitution.ipynb:559,760–837` | Test préparatoire TP14, clustering et substitution à implémenter. [PR #65](https://github.com/SDMM27/NutriScope/pull/65) |
| 17 | `models/evaluation_images_test.json`, `docs/ml/tp17_execution.md`, `docs/ml/limites_images.md` à `167d785` | 428/525 correctes, 373/525 acceptées au seuil 0,80, 349/373 correctes parmi acceptées. Le résultat historique est attribué à la branche et aux artefacts. [Rapport d’exécution](https://github.com/SDMM27/NutriScope/blob/167d785/docs/ml/tp17_execution.md) |
| 18 | `notebooks/other/clement/tp18_1_architecture_assistant_guide.ipynb`, `docs/assistant_architecture.md` dans #70, `src/assistant/catalogue.py:34` et `src/assistant/outils.py:89` à `f5960b7` | Preuve historique notebook sur le catalogue, ADR équipe en PR, adaptateur CSV atelier et test réel mono-tour. [PR #69](https://github.com/SDMM27/NutriScope/pull/69), [PR #70](https://github.com/SDMM27/NutriScope/pull/70) |
| 19 | `src/rag/indexer.py:35,106`, `src/rag/recherche.py:42`, `docs/ia/corpus.md`, `notebooks/other/clement/TP19/README_tp19_etape1.md:109` à `f5960b7` | Recherche d’extraits, documents à découper, registre des licences, génération citée à venir. [PR #71](https://github.com/SDMM27/NutriScope/pull/71) |
| 20 | `eval/questions.csv`, `resultats/retrieval_fiches.csv`, `src/eval/` à `f5960b7` | 8 questions produits, 6 comparaisons, 8 connaissances, 3 mixtes, 5 pièges. Les fiches attendues des 14 cas produits/comparaisons sont retrouvées dans le top 5 enregistré. Portée limitée au lot atelier de 22 fiches |
| 21–22 | Cahier 669–707, `src/assistant/assistant.py:72–81` à `f5960b7` | Nouvelle conversation par appel sur #71, aucun LangChain en source dans les arbres consultés. Réutilisation possible de l’historique annoncé sur #70 |
| 23–31 | Cahier 711–929, arbres Git, README et tags | Aucun parcours applicatif de l’API au déploiement confirmé. Pas de preuve pédagogique pour les séances futures hors dépôt |

## Rejeu des tests

Environnement commun : Windows, Python Codex 3.12.14 AMD64, modules du `.venv/Lib/site-packages` local sur PYTHONPATH, pytest 9.1.1, Matplotlib 3.11.1, DuckDB 1.5.5. Le lanceur `.venv/Scripts/python.exe -V` échoue, sa cible Python a disparu. Pas d’installation. Écriture des fixtures dans des dossiers TEMP distincts.

- **Develop, TP4/9/10/11/12/13.** `python -B -m pytest -ra --tb=short -p no:cacheprovider --basetemp <temp-neuf> tests` avec autoload de plugins désactivé et moteur Agg. 137 succès, zéro échec et zéro sauté en 12,81 s. Par module : benchmark 5, nettoyage 42, EDA 28, ETL 2, rapport 6, stockage 17, contrôles 4, viz 33. Premier essai sans dossier temporaire dédié : 110 succès et 27 erreurs de préparation WinError 5.
- **Archive f5960b7, TP18/19/20.** `python -B -m pytest -q -p no:cacheprovider --tb=short --basetemp <temp-neuf> tests/test_assistant.py tests/test_corpus.py tests/test_evaluation.py tests/test_outils.py tests/test_rag.py`, Chroma 1.5.9, catalogue local via NUTRISCOPE_CATALOGUE, télémétrie désactivée. 42 succès et 1 échec en 4,38 s ; contrôle indépendant même bilan en 3,94 s. `tests/test_rag.py:83::test_todo2_une_valeur_devenue_inconnue_disparait_de_l_index` : l’upsert conserve l’ancienne valeur A lorsqu’une clé de métadonnée est omise. Des essais précédents ont rencontré l’absence du CSV dans l’archive et l’ACL du dossier pytest par défaut, corrigées pour les deux relevés.
- **Archive 9320531, TP14.** `python -B -m pytest -q -p no:cacheprovider --tb=short tests/test_ml_nutriscore.py` : module `src.ml_nutriscore` absent, 1 erreur de collecte en 0,90 s, 0 test exécuté.
- **TP19 réel technique.** `python -B verifier_rag.py`, serveur Ollama loopback, qwen3-embedding:0.6b, Chroma temporaire, sortie 0 et 6/6 contrôles. Dimension 1 024, vecteur de norme 1,0000, distance cosinus 0,0000 à auto-requête.
- **TP18 réel.** `Invoke-RestMethod http://127.0.0.1:11434/api/tags -TimeoutSec 4` puis appel Python de `repondre` avec client OpenAI local, délai 20 s, retries 0, qwen3:8b et `NUTRISCOPE_CATALOGUE` local. Produit 3017620422003, appel `chercher_produit` OK, note E, 539 kcal et 0,107 g de sel pour 100 g vérifiés contre le lot. 8,06 s, 1 301 jetons entrée et 102 sortie.
- **Non rejoués.** Tests propres de #70, notebooks d’entraînement et suite TensorFlow du TP17, ingestion documentaire complète, PostgreSQL actif et traitement du Parquet brut de 7,95 Go. Aucun rejeu de déploiement, évaluation interéquipes ou conversation LangChain.

- **TP19–20, rejouabilité du lot.** En archive f5960b7, `python -B -m src.corpus.fiches`, `python -B -m src.rag.indexer`, puis `python -B -m src.eval.retrieval --k 5 --sortie resultats/audit_retrieval_fiches.csv`. Sortie 0, 22/22 fiches indexées en 2,9 s avec le modèle d’embeddings Ollama local. Hit@5 de 14/14 en conditions réelles sur ce lot, premier attendu au rang 1 dans les 14 cas, sans génération sourcée.
