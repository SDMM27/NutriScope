# Synthèse EDA de référence — NutriScope

> Document de référence du projet, cité jusqu'au jury (BC02). Produit au TP 10 (30/09/2025).
> Source : Open Food Facts, © Open Food Facts contributors — ODbL.
> Détail et figures : `notebooks/eda_reference.ipynb` · registre : `docs/data/registre_hypotheses.csv`.

## Contexte

- **Données** : `data/echantillon_france.csv` (extrait France d'Open Food Facts, 8 689 produits).
- **Nettoyage** : *minimal, cas dégradé assumé*. Le nettoyage du TP 9 (`src.cleaning.nettoyer`) est livré et mergé sur `develop`, mais son pipeline cible le Parquet (rayons dans `food_groups_tags`) ; retrouver nos rayons `pnns_groups_1` à partir de cette colonne est une tâche du TP 12, pas encore faite. En attendant — et comme la référence du formateur — l'EDA tourne sur l'échantillon avec `eda_lib.nettoyage_minimal` (doublons de code-barres → première occurrence ; nutriment hors 0–100 g/100 g et énergie hors 0–900 kcal → ligne écartée ; manquants conservés, comme `strategie_manquants` du TP 9). **8 689 → 8 400 produits.**
- **Périmètre** : les comparaisons par rayon portent sur les **6 674 produits de rayon connu** (`pnns_groups_1`). Le rayon `unknown` (1 726 produits, **20,5 %**) est conservé mais écarté des comparaisons et signalé (message 2).

## Messages

1. **Un rayon domine le sucre.** Les snacks sucrés sont à **38 g de sucres/100 g en médiane** (quartiles 24–53), six fois le rayon suivant (boissons, 6,1 g). C'est le message d'ouverture pour le TP 11.
2. **Un cinquième du périmètre est hors rayon.** Le rayon `unknown` (20,5 %) n'a que **8,5 % de scores** et 62 % de fiches complètes : non comparable, à trancher au TP 12.
3. **Le profil nutritionnel change radicalement selon le rayon.** 66 % de E dans les snacks sucrés, 50 % de A dans les fruits et légumes ; **V de Cramér 0,34** sur 5 149 produits notés — le rayon est lié au grade sans le déterminer.
4. **La complétude est correcte mais inégale.** 79,5 % de fiches complètes sur les rayons connus (dix rayons entre 71 et 92 %), mais **boissons alcoolisées à 14 %** (1 % de scores) et aliments pour bébés sans aucun score. Les marques les plus présentes, Carrefour et Auchan, ne sont complètes qu'à **60 %**.
5. **5,5 % des produits portent une incohérence métier** (465 sur 8 400). L'énergie déclarée et l'énergie calculée (4/4/9) concordent (corrélation 0,97, écart médian 1,7 kcal) ; 119 produits s'en écartent de plus de 150 kcal, souvent une erreur d'unité (kJ dans le champ kcal).
6. **Le signal pour le Nutri-Score est porté par les graisses et l'énergie.** Spearman : saturés **0,54**, énergie **0,52**, puis lipides, sucres, sel, glucides. **Protéines (0,05) et fibres (−0,08) ≈ nuls.** Deux paires redondantes : sel/sodium (0,99), lipides/saturés (0,89).
7. **Un chiffre global masque des rayons opposés (Simpson).** Sucres × score : de −0,34 (snacks salés) à 0,79 (boissons) ; sel × score : 0,23 (fruits-légumes) à 0,83 (viandes). Chez les laitiers, le −0,30 global devient positif dans chaque sous-rayon.
8. **Les extrêmes restants sont surtout de vraies valeurs.** 1 371 produits (20,5 %) ont une valeur à plus de 3,5 MAD de la médiane de leur rayon ; sur les 15 plus extrêmes relus à la main : **9 vraies** (noix de coco, poudres, sirops), 5 résiduelles (sels de boisson aberrants), 1 vraie valeur dans un rayon faux.

## Registre d'hypothèses

Tests **exploratoires** stratifiés par rayon (`comparer_deux_groupes` : médianes, d de Cohen, Mann-Whitney). Le d de Cohen est lu à côté de la p-value, qui devient minuscule dès que `n` est grand.

| Hypothèse | Résultat | Décision |
| --- | --- | --- |
| H1 — bio → meilleur score (par rayon) | Un peu meilleur dans 8 rayons/9 (d médian −0,31), nul là où c'est déjà sain | **Reformulée** : effet de composition, pas un meilleur profil |
| H2 — NOVA 4 → moins bon score (par rayon) | Confirmée dans les 9 rayons, d de 0,20 à 0,77 | **Confirmée** ; feature candidate TP 14, prudence (fuite) |
| H3 — A moins sucré que E (par rayon) | Testable dans 3 rayons ; vraie en viandes, **inversée** en snacks salés | **Rejetée telle quelle** |
| H4 — sel lié au score plus fort par rayon qu'au global | Hétérogène : plus fort dans 6 rayons/9, plus faible dans 3 | **Reformulée** |

## Décisions par TP

- **TP 9 (nettoyage)** : coder les cinq incohérences métier (`normaliser_unites`, `borner_nutriments`, `corriger_energie`), regrouper les graphies de marques (`normaliser_textes`), ajouter deux drapeaux issus des extrêmes — `sel_boisson_aberrant` (boisson > 2 g de sel) et `lipides_egaux_glucides` (> 20 g).
- **TP 11 (état du marché)** : ouvrir sur le message 1 (snacks sucrés) ; raconter les grades par rayon (message 3).
- **TP 12 (catégorisation)** : décider du sort du rayon `unknown` (20,5 %) ; retrouver les rayons dans le Parquet complet via `food_groups_tags` ([0] = rayon, [1] = sous-rayon), qui remplace `pnns_groups_1/2` ; corriger les rayons faux (ex. sirop d'érable en boissons alcoolisées).
- **TP 14 (modèle)** : features saturés, énergie, lipides, sucres, sel, glucides ; **retirer le sodium** (répète le sel) ; **donner le rayon au modèle** (stratification) ; tester `log1p` sur sucres/sel et comparer linéaire vs arbres (relations non linéaires) ; tester NOVA 4 avec prudence (fuite possible) ; ne **pas** retenir le label bio comme proxy de qualité.

## Limites

- Échantillon France (8 400 produits), pas le périmètre complet ; nettoyage minimal, pas encore celui du TP 9.
- Manquants conservés (16–19 % par nutriment, ~50 % pour les fibres) : aucune imputation.
- Effectifs par marque sous-estimés (graphies non regroupées).
- Tests de la section 5 **exploratoires** : pas de correction pour comparaisons multiples, pas d'hypothèse préenregistrée. La rigueur inférentielle est vue au module 3.4.

_Données : Open Food Facts, © Open Food Facts contributors — ODbL._
