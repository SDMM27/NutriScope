# Guide de contribution

Ce document formalise les conventions déjà utilisées sur le projet NutriScope. Il s'adresse aux deux collaborateurs actuels (Sacha Don, Clément Welsch) et à toute personne qui rejoindrait le projet.

## Branches

- `main` : version de rendu / stable du TP. On n'y pousse jamais directement.
- `develop` : branche d'intégration. Toutes les branches de travail partent de `develop` et y retournent via une PR.
- Branches de travail : `Prénom/type/description-courte`, par exemple :
  - `Sacha/feat/loading_notebook_food_parquet`
  - `Klement/fix/gitignore`
  - `Sacha/docs/food_parquet_structure`

Types utilisés : `feat` (nouvelle fonctionnalité / exercice traité), `fix` (correction), `docs` (documentation, journal, README).

## Messages de commit

Les messages sont rédigés **en français**, à l'impératif ou en description courte de l'action. On ne préfixe jamais les commits par un type (`feat:`, `fix:`, ...) : le type est déjà porté par le nom de la branche (voir [Branches](#branches)). Le message est donc juste la description courte de ce qui a été fait :

```
description courte de ce qui a été fait
```

- La description reste courte (une ligne, ~72 caractères), au présent/infinitif : `ajoute`, `corrige`, `renomme`, plutôt que `ajouté`/`corrigé`.
- Un commit = un changement logique cohérent (ex. répondre à une question du TP, corriger un bug de chargement, mettre à jour le journal).
- Pas de commit fourre-tout mélangeant plusieurs sujets (ex. réponses au TP + modification du gitignore).

Exemples :
```
ajoute le chargement du fichier food.parquet
gère l'erreur de lecture du parquet avec un except
justifie le seuil de complétude retenu pour le profiling
```

## Taille des Pull Requests

- Une PR correspond à **une branche de travail = un sujet** : un exercice de TP, une correction, un ajout de documentation. Pas de PR qui mélange plusieurs TP ou plusieurs sujets indépendants.
- Cible une PR facilement relisable en une fois : un notebook complété, un module ou un fichier de doc à la fois plutôt que l'ensemble du TP d'un coup.
- Si une PR grossit trop (plusieurs notebooks, plusieurs sujets non liés), la découper en plusieurs PRs plus petites vers `develop`.
- Titre de la PR clair sur le contenu (ex. "TP2 - Profiling des données"), description listant rapidement ce qui a été traité.

## Relecture (qui relit quoi)

Équipe à deux personnes : **Sacha Don** et **Clément Welsch**.

- Toute PR vers `develop` est relue et approuvée par **l'autre collaborateur** (pas d'auto-merge sans relecture croisée), même sur un petit projet de TP — l'objectif est de repérer les erreurs de raisonnement/calcul sur les données avant intégration.
- L'auteur de la PR ne merge pas sa propre PR : c'est le relecteur qui merge après validation.
- `main` n'est mis à jour qu'à partir de `develop`, une fois le TP ou la partie concernée validée par les deux, jamais via une PR de branche de travail directement.
- En cas de désaccord sur une méthode (ex. choix d'un seuil, format de donnée), la discussion se fait dans les commentaires de la PR, et le choix retenu est documenté dans `docs/journal.md`.

## Documentation

- Tout choix technique structurant (format de données, seuils, méthode de nettoyage...) est justifié dans [docs/journal.md](docs/journal.md), pas seulement dans le code ou la PR.
