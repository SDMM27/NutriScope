# Rapport de nettoyage NutriScope

- Généré le 2026-10-06 par `python -m src.report` — ne pas éditer à la main
- Source : `data/extracts/france_brut.parquet`
- Données : Open Food Facts, © Open Food Facts contributors — licence ODbL

## Volumétrie

|  | avant | après | écart |
|---|---|---|---|
| lignes | 1 247 336 | 1 247 309 | -27 |
| colonnes | 23 | 23 | 0 |
| codes distincts | 1 247 309 | 1 247 309 | 0 |

## Lignes touchées par règle

Une ligne touchée par plusieurs sous-règles compte une fois dans « touchées », une fois par sous-règle dans le détail.

| règle | lignes avant | lignes après | touchées | détail |
|---|---|---|---|---|
| `typer_colonnes` | 1 247 336 | 1 247 336 | 0 | — |
| `dedupliquer_codes` | 1 247 336 | 1 247 309 | 27 | doublons_supprimes : 27 |
| `normaliser_unites` | 1 247 309 | 1 247 309 | 116 028 | kcal_derivees : 353 ; kcal_recalculees : 113 583 ; sodium_recalcule : 2 291 |
| `borner_nutriments` | 1 247 309 | 1 247 309 | 875 | fat_100g_negatifs : 1 ; fat_100g_sup_borne : 44 ; saturated-fat_100g_negatifs : 1 ; saturated-fat_100g_sup_borne : 17 ; carbohydrates_100g_sup_borne : 77 ; sugars_100g_sup_borne : 47 ; fiber_100g_negatifs : 58 ; fiber_100g_sup_borne : 20 ; proteins_100g_negatifs : 1 ; proteins_100g_sup_borne : 31 ; salt_100g_sup_borne : 54 ; sodium_100g_sup_borne : 54 ; sucres_sup_glucides : 411 ; satures_sup_lipides : 205 |
| `corriger_energie` | 1 247 309 | 1 247 309 | 2 512 | nulles_recalculees : 204 ; nulles_invalidees : 32 ; sup_900_recalculees : 89 ; sup_900_invalidees : 119 ; incoherentes_recalculees : 2 057 ; incoherentes_invalidees : 11 |
| `traiter_categories_vides` | 1 247 309 | 1 247 309 | 674 091 | categories_vides : 674 091 |
| `strategie_manquants` | 1 247 309 | 1 247 309 | 0 | — |

## Anomalies métier

Lignes en anomalie, mêmes définitions que le diagnostic de la démo 3.2.1.

| anomalie | avant | après |
|---|---|---|
| nutriment hors 0–100 g | 274 | 0 |
| énergie hors 0–900 kcal | 1 117 | 0 |
| énergie incohérente avec 4/4/9 | 20 213 | 65 |
| énergie nulle avec macronutriments | 3 336 | 0 |
| sucres > glucides | 427 | 0 |
| saturés > lipides | 217 | 0 |
| sel ≠ sodium × 2,5 | 2 291 | 0 |
| au moins une | 24 741 | 65 |

## Manquants sur les colonnes clés

| colonne | avant | après |
|---|---|---|
| `product_name` | 118 170 (9.5 %) | 118 163 (9.5 %) |
| `brands` | 597 617 (47.9 %) | 597 605 (47.9 %) |
| `food_groups_tags` | 25 028 (2.0 %) | 699 108 (56.0 %) |
| `pnns_groups_1` | 699 125 (56.0 %) | 699 108 (56.0 %) |
| `nutriscore_grade` | 25 040 (2.0 %) | 25 026 (2.0 %) |
| `energy-kcal_100g` | 359 477 (28.8 %) | 359 274 (28.8 %) |
| `fat_100g` | 366 472 (29.4 %) | 366 507 (29.4 %) |
| `saturated-fat_100g` | 367 656 (29.5 %) | 367 869 (29.5 %) |
| `carbohydrates_100g` | 366 211 (29.4 %) | 366 278 (29.4 %) |
| `sugars_100g` | 366 554 (29.4 %) | 367 003 (29.4 %) |
| `fiber_100g` | 867 348 (69.5 %) | 867 409 (69.5 %) |
| `proteins_100g` | 364 825 (29.2 %) | 364 847 (29.3 %) |
| `salt_100g` | 420 869 (33.7 %) | 420 911 (33.7 %) |

## Produits par rayon après nettoyage

| rayon | produits | part |
|---|---|---|
| (vide) | 699 108 | 56.0 % |
| Sugary snacks | 115 098 | 9.2 % |
| Fish meat eggs | 97 974 | 7.9 % |
| Milk and dairy products | 62 953 | 5.0 % |
| Cereals and potatoes | 57 020 | 4.6 % |
| Beverages | 46 342 | 3.7 % |
| Composite foods | 39 683 | 3.2 % |
| Fruits and vegetables | 39 585 | 3.2 % |
| Fats and sauces | 39 284 | 3.1 % |
| Salty snacks | 30 647 | 2.5 % |
| Alcoholic beverages | 17 073 | 1.4 % |
| Baby foods and milks | 2 542 | 0.2 % |

## Colonnes ajoutées et retirées

- ajoutées : aucune
- retirées : aucune
