# Rapport de nettoyage NutriScope

- Généré le 2026-10-19 par `python -m src.report` — ne pas éditer à la main
- Source : `data/food.parquet`
- Données : Open Food Facts, © Open Food Facts contributors — licence ODbL

## Volumétrie

|  | avant | après | écart |
|---|---|---|---|
| lignes | 1 273 567 | 1 273 539 | -28 |
| colonnes | 24 | 24 | 0 |
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

Les rayons PNNS (`pnns_groups_1`) sont absents. La répartition ci-dessous utilise les groupes Open Food Facts (`food_groups_tags`). Un produit pouvant avoir plusieurs groupes, les parts ne s'additionnent pas nécessairement à 100 %.

| groupe Open Food Facts | produits | part des produits |
|---|---|---|
| en:sugary-snacks | 118 574 | 9.3 % |
| en:fish-meat-eggs | 99 311 | 7.8 % |
| en:milk-and-dairy-products | 64 043 | 5.0 % |
| en:cereals-and-potatoes | 58 540 | 4.6 % |
| en:sweets | 52 066 | 4.1 % |
| en:beverages | 47 595 | 3.7 % |
| en:biscuits-and-cakes | 44 976 | 3.5 % |
| en:fruits-and-vegetables | 40 817 | 3.2 % |
| en:fats-and-sauces | 39 826 | 3.1 % |
| en:composite-foods | 39 497 | 3.1 % |
| en:meat | 36 038 | 2.8 % |
| en:processed-meat | 35 170 | 2.8 % |
| en:cheese | 32 488 | 2.6 % |
| en:salty-snacks | 30 940 | 2.4 % |
| en:one-dish-meals | 30 745 | 2.4 % |
| en:dressings-and-sauces | 26 723 | 2.1 % |
| en:cereals | 25 747 | 2.0 % |
| en:fish-and-seafood | 22 436 | 1.8 % |
| en:poultry | 22 204 | 1.7 % |
| en:alcoholic-beverages | 18 012 | 1.4 % |
| en:vegetables | 17 226 | 1.4 % |
| en:unsweetened-beverages | 15 709 | 1.2 % |
| en:sweetened-beverages | 14 917 | 1.2 % |
| en:milk-and-yogurt | 14 770 | 1.2 % |
| en:bread | 13 916 | 1.1 % |
| en:meat-other-than-poultry | 13 834 | 1.1 % |
| en:chocolate-products | 13 799 | 1.1 % |
| en:fruits | 13 628 | 1.1 % |
| en:fats | 13 103 | 1.0 % |
| en:fatty-fish | 11 874 | 0.9 % |
| en:appetizers | 11 818 | 0.9 % |
| en:salty-and-fatty-products | 11 777 | 0.9 % |
| en:dairy-desserts | 8 402 | 0.7 % |
| en:ice-cream | 8 383 | 0.7 % |
| en:pastries | 7 733 | 0.6 % |
| en:nuts | 7 345 | 0.6 % |
| en:breakfast-cereals | 7 340 | 0.6 % |
| en:dried-fruits | 6 450 | 0.5 % |
| en:teas-and-herbal-teas-and-coffees | 6 373 | 0.5 % |
| en:legumes | 6 235 | 0.5 % |
| en:pizza-pies-and-quiches | 5 576 | 0.4 % |
| en:potatoes | 4 360 | 0.3 % |
| en:fruit-juices | 3 585 | 0.3 % |
| en:soups | 3 243 | 0.3 % |
| en:eggs | 3 240 | 0.3 % |
| en:sandwiches | 3 176 | 0.2 % |
| en:baby-foods-and-milks | 2 549 | 0.2 % |
| en:plant-based-milk-substitutes | 2 526 | 0.2 % |
| en:artificially-sweetened-beverages | 2 241 | 0.2 % |
| en:baby-foods | 2 004 | 0.2 % |
| en:offals | 1 902 | 0.1 % |
| en:lean-fish | 1 374 | 0.1 % |
| en:waters-and-flavored-waters | 1 343 | 0.1 % |
| en:fruit-nectars | 901 | 0.1 % |
| en:vegetable-margarines | 739 | 0.1 % |
| en:baby-milks | 545 | 0.0 % |

## Colonnes ajoutées et retirées

- ajoutées : aucune
- retirées : aucune
