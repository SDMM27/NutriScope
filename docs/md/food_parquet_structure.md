# Structure du fichier `data/food.parquet`

> Export du jeu de données [Open Food Facts](https://world.openfoodfacts.org/data) au format Parquet.
> Document généré pour être fourni en contexte à une IA (RAG) afin de faciliter l'écriture de requêtes (DuckDB/pandas) sur ce fichier.

## Vue d'ensemble

- **Fichier** : `data/food.parquet`
- **Nombre de lignes** : 4 636 471 produits (tous pays confondus)
- **Nombre de colonnes** : 111
- **Une ligne = un produit alimentaire** référencé sur Open Food Facts, identifié par son `code` (code-barres).
- Beaucoup de colonnes sont des **listes** (`VARCHAR[]`, suffixe `_tags` en général) ou des **structures imbriquées** (`STRUCT(...)`, parfois `STRUCT(...)[]` = liste de structures, notamment pour les champs multilingues comme `product_name`).
- Le sous-ensemble France (`'en:france' IN countries_tags`) contient environ 1 249 256 produits.

## Comment lire ce fichier

- Le fichier est volumineux (~7,7 Go) : privilégier **DuckDB** pour interroger le Parquet sans tout charger en mémoire, plutôt que `pandas.read_parquet` seul.
  ```python
  import duckdb
  duckdb.sql("SELECT * FROM 'data/food.parquet' WHERE 'en:france' IN countries_tags LIMIT 10").df()
  ```
- Le paramètre `filters=` de `pandas.read_parquet(engine="pyarrow")` ne gère que des comparaisons simples (`==`, `in`, ...) sur des colonnes scalaires : il **ne fonctionne pas** pour tester l'appartenance à une valeur dans une colonne de type liste (ex. `countries_tags`). Utiliser DuckDB (`'en:france' IN countries_tags`) dans ce cas.
- Colonnes `*_tags` : listes de tags normalisés (ex. `"en:france"`, `"en:organic"`), pratiques pour filtrer/grouper. Les colonnes sans suffixe `_tags` correspondantes contiennent souvent le texte brut/original (ex. `brands` vs `brands_tags`, `labels` vs `labels_tags`).
- Colonnes multilingues (`product_name`, `ingredients_text`, `generic_name`, `packaging_text`) : listes de structures `{lang, text}` — un produit peut avoir un nom/texte différent par langue.
- `nutriments` : liste de structures détaillant chaque nutriment (nom, valeur, valeur pour 100g, valeur par portion, unité, + équivalents "prepared").

## Colonnes

### Identification & informations générales

| Colonne | Type | Description |
|---|---|---|
| `code` | VARCHAR | Code-barres / identifiant unique du produit |
| `lang` | VARCHAR | Langue principale de la fiche produit |
| `link` | VARCHAR | URL/lien externe associé au produit |
| `creator` | VARCHAR | Utilisateur ayant créé la fiche |
| `owner` | VARCHAR | Compte propriétaire de la fiche (producteur, le cas échéant) |
| `brands` | VARCHAR | Marques du produit (texte brut, séparées par virgules) |
| `brands_tags` | VARCHAR[] | Marques normalisées en tags |
| `categories` | VARCHAR | Catégories du produit (texte brut) |
| `categories_tags` | VARCHAR[] | Catégories normalisées en tags |
| `categories_properties` | STRUCT(ciqual_food_code INTEGER, agribalyse_food_code INTEGER, agribalyse_proxy_food_code INTEGER) | Codes de correspondance vers les bases CIQUAL / Agribalyse |
| `product_name` | STRUCT(lang, text)[] | Nom du produit, par langue |
| `generic_name` | STRUCT(lang, text)[] | Nom générique du produit, par langue |
| `quantity` | VARCHAR | Quantité/contenance déclarée (texte, ex. "500 g") |
| `product_quantity` | VARCHAR | Quantité normalisée |
| `product_quantity_unit` | VARCHAR | Unité de la quantité normalisée |
| `serving_size` | VARCHAR | Taille de portion déclarée (texte) |
| `serving_quantity` | VARCHAR | Taille de portion normalisée |
| `nutrition_data_per` | VARCHAR | Base de déclaration nutritionnelle ("100g" ou "serving") |

### Localisation & lieux

| Colonne | Type | Description |
|---|---|---|
| `countries_tags` | VARCHAR[] | Pays de vente du produit (tags, ex. `en:france`) |
| `main_countries_tags` | VARCHAR[] | Pays principaux de vente |
| `origins` | VARCHAR | Origine des ingrédients (texte brut) |
| `origins_tags` | VARCHAR[] | Origine des ingrédients (tags) |
| `manufacturing_places` | VARCHAR | Lieux de fabrication (texte brut) |
| `manufacturing_places_tags` | VARCHAR[] | Lieux de fabrication (tags) |
| `purchase_places_tags` | VARCHAR[] | Lieux d'achat déclarés |
| `stores` | VARCHAR | Magasins où le produit a été trouvé (texte brut) |
| `stores_tags` | VARCHAR[] | Magasins (tags) |
| `cities_tags` | VARCHAR[] | Villes associées au produit |
| `emb_codes` | VARCHAR | Codes d'emballeur (texte brut) |
| `emb_codes_tags` | VARCHAR[] | Codes d'emballeur (tags) |

### Ingrédients & composition

| Colonne | Type | Description |
|---|---|---|
| `ingredients` | VARCHAR | Liste d'ingrédients (texte brut) |
| `ingredients_text` | STRUCT(lang, text)[] | Liste d'ingrédients, par langue |
| `ingredients_tags` | VARCHAR[] | Ingrédients normalisés en tags |
| `ingredients_original_tags` | VARCHAR[] | Ingrédients normalisés, version non retravaillée |
| `ingredients_n` | INTEGER | Nombre d'ingrédients détectés |
| `known_ingredients_n` | INTEGER | Nombre d'ingrédients reconnus |
| `unknown_ingredients_n` | INTEGER | Nombre d'ingrédients non reconnus |
| `unknown_nutrients_tags` | VARCHAR[] | Nutriments non reconnus |
| `ingredients_with_specified_percent_n` | INTEGER | Nombre d'ingrédients avec pourcentage précisé |
| `ingredients_with_unspecified_percent_n` | INTEGER | Nombre d'ingrédients sans pourcentage précisé |
| `ingredients_percent_analysis` | INTEGER | Indicateur d'analyse des pourcentages d'ingrédients |
| `ingredients_without_ciqual_codes` | VARCHAR[] | Ingrédients sans correspondance CIQUAL |
| `ingredients_without_ciqual_codes_n` | INTEGER | Nombre d'ingrédients sans correspondance CIQUAL |
| `ciqual_food_name_tags` | VARCHAR[] | Noms d'aliments CIQUAL associés |
| `ingredients_analysis_tags` | VARCHAR[] | Résultat d'analyse (ex. végétarien, végan, huile de palme) |
| `ingredients_from_palm_oil_n` | INTEGER | Nombre d'ingrédients contenant de l'huile de palme |
| `additives_n` | INTEGER | Nombre d'additifs détectés |
| `additives_tags` | VARCHAR[] | Additifs (tags, ex. `en:e330`) |
| `new_additives_n` | INTEGER | Nombre de nouveaux additifs détectés |
| `allergens_tags` | VARCHAR[] | Allergènes déclarés |
| `traces_tags` | VARCHAR[] | Traces éventuelles d'allergènes |
| `food_groups_tags` | VARCHAR[] | Groupes alimentaires (classification OFF) |
| `nucleotides_tags` | VARCHAR[] | Nucléotides détectés |
| `minerals_tags` | VARCHAR[] | Minéraux détectés |
| `vitamins_tags` | VARCHAR[] | Vitamines détectées |
| `with_sweeteners` | INTEGER | Indicateur de présence d'édulcorants |
| `with_non_nutritive_sweeteners` | INTEGER | Indicateur de présence d'édulcorants non nutritifs |

### Nutrition & scores

| Colonne | Type | Description |
|---|---|---|
| `nutriments` | STRUCT(name, value, "100g", serving, unit, prepared_value, prepared_100g, prepared_serving, prepared_unit)[] | Détail de chaque nutriment (energy, sugars, salt, proteins, etc.), valeurs brutes / pour 100g / par portion / produit préparé |
| `no_nutrition_data` | BOOLEAN | Vrai si aucune donnée nutritionnelle n'est renseignée |
| `nutrient_levels_tags` | VARCHAR[] | Niveaux des nutriments clés (bas/modéré/élevé) |
| `nutriscore_grade` | VARCHAR | Note Nutri-Score (a à e) |
| `nutriscore_score` | INTEGER | Score numérique Nutri-Score |
| `nova_group` | INTEGER | Groupe NOVA (niveau de transformation, 1 à 4) |
| `nova_groups` | VARCHAR | Groupe NOVA (texte) |
| `nova_groups_tags` | VARCHAR[] | Groupe NOVA (tags) |
| `environmental_score_grade` | VARCHAR | Note Éco-Score / Green-Score |
| `environmental_score_score` | INTEGER | Score numérique Éco-Score |
| `environmental_score_tags` | VARCHAR[] | Tags liés à l'Éco-Score |
| `environmental_score_data` | VARCHAR | Détail brut du calcul de l'Éco-Score |

### Emballage

| Colonne | Type | Description |
|---|---|---|
| `packaging` | VARCHAR | Description de l'emballage (texte brut) |
| `packaging_text` | STRUCT(lang, text)[] | Description de l'emballage, par langue |
| `packaging_tags` | VARCHAR[] | Emballage normalisé en tags |
| `packaging_shapes_tags` | VARCHAR[] | Formes d'emballage |
| `packaging_recycling_tags` | VARCHAR[] | Consignes de recyclage |
| `packagings` | STRUCT(material, number_of_units, quantity_per_unit, quantity_per_unit_unit, quantity_per_unit_value, recycling, shape, weight_measured)[] | Détail structuré des composants d'emballage |
| `packagings_complete` | BOOLEAN | Indique si la description des emballages est complète |

### Qualité des données & complétude

| Colonne | Type | Description |
|---|---|---|
| `complete` | INTEGER | Indicateur (0/1) de fiche complète |
| `completeness` | FLOAT | Score de complétude de la fiche (0 à 1) |
| `data_quality_errors_tags` | VARCHAR[] | Erreurs de qualité de données détectées |
| `data_quality_warnings_tags` | VARCHAR[] | Avertissements de qualité de données |
| `data_quality_info_tags` | VARCHAR[] | Informations de qualité de données |
| `data_sources_tags` | VARCHAR[] | Sources d'import des données |
| `states_tags` | VARCHAR[] | États d'avancement de la fiche (photos, ingrédients, nutrition renseignés...) |
| `misc_tags` | VARCHAR[] | Tags divers |
| `obsolete` | BOOLEAN | Vrai si le produit est marqué obsolète |
| `schema_version` | INTEGER | Version du schéma de données Open Food Facts |

### Images

| Colonne | Type | Description |
|---|---|---|
| `images` | STRUCT(key, imgid, rev, sizes STRUCT("100"/"200"/"400"/"full" → {h, w}), uploaded_t, uploader)[] | Métadonnées des images du produit (identifiants, dimensions par taille, uploader, date) |
| `max_imgid` | INTEGER | Identifiant de la dernière image ajoutée |
| `photographers` | VARCHAR[] | Utilisateurs ayant ajouté des photos |
| `last_image_t` | BIGINT | Horodatage (epoch) de la dernière image ajoutée |

### Historique, édition & popularité

| Colonne | Type | Description |
|---|---|---|
| `created_t` | BIGINT | Horodatage (epoch) de création de la fiche |
| `last_modified_t` | BIGINT | Horodatage (epoch) de dernière modification |
| `last_modified_by` | VARCHAR | Dernier utilisateur ayant modifié la fiche |
| `last_updated_t` | BIGINT | Horodatage (epoch) de dernière mise à jour |
| `last_editor` | VARCHAR | Dernier éditeur de la fiche |
| `last_edit_dates_tags` | VARCHAR[] | Dates d'édition (tags) |
| `entry_dates_tags` | VARCHAR[] | Dates de création (tags) |
| `editors` | VARCHAR[] | Liste des utilisateurs ayant édité la fiche |
| `informers_tags` | VARCHAR[] | Utilisateurs ayant renseigné des informations |
| `correctors_tags` | VARCHAR[] | Utilisateurs ayant corrigé la fiche |
| `checkers_tags` | VARCHAR[] | Utilisateurs ayant vérifié la fiche |
| `owner_fields` | STRUCT(field_name, timestamp)[] | Champs renseignés par le propriétaire, avec horodatage |
| `rev` | INTEGER | Numéro de révision de la fiche |
| `scans_n` | INTEGER | Nombre total de scans du produit |
| `unique_scans_n` | INTEGER | Nombre de scans uniques |
| `popularity_key` | BIGINT | Clé interne de popularité |
| `popularity_tags` | VARCHAR[] | Tags de popularité (ex. classement par mois/pays) |
| `languages_tags` | VARCHAR[] | Langues détectées sur l'emballage |
| `labels` | VARCHAR | Labels/certifications (texte brut, ex. "Bio, Sans gluten") |
| `labels_tags` | VARCHAR[] | Labels/certifications normalisés en tags |
| `compared_to_category` | VARCHAR | Catégorie de référence utilisée pour les comparaisons |

## Colonnes clés utilisées dans le projet

D'après les notebooks du projet (`load_and_display_food_data.ipynb`, `tp2_profiling.ipynb`) :

- `code` : identifiant produit
- `brands` / `brands_tags` : marques
- `countries_tags` : filtre France (`'en:france' IN countries_tags`)
- `purchase_places_tags`, `lang`
- `created_t` : date de création
- `nutriscore_grade` / `nutriscore_score` : taux de renseignement du Nutri-Score
- `nutriments` : accès aux valeurs `energy_100g`, `sugars_100g`, `salt_100g` (à extraire de la liste de structures)
