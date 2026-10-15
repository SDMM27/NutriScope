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

Les tests unitaires et le test d'intégration utilisent de petits jeux synthétiques. Un échantillon de 1 000 lignes françaises du Parquet réel a aussi été passé dans le pipeline, dans un répertoire temporaire. Le traitement complet du fichier source et l'import PostgreSQL sont des étapes distinctes; ils ne sont pas inclus dans les tests.
