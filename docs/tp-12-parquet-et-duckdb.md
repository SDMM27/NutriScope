# TP 12 — Parquet & DuckDB · mer 08/10 (C. Ringot, ½ j après 3.5)

> Module : 3.5 — Pipelines & services data cloud, introduction
> Durée : ½ journée (13h30 – 17h30), en équipe fil rouge, dans le dépôt Git de l'équipe
> Difficulté : 3 / 5
> Type : TP fil rouge, code exécuté, mesures réelles, documentation versionnée

**Objectif : basculer le stockage analytique et mesurer ce qu'on y gagne.**

1. Convertir les données nettoyées en Parquet, partitionnées par rayon ; choisir et justifier les types.
2. Rejouer les cinq requêtes de contrôle du TP 4 en DuckDB directement sur les Parquet.
3. Benchmark honnête : temps et mémoire CSV vs base relationnelle vs Parquet/DuckDB sur trois requêtes types.
4. Clarifier l'architecture cible dans `docs/architecture.md` : la base relationnelle sert l'application, les Parquet servent l'analyse et le ML — qui lit quoi.
5. Préparer les exports d'entraînement pour la phase 4 : un Parquet « features » propre, figé, daté.

**À committer** : scripts de conversion + benchmark chiffré + `docs/architecture.md` mis à jour.

Données : © Open Food Facts contributors — ODbL (à rappeler dans chaque fichier produit).

## Mise en situation

Le 14 octobre, la direction de NutriScope attend une commande unique du CSV brut aux données prêtes pour le machine learning (TP 13, jalon J3). Aujourd'hui, votre dépôt a un nettoyage testé (`src/cleaning.py`, TP 9), une base relationnelle chargée par script (TP 4) et un notebook d'EDA (TP 10). Il lui manque le stockage sur lequel l'analyse et les modèles vont s'appuyer pendant cinq mois : des fichiers Parquet typés, partitionnés, lus par DuckDB, et un premier export d'entraînement que le TP 14 (20/10) lira sans discussion. Christophe Ringot joue le client : il veut des chiffres (pas des impressions) et un document d'architecture qu'un nouveau membre de l'équipe comprend en cinq minutes.

Le module 3.5 vous a donné les outils : la démo 3.5.1 (conversion, métadonnées, requêtes, élagage), l'exercice 3.5.1 (requêtes DuckDB : agrégat, fenêtre, jointure), l'exercice 3.5.2 (partitionnement, types, mesures), la méthode du benchmark honnête (slide 19), et la définition d'un export figé (slide 20).

## Ce que vous aurez à la fin

- `src/storage/convert_parquet.py` (ou équivalent) : données nettoyées → `data/parquet/produits/rayon=<slug>/…`, types posés, schéma écrit ;
- `sql/controles.sql` + `src/storage/run_queries.py` : les cinq requêtes de contrôle rejouées en DuckDB, résultats dans `docs/data/controle.md` ;
- `src/storage/benchmark.py` + `docs/data/benchmark.md` : trois requêtes, trois moteurs, temps et mémoire, sur l'extrait complet ;
- `docs/architecture.md` mis à jour : qui lit quoi ;
- `src/storage/export_features.py` : `data/exports/features_nutriscore_<AAAAMMJJ>.parquet` + `schema.json` ;
- au moins dix tests pytest sur ces scripts, verts sur l'échantillon.

## Prérequis

- Le dépôt d'équipe à jour : `src/cleaning.py` du TP 9 opérationnel, la base du TP 4 rechargeable, l'extrait France dans `data/raw/` (hors Git)
- `venv` de l'équipe avec `duckdb`, `pyarrow`, `pandas`, `pytest` (versions du `requirements.txt` du module)
- Le jeu partagé `supports/data-nutriscope/` pour les tests (échantillon) et les mesures (extrait)
- Décision d'équipe prise au TP 2 : le périmètre de rayons ; vos rayons cibles seront les partitions les plus consultées

## Les cinq requêtes de contrôle

Le point 2 renvoie aux « cinq requêtes de contrôle du TP 4 ». Chaque équipe a écrit les siennes ; pour que le TP soit comparable entre équipes, on fixe ici ce qu'elles doivent couvrir. Reprenez vos requêtes si elles y répondent, complétez-les sinon :

| # | Contrôle | Ce qu'elle renvoie | Ce qu'on attend après le TP 9 |
|---|---|---|---|
| 1 | **Comptage par rayon** | une ligne par rayon : nombre de produits, part en % | la somme égale la volumétrie totale ; une partition = une ligne |
| 2 | **Complétude** | par rayon : % de Nutri-Score renseigné (a-e), % avec les sept nutriments clés présents, % avec catégories | des taux cohérents avec l'EDA du TP 10 |
| 3 | **Doublons** | codes-barres en double (groupes, lignes en trop) ; couples nom + marque répétés | **0** code en double ; les couples répétés sont une information, pas une erreur |
| 4 | **Bornes et cohérences** | nutriments hors [0, 100] ; énergie hors [0, 900] kcal ; sucres > glucides ; saturés > lipides ; sel ≠ sodium × 2,5 ; énergie nulle avec macronutriments | **0** hors bornes ; les cohérences restantes sont listées, pas cachées |
| 5 | **Distribution du Nutri-Score** | par grade (a-e, unknown, not-applicable, null) : produits, part, score moyen | les cinq grades présents ; la part « unknown » connue |

Les sept nutriments clés : `energy-kcal_100g`, `fat_100g`, `saturated-fat_100g`, `carbohydrates_100g`, `sugars_100g`, `proteins_100g`, `salt_100g`.

## Étapes

### Étape 1 — Brancher la conversion sur vos données nettoyées 

1. Écrivez `convert_parquet.py` : lecture de la sortie de `src/cleaning.py` (un Parquet ou un CSV nettoyé ; à défaut, appliquez le nettoyage à la volée en appelant vos fonctions du TP 9), ajout d'une colonne `rayon` = slug de `pnns_groups_1` (`unknown` si vide), `COPY ... TO ... (FORMAT PARQUET, PARTITION_BY (rayon), COMPRESSION ZSTD, OVERWRITE_OR_IGNORE)`.
2. Posez les types dans le `SELECT` : `code` en texte, nutriments en `FLOAT`, `additives_n` et `nutriscore_score` en `SMALLINT`, `nova_group` en `TINYINT`, `created_t` et `last_modified_t` en `TIMESTAMP` ; ou d'autres, si vous les justifiez.
3. Écrivez `schema_produits.json` à côté du dossier : une entrée par colonne avec le type et une justification d'une ligne ; la clé de partition ; la compression ; le nombre de lignes ; la licence.
4. Supprimez le dossier cible avant d'écrire : la conversion doit être rejouable sans partition orpheline.

Point de contrôle 1 : `ls data/parquet/produits/` montre un dossier `rayon=…` par rayon (une douzaine) ; `SELECT count(*) FROM read_parquet('data/parquet/produits/**/*.parquet', hive_partitioning = true)` égale le nombre de lignes nettoyées ; un `code` commençant par `0` a gardé son zéro.

### Étape 2 — Rejouer les cinq contrôles sur les Parquet 

1. Mettez les cinq requêtes dans un seul fichier SQL, chacune précédée d'un marqueur (`-- @nom: comptage_par_rayon`), écrites contre une vue `produits`.
2. `run_queries.py` crée la vue sur le jeu partitionné, découpe le fichier sur les marqueurs, exécute chaque requête, écrit un Markdown (`docs/data/controle.md`) avec un tableau par contrôle.
3. Comparez avec les mêmes contrôles sur votre base du TP 4 : les comptages doivent coïncider. S'ils diffèrent, c'est que la base et le Parquet ne partent pas du même nettoyé ; corrigez la chaîne, pas le rapport.

Point de contrôle 2 : `docs/data/controle.md` contient cinq tableaux ; « codes en double » vaut 0 ; « nutriment hors [0, 100] » vaut 0.

### Étape 3 — Le benchmark honnête

1. Trois requêtes types, écrites pour les trois moteurs : un **agrégat par rayon** (comptage, moyennes), un **filtre et tri** (par exemple les 20 céréales du petit-déjeuner notées les plus sucrées), un **agrégat à forte cardinalité** (complétude du Nutri-Score par marque, top 20). Choisissez des requêtes que votre EDA fait vraiment.
2. Les trois moteurs : **pandas sur le CSV** nettoyé (lecture comprise dans le temps), **la base relationnelle** (votre SQLite ou PostgreSQL du TP 4, sans index ajouté pour l'occasion, ou construite par le script à partir du nettoyé), **DuckDB sur le Parquet partitionné**. Bonus : DuckDB sur le CSV, pour séparer l'effet du moteur de celui du format.
3. La méthode : chaque mesure dans un **sous-processus neuf** (`subprocess.run([sys.executable, "benchmark.py", "--une", moteur, requete])`) ; temps = lecture + requête ; mémoire = pic RSS du processus (`resource.getrusage(RUSAGE_SELF).ru_maxrss` : octets sur macOS, kilo-octets sur Linux) ; trois répétitions, médiane des temps, maximum des pics ; mesure de référence « imports seulement » pour connaître le poids de l'interpréteur.
4. Vérifiez avant de chronométrer que les trois moteurs renvoient le **même nombre de lignes** et les mêmes premières valeurs.
5. Exécutez sur l'échantillon (pour les tests) puis sur l'**extrait complet** (pour le rapport) ; écrivez `docs/data/benchmark.md` : machine, versions, coût de construction de chaque support, tableau requête × moteur × temps × mémoire, trois phrases de lecture.

Point de contrôle 3 : le tableau de l'extrait montre trois ordres de grandeur entre pandas sur CSV et DuckDB sur Parquet pour l'agrégat par rayon ; les pics mémoire sont cohérents (plusieurs Go pour pandas, une centaine de Mo pour DuckDB) ; le rapport indique ce que « honnête » veut dire.

### Étape 4 — `docs/architecture.md` 

Écrivez ou mettez à jour le document avec : un tableau des magasins de données (brut, nettoyé, base, Parquet, exports : contenu, producteur, format, emplacement, dans Git ou non) ; un tableau « qui lit quoi » (API, notebooks d'EDA, entraînement, contrôles, assistant : ce qu'ils lisent, pourquoi, ce qu'ils ne lisent pas) ; cinq règles (source de vérité unique, données hors Git, Parquet reconstruit à chaque exécution, export non réécrit, partition par rayon seulement, avec le paragraphe de l'exercice 3.5.2) ; un schéma du flux en texte ; ce qui change en phase 6-7 (stockage objet, base managée).

Point de contrôle 4 : un membre d'une autre équipe lit le document en cinq minutes et sait dire où l'API lira un produit et où le TP 14 lira ses features.

### Étape 5 — L'export d'entraînement figé 

1. `export_features.py` lit le Parquet partitionné, filtre les produits **utilisables** pour prédire le Nutri-Score : grade a-e, sept nutriments clés présents, cohérences respectées (sucres ≤ glucides, saturés ≤ lipides, énergie > 0), et écrit les colonnes : identifiant `code`, `rayon`, nutriments, `additives_n`, `nova_group`, deux ou trois ratios (part des sucres dans les glucides, part des saturés dans les lipides, part de l'énergie venant des lipides), `nutriscore_score`, et la cible `nutriscore_grade`.
2. Le fichier s'appelle `features_nutriscore_<AAAAMMJJ>.parquet` et **refuse d'écraser** un fichier existant (option `--force` pour forcer).
3. `schema.json` à côté : nom, date de gel, source, commit Git, nombre de lignes, SHA-256 du fichier, cible, identifiant, filtres appliqués, répartition de la cible, une entrée par colonne (type, unité, description, % de manquants, politique de manquants prévue pour le TP 14), licence, usage prévu.
4. Le split train / test n'est **pas** fait ici : c'est le TP 13, avec une graine et une stratification sur la cible.

Point de contrôle 5 : `schema.json` liste les mêmes colonnes que le Parquet, dans le même ordre ; la cible n'a aucun manquant ; relancer le script sans `--force` échoue ; relancer avec `--force` produit la même empreinte SHA-256 (export reproductible).

### Étape 6 — Tests et commit 

Au moins dix tests pytest sur l'échantillon partagé (jamais sur l'extrait) : la conversion crée une partition par rayon et conserve toutes les lignes ; les types sont ceux du schéma ; les zéros de tête survivent ; la conversion est rejouable sans fichier orphelin ; les cinq requêtes se lisent depuis le SQL et s'exécutent ; le comptage par rayon totalise le jeu ; zéro doublon et zéro hors-borne ; les trois moteurs rendent le même nombre de lignes ; l'export est daté, décrit, sans manquant sur la cible, et refuse de s'écraser.

Commit final : scripts, SQL, `docs/data/controle.md`, `docs/data/benchmark.md`, `docs/architecture.md`, `schema.json`, tests. Les Parquet et la base restent hors Git (`.gitignore`), le journal prend ses trois lignes.

## Conseils

- Posez `types={'code': 'VARCHAR'}` (DuckDB) ou `dtype={'code': 'string'}` (pandas) à chaque lecture de CSV : un code-barres n'est pas un nombre.
- `COPY ... PARTITION_BY` ne crée pas les dossiers parents : `mkdir(parents=True)` avant.
- Le benchmark sur l'extrait prend deux à trois minutes ; lancez-le pendant que vous écrivez `docs/architecture.md`.
- Ne vous battez pas pour « gagner » le benchmark : si votre base PostgreSQL bat DuckDB sur le filtre et tri grâce à un index, écrivez-le ; c'est exactement ce que le document d'architecture doit dire (accès par clé → base ; balayage → Parquet).
- Les valeurs qui restent aberrantes après votre nettoyage (un sel à 588 g/100 g) apparaissent dans le contrôle 4 : elles retournent au TP 9 sous forme de règle, pas au TP 12 sous forme de filtre.

## Dépannage

| Symptôme | Cause probable | Correction |
|---|---|---|
| `IO Error: Failed to create directory` | dossier parent absent | `Path(...).parent.mkdir(parents=True, exist_ok=True)` |
| `Binder Error: Cannot mix values of type VARCHAR and INTEGER_LITERAL` | une colonne numérique lue en texte (colonne vide dans un CSV) | `types={...}` explicites à la lecture |
| La partition `rayon=unknown` manque ou une partition `rayon=` vide apparaît | `pnns_groups_1` NULL ou chaîne vide non traité | `coalesce(nullif(pnns_groups_1, ''), 'unknown')` avant le slug |
| Les comptages Parquet ≠ base | base chargée depuis une autre version du nettoyé | rejouer le chargement de la base depuis le même fichier |
| Temps de benchmark identiques d'un moteur à l'autre | mesures dans le même processus, caches partagés | sous-processus neuf par mesure |
| `ru_maxrss` énorme ou minuscule | unité différente selon l'OS | octets sur macOS, Ko sur Linux : normaliser |
| pandas lit l'extrait en 4 Go et échoue | machine à 8 Go | passer `low_memory=False` ne suffit pas : lire seulement les colonnes utiles (`usecols`), et le dire dans le rapport |
| `FileExistsError` au second export | comportement voulu | changer la date ou `--force` |
| `pytest` lent | tests sur l'extrait | fixtures sur l'échantillon, `scope="session"` pour la conversion |

## Grille d'évaluation

| Critère | Points | Observable |
|---|---|---|
| Conversion rejouable, partition par rayon, types posés et justifiés dans un schéma écrit | 4 | `convert_parquet.py`, `schema_produits.json`, dossier `rayon=*` |
| Les cinq contrôles rejoués en DuckDB, résultats versionnés, cohérents avec la base | 3 | `sql/controles.sql`, `docs/data/controle.md` |
| Benchmark : trois requêtes, trois moteurs, méthode honnête expliquée, mesures sur l'extrait | 4 | `benchmark.py`, `docs/data/benchmark.md` |
| `docs/architecture.md` : magasins, qui lit quoi, règles, évolution phase 6-7 | 3 | le document, relu par une autre équipe |
| Export features figé, daté, avec `schema.json` complet, non réécrit sans `--force` | 3 | `export_features.py`, `schema.json`, le fichier daté |
| Tests (≥ 10) verts sur l'échantillon, dépôt propre (données hors Git), crédit ODbL | 3 | `python -m pytest -q`, `.gitignore`, en-têtes |
| **Total** | **20** | |

Bonus (hors barème) : DuckDB sur CSV dans le benchmark ; mesure avec et sans partition ; `EXPLAIN` d'une requête filtrée par rayon dans le rapport.

## Ce qui sera repris au TP 13 (mar 14/10, journée, jalon J3)

- Vos trois scripts deviennent trois cibles du `Makefile` (ou trois sous-commandes de `python -m nutriscope.pipeline`), après `nettoyer` et `charger_base`.
- `docs/architecture.md` est la première page de `docs/data/pipeline.md`.
- L'export features reçoit son split train / test stratifié, gelé dans `data/exports/` avec sa graine.
- Le benchmark ne se rejoue pas : il est cité.

