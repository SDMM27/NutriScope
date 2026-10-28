# Préparation des données pour la classification du Nutri-Score

## État

Le TP14 prépare la première expérimentation de classification A–E. L'export ML documente déjà les variables candidates et un découpage `train`/`test` figé. La fonction de préparation, l'entraînement, la comparaison des modèles et l'analyse des erreurs restent à réaliser.

Le schéma a été vérifié dans les Parquets du dépôt avec DuckDB : `data/nutriscope_ml_sample.parquet` contient 30 041 lignes (24 076 train, 5 965 test) et `data/nutriscope_ml_full.parquet` 422 470 lignes (337 976 train, 84 494 test). Les deux fichiers contiennent les colonnes listées ci-dessous, dont `split`, les sept nutriments obligatoires, les variables optionnelles et les champs d'identification.

Le notebook d'exercice est [TP14 — Préparer les jeux de classification](../../notebooks/tp14-preparer-donnees-classification-nutriscore.ipynb).

## Comportement attendu de la première brique

La fonction `preparer_jeux_classification(df)` devra séparer les lignes selon la colonne `split` existante et fournir les features et la cible aux ensembles train et test. Elle conservera séparément les informations d'identification et le score de référence pour l'analyse finale des erreurs.

Les features retenues suivent le cadrage TP14 : les sept nutriments obligatoires, `fiber_100g`, `fruits-vegetables-legumes_100g`, `nova_group`, `additives_n`, `pnns_groups_1` et `pnns_groups_2`. Les colonnes `nutriscore_grade`, `nutriscore_score`, `code`, `product_name`, `brands` et `split` ne sont jamais des features. Le score reste toutefois disponible comme référence de diagnostic.

Les valeurs manquantes des variables optionnelles sont conservées à cette étape ; leur traitement doit être appris dans le pipeline de prétraitement, ajusté uniquement sur les données d'entraînement. Aucun nouveau découpage aléatoire n'est fait ici.

Les colonnes requises manquantes, les valeurs de grade hors `a`–`e`, les valeurs de `split` autres que `train`/`test` et un jeu train ou test vide doivent produire une erreur explicite. Cette préparation ne calcule aucun score de modèle et n'ouvre pas la base PostgreSQL.

## Tests d'acceptation

`tests/test_ml_nutriscore.py` décrit les cas nominaux, l'exclusion des fuites, la conservation des manquants optionnels, les colonnes absentes, les valeurs de contrôle inattendues et les partitions vides. Ces tests définissent le contrat ; tant que `src/ml_nutriscore.py` n'est pas écrit, ils ne peuvent pas réussir.

Commande ciblée depuis la racine :

```powershell
python -m pytest -q -p no:cacheprovider --basetemp=.pytest-tmp tests/test_ml_nutriscore.py
```

Utiliser un interpréteur Python fonctionnel avec les dépendances du projet. L'environnement `.venv` présent dans le dépôt peut référencer un interpréteur absent.

## Vérifications observées le 20 octobre 2026

Le notebook est un JSON Jupyter valide. Le lancement des tests d'acceptation a été tenté avec Python 3.12 et les dépendances du dépôt ; pytest s'arrête à la collecte avec `ModuleNotFoundError: No module named 'src.ml_nutriscore'`, car l'implémentation n'a pas encore été écrite. Aucun test d'acceptation n'a donc été exécuté avec succès à ce stade.
