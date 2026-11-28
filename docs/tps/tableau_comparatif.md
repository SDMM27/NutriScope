# TP14 — Tableau comparatif des modèles

> Canevas préparé le 26 novembre 2026. Remplacer « À RENSEIGNER » par des mesures produites par le notebook ; ne pas recopier les repères de l’énoncé.

## Conditions de comparaison

| Élément | Valeur retenue |
| --- | --- |
| Parquet / version / empreinte | À RENSEIGNER |
| Nombre de lignes | À RENSEIGNER |
| Split | Split du TP13, conservé tel quel |
| Validation croisée | Stratifiée, 5 plis, shuffle=True, random_state=42, mêmes indices |
| Features candidates | 7 nutriments obligatoires, variables optionnelles et catégories prévues par le sujet |
| Colonnes exclues | nutriscore_score, code, product_name, brands, split et la cible |
| Prétraitement | Imputation, indicateurs de manque, standardisation et one-hot avec regroupement rare, appris dans le pipeline |

## Résultats CV sur le train

Consigner les moyennes et écarts-types réellement calculés. Les temps doivent provenir de l’exécution du notebook.

| Modèle | F1 macro (moy. ± écart-type) | Accuracy | Balanced accuracy | Fit moyen (s) | Prédiction moyenne (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Dummy — classe majoritaire | À RENSEIGNER | À RENSEIGNER | À RENSEIGNER | À RENSEIGNER | À RENSEIGNER |
| Dummy — stratifié | À RENSEIGNER | À RENSEIGNER | À RENSEIGNER | À RENSEIGNER | À RENSEIGNER |
| Arbre — profondeur 3 | À RENSEIGNER | À RENSEIGNER | À RENSEIGNER | À RENSEIGNER | À RENSEIGNER |
| Arbre — profondeur 8 | À RENSEIGNER | À RENSEIGNER | À RENSEIGNER | À RENSEIGNER | À RENSEIGNER |
| Régression logistique | À RENSEIGNER | À RENSEIGNER | À RENSEIGNER | À RENSEIGNER | À RENSEIGNER |
| Forêt aléatoire | À RENSEIGNER | À RENSEIGNER | À RENSEIGNER | À RENSEIGNER | À RENSEIGNER |
| Modèle équilibré (si retenu) | À RENSEIGNER | À RENSEIGNER | À RENSEIGNER | À RENSEIGNER | À RENSEIGNER |

## Test final — après le choix du modèle

| Modèle retenu | F1 macro | Accuracy | Balanced accuracy | Écart CV/test en F1 macro |
| --- | ---: | ---: | ---: | ---: |
| À RENSEIGNER | À RENSEIGNER | À RENSEIGNER | À RENSEIGNER | À RENSEIGNER |

**Matrice de confusion normalisée par ligne :** À RENSEIGNER (chaque ligne somme à 1).

**Classes difficiles et direction des confusions :** À RENSEIGNER.

## Analyse à rédiger après les mesures

- Rapport accuracy / F1 macro de la baseline majoritaire et explication : À RENSEIGNER.
- Déséquilibre des classes et effet de class_weight balanced : À RENSEIGNER.
- Fuite reproduite avec nutriscore_score : F1 macro et importance par permutation : À RENSEIGNER.
- Contrôle anti-fuite et contrôle négatif : À RENSEIGNER.
- Importances du modèle honnête, cohérence avec les composantes officielles et proxies : À RENSEIGNER.
- Trois erreurs réelles de natures différentes : produit, nutriments, diagnostic et action : À RENSEIGNER.
- Phrase de synthèse à reporter dans docs/journal.md : À RENSEIGNER.

## Références

- Énoncé : [tp-14-predire-le-nutriscore.md](tp-14-predire-le-nutriscore.md).
- Notebook : [notebooks/ml_nutriscore.ipynb](../../../notebooks/ml_nutriscore.ipynb).
- Données Open Food Facts contributors, licence ODbL 1.0.
