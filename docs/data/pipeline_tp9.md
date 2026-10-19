# Pipeline de données TP9

## Exécution

Depuis la racine du dépôt et avec l'environnement Python du projet :

```powershell
python src/extract_perimeter.py
```

Cette commande projette les colonnes utiles de `data/food.parquet`, filtre les produits français avec DuckDB, écrit l'extrait intermédiaire `data/extracts/france_brut.parquet`, applique `nettoyer()` une seule fois, produit `docs/data/rapport_nettoyage.md` et écrit les cinq Parquets attendus par PostgreSQL dans `data/extracts/`.

Pour régénérer le même jeu de fichiers et le rapport en choisissant le chemin de la source et du rapport :

```powershell
python -m src.report --source data/food.parquet --sortie docs/data/rapport_nettoyage.md
```

Le chargeur appelle la même préparation avant de vider la base et d'insérer les Parquets :

```powershell
python src/load_database.py
```

La dernière commande s'adresse à la base PostgreSQL configurée dans `src/config/settings.py`. Vérifier cette configuration et utiliser un environnement de base approprié avant de l'exécuter.

## Décisions de traitement

DuckDB inspecte le schéma, projette les colonnes nécessaires et effectue le filtre France en une lecture source. Le Parquet intermédiaire évite de répéter cette lecture pendant le nettoyage, la création du rapport et la préparation relationnelle. Le nettoyage pandas travaille sur cette projection limitée, avec la déduplication globale intacte.

Les caractères NUL et les espaces en bordure sont retirés des codes dans `typer_colonnes`, avant la déduplication : deux codes qui deviennent identiques après cette correction ne peuvent donc pas créer des fiches ou relations incohérentes dans PostgreSQL. Un code vide après normalisation devient manquant, puis est supprimé par la règle de déduplication. Les espaces internes sont conservés. Le compte rendu indique séparément les codes normalisés. Les nutriments passent explicitement des noms Open Food Facts aux noms attendus par `src/cleaning.py`, puis aux colonnes SQL dans `src/etl_pipeline.py`. Les marques, catégories et relations sont construites après déduplication et uniquement à partir des codes conservés. `brand_name` reste dans `products.parquet` car le chargeur s'en sert pour résoudre `brand_id`.

Le champ `pnns_groups_1` est conservé lorsqu'il existe; s'il manque, il reste absent ou nul. La règle 4/4/9 n'exclut que la valeur explicitement classée `Alcoholic beverages`. Une classification inconnue ne reçoit aucune catégorie supposée et reste incluse dans le contrôle énergétique.

Les contrôles de plages SQL et la conversion des valeurs non finies en valeurs manquantes sont appliqués lors du mapping des nutriments. Le chargeur garde également ses protections d'intégrité et d'insertion.

## Validation

Les 54 tests unitaires et d'intégration passent. Ils utilisent principalement de petits jeux synthétiques. Le 15 octobre 2026, le pipeline complet a aussi été exécuté sur `data/food.parquet` : DuckDB a extrait 1 273 567 lignes françaises, puis le nettoyage a conservé 1 273 539 produits. Les cinq Parquets et le rapport ont été générés.

Les Parquets ont été contrôlés après génération : aucune clé produit, marque ou catégorie dupliquée, et aucun lien orphelin dans les relations produits-catégories, les nutriments ou les marques. La source ne fournit pas `pnns_groups_1`; le rapport présente donc la répartition multi-catégorie d'Open Food Facts à partir de `food_groups_tags`.

Le 19 octobre 2026, les cinq Parquets ont été chargés dans PostgreSQL 17. Les volumes sont conformes aux fichiers générés :

| Table | Lignes |
|---|---:|
| `brands` | 104 862 |
| `categories` | 56 |
| `products` | 1 273 539 |
| `products_categories` | 1 149 684 |
| `nutrients` | 1 273 539 |

Le chargeur vérifie maintenant que le Parquet `products` ne contient aucun code nul, vide ou dupliqué **avant** de vider les tables PostgreSQL. Les contrôles directs dans PostgreSQL n'ont détecté aucun doublon de clé, aucune clé étrangère orpheline et aucune valeur nutritionnelle hors bornes. La requête TP4 « produits sans catégorie » en compte 713 835 (56,1 %), ce qui correspond aux produits sans `food_groups_tags` dans le rapport. La requête de complétude par rayon a été mise à jour avec les groupes `food_groups_tags` retenus pour les six rayons. Les boissons alcoolisées sont exclues du rayon « Boissons » pour cet indicateur ; les produits multi-groupes peuvent être comptés dans plusieurs rayons, les volumes ne sont donc pas exclusifs. L'exécution sur la base rechargée renvoie les six rayons : 47 595 boissons (70,3 % avec Nutri-Score), 64 043 produits laitiers (84,9 %), 58 540 céréales et petit-déjeuner (82,7 %), 149 514 biscuits et snacks (81,0 %), 42 740 plats préparés et conserves (89,7 %) et 39 826 sauces et condiments (79,0 %).
