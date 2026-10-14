# Journal de développement NutriScope

Ce journal retrace les principales étapes du développement de NutriScope : choix techniques, préparation des données, mise en place du pipeline ETL, organisation du code, nettoyage des données et tests automatisés.

Les entrées sont classées chronologiquement. Les contributeurs sont identifiés à partir des commits, des issues et des pull requests du dépôt GitHub.

* **Clément Welsch (`clement-welsch`)** : développement Python, architecture, intégration, nettoyage des données et tests.
* **Sacha Don (`SDMM27`)** : extraction et analyse des données, travaux sur la structure du projet et contribution au pipeline de nettoyage.
* **Binôme** : travaux dont la réalisation est collective ou pour lesquels l'attribution individuelle ne peut pas être établie avec certitude.

Une issue décrit un objectif de travail ; une pull request documente une proposition de modification ; un commit enregistre un changement. Ces éléments ne sont pas interchangeables et leur statut doit être pris en compte dans la lecture de cet historique.

---

## 29 juillet 2026 — Choix du format des données Open Food Facts

**Contributeur : binôme — décision technique**

### Contexte

Le projet nécessite de traiter un volume important de données issues d'Open Food Facts. Le format retenu doit permettre de stocker les données efficacement et de faciliter leur traitement avec Python et des outils SQL.

### Options étudiées

Trois formats sont envisagés :

* **CSV** : simple à lire et à manipuler, mais potentiellement coûteux en espace de stockage et en temps de traitement sur de gros volumes. Il représente également mal les structures imbriquées.
* **JSONL** : permet de stocker un objet JSON par ligne et de représenter des structures complexes, mais peut nécessiter de parcourir et de décoder de nombreux enregistrements lors de traitements volumineux.
* **Parquet** : format binaire orienté colonnes, qui offre une compression efficace et permet de ne lire que les colonnes nécessaires à une opération.

### Décision

Le format Parquet est retenu pour les données préparées du projet.

### Justification

Parquet est adapté aux analyses de données volumineuses et s'intègre bien à pandas et à DuckDB. Sa structure orientée colonnes permet de limiter les lectures aux champs nécessaires.

Ce choix est cohérent avec l'objectif de construire un pipeline de préparation et de chargement des données vers une base PostgreSQL.

---

## Étape suivante — Exploration et préparation des données

**Période : été 2026 — attribution individuelle à confirmer à partir de l'historique détaillé des commits**

### Objectif

Identifier les données Open Food Facts utiles à NutriScope et préparer des jeux de données exploitables par les traitements Python et la base relationnelle.

### Évolutions du projet

Le dépôt organise les données préparées en plusieurs ensembles métier :

* marques ;
* catégories ;
* produits ;
* relations entre produits et catégories ;
* nutriments.

Les données sont transformées en fichiers Parquet avant leur chargement dans PostgreSQL.

### Organisation retenue

La séparation des données en ensembles métier facilite leur exploitation et leur intégration dans des tables relationnelles distinctes.

Cette organisation permet notamment de représenter les relations entre produits et catégories sans devoir conserver toutes les informations dans une seule table.

### État documenté

Le README du dépôt décrit un pipeline ETL utilisant Python, pandas, Parquet, DuckDB et PostgreSQL. Il indique également les étapes de validation des données et de contrôle de la base après chargement.

Les dates précises de mise en place de chaque composant devront être confirmées par l'historique complet des commits.

---

## 2 septembre 2026 — Contrôles SQL de la base de données

**Contributeur : SDMM27 — issue #18**

### Objectif

Formaliser les commandes SQL permettant de contrôler les données après leur intégration dans la base.

### Enjeu technique

Le chargement des fichiers ne suffit pas à garantir la cohérence de la base. Il faut également pouvoir vérifier les volumes, les relations entre les tables et la présence éventuelle d'anomalies.

### Apport au projet

Cette étape s'inscrit dans la démarche de validation du pipeline ETL : les transformations doivent être suivies de contrôles permettant de détecter les incohérences avant l'exploitation des données par les fonctionnalités applicatives.

---

## 9 septembre 2026 — Évolution fonctionnelle : substitution de produits

**Contributeur : SDMM27 — issue #25**

### Objectif

Étudier la possibilité de scanner une liste de courses complète et de proposer des produits de substitution pour chaque article.

### Intérêt fonctionnel

Cette fonctionnalité étend l'objectif initial d'analyse d'un produit isolé à une utilisation plus large, orientée vers les choix alimentaires.

Elle suppose de disposer de données produits suffisamment structurées et fiables pour comparer les caractéristiques nutritionnelles et identifier des alternatives pertinentes.

### État

L'issue documente un objectif fonctionnel. Elle ne suffit pas, à elle seule, à établir que la fonctionnalité est implémentée.

---

## 17 septembre 2026 — Structuration des travaux du TP9

**Contributeur principal : Clément Welsch — issues #33, #35, #36 et #37**

Le 17 septembre, plusieurs issues sont ouvertes pour décomposer le travail de nettoyage des données en tâches indépendantes et vérifiables.

Cette organisation distingue quatre objectifs complémentaires.

### Issue #33 — Création de `src/cleaning.py`

**Responsable principal : Clément Welsch**

L'objectif est de regrouper les règles de nettoyage dans un module Python dédié.

Les règles prévues concernent notamment :

* la normalisation des unités ;
* le bornage des valeurs nutritionnelles ;
* le contrôle des valeurs énergétiques ;
* la déduplication des codes-barres ;
* le traitement des catégories vides.

Chaque règle doit être implémentée sous forme de fonction documentée, testable indépendamment et ne modifiant pas directement les données reçues en entrée.

La définition précise du comportement attendu pour les valeurs aberrantes doit précéder leur implémentation.

### Issue #35 — Tests automatisés avec pytest

**Responsable principal : Clément Welsch**

L'objectif est de vérifier le comportement de chaque règle de nettoyage, notamment sur les cas particuliers identifiés lors des précédents travaux.

Les tests doivent couvrir :

* les cas nominaux ;
* les valeurs manquantes ;
* les valeurs limites ;
* les données aberrantes ou incohérentes ;
* la préservation des données d'entrée ;
* les cas particuliers identifiés lors de l'analyse des données.

La répartition initiale prévoit également une contribution de Sacha Don aux tests concernant les doublons, les catégories et les cas particuliers.

### Issue #36 — Rapport avant/après du nettoyage

**Responsable principal : Clément Welsch**

L'objectif est de produire un rapport mesurant l'impact des règles de nettoyage.

Les indicateurs envisagés comprennent :

* la volumétrie avant et après traitement ;
* le nombre de lignes touchées par règle ;
* le nombre de lignes supprimées ;
* l'impact cumulé des transformations ;
* le nombre de valeurs manquantes.

Ce rapport doit rendre les transformations observables et faciliter la validation des résultats.

### Issue #37 — Intégration du nettoyage au chargement de la base

**Responsable principal : Clément Welsch**

L'objectif est de relier le pipeline de nettoyage au chargement de la base de données.

Le principe consiste à faire passer les données par les règles de nettoyage avant leur intégration, afin d'éviter de charger directement des données brutes non contrôlées.

Cette intégration doit préserver la cohérence du pipeline existant et permettre de vérifier les données après chargement.

---

## 17 septembre 2026 — Préparation de l'assistant RAG

**Contributeur principal : Clément Welsch — issue #29**

### Objectif

Étudier la création de modèles et de systèmes RAG personnalisés avec LM Studio afin de faciliter la relecture et l'exploitation de documents techniques.

### Intérêt pour le projet

Cette piste prépare une future fonctionnalité d'assistance conversationnelle s'appuyant sur des documents ou des données de référence.

Elle constitue un axe distinct du nettoyage des données : le pipeline ETL prépare les données structurées, tandis qu'une architecture RAG vise à retrouver des informations pertinentes dans un corpus documentaire.

### État

L'issue formalise une intention de développement. Elle ne constitue pas une preuve que l'assistant RAG est déjà intégré à l'application finale.

---

## 17 septembre 2026 — Mise en place d'une piste d'intégration continue

**Contributeur : Clément Welsch — pull request #39**

Une pull request intitulée `Create python-app.yml` est ouverte pour travailler sur l'automatisation des vérifications d'un projet Python.

### Objectif

Automatiser l'exécution de contrôles du code afin de détecter les régressions plus tôt dans le cycle de développement.

### État

La pull request apparaît encore ouverte dans le dépôt et porte le libellé `invalid`. Elle doit donc être considérée comme une tentative d'intégration continue, et non comme une automatisation validée.

---

## 24 septembre 2026 — Mise en place du contrat commun de nettoyage

**Contributeur principal : Sacha Don — pull request #41**

### Contexte

Les règles de nettoyage doivent partager une interface commune afin de pouvoir être exécutées dans un ordre défini et de produire des résultats comparables.

### Modifications documentées

La pull request introduit le squelette du module `src/cleaning.py`, avec notamment :

* la structure `CompteRendu` ;
* des constantes communes ;
* la fonction `typer_colonnes` ;
* la fonction `lire_brut()` ;
* la fonction `nettoyer()` ;
* la liste `REGLES`.

Elle ajoute également une configuration de tests via `tests/conftest.py` et des tests dans `tests/test_cleaning.py`.

Le premier point de contrôle couvre les types, la pureté des fonctions et l'idempotence. La pull request annonce cinq tests réussis.

### Contrat retenu

Les règles doivent être exécutables indépendamment et intégrables dans une séquence commune. La liste `REGLES` centralise leur ordre d'application.

L'ordre prévu comprend la normalisation des types, le traitement des textes, les doublons, les unités, les bornes nutritionnelles, l'énergie, les catégories et les valeurs manquantes.

### Validation

La pull request #41 est fusionnée dans `develop` le 24 septembre 2026 par Clément Welsch.

Cette fusion constitue une étape structurante du TP9 : elle établit le contrat commun sur lequel les règles de nettoyage peuvent être développées et testées.

---

## 29 septembre 2026 — Réexamen du champ des catégories Open Food Facts

**Contributeur : SDMM27 — issue #46**

### Contexte

Le champ `categories_tags` est remis en question au profit du champ `food_tag_groups`.

### Objectif

Évaluer le champ le plus approprié pour représenter les catégories ou groupes alimentaires utilisés par NutriScope.

### Enjeu technique

Le choix du champ source influence la cohérence des catégories, les transformations nécessaires et la compatibilité avec les règles de nettoyage.

Il est important de distinguer les catégories descriptives des groupes alimentaires normalisés, car ils ne répondent pas nécessairement au même besoin métier.

### État

L'issue est ouverte et placée dans le backlog. Le changement de champ constitue donc une proposition à examiner, et non une décision dont l'application serait confirmée.

---

## 30 septembre 2026 — Mutualisation des dépendances Python

**Contributeur : SDMM27 — issue #47**

### Objectif

Créer un fichier `requirements.txt` afin de partager une liste commune de dépendances entre les environnements de développement.

### Enjeu

Une liste de dépendances commune réduit les différences entre les environnements des contributeurs et facilite la reproduction des tests.

Elle contribue également à simplifier l'installation du projet pour un nouvel intervenant.

### État

L'issue documente ce besoin. La réalisation effective doit être confirmée par les commits correspondants.

---

## 14 octobre 2026 — Finalisation du nettoyage des catégories et du rapport

**Contributeur : Clément Welsch — pull request #52**

### Contexte

Les dernières évolutions du TP9 portent sur le traitement des catégories, la génération des comptes rendus et la validation du pipeline complet.

La pull request #52, intitulée `TP9: finalize category cleaning and report generation`, rassemble ces travaux sur la branche `Klement/feat/9_3_categories`.

### Modifications documentées

Les changements annoncés couvrent :

* le traitement des catégories vides dans les colonnes disponibles ;
* la prise en charge de DataFrames dont certaines colonnes de catégories sont absentes ;
* la restauration de la génération du rapport ;
* l'amélioration de la compatibilité des comptes rendus ;
* la validation du pipeline de nettoyage.

### Gestion des catégories

La règle de traitement des catégories doit fonctionner même lorsque le schéma d'entrée ne contient pas toutes les colonnes attendues.

Cette adaptation permet d'appliquer le nettoyage à des DataFrames de structures différentes sans provoquer d'erreur uniquement parce qu'une colonne de catégories est absente.

### Tests et validation

La pull request annonce :

* **43 tests réussis** ;
* la vérification des transformations attendues ;
* la vérification de l'idempotence du pipeline ;
* la couverture de la génération du rapport par des tests automatisés.

La commande de validation documentée est :

```bash
python -m pytest -v
```

### Commits associés

La pull request réunit quatre commits :

* `346fc21` — `fix issue with _compte_rendu and doubloons` ;
* `eefb23a` — `update tp9 notebook` ;
* `9d78bf8` — `add new test nettoyer` ;
* `77d940e` — `fix: restore report generation and handle optional category columns`.

Ces changements couvrent les corrections des comptes rendus et des doublons, la mise à jour du notebook, l'ajout d'un test d'intégration du nettoyage et la correction du rapport.

### État au 14 octobre 2026

La pull request #52 est ouverte dans le dépôt public. Les tests annoncés sont réussis, mais la fusion dans `develop` ne doit pas être considérée comme acquise tant que GitHub ne confirme pas sa réalisation.

---

## Synthèse de l'évolution du projet

Les travaux documentés montrent une progression en plusieurs étapes :

1. **Choix du stockage** : adoption de Parquet pour les données préparées.
2. **Préparation des données** : organisation des jeux de données métier et mise en place du pipeline ETL.
3. **Contrôles de la base** : formalisation des vérifications SQL.
4. **Structuration du TP9** : décomposition du nettoyage en règles, tests, rapport et intégration.
5. **Contrat commun** : définition de l'interface des règles et de leur ordre d'exécution.
6. **Qualité des données** : prise en charge des unités, des bornes, des doublons, de l'énergie, des catégories et des valeurs manquantes.
7. **Validation automatisée** : développement des tests et du rapport de nettoyage.
8. **Évolutions fonctionnelles à venir** : substitution de produits, reconnaissance et assistant conversationnel RAG.

## Points restant à documenter ou à confirmer

* Les dates et auteurs des premières étapes d'extraction et de préparation des données, à partir de l'historique complet des commits.
* L'état final de l'intégration du nettoyage au chargement de la base, correspondant à l'issue #37.
* Le statut final de l'issue #33 et des tests associés à l'issue #35.
* La décision définitive concernant le champ `food_tag_groups`.
* L'état de la mutualisation des dépendances Python.
* Le résultat final de la pull request #52 et la synchronisation de `develop`.
* La mise en place effective de l'intégration continue proposée dans la pull request #39.

Ce journal doit être enrichi à chaque étape significative en privilégiant les faits vérifiables : date, contributeur, modification, justification et résultat des validations.
