# TP 13 — Pipeline bout-en-bout · mar 14/10 (C. Ringot, journée)

> Module : 3.5 — Pipelines & services data cloud, introduction
> Durée : une journée (9h00 – 17h30), en équipe fil rouge, dans le dépôt Git de l'équipe
> Difficulté : 4 / 5
> Type : TP fil rouge, **jalon J3** — livrable évalué, tag `v0.3`

**Objectif : une commande unique du CSV brut aux données prêtes pour le ML. Jalon J3.**

1. Assembler tous les morceaux (chargement, nettoyage, base, Parquet, exports ML) en un pipeline orchestré : `Makefile` ou CLI `python -m nutriscope.pipeline`.
2. Chaque étape est relançable seule ; les sorties sont datées et reproductibles (graines fixées).
3. Figer les jeux d'entraînement/test de la phase 4 : split documenté, stratifié sur le Nutri-Score, gelé dans `data/exports/` (hors Git, mais régénérable).
4. Test grandeur nature : chaque équipe clone le dépôt d'une autre sur une machine vierge et déroule son README. Ce qui casse est corrigé dans la journée.
5. Rédaction de `docs/data/pipeline.md` : schéma du flux, commandes, durées.

**À committer** : pipeline fonctionnel + doc + tag `v0.3`. **Jalon J3 atteint.**

Données : © Open Food Facts contributors — ODbL (à rappeler dans chaque fichier produit).

## Mise en situation

Depuis le 24 septembre, votre dépôt s'est enrichi par couches : un nettoyage
testé (TP 9), une base chargée par script (TP 4), un notebook d'exploration
(TP 10), une conversion Parquet et un export features (TP 12). Chaque brique
fonctionne. Mais aujourd'hui, pour obtenir des données prêtes, un membre de
l'équipe doit se souvenir de l'ordre, des options, des chemins — et personne
d'autre ne sait le faire.

C'est exactement la situation que la direction de NutriScope refuse
d'emporter en phase 4. À partir du 20 octobre, quatre modules de machine
learning vont consommer vos données pendant cinq mois. Si le jeu
d'entraînement change en silence entre deux séances, aucune comparaison de
modèles ne vaudra plus rien.

Ce qu'on vient chercher aujourd'hui tient en une phrase :
**quelqu'un qui n'a jamais vu votre dépôt doit pouvoir cloner, taper une
commande, et obtenir les mêmes fichiers que vous.** Le point 4 n'est pas une
formalité : une autre équipe va vraiment dérouler votre README sur sa machine,
devant vous, et ce qui casse se corrige avant 17 heures.

C'est le jalon J3. Le module 3.5 vous a donné le vocabulaire (idempotence,
sorties datées, `_SUCCESS`, export figé) et la démo 3.5.2 vous a montré les
trois façons d'orchestrer le même flux — Airflow, Prefect, et le `Makefile`.
Pour un pipeline qui tourne en moins d'une minute, c'est le troisième qui
gagne, et le module vous a dit pourquoi.

## Ce que vous aurez à la fin

- une commande unique (`make pipeline` ou `python -m nutriscope.pipeline all`)
  qui va du CSV brut aux exports, sur une machine où rien n'a été préparé ;
- cinq étapes lançables séparément, chacune idempotente et datée ;
- `data/exports/features_<date>.parquet` avec sa colonne `split` figée,
  stratifiée sur le Nutri-Score, et son `schema.json` ;
- un journal des durées, exploité dans la documentation ;
- `docs/data/pipeline.md` : schéma du flux, commandes, durées mesurées ;
- un `README.md` qui a résisté au test d'une autre équipe ;
- des tests pytest verts sur l'échantillon (au moins douze) ;
- le tag `v0.3` posé sur un dépôt propre.

## Prérequis

- **TP 4** : votre schéma relationnel et le script qui charge la base
- **TP 9** : `src/cleaning.py` — une règle = une fonction pure testée, avec son compte rendu
- **TP 12** : `convert_parquet.py`, `export_features.py`, `schema.json`, `docs/architecture.md`
- Le `venv` d'équipe (`pandas`, `duckdb`, `pyarrow`, `pytest`) et un `requirements.txt` à jour
- Le jeu partagé `supports/data-nutriscope/` : l'échantillon pour les tests, l'extrait pour les mesures
- Git : le dépôt d'équipe à jour, et de quoi poser un tag

Si l'une de ces briques n'est pas au niveau, ne la réécrivez pas ce matin :
branchez-la telle quelle et notez la dette dans le journal. Le TP 13 assemble,
il ne refait pas les TP précédents.

## Les cinq étapes du pipeline

Pour que les pipelines des équipes restent comparables, on fixe ici les cinq
étapes et leurs noms. Le reste (langage de la CLI, structure des dossiers,
options) vous appartient.

| Étape          | Entrée                | Sortie                                  | Ce qu'elle garantit                          |
| -------------- | --------------------- | --------------------------------------- | -------------------------------------------- |
| `charger`      | CSV ou Parquet source | données brutes figées + manifeste       | code-barres en texte, empreinte de la source |
| `nettoyer`     | brut                  | nettoyé + rapport + journal des règles  | les règles du TP 9, dans l'ordre, tracées    |
| `charger_base` | nettoyé               | base relationnelle + contrôles          | rechargement complet, jamais de doublon      |
| `parquet`      | nettoyé               | Parquet partitionné par rayon + schéma  | types posés, pas de partition orpheline      |
| `exports`      | Parquet               | features datées + `schema.json` + split | export figé, split stratifié, graine fixée   |

`charger_base` et `parquet` partent **tous les deux du même nettoyé** : c'est
la règle de la source de vérité unique posée au TP 12. Si votre base et vos
Parquet ne comptent pas le même nombre de produits, c'est la chaîne qui est
fausse, pas le rapport.

## Étapes

### Étape 1 — Assembler les morceaux en une commande

1. Créez le point d'entrée : un package `nutriscope/` avec `pipeline.py`
   exposant `python -m nutriscope.pipeline [étape|all]`, ou un `Makefile` avec
   une cible par étape plus `pipeline`. Si vous faites les deux, le `Makefile`
   n'est qu'une façade sur la CLI : la logique ne vit qu'à un endroit.
2. Écrivez une fonction par étape, avec la même signature, qui retourne ce
   qu'elle a produit (durée, lignes, fichiers écrits). Le corps appelle vos
   modules existants : ne recopiez pas la logique du TP 9 ou du TP 12,
   **importez-la** (ou copiez le module entier en le citant, si l'import
   traverse des dossiers instables).
3. Décidez où vont les sorties (`data/raw/`, `data/clean/`, `data/db/`,
   `data/parquet/`, `data/exports/`) et mettez **tout `data/` dans
   `.gitignore`**. Le dépôt contient le code qui produit les données, jamais
   les données.
4. Résolvez le chemin de la source par rapport au fichier, pas par rapport au
   dossier courant, et acceptez une variable d'environnement qui l'écrase
   (comme au TP 12). Un pipeline qui ne marche que lancé depuis la racine n'est
   pas un pipeline.

**Point de contrôle 1** : dans un dossier vide de sorties, `make pipeline` (ou
`python -m nutriscope.pipeline all`) enchaîne les cinq étapes et affiche pour
chacune le nombre de lignes traitées. Les comptages de la base et du Parquet
sont identiques.

### Étape 2 — Rendre chaque étape relançable seule et idempotente

1. **Datez toutes les sorties** : `produits_propres_<AAAAMMJJ>.parquet`,
   `features_<AAAAMMJJ>.parquet`. Deux exécutions à deux dates cohabitent ;
   deux exécutions le même jour produisent le même fichier.
2. **Chaque étape résout son entrée elle-même** : elle cherche la sortie datée
   du jour, puis la plus récente du même type, et si elle ne trouve rien, elle
   échoue avec un message qui dit _quelle étape lancer avant_. Une trace Python
   brute n'est pas un message d'erreur.
3. **Idempotence** : relancée le même jour sur les mêmes données, une étape
   réécrit les mêmes octets. Cela suppose de trier avant d'écrire (`ORDER BY`),
   de fixer les graines, et de ne pas glisser d'horodatage dans le fichier de
   données lui-même (il va dans le manifeste, à côté).
4. **Pas de sortie à moitié écrite** : un dossier partitionné reçoit un
   marqueur `_SUCCESS` écrit _en dernier_, et une étape qui lit ce dossier
   vérifie le marqueur. Un dossier sans marqueur est un dossier incomplet.
5. **Un journal des durées** : une ligne par étape terminée (JSON Lines,
   CSV, peu importe) avec l'horodatage, l'étape, la durée, le statut, les
   lignes traitées. Les échecs y figurent aussi, sinon le journal ment.

**Point de contrôle 2** : vous effacez `data/exports/`, vous lancez la seule
étape `exports`, elle retrouve le Parquet de la veille et travaille. Vous
relancez `parquet` deux fois de suite : le second passage ne change aucun
fichier (comparez les empreintes).

### Étape 3 — Figer le split train / test de la phase 4

C'est le point que la phase 4 utilisera le plus, et celui qui se répare le
moins bien après coup.

1. Ajoutez à l'export features une colonne `split` valant `train` ou `test`,
   **stratifiée sur `nutriscore_grade`** : chaque grade doit avoir la même
   part de test (20 % est un choix raisonnable ; justifiez le vôtre).
   Pourquoi stratifier : les grades a et b sont minoritaires ; un tirage
   purement aléatoire peut laisser une classe presque vide dans le test, et
   toutes vos métriques de classification deviendraient instables.
2. **Graine fixée à 42**, écrite dans le code _et_ dans le schéma. Vérifiez
   que deux exécutions donnent la même affectation **produit par produit**,
   pas seulement les mêmes effectifs.
3. Le fichier est **figé** : il refuse de s'écraser sans une option explicite
   (`--force`). Un jeu d'entraînement qui change en silence invalide toutes
   les comparaisons de modèles de la phase 4.
4. Complétez `schema.json` : méthode du split, graine, part de test, effectifs
   train et test **par grade**, SHA-256 du fichier, commit Git, filtres
   appliqués, et la règle d'usage écrite noir sur blanc — _`fit` sur le train
   seulement ; le test n'est regardé qu'une fois, à la fin ; la validation
   croisée se fait à l'intérieur du train._
5. Tout cela vit dans `data/exports/`, **hors Git mais régénérable** : la
   commande et la graine sont dans le dépôt, le fichier non.

**Point de contrôle 3** : un petit script (ou un test) montre la part de test
par grade — cinq valeurs autour de 20 % — et prouve que relancer avec
`--force` redonne la même empreinte SHA-256.

### Étape 4 — Le test « machine vierge » par une autre équipe

Le TP est co-évalué : à 14h30, les équipes échangent leurs dépôts.

1. **Avant l'échange**, écrivez le `README.md` comme si vous ne connaissiez
   rien au projet : version de Python, création du `venv`, installation des
   dépendances, où placer les données (ou quelle variable définir), la
   commande, la sortie attendue, et comment vérifier que ça a marché. Pas de
   « il suffit de », pas d'étape implicite.
2. **Testez-le vous-même d'abord**, dans un clone frais et un `venv` neuf :
   `git clone` dans `/tmp`, nouvel environnement, `pip install -r
requirements.txt`, la commande. Les trois pannes classiques sortent ici :
   une dépendance jamais déclarée, un chemin absolu d'un poste, un fichier de
   données qu'on croyait versionné.
3. **Échangez** : vous déroulez le README de l'autre équipe sans lui parler,
   en notant chaque endroit où vous avez dû deviner. Rendez-lui une liste
   écrite, pas des commentaires à l'oral.
4. **Corrigez dans la journée** ce qui a cassé chez vous, et committez la
   correction. C'est la partie du TP qui compte le plus : un pipeline qui ne
   tourne que sur le portable de celui qui l'a écrit n'est pas un livrable.

**Point de contrôle 4** : une autre équipe a obtenu vos fichiers de sortie sur
sa machine, et vos corrections sont committées avec un message qui dit ce qui
manquait.

### Étape 5 — `docs/data/pipeline.md`

Le document que lira toute la phase 4. Trois sections au minimum :

1. **Le schéma du flux** : en texte (un bloc de caractères suffit et se
   versionne bien), de la source aux exports, avec les artefacts intermédiaires
   et, pour chacun, qui le lit. Faites apparaître que la base sert
   l'application et que le Parquet sert l'analyse et le ML — c'est la reprise
   de `docs/architecture.md` du TP 12.
2. **Les commandes** : la commande unique, chaque étape seule, l'option pour
   l'extrait complet, l'option pour rejouer une date, la commande de test, et
   ce qu'on fait quand tout est cassé (`clean` puis relance).
3. **Les durées réelles** : un tableau étape par étape, sur l'échantillon
   **et** sur l'extrait complet, avec la machine et les versions. Ce sont les
   durées de votre journal, pas des estimations. Ajoutez deux ou trois phrases
   de lecture : quelle étape domine, pourquoi, et ce que cela implique
   (par exemple : faut-il un orchestrateur ?).

Ajoutez la section « ce que la phase 4 lira » : le nom du fichier d'export,
son schéma, et les interdits (ne pas recalculer le split, ne pas utiliser
`nutriscore_score` pour prédire le grade, ne pas utiliser `code`,
`product_name` ou `brands` comme features).

**Point de contrôle 5** : un formateur lit le document en cinq minutes et sait
relancer votre pipeline sans vous poser de question.

### Étape 6 — Tests, propreté, tag `v0.3`

1. Au moins **douze tests** pytest, sur l'échantillon uniquement, dans des
   dossiers temporaires : chaque étape produit ce qu'elle annonce ; une étape
   relancée ne change rien ; une étape lancée sans son entrée échoue avec un
   message utile ; le split est stratifié, reproductible et figé ; le schéma
   décrit exactement le fichier écrit.
2. Vérifiez le dépôt : `data/` ignoré, `requirements.txt` épinglé, aucun chemin
   absolu, crédit ODbL dans les fichiers produits, journal `docs/journal.md` à
   jour.
3. Committez, puis posez le tag :

```bash
git add -A && git commit -m "TP 13 : pipeline bout-en-bout, split figé, doc (jalon J3)"
git tag -a v0.3 -m "Jalon J3 : pipeline bout-en-bout"
git push && git push --tags
```

**Point de contrôle 6** : `python -m pytest -q` est vert, `git tag` montre
`v0.3`, et un `git status` ne montre aucun fichier de données.

## Conseils

- Faites tourner le pipeline sur l'**échantillon** toute la journée ; ne
  passez à l'extrait complet que pour le tableau des durées, en fin de matinée,
  pendant que vous écrivez la documentation.
- L'idempotence se perd toujours au même endroit : un horodatage écrit dans le
  fichier de données, ou un `GROUP BY` sans `ORDER BY` avant l'écriture.
  Mettez l'horodatage dans le manifeste, à côté.
- Ne construisez pas d'orchestrateur. Airflow au jalon J3 pour un flux de
  vingt secondes, c'est une semaine de travail pour un problème que vous
  n'avez pas — et le module vous a montré à quel moment il devient justifié.
- Écrivez le `README.md` **avant** midi, pas à 16h30 : c'est lui qui est
  évalué par une autre équipe, et c'est le seul livrable que vous ne pouvez
  pas corriger après coup.
- Le split est le seul point du TP qu'on ne peut pas rattraper au TP 14 : si
  votre graine bouge entre deux séances, tous les résultats de la phase 4
  deviennent incomparables.
- Une étape qui échoue doit le dire dans le journal. Un pipeline silencieux qui
  s'arrête au milieu est pire qu'un pipeline qui plante bruyamment.

## Dépannage

| Symptôme                                                                      | Cause probable                                           | Correction                                                                        |
| ----------------------------------------------------------------------------- | -------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `ModuleNotFoundError: nutriscope`                                             | lancé depuis le mauvais dossier, ou pas de `__init__.py` | lancer depuis la racine du package, vérifier `__init__.py`, ou `pip install -e .` |
| Le pipeline marche chez vous, pas chez l'autre équipe                         | chemin absolu, ou dépendance installée « à la main »     | résoudre les chemins par rapport au fichier, compléter `requirements.txt`         |
| La seconde exécution d'une étape change le fichier                            | horodatage dans les données, ou tri non déterministe     | `ORDER BY` avant écriture, horodatage dans le manifeste                           |
| `exports` ne trouve pas le Parquet alors qu'il existe                         | dossier écrit par une exécution interrompue              | vérifier `_SUCCESS`, relancer `parquet`                                           |
| `FileExistsError` sur l'export                                                | comportement voulu : l'export est figé                   | changer de date, ou `--force` en l'assumant                                       |
| Une classe (grade a) presque absente du test                                  | split aléatoire non stratifié                            | stratifier par grade, vérifier la part par classe                                 |
| Deux exécutions donnent des effectifs identiques mais des produits différents | graine non fixée, ou hasard global partagé               | un générateur local par groupe, graine explicite                                  |
| Les comptages base ≠ Parquet                                                  | les deux étapes ne partent pas du même nettoyé           | résoudre l'entrée depuis `clean/`, pas depuis une ancienne sortie                 |
| `git status` montre des Parquet                                               | `data/` non ignoré, ou fichiers déjà suivis              | `.gitignore` puis `git rm --cached -r data/`                                      |
| Le pipeline sur l'extrait sature la mémoire                                   | tout chargé en pandas d'un coup                          | lire par DuckDB, ou seulement les colonnes utiles                                 |
| `pytest` dure plusieurs minutes                                               | tests sur l'extrait complet                              | fixtures sur l'échantillon, pipeline exécuté une fois par session                 |

## Grille d'évaluation

| Critère                                                                      | Points | Observable                                                                 |
| ---------------------------------------------------------------------------- | ------ | -------------------------------------------------------------------------- |
| Une commande unique enchaîne les cinq étapes, du brut aux exports            | 4      | `make pipeline` ou `python -m nutriscope.pipeline all` sur un dossier vide |
| Chaque étape est lançable seule, idempotente, à sorties datées               | 4      | relance isolée d'`exports`, double exécution sans changement, noms datés   |
| Split train / test stratifié sur le grade, graine fixée, figé et documenté   | 4      | colonne `split`, part par grade, `schema.json`, refus de réécriture        |
| Test machine vierge réussi par une autre équipe, corrections committées      | 3      | `README.md`, retours écrits de l'autre équipe, commits du jour             |
| `docs/data/pipeline.md` : flux, commandes, durées réelles mesurées           | 3      | le document, le journal des durées                                         |
| Tests (≥ 12) verts, dépôt propre (données hors Git), crédit ODbL, tag `v0.3` | 2      | `python -m pytest -q`, `.gitignore`, `git tag`                             |
| **Total**                                                                    | **20** |                                                                            |

Bonus (hors barème) : une cible `make extrait` qui mesure le flux complet sur
l'extrait France ; un test qui compare les empreintes SHA-256 de deux
exécutions ; la reprise automatique d'un pipeline interrompu.

## Ce que la phase 4 utilisera (à partir du 20/10)

- **`data/exports/features_<date>.parquet` et sa colonne `split`** : le TP 14
  (« Prédire le Nutri-Score », lun 20/10) lit ce fichier et ce split. Il ne
  recalcule rien : c'est ce qui rend les résultats des TP 14, 15 et 16
  comparables entre eux et entre équipes.
- **`schema.json`** : types, unités, taux de manquants et politique
  d'imputation prévue par colonne — le pipeline scikit-learn du TP 14 s'écrit
  en le lisant.
- **La commande unique** : quand une règle de nettoyage changera en novembre,
  vous régénérerez tout — avec une nouvelle date, sans écraser l'ancien export
  — et vous saurez dire quel modèle a été entraîné sur quelles données.
- **Le journal des durées** : il vous dira s'il faut industrialiser davantage
  (orchestrateur, phase 6-7) ou si un `Makefile` suffit encore.

## Solution de référence

L'implémentation de référence du formateur, remise après le TP, est autonome :
elle tourne sur le jeu partagé, sans réseau, et embarque les règles du TP 9
copiées telles quelles. Elle ne remplace pas votre pipeline — elle montre une
façon de tenir les cinq points. À consulter après votre propre tentative.
