# Rapport de nettoyage NutriScope

- Généré le 2026-09-24 par `python -m src.report` — ne pas éditer à la main
- Source : `data/echantillon_france.csv`
- Données : Open Food Facts, © Open Food Facts contributors — licence ODbL

## Volumétrie

|  | avant | après | écart |
|---|---|---|---|
| lignes | 8 689 | 8 689 | 0 |
| colonnes | 34 | 34 | 0 |
| codes distincts | 8 663 | 8 663 | 0 |

## Lignes touchées par règle

Une ligne touchée par plusieurs sous-règles compte une fois dans « touchées », une fois par sous-règle dans le détail.

| règle | lignes avant | lignes après | touchées | détail |
|---|---|---|---|---|
| `typer_colonnes` | 8 689 | 8 689 | 0 | — |
| `normaliser_unites` | 8 689 | 8 689 | 1 028 | kcal_derivees : 3 ; kcal_recalculees : 924 ; sodium_recalcule : 136 |
| `borner_nutriments` | 8 689 | 8 689 | 365 | fat_100g_negatifs : 1 ; fat_100g_sup_borne : 31 ; saturated-fat_100g_negatifs : 1 ; saturated-fat_100g_sup_borne : 9 ; carbohydrates_100g_sup_borne : 50 ; sugars_100g_sup_borne : 32 ; fiber_100g_negatifs : 2 ; fiber_100g_sup_borne : 5 ; proteins_100g_negatifs : 1 ; proteins_100g_sup_borne : 17 ; salt_100g_sup_borne : 33 ; sodium_100g_sup_borne : 33 ; sucres_sup_glucides : 123 ; satures_sup_lipides : 121 |
| `corriger_energie` | 8 689 | 8 689 | 97 | nulles_recalculees : 3 ; sup_900_recalculees : 8 ; sup_900_invalidees : 45 ; incoherentes_recalculees : 41 |

## Anomalies métier

Lignes en anomalie, mêmes définitions que le diagnostic de la démo 3.2.1.

| anomalie | avant | après |
|---|---|---|
| nutriment hors 0–100 g | 127 | 0 |
| énergie hors 0–900 kcal | 153 | 0 |
| énergie incohérente avec 4/4/9 | 288 | 2 |
| énergie nulle avec macronutriments | 23 | 0 |
| sucres > glucides | 130 | 0 |
| saturés > lipides | 126 | 0 |
| sel ≠ sodium × 2,5 | 136 | 0 |
| au moins une | 733 | 2 |

## Manquants sur les colonnes clés

| colonne | avant | après |
|---|---|---|
| `product_name` | 4 (0.0 %) | 4 (0.0 %) |
| `brands` | 2 671 (30.7 %) | 2 671 (30.7 %) |
| `categories_tags` | 1 571 (18.1 %) | 1 571 (18.1 %) |
| `pnns_groups_1` | 26 (0.3 %) | 26 (0.3 %) |
| `nutriscore_grade` | 36 (0.4 %) | 36 (0.4 %) |
| `energy-kcal_100g` | 1 629 (18.7 %) | 1 671 (19.2 %) |
| `fat_100g` | 1 673 (19.3 %) | 1 705 (19.6 %) |
| `saturated-fat_100g` | 1 709 (19.7 %) | 1 840 (21.2 %) |
| `carbohydrates_100g` | 1 672 (19.2 %) | 1 722 (19.8 %) |
| `sugars_100g` | 1 703 (19.6 %) | 1 858 (21.4 %) |
| `fiber_100g` | 5 129 (59.0 %) | 5 136 (59.1 %) |
| `proteins_100g` | 1 671 (19.2 %) | 1 689 (19.4 %) |
| `salt_100g` | 1 961 (22.6 %) | 1 994 (22.9 %) |

## Produits par rayon après nettoyage

| rayon | produits | part |
|---|---|---|
| unknown | 1 854 | 21.3 % |
| Sugary snacks | 1 427 | 16.4 % |
| Fish Meat Eggs | 1 198 | 13.8 % |
| Milk and dairy products | 783 | 9.0 % |
| Cereals and potatoes | 700 | 8.1 % |
| Beverages | 553 | 6.4 % |
| Composite foods | 509 | 5.9 % |
| Fat and sauces | 509 | 5.9 % |
| Fruits and vegetables | 489 | 5.6 % |
| Salty snacks | 381 | 4.4 % |
| Alcoholic beverages | 209 | 2.4 % |
| Baby foods | 51 | 0.6 % |
| (vide) | 26 | 0.3 % |

## Colonnes ajoutées et retirées

- ajoutées : aucune
- retirées : aucune
