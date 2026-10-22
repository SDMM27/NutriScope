# Stratégie de gestion des valeurs manquantes

## Objectif

La gestion des valeurs manquantes doit permettre de conserver autant que possible les produits exploitables sans créer de fausses informations.

La stratégie dépend de la colonne et de son usage dans NutriScope.

Le principe général est de distinguer :

* une donnée réellement absente (`NULL`) ;
* une valeur nulle (`0`) ;
* une donnée indispensable à l'identification ou à l'intégrité de la base.

Aucune valeur nutritionnelle manquante n'est imputée arbitrairement à `0`.

## Stratégie par colonne

| Table                 | Colonne            | Usage                                                       | Stratégie                | Justification                                                                                 |
| --------------------- | ------------------ | ----------------------------------------------------------- | ------------------------ | --------------------------------------------------------------------------------------------- |
| `products`            | `code`             | Identifiant produit et clé de jointure                      | Supprimer                | Un produit sans code ne peut pas être identifié de manière fiable dans la base.               |
| `products`            | `name`             | Affichage et recherche                                      | Conserver `NULL`         | Le produit peut rester exploitable même si son nom est absent.                                |
| `products`            | `completeness`     | Indicateur de qualité et sélection lors de la déduplication | Conserver `NULL`         | L'absence de complétude ne doit pas entraîner la suppression du produit.                      |
| `products`            | `brand_id`         | Information sur la marque                                   | Conserver `NULL`         | Une marque inconnue n'empêche pas l'existence du produit.                                     |
| `products`            | `nutriscore_grade` | Affichage du Nutri-Score                                    | Conserver `NULL`         | L'absence de Nutri-Score ne rend pas le produit inutilisable pour les autres fonctionnalités. |
| `products`            | `nutriscore_score` | Analyse et affichage du Nutri-Score                         | Conserver `NULL`         | Le score ne doit pas être inventé lorsqu'il est absent.                                       |
| `products_categories` | `category_id`      | Catégorisation du produit                                   | Ne pas créer de relation | Un produit sans catégorie doit rester présent dans `products`.                                |
| `nutrients`           | `energy`           | Information et calculs nutritionnels                        | Conserver `NULL`         | Une énergie inconnue ne doit pas être remplacée par une valeur arbitraire.                    |
| `nutrients`           | `energy_kcal`      | Information et calculs nutritionnels                        | Conserver `NULL`         | Une énergie inconnue ne doit pas être interprétée comme zéro.                                 |
| `nutrients`           | `proteins`         | Analyse nutritionnelle                                      | Conserver `NULL`         | Le produit reste exploitable pour les traitements ne nécessitant pas cette donnée.            |
| `nutrients`           | `carbohydrates`    | Analyse nutritionnelle                                      | Conserver `NULL`         | Le produit reste exploitable pour les traitements ne nécessitant pas cette donnée.            |
| `nutrients`           | `sugars`           | Analyse nutritionnelle                                      | Conserver `NULL`         | Le produit reste exploitable pour les traitements ne nécessitant pas cette donnée.            |
| `nutrients`           | `fat`              | Analyse nutritionnelle                                      | Conserver `NULL`         | Le produit reste exploitable pour les traitements ne nécessitant pas cette donnée.            |
| `nutrients`           | `saturated_fat`    | Analyse nutritionnelle                                      | Conserver `NULL`         | Le produit reste exploitable pour les traitements ne nécessitant pas cette donnée.            |
| `nutrients`           | `fiber`            | Analyse nutritionnelle                                      | Conserver `NULL`         | Le produit reste exploitable pour les traitements ne nécessitant pas cette donnée.            |
| `nutrients`           | `salt`             | Analyse nutritionnelle                                      | Conserver `NULL`         | Le produit reste exploitable pour les traitements ne nécessitant pas cette donnée.            |

## Règles par usage

### Identification du produit

Le `code` est la clé primaire de `products`. Un produit sans code ne peut donc pas être chargé dans cette table.

Les lignes dont le code est absent sont supprimées avant le chargement.

### Informations descriptives

Les informations comme le nom et la marque sont utiles pour l'affichage mais ne sont pas nécessaires à l'existence du produit dans la base.

Une information absente est donc conservée sous forme de `NULL`.

### Catégories

L'absence de catégorie ne justifie pas la suppression du produit.

Le produit reste présent dans `products`, mais aucune relation n'est créée dans `products_categories` lorsqu'aucune catégorie n'est disponible.

### Données nutritionnelles

Les données nutritionnelles manquantes sont conservées sous forme de `NULL`.

Elles ne sont pas remplacées par zéro et ne sont pas imputées à partir d'une moyenne ou d'une autre valeur arbitraire.

Un produit peut donc être conservé même si certaines données nutritionnelles sont absentes.

Les traitements nécessitant une donnée nutritionnelle particulière doivent explicitement exclure les lignes où cette donnée est `NULL`.

### Données nécessaires aux calculs

Lorsqu'un calcul nécessite plusieurs données, une ligne contenant une ou plusieurs valeurs manquantes ne doit pas recevoir une valeur calculée artificiellement.

Par exemple, le calcul de l'énergie à partir des macronutriments ne peut être effectué que lorsque les données nécessaires sont disponibles.

## Principe de conservation

La stratégie générale de NutriScope est donc :

> **Conserver le produit lorsque son identité est exploitable, conserver les informations inconnues sous forme de `NULL`, et exclure uniquement les données impossibles à identifier ou incompatibles avec les contraintes structurelles de la base.**

Cette stratégie permet de limiter la perte de données tout en évitant de transformer une absence d'information en information incorrecte.
