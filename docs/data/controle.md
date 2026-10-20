# Contrôles qualité sur le Parquet (TP 12)

Données : © Open Food Facts contributors — ODbL 1.0 (https://opendatacommons.org/licenses/odbl/1-0/).

Date : 2026-10-20 · source : `data/parquet/produits` (vue `produits`, requêtes dans `sql/controles.sql`).

## comptage_par_rayon

| rayon | nb_produits | part_pct |
|---|---|---|
| unknown | 713 835 | 56,05 |
| sugary-snacks | 118 574 | 9,31 |
| fish-meat-eggs | 99 311 | 7,80 |
| milk-and-dairy-products | 64 043 | 5,03 |
| cereals-and-potatoes | 58 540 | 4,60 |
| beverages | 47 595 | 3,74 |
| fruits-and-vegetables | 40 817 | 3,21 |
| fats-and-sauces | 39 826 | 3,13 |
| composite-foods | 39 497 | 3,10 |
| salty-snacks | 30 940 | 2,43 |
| alcoholic-beverages | 18 012 | 1,41 |
| baby-foods-and-milks | 2 549 | 0,20 |

## completude

| rayon | nb_produits | nutriscore_pct | sept_nutriments_pct | categorie_pct |
|---|---|---|---|---|
| unknown | 713 835 | 5,31 | 52,74 | 0 |
| sugary-snacks | 118 574 | 79,27 | 81,09 | 100 |
| fish-meat-eggs | 99 311 | 79,76 | 79,89 | 100 |
| milk-and-dairy-products | 64 043 | 84,85 | 85,23 | 100 |
| cereals-and-potatoes | 58 540 | 82,72 | 85,20 | 100 |
| beverages | 47 595 | 70,34 | 77,78 | 100 |
| fruits-and-vegetables | 40 817 | 72,83 | 73,64 | 100 |
| fats-and-sauces | 39 826 | 79 | 83,97 | 100 |
| composite-foods | 39 497 | 89,82 | 90,84 | 100 |
| salty-snacks | 30 940 | 87,63 | 87,97 | 100 |
| alcoholic-beverages | 18 012 | 0,32 | 10,79 | 100 |
| baby-foods-and-milks | 2 549 | 0 | 86,98 | 100 |

## doublons

| codes_en_double_groupes | lignes_en_trop | couples_nom_marque_repetes_groupes |
|---|---|---|
| 0 | 0 | 29 462 |

## bornes_coherences

| controle | nb |
|---|---|
| fat_100g hors [0, 100] | 0 |
| saturated-fat_100g hors [0, 100] | 0 |
| carbohydrates_100g hors [0, 100] | 0 |
| sugars_100g hors [0, 100] | 0 |
| fiber_100g hors [0, 100] | 0 |
| proteins_100g hors [0, 100] | 0 |
| salt_100g hors [0, 100] | 0 |
| sodium_100g hors [0, 40] | 0 |
| energy-kcal_100g hors [0, 900] | 0 |
| sucres > glucides | 319 |
| saturés > lipides | 339 |
| sel ≠ sodium × 2,5 (écart > 0,1) | 43 |
| énergie nulle avec macronutriments > 0 | 0 |

## distribution_nutriscore

| grade | nb_produits | part_pct | score_moyen |
|---|---|---|---|
| a | 63 906 | 5,02 | -2,90 |
| b | 49 862 | 3,92 | 0,58 |
| c | 97 993 | 7,69 | 5,61 |
| d | 124 302 | 9,76 | 14,07 |
| e | 133 827 | 10,51 | 23,25 |
| not-applicable | 42 463 | 3,33 |  |
| null | 24 422 | 1,92 |  |
| unknown | 736 764 | 57,85 |  |

## Cohérence avec la base PostgreSQL (TP 9, 19/10)

| Mesure | PostgreSQL | Parquet |
|---|---|---|
| produits | 1 273 539 | 1 273 539 |
| sans catégorie | 713 835 | 713 835 (`unknown`) |
| produits laitiers / céréales | 64 043 / 58 540 | 64 043 / 58 540 |
| boissons (hors alcool) | 47 595 | 47 595 |
| sauces et condiments | 39 826 | 39 826 |
| codes en double, hors bornes | 0 | 0 |

Même nettoyé, mêmes comptages. Les cohérences du contrôle 4 (sucres > glucides, saturés > lipides) viennent de la tolérance de 0,5 g du TP 9 : elles sont listées, pas filtrées.
