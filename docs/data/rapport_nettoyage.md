# Rapport de nettoyage NutriScope

- Généré le 2026-10-15 par `python -m src.report` — ne pas éditer à la main
- Source : `data/food.parquet`
- Données : Open Food Facts, © Open Food Facts contributors — licence ODbL

## Volumétrie

|  | avant | après | écart |
|---|---|---|---|
| lignes | 1 273 567 | 1 273 539 | -28 |
| colonnes | 22 | 22 | 0 |
| codes distincts | 1 273 539 | 1 273 539 | 0 |

## Lignes touchées par règle

Une ligne touchée par plusieurs sous-règles compte une fois dans « touchées », une fois par sous-règle dans le détail.

| règle | lignes avant | lignes après | touchées | détail |
|---|---|---|---|---|
| `typer_colonnes` | 1 273 567 | 1 273 567 | 0 | — |
| `dedupliquer_codes` | 1 273 567 | 1 273 539 | 28 | doublons_supprimes : 28 |
| `normaliser_unites` | 1 273 539 | 1 273 539 | 118 187 | kcal_derivees : 333 ; kcal_recalculees : 115 011 ; sodium_recalcule : 3 072 |
| `borner_nutriments` | 1 273 539 | 1 273 539 | 883 | fat_100g_negatifs : 1 ; fat_100g_sup_borne : 45 ; saturated-fat_100g_negatifs : 1 ; saturated-fat_100g_sup_borne : 17 ; carbohydrates_100g_sup_borne : 83 ; sugars_100g_sup_borne : 46 ; fiber_100g_negatifs : 19 ; fiber_100g_sup_borne : 21 ; proteins_100g_negatifs : 1 ; proteins_100g_sup_borne : 35 ; salt_100g_sup_borne : 57 ; sodium_100g_sup_borne : 57 ; sucres_sup_glucides : 426 ; satures_sup_lipides : 232 |
| `corriger_energie` | 1 273 539 | 1 273 539 | 2 590 | nulles_recalculees : 205 ; nulles_invalidees : 31 ; sup_900_recalculees : 67 ; sup_900_invalidees : 80 ; incoherentes_recalculees : 2 183 ; incoherentes_invalidees : 24 |
| `traiter_categories_vides` | 1 273 539 | 1 273 539 | 689 423 | categories_vides : 689 423 |
| `strategie_manquants` | 1 273 539 | 1 273 539 | 0 | — |

## Anomalies métier

Lignes en anomalie, mêmes définitions que le diagnostic de la démo 3.2.1.

| anomalie | avant | après |
|---|---|---|
| nutriment hors 0–100 g | 246 | 0 |
| énergie hors 0–900 kcal | 1 107 | 0 |
| énergie incohérente avec 4/4/9 | 20 177 | 0 |
| énergie nulle avec macronutriments | 3 332 | 0 |
| sucres > glucides | 440 | 0 |
| saturés > lipides | 244 | 0 |
| sel ≠ sodium × 2,5 | 3 072 | 0 |
| au moins une | 25 490 | 0 |

## Manquants sur les colonnes clés

| colonne | avant | après |
|---|---|---|
| `product_name` | 0 (0.0 %) | 0 (0.0 %) |
| `brands_tags` | 557 739 (43.8 %) | 557 734 (43.8 %) |
| `food_groups_tags` | 24 423 (1.9 %) | 713 835 (56.1 %) |
| `pnns_groups_1` | 1 273 567 (100.0 %) | 1 273 539 (100.0 %) |
| `nutriscore_grade` | 24 436 (1.9 %) | 24 422 (1.9 %) |
| `energy-kcal_100g` | 367 236 (28.8 %) | 367 025 (28.8 %) |
| `fat_100g` | 374 212 (29.4 %) | 374 247 (29.4 %) |
| `saturated-fat_100g` | 375 745 (29.5 %) | 375 984 (29.5 %) |
| `carbohydrates_100g` | 373 975 (29.4 %) | 374 047 (29.4 %) |
| `sugars_100g` | 374 570 (29.4 %) | 375 032 (29.4 %) |
| `fiber_100g` | 881 765 (69.2 %) | 881 787 (69.2 %) |
| `proteins_100g` | 372 573 (29.3 %) | 372 598 (29.3 %) |
| `salt_100g` | 430 836 (33.8 %) | 430 880 (33.8 %) |

## Produits par rayon après nettoyage

Indisponible : `pnns_groups_1` est absent ou entièrement manquant dans les données préparées.

## Colonnes ajoutées et retirées

- ajoutées : aucune
- retirées : aucune
