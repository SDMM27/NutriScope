Le `journal.md` est un **journal de bord narratif**. Pour `PROJECT_LOG.md`, je partirais sur quelque chose de plus opérationnel : une **chronologie des décisions, changements techniques, problèmes et points de bascule**, sans reprendre chaque semaine sous forme de récit.

Voici le contenu que je te propose :

# PROJECT_LOG.md

## Historique du projet NutriScope

Ce fichier conserve l'historique technique et décisionnel de NutriScope.

Contrairement au journal de bord, il ne cherche pas à raconter chaque semaine du projet. Il sert à retrouver rapidement :

* les décisions importantes ;
* les changements d'orientation ;
* les problèmes rencontrés ;
* les solutions retenues ;
* les choix concernant les données et l'architecture ;
* les éléments qui pourront être utiles pour comprendre l'évolution du projet.

L'objectif est de pouvoir revenir sur le projet plusieurs semaines ou plusieurs mois plus tard et comprendre **pourquoi l'état actuel de NutriScope est celui-ci**.

---

# 1. Initialisation du projet

## Juillet 2026

### Objectif initial

NutriScope est lancé autour de l'idée d'une application permettant d'obtenir rapidement des informations sur un produit alimentaire.

Le projet doit progressivement aller au-delà d'un simple affichage du Nutri-Score avec plusieurs fonctionnalités envisagées :

* consultation des informations nutritionnelles ;
* explication du score ;
* comparaison entre produits ;
* proposition de produits de substitution ;
* assistant basé sur un système RAG.

Le projet doit également servir de support à la mise en pratique de plusieurs technologies liées aux données et à l'intelligence artificielle.

### Première difficulté : volume des données

L'exploration initiale d'Open Food Facts montre rapidement que le dataset est trop volumineux pour être manipulé simplement comme un fichier CSV classique.

### Décision

Le format **Parquet** est retenu pour travailler avec les données.

**DuckDB** est choisi pour interroger directement les données sans devoir charger l'ensemble du dataset en mémoire.

Cette décision devient la base du travail d'exploration et d'extraction des données.

---

# 2. Exploration d'Open Food Facts

## Juillet / août 2026

L'exploration du dataset permet d'identifier plusieurs difficultés :

* nombre important de colonnes ;
* informations nutritionnelles réparties dans plusieurs champs ;
* données parfois présentes sous plusieurs formes ;
* informations manquantes ;
* catégories hétérogènes ;
* qualité variable des fiches produits.

Une première conclusion importante apparaît :

> Le travail de préparation des données sera une partie majeure du projet.

Le dataset ne peut pas être considéré comme une donnée directement exploitable par les futurs modèles.

---

# 3. Définition du périmètre produit

## Fin août 2026

Le catalogue Open Food Facts étant trop large pour être traité intégralement dans le cadre du projet, un périmètre plus restreint est défini.

Six grands rayons sont retenus :

1. boissons ;
2. produits laitiers ;
3. céréales et petit-déjeuner ;
4. biscuits et snacks ;
5. plats préparés et conserves ;
6. sauces et condiments.

### Problème

Les catégories Open Food Facts ne correspondent pas directement à ces six rayons.

Un simple mapping manuel risquerait donc de produire un classement arbitraire.

### Décision

Les catégories doivent être confrontées aux données réelles avant de valider définitivement leur utilisation.

Les éléments observés comprennent notamment :

* le nombre de produits concernés ;
* la qualité des informations nutritionnelles ;
* la disponibilité des images ;
* les recouvrements entre catégories.

---

# 4. Profiling des données

## Fin août / début septembre 2026

Le profiling permet de mieux mesurer la qualité réelle des données.

Le périmètre France représente environ **1,25 million de produits**.

Les contrôles portent notamment sur :

* les valeurs manquantes ;
* les doublons ;
* les valeurs aberrantes ;
* la cohérence des données nutritionnelles ;
* la disponibilité des informations nécessaires aux fonctionnalités futures.

### Anomalies identifiées

Plusieurs types d'anomalies sont observés :

* valeurs nutritionnelles négatives ;
* valeurs supérieures à 100 g pour 100 g de produit ;
* incohérences entre différentes valeurs énergétiques ;
* informations incomplètes ;
* fiches produits présentant des niveaux de qualité différents.

### Conséquence

Le passage direct de l'extraction au machine learning est abandonné comme approche immédiate.

Le nettoyage et la fiabilisation des données deviennent une étape préalable obligatoire.

---

# 5. Jalon J1 : cadrage initial

## Début septembre 2026

Le premier jalon permet de stabiliser les premières décisions concernant le projet.

L'architecture générale du dépôt commence à prendre forme et les choix effectués jusque-là sont progressivement documentés.

### Décision importante : Nutri-Score

Le Nutri-Score ne doit pas être utilisé directement comme variable d'entrée des futurs modèles.

Il doit rester une référence ou une cible selon les cas d'utilisation.

### Raisonnement

Utiliser directement le Nutri-Score comme variable d'entrée pourrait conduire à un modèle qui obtient de bonnes performances en ayant accès à une information très proche de la réponse recherchée.

Le choix vise donc à éviter une forme de fuite d'information dans les futurs travaux de machine learning.

---

# 6. Première structuration des données

## Septembre 2026

Le projet passe progressivement de l'exploration à la conception.

Le fichier Open Food Facts contient de nombreuses informations utiles, mais sa structure n'est pas adaptée telle quelle à la base de données de NutriScope.

Plusieurs informations sont répétées et certaines colonnes regroupent plusieurs valeurs.

### Décision

Les données doivent être transformées avant leur chargement en base.

L'objectif n'est pas de reproduire la structure du fichier Open Food Facts, mais de construire une structure adaptée aux besoins de NutriScope.

Les principales entités commencent à être séparées :

* produits ;
* marques ;
* catégories ;
* nutriments.

---

# 7. Jalon J2 : cadrage et backlog

## Semaine du 15 septembre 2026

Le deuxième jalon permet de préciser davantage le périmètre et le backlog.

La progression envisagée devient :

**nettoyage des données → base de données → machine learning → RAG → application**

### Organisation du travail

La répartition du travail se stabilise progressivement :

* **Sacha** : extraction et travail sur les données sources ;
* **Clément** : traitement des données, base de données et organisation technique ;
* **ensemble** : décisions ayant un impact sur le périmètre ou l'architecture générale.

Cette organisation permet de travailler en parallèle tout en conservant les décisions importantes au niveau de l'équipe.

---

# 8. Conception du nettoyage

## Semaine du 22 septembre 2026

L'analyse du dataset montre qu'une anomalie sur une donnée ne signifie pas nécessairement que l'ensemble du produit doit être supprimé.

### Décision

Le nettoyage est conçu autour de **règles indépendantes**.

Une règle doit pouvoir :

* corriger une valeur lorsqu'une correction fiable est possible ;
* supprimer une valeur incorrecte lorsque le produit reste exploitable ;
* supprimer un produit lorsque l'information nécessaire est trop incertaine ;
* produire un compte rendu permettant de mesurer son impact.

Cette approche permet de limiter les suppressions inutiles.

---

# 9. Implémentation du nettoyage

## Fin septembre / début octobre 2026

Le nettoyage commence à être implémenté concrètement.

Les règles précédemment définies sont transformées en traitements vérifiables par des tests.

### Cas traités

Plusieurs situations particulières sont rencontrées :

* valeurs nutritionnelles aberrantes ;
* incohérences d'unités ;
* doublons ;
* produits dont certaines données sont incomplètes ;
* catégories vides ;
* incohérences sur les valeurs énergétiques.

### Doublons

Deux fiches peuvent représenter le même produit tout en contenant des niveaux d'information différents.

### Décision

Lorsqu'un doublon est identifié, la fiche la plus complète est privilégiée.

L'objectif est de réduire la duplication sans perdre inutilement des informations.

### Identifiants

Certains codes internes ne permettent pas d'identifier correctement un produit.

### Décision

Lorsqu'un identifiant ne permet pas d'assurer une unicité fiable, il est préférable de ne pas le conserver plutôt que de créer artificiellement une fausse correspondance entre produits.

---

# 10. Évolution du pipeline de données

## Semaine du 6 octobre 2026

L'avancement du nettoyage fait apparaître une question d'architecture importante :

**à quel moment les données doivent-elles être découpées en plusieurs fichiers ?**

L'approche initiale consistait à extraire directement plusieurs fichiers depuis le Parquet puis à les traiter séparément.

Cette organisation présente un risque de duplication du nettoyage et d'incohérence entre les différents fichiers.

### Nouvelle organisation retenue

Le pipeline est réorienté vers une chaîne commune :

**Open Food Facts**
↓
**Extraction du périmètre France**
↓
**Nettoyage**
↓
**Jeu de données propre**
↓
**Découpage des données**
↓
**Chargement en base**

### Pourquoi ce changement ?

Le nettoyage est effectué une seule fois sur une base commune.

Les différentes tables nécessaires à la base sont ensuite produites à partir d'un jeu de données déjà nettoyé.

Cela permet :

* d'éviter de répéter les mêmes traitements ;
* de limiter les divergences entre les fichiers ;
* de simplifier le raisonnement sur la qualité des données ;
* de séparer clairement nettoyage et modélisation de la base.

Le jeu de données propre devient donc une étape intermédiaire importante du pipeline.

---

# 11. État du projet au 6 octobre 2026

À cette date, NutriScope se trouve encore principalement dans la phase de préparation des données.

La structure logique de la base commence à être stabilisée autour de plusieurs ensembles :

* produits ;
* marques ;
* catégories ;
* nutriments.

Le nettoyage est en cours d'implémentation et les premières règles sont couvertes par des tests.

La chaîne complète de données n'est cependant pas encore totalement stabilisée.

### Prochaine priorité

Finaliser le pipeline :

1. extraire le périmètre France ;
2. appliquer les règles de nettoyage ;
3. produire le jeu de données propre ;
4. générer les données nécessaires aux différentes tables ;
5. charger la base ;
6. contrôler la cohérence des données chargées.

Une fois cette étape suffisamment stable, le projet pourra avancer vers les traitements de machine learning et le RAG.

---

# 12. Décisions structurantes

Cette section regroupe les décisions qui ont le plus influencé l'évolution du projet.

| Décision                                                | Raisons                                                             |
| ------------------------------------------------------- | ------------------------------------------------------------------- |
| Utiliser Parquet                                        | Dataset trop volumineux pour une manipulation classique en CSV      |
| Utiliser DuckDB                                         | Interroger les données sans tout charger en mémoire                 |
| Limiter le périmètre à six rayons                       | Garder un périmètre réalisable et cohérent                          |
| Valider les catégories avec les données réelles         | Éviter un mapping arbitraire                                        |
| Profiler avant le machine learning                      | Mesurer la qualité réelle des données                               |
| Ne pas utiliser directement le Nutri-Score comme entrée | Éviter une fuite d'information vers les modèles                     |
| Nettoyer règle par règle                                | Préserver les produits exploitables malgré des anomalies partielles |
| Privilégier la fiche la plus complète en cas de doublon | Réduire les doublons sans perdre d'information                      |
| Écarter les identifiants non fiables                    | Éviter de créer une fausse unicité                                  |
| Nettoyer avant de découper les données                  | Garantir une base commune et éviter les traitements répétés         |
| Utiliser un jeu de données propre intermédiaire         | Séparer clairement nettoyage et préparation de la base              |

---

# 13. État actuel

**Dernière mise à jour : 6 octobre 2026**

### Phase actuelle

**Préparation et fiabilisation des données**

### Réalisé

* exploration d'Open Food Facts ;
* choix du format Parquet ;
* utilisation de DuckDB pour l'exploration ;
* définition du périmètre France ;
* définition de six rayons ;
* profiling des données ;
* identification des principales anomalies ;
* définition d'une stratégie de nettoyage ;
* première implémentation des règles de nettoyage ;
* ajout de tests ;
* définition de la structure générale des données en base ;
* évolution du pipeline vers un nettoyage avant découpage.

### En cours

* stabilisation du nettoyage ;
* production du jeu de données propre ;
* préparation des données pour les différentes tables ;
* chargement et validation de la base.

### À venir

* finalisation du pipeline de données ;
* validation de la base ;
* préparation des données pour le machine learning ;
* premiers travaux de machine learning ;
* construction du RAG ;
* intégration des fonctionnalités dans l'application.

---

# 14. Principes retenus

Plusieurs principes se dégagent progressivement du développement de NutriScope.

### Les données avant les modèles

Le projet ne doit pas commencer par entraîner un modèle sur des données dont la qualité n'est pas maîtrisée.

### Une anomalie ne signifie pas nécessairement que le produit est inutilisable

Le nettoyage doit être suffisamment fin pour corriger ou supprimer une information sans supprimer systématiquement toute la fiche.

### Les transformations doivent rester traçables

Les règles appliquées aux données doivent pouvoir être comprises, testées et évaluées.

### La structure technique doit suivre les besoins du projet

Le format Open Food Facts est une source de données, pas nécessairement la structure idéale de la base finale.

### Les décisions doivent rester réversibles autant que possible

Lorsqu'une hypothèse est remise en question par l'analyse des données, le pipeline doit permettre de revenir en arrière et de modifier le traitement sans devoir reconstruire tout le projet.

---

# 15. Point de référence pour la suite

Le prochain objectif majeur est d'obtenir une chaîne de données reproductible et cohérente :

**Open Food Facts → extraction France → nettoyage → données propres → découpage → base de données**

Cette chaîne constitue désormais le socle sur lequel pourront être construits les futurs composants de NutriScope.

Le machine learning et le RAG ne doivent intervenir qu'une fois cette base suffisamment fiable pour que leurs résultats puissent être interprétés correctement.

Ce format est volontairement plus **technique et historique** que `journal.md` : le journal raconte l'évolution du projet, tandis que `PROJECT_LOG.md` permet de retrouver rapidement **les décisions et leur justification**. Il devrait donc rester utile même si le projet continue pendant plusieurs mois.
