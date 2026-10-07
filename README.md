# NutriScope

## Présentation

NutriScope est un projet de service d'aide au choix alimentaire développé dans le cadre de la formation **Développeur en Intelligence Artificielle**.

L'objectif est de permettre à un utilisateur d'obtenir rapidement des informations utiles sur un produit alimentaire, au-delà du simple affichage d'un score nutritionnel.

À terme, NutriScope doit permettre notamment :

* d'identifier un produit à partir de son code-barres ;
* d'afficher ses informations nutritionnelles ;
* d'expliquer sa qualité nutritionnelle ;
* de présenter son Nutri-Score ;
* de proposer des produits de substitution ;
* de répondre aux questions de l'utilisateur à l'aide d'un assistant basé sur un système RAG.

Le projet s'appuie principalement sur les données ouvertes d'**Open Food Facts**.

---

## Équipe

* **Clément Welsch**
* **Sacha Don**

La répartition du travail s'organise principalement autour de deux axes :

* extraction et préparation des données sources ;
* traitement des données, base de données et organisation technique.

Les décisions ayant un impact sur l'ensemble du projet sont prises collectivement.

---

## Périmètre actuel

Le catalogue Open Food Facts étant très volumineux, NutriScope ne cherche pas à traiter l'ensemble des produits disponibles.

Le périmètre actuel se concentre sur six grands rayons :

1. boissons ;
2. produits laitiers ;
3. céréales et petit-déjeuner ;
4. biscuits et snacks ;
5. plats préparés et conserves ;
6. sauces et condiments.

Les catégories Open Food Facts ne correspondant pas directement à ces rayons, leur utilisation fait l'objet d'un travail de validation à partir des données réelles.

---

## Technologies

### Langage

* Python 3.12

### Données

* Pandas
* Parquet
* DuckDB
* PostgreSQL
* SQL

### Qualité et tests

* pytest
* Git
* GitHub
* environnement virtuel Python

### Intelligence artificielle

Les briques d'intelligence artificielle sont intégrées progressivement au projet.

Les fonctionnalités prévues comprennent notamment :

* analyse et exploitation des données nutritionnelles ;
* recommandation et substitution de produits ;
* reconnaissance automatique de produits ;
* système RAG ;
* assistant conversationnel.

Ces fonctionnalités ne constituent pas encore le cœur de l'architecture actuelle. Le projet se concentre d'abord sur la construction d'une base de données fiable.

---

# Données

## Source

Les données utilisées proviennent principalement d'Open Food Facts.

Les données brutes sont trop volumineuses pour être traitées comme un simple fichier CSV en mémoire. Le format **Parquet** et **DuckDB** sont donc utilisés pour faciliter leur exploration et leur traitement.

La source principale est :

* [Open Food Facts](https://world.openfoodfacts.org/)

## Volumétrie

Le périmètre France représente actuellement environ **1,25 million de produits**.

Les principaux jeux de données préparés pour le projet sont :

| Donnée                          | Volume approximatif |
| ------------------------------- | ------------------: |
| Marques                         |              79 577 |
| Catégories                      |              37 442 |
| Produits                        |           1 247 309 |
| Relations produits / catégories |           3 939 635 |
| Nutriments                      |           1 247 309 |

Les volumes peuvent évoluer au fil des traitements et des règles de nettoyage.

---

# Pipeline de données

L'architecture du pipeline a évolué au cours du projet.

L'organisation actuellement retenue est :

```text
Open Food Facts
       │
       ▼
Extraction du périmètre France
       │
       ▼
Nettoyage et validation
       │
       ▼
Jeu de données propre
       │
       ▼
Découpage des données
       │
       ▼
Préparation des tables
       │
       ▼
PostgreSQL
       │
       ├──────────────┐
       ▼              ▼
   Analyse       Fonctionnalités IA
                      │
              ┌───────┴────────┐
              ▼                ▼
        Substitution          RAG
              │                │
              └───────┬────────┘
                      ▼
                 Application
                 NutriScope
```

Cette organisation permet de réaliser le nettoyage sur une base commune avant de créer les différents jeux de données nécessaires à la base.

Elle évite notamment de nettoyer plusieurs fois les mêmes données et limite les risques d'incohérence entre les différentes tables.

---

# Nettoyage des données

Le profiling du dataset a montré que les données Open Food Facts contiennent de nombreuses anomalies.

Nous avons notamment rencontré :

* des valeurs nutritionnelles négatives ;
* des valeurs supérieures aux bornes attendues ;
* des incohérences sur les valeurs énergétiques ;
* des valeurs manquantes ;
* des doublons ;
* des catégories vides ;
* des fiches produits plus ou moins complètes.

## Principe de nettoyage

Une anomalie sur une donnée ne signifie pas nécessairement que le produit entier doit être supprimé.

Le nettoyage est donc réalisé **règle par règle**.

Selon le cas, une règle peut :

* corriger une valeur lorsqu'une correction fiable est possible ;
* supprimer uniquement une valeur incorrecte ;
* conserver le produit malgré une donnée manquante ;
* supprimer le produit lorsqu'une information essentielle est trop incertaine.

Cette approche permet de conserver autant de données exploitables que possible.

## Doublons

Deux fiches peuvent correspondre au même produit tout en présentant des niveaux de complétude différents.

Lorsqu'un doublon est identifié, la fiche la plus complète est privilégiée.

Les identifiants qui ne permettent pas d'assurer une identification fiable ne sont pas conservés comme clé d'unicité artificielle.

## Tests

Les règles de nettoyage sont accompagnées de tests automatisés avec `pytest`.

Les tests permettent notamment de vérifier :

* les cas normaux ;
* les valeurs manquantes ;
* les valeurs aberrantes ;
* les cas limites ;
* les cas particuliers rencontrés pendant le profiling ;
* le comportement des règles de nettoyage.

L'objectif est de rendre le nettoyage reproductible et de limiter les régressions lors des évolutions du projet.

---

# Base de données

Les données propres sont destinées à être organisées dans une base **PostgreSQL**.

La structure est progressivement séparée en plusieurs ensembles :

* `brands`
* `categories`
* `products`
* `products_categories`
* `nutrients`

Cette organisation permet de séparer les informations relatives aux produits, aux marques, aux catégories et aux données nutritionnelles.

Les relations entre les différentes entités sont assurées par des clés et des contraintes d'intégrité adaptées au modèle relationnel.

---

# Machine Learning et RAG

Le machine learning et le RAG constituent les prochaines grandes étapes du projet.

Cependant, ils ne doivent pas être construits sur une donnée insuffisamment maîtrisée.

La priorité actuelle est donc de stabiliser :

1. l'extraction ;
2. le nettoyage ;
3. le jeu de données propre ;
4. la préparation des données ;
5. la base PostgreSQL ;
6. les contrôles de cohérence.

Une fois cette chaîne stabilisée, elle servira de socle aux fonctionnalités d'intelligence artificielle.

## Nutri-Score

Le Nutri-Score est considéré comme une information de référence du projet.

Il ne doit pas être utilisé automatiquement comme variable d'entrée des futurs modèles lorsqu'il constitue directement ou indirectement la réponse recherchée.

Cette précaution vise notamment à éviter les phénomènes de fuite d'information dans les expérimentations de machine learning.

---

# Organisation du projet

La structure du dépôt évolue avec le développement du projet.

Les principaux répertoires sont actuellement organisés autour de :

```text
NutriScope/
│
├── data/
│
├── docs/
│
├── notebooks/
│
├── sql/
│
├── src/
│
├── tests/
│
├── CONTRIBUTING.md
├── PROJECT_LOG.md
└── README.md
```

## `data/`

Contient les données utilisées par le projet.

Les données sources volumineuses et les fichiers générés localement ne sont pas nécessairement versionnés dans Git.

## `docs/`

Contient la documentation du projet.

Le journal de bord et les documents de suivi permettent de conserver les décisions et l'évolution du projet.

## `notebooks/`

Contient les notebooks utilisés pour l'exploration et l'analyse des données.

## `sql/`

Contient les éléments SQL liés à la base de données et aux contrôles associés.

## `src/`

Contient le code Python du projet :

* traitement des données ;
* nettoyage ;
* validation ;
* accès à la base ;
* pipeline ETL ;
* fonctions utilitaires.

## `tests/`

Contient les tests automatisés du projet.

---

# Documentation du projet

Deux documents jouent des rôles différents dans le suivi du projet.

### `journal.md`

Le journal de bord décrit l'évolution du projet au fil des semaines :

* travaux réalisés ;
* répartition du travail ;
* problèmes rencontrés ;
* décisions prises ;
* apprentissages.

### `PROJECT_LOG.md`

Le journal technique conserve principalement l'historique des décisions structurantes et des changements d'architecture.

Il permet notamment de comprendre pourquoi certaines décisions techniques ont été prises et comment le pipeline actuel a été construit.

---

# État du projet

**Dernière mise à jour : 7 octobre 2026**

## Réalisé

* exploration des données Open Food Facts ;
* choix du format Parquet ;
* mise en place de DuckDB pour l'exploration ;
* définition du périmètre France ;
* définition d'un périmètre de six rayons ;
* profiling des données ;
* identification des principales anomalies ;
* conception des règles de nettoyage ;
* implémentation progressive du nettoyage ;
* mise en place de tests automatisés ;
* conception de la structure relationnelle ;
* préparation de PostgreSQL ;
* évolution du pipeline vers un nettoyage commun avant le découpage des données.

## En cours

* finalisation du pipeline de nettoyage ;
* production du jeu de données propre ;
* préparation des données destinées aux différentes tables ;
* chargement de la base ;
* contrôles de cohérence après chargement.

## À venir

* stabilisation complète du pipeline de données ;
* validation de la base ;
* exploitation avancée des données nutritionnelles ;
* fonctionnalité de substitution de produits ;
* machine learning ;
* reconnaissance automatique des produits ;
* architecture RAG ;
* assistant conversationnel ;
* intégration des différentes briques dans l'application finale.

---

# Principes du projet

NutriScope suit progressivement plusieurs principes structurants.

### La qualité des données avant les modèles

Les modèles d'intelligence artificielle doivent reposer sur des données suffisamment fiables et comprises.

### Une anomalie doit être traitée au niveau approprié

Lorsqu'une seule information est incorrecte, le produit entier ne doit pas être supprimé sans raison.

### Les transformations doivent être explicites

Les règles de nettoyage et de transformation doivent être compréhensibles, testables et reproductibles.

### La source et la base applicative sont deux choses différentes

Open Food Facts constitue la source de données. Sa structure n'a pas vocation à être reproduite telle quelle dans la base de NutriScope.

### Les décisions techniques doivent rester traçables

Les choix importants et leur justification sont conservés dans `PROJECT_LOG.md`.

---

# Liens

* [Dépôt GitHub NutriScope](https://github.com/SDMM27/NutriScope)
* [Open Food Facts](https://world.openfoodfacts.org/)
* [Open Food Facts — Wiki](https://wiki.openfoodfacts.org/)

---

## Licence et données

Les conditions d'utilisation et de redistribution des données Open Food Facts doivent être respectées conformément aux conditions applicables à la source.

Le projet doit également tenir compte des contraintes réglementaires et de protection des données applicables aux futures fonctionnalités de l'application.
