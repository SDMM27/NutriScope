# NutriScope

**Version : 0.0.001**

## Description

**NutriScope** est un projet de service d'aide au choix alimentaire développé dans le cadre de la formation **Développeur en Intelligence Artificielle**.

L'objectif est de permettre à un utilisateur de scanner un produit alimentaire en magasin afin d'obtenir :

* une identification du produit ;
* une explication de sa qualité nutritionnelle ;
* son Nutri-Score et les informations nutritionnelles associées ;
* des alternatives alimentaires plus adaptées ;
* à terme, un assistant conversationnel permettant d'interroger les données alimentaires.

Le projet s'appuie principalement sur les données ouvertes de **Open Food Facts**.

## Collaborateurs

* **Sacha Don**
* **Clément Welsch**

Les responsabilités sont réparties entre les travaux liés à l'extraction et à l'analyse des données, et ceux liés à la base de données, au développement Python, à l'architecture et à l'intégration.

## Technologies

### Langage

* Python 3.12.10

### Traitement et stockage des données

* Pandas
* Parquet
* DuckDB
* PostgreSQL
* SQL

### Développement et qualité

* pytest
* Git / GitHub
* environnement virtuel Python (`.venv`)

### IA — à venir

Le projet prévoit également l'intégration progressive de briques d'intelligence artificielle, notamment :

* reconnaissance de produits ;
* traitement et exploitation des informations nutritionnelles ;
* système de recommandation/substitution ;
* assistant conversationnel basé sur une architecture **RAG**.

Ces composants ne font pas encore partie de l'architecture fonctionnelle finale présentée dans ce README.

## Source des données

Les données utilisées proviennent principalement d'**Open Food Facts** :

* [Open Food Facts — Data](https://world.openfoodfacts.org/data)

Les données brutes sont transformées en plusieurs fichiers Parquet avant leur intégration dans la base de données.

Les principaux jeux de données utilisés sont :

* `brands.parquet`
* `categories.parquet`
* `products.parquet`
* `products_categories.parquet`
* `nutrients.parquet`

## Pipeline de données

Le projet utilise actuellement un pipeline **ETL** permettant de transformer les données Open Food Facts et de les charger dans PostgreSQL.

### Étapes principales

1. Extraction des données Open Food Facts.
2. Transformation et préparation des données au format Parquet.
3. Contrôle de la présence et de la structure des fichiers.
4. Nettoyage et validation des données.
5. Lecture des fichiers Parquet avec DuckDB.
6. Chargement des données dans PostgreSQL.
7. Vérification finale de la volumétrie et de l'intégrité des données.
8. Mesure du temps d'exécution des différentes étapes.

### Volumétrie actuelle

Le pipeline traite actuellement environ :

| Donnée                        |    Volume |
| ----------------------------- | --------: |
| Marques                       |    79 577 |
| Catégories                    |    37 442 |
| Produits                      | 1 247 309 |
| Relations produits/catégories | 3 939 635 |
| Nutriments                    | 1 247 309 |

Le fichier source `nutrients.parquet` contient davantage de lignes que la table finale en raison de doublons sur les codes produits. Les données sont donc dédoublonnées avant leur intégration.

## Pipeline de nettoyage des données

Le module `src/cleaning.py` fournit un pipeline de nettoyage reproductible pour préparer les données Open Food Facts avant leur exploitation dans les étapes suivantes du projet NutriScope.

### Objectifs

* Normaliser les types et les unités des données.
* Dédupliquer les produits à partir de leur code.
* Détecter et traiter les valeurs nutritionnelles invalides ou incohérentes.
* Normaliser les catégories vides.
* Conserver les valeurs manquantes lorsqu'aucune correction fiable n'est possible.
* Produire un journal des transformations effectuées.

### Ordre des règles

Le pipeline applique les règles suivantes dans cet ordre :

1. `typer_colonnes` : normalisation des types de colonnes.
2. `dedupliquer_codes` : traitement des produits en doublon.
3. `normaliser_unites` : harmonisation des unités et des valeurs nutritionnelles.
4. `borner_nutriments` : invalidation des valeurs nutritionnelles hors limites définies.
5. `corriger_energie` : correction des valeurs énergétiques lorsqu'un calcul fiable est possible.
6. `traiter_categories_vides` : remplacement des chaînes de catégories vides par des valeurs manquantes.
7. `strategie_manquants` : conservation des valeurs manquantes sans imputation artificielle.

L'ordre est défini dans `REGLES` dans `src/cleaning.py`.

### Traitement des catégories

La règle `traiter_categories_vides` examine les colonnes disponibles parmi `categories`, `categories_tags` et `food_groups_tags`.

* Les chaînes vides ou composées uniquement d'espaces sont remplacées par `pd.NA`.
* Les valeurs renseignées sont conservées.
* Les colonnes absentes sont ignorées.
* Les catégories manquantes ne sont pas reconstruites artificiellement.

Cette approche permet d'appliquer la règle à des DataFrames dont le schéma varie selon les données disponibles, sans provoquer d'erreur lorsqu'une colonne de catégories est absente.

### Contrat des règles de nettoyage

Chaque règle suit le contrat suivant :

```python
regle(df) -> (DataFrame, CompteRendu)
```

Les règles :

* travaillent sur une copie du DataFrame d'entrée ;
* retournent un DataFrame nettoyé et un objet `CompteRendu` ;
* fournissent des indicateurs sur les lignes touchées et les opérations réalisées ;
* doivent être idempotentes : appliquer deux fois la même règle ne doit pas modifier davantage les données déjà nettoyées.

Le nombre de lignes touchées correspond au nombre de lignes distinctes concernées par au moins une opération de la règle. Les détails permettent de distinguer les différents types d'opérations.

Le pipeline `nettoyer()` applique les règles dans l'ordre défini et retourne le DataFrame final ainsi que le journal des comptes rendus.

### Exécution des tests

Depuis la racine du projet, dans l'environnement Python du projet :

```bash
python -m pytest -v
```

La suite de tests validée pour cette version comporte **43 tests réussis**.

Les tests couvrent notamment :

* le comportement des règles de nettoyage ;
* la préservation du DataFrame d'entrée ;
* l'idempotence du pipeline ;
* le traitement des doublons et des index non uniques ;
* le calcul des comptes rendus ;
* la gestion des colonnes de catégories absentes ;
* la génération reproductible du rapport de nettoyage.

### Périmètre et limites

Le pipeline traite la qualité structurelle et métier des données en appliquant des règles déterministes. Il ne réalise pas d'imputation statistique, de normalisation pour l'apprentissage automatique ou de sélection de variables. Ces opérations relèvent des étapes de préparation spécifiques aux modèles.

Les corrections ne sont appliquées que lorsqu'elles sont suffisamment justifiées par les règles définies. Les valeurs douteuses qui ne peuvent pas être corrigées de manière fiable sont invalidées plutôt que remplacées arbitrairement.


## Rapport avant / après

Un rapport reproductible permet de mesurer l'impact du nettoyage des données.

Il permet notamment de suivre :

* le nombre de lignes avant traitement ;
* le nombre de colonnes ;
* le nombre de valeurs manquantes ;
* le nombre de lignes modifiées par règle ;
* le nombre de lignes supprimées ;
* l'impact cumulé des différentes règles ;
* la volumétrie finale.

Cela permet de rendre les choix de nettoyage mesurables et traçables.

## Base de données

Les données finales sont stockées dans une base **PostgreSQL**.

Les principales tables sont :

* `brands`
* `categories`
* `products`
* `products_categories`
* `nutrients`

Les relations entre les tables sont gérées par des clés étrangères.

L'ordre de chargement respecte les dépendances entre les tables :

1. `brands`
2. `categories`
3. `products`
4. `products_categories`
5. `nutrients`

Avant un nouveau chargement complet, les anciennes données sont supprimées afin de garantir un état cohérent de la base.

## Architecture du projet

```text
NutriScope/
│
├── .venv/
│
├── data/
│   └── extracts/
│       ├── brands.parquet
│       ├── categories.parquet
│       ├── products.parquet
│       ├── products_categories.parquet
│       └── nutrients.parquet
│
├── docs/
│   └── journal.md
│
├── notebooks/
│   └── first_notebook.ipynb
│
├── src/
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   └── timer.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   └── cleanup.py
│   │
│   ├── validation/
│   │   ├── __init__.py
│   │   └── checks.py
│   │
│   ├── etl/
│   │   ├── __init__.py
│   │   ├── brands.py
│   │   ├── categories.py
│   │   ├── products.py
│   │   ├── products_categories.py
│   │   └── nutrients.py
│   │
│   └── load_database.py
│
├── tests/
│   └── ...
│
├── README.md
└── requirements.txt
```

## Organisation du code

### `src/config/`

Centralise la configuration du projet.

`settings.py` contient notamment les paramètres nécessaires à la connexion et au fonctionnement du pipeline.

### `src/utils/`

Contient les utilitaires génériques du projet.

`timer.py` fournit les fonctions permettant de mesurer les temps d'exécution des différentes étapes du pipeline.

### `src/database/`

Regroupe les fonctionnalités liées à PostgreSQL :

* création et gestion des connexions ;
* nettoyage de la base ;
* opérations nécessaires au chargement des données.

### `src/validation/`

Contient les contrôles permettant de vérifier la cohérence des données et de la base après traitement.

### `src/etl/`

Contient les traitements spécifiques à chaque type de donnée :

* marques ;
* catégories ;
* produits ;
* relations produits/catégories ;
* nutriments.

Chaque module est responsable de la préparation et du chargement de son propre jeu de données.

### `src/load_database.py`

Ce script constitue le **point d'entrée principal du pipeline de chargement**.

Il orchestre notamment :

1. la vérification des fichiers d'entrée ;
2. la connexion à DuckDB ;
3. la connexion à PostgreSQL ;
4. le nettoyage de la base ;
5. le chargement des différentes tables ;
6. les contrôles finaux ;
7. la mesure du temps total d'exécution.

Le script a remplacé l'ancien `load_parquet.py`, dont le nom était devenu trompeur : le pipeline ne se contente pas de charger des fichiers Parquet, il utilise Parquet comme source d'un véritable processus ETL vers PostgreSQL.

## Architecture cible

L'architecture actuelle constitue la base technique du projet.

```text
                 Open Food Facts
                        │
                        ▼
                Données brutes
                        │
                        ▼
                Extraction / ETL
                        │
                        ▼
                     Parquet
                        │
                        ▼
                    DuckDB
                        │
             Transformation /
                validation
                        │
                        ▼
                   PostgreSQL
                        │
             ┌──────────┼──────────┐
             ▼          ▼          ▼
          Analyse    Substitution   RAG
             │          │          │
             └──────────┼──────────┘
                        ▼
                  Application
                  NutriScope
```

PostgreSQL constitue le stockage principal des données produits. Les futures fonctionnalités d'IA pourront exploiter cette base ainsi que des sources documentaires dédiées au système RAG.

## Liens utiles

* [Open Food Facts](https://world.openfoodfacts.org/)
* [Open Food Facts — Data](https://world.openfoodfacts.org/data)
* [Open Food Facts — Wiki](https://wiki.openfoodfacts.org/FR:Accueil)
* [Open Food Facts Python API](https://github.com/openfoodfacts/openfoodfacts-python)

## État du projet

### Réalisé

* [x] Exploration des données Open Food Facts
* [x] Extraction des données nécessaires
* [x] Conversion et stockage intermédiaire au format Parquet
* [x] Mise en place de DuckDB
* [x] Mise en place de PostgreSQL
* [x] Pipeline ETL
* [x] Séparation du code par responsabilité
* [x] Nettoyage des données
* [x] Gestion explicite des valeurs manquantes
* [x] Contrôles de validation
* [x] Tests automatisés avec pytest
* [x] Rapport avant / après du nettoyage
* [x] Mesure des temps d'exécution
* [x] Chargement des données dans PostgreSQL

### À venir

* [ ] Exploitation avancée des données nutritionnelles
* [ ] Fonctionnalité de substitution de produits
* [ ] Reconnaissance automatique des produits
* [ ] Mise en place de l'architecture RAG
* [ ] Assistant conversationnel NutriScope
* [ ] Intégration des différentes briques dans l'application finale
