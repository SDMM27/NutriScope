# Pipeline TP13

## Flux et artefacts

```text
Parquet Open Food Facts
  -> charger       raw/produits_bruts_<date>.parquet + manifeste SHA-256
  -> nettoyer      clean/produits_propres_<date>.parquet + rapport et journal des règles
       |-> charger_base  PostgreSQL, lu par l'application
       -> parquet       parquet/produits_<date>/, lu par DuckDB pour l'analyse
            -> exports  exports/features_nutriscore_<date>.parquet + schéma JSON, lus en ML
```

`charger_base` et `parquet` lisent le même nettoyé. Le dossier partitionné contient
un schéma et un marqueur `_SUCCESS`. L'exporteur ignore les dossiers incomplets.
Les fichiers produits vivent hors Git, sous le dossier passé à `--dossier-donnees`.
Données © Open Food Facts contributors, licence [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/).

## Commandes et rejeu

Installe l'environnement et initialise un PostgreSQL de test avec le [README](../../README.md#lancer-le-pipeline-tp13).
Les variables `NUTRISCOPE_DB_HOST`, `NUTRISCOPE_DB_PORT`, `NUTRISCOPE_DB_NAME`,
`NUTRISCOPE_DB_USER` et `NUTRISCOPE_DB_PASSWORD` permettent de cibler cette base.
Les commandes suivantes reprennent la variable PowerShell `$python` du README.

Pour reproduire le petit Parquet utilisé lors des mesures, depuis la racine :

```powershell
@'
import duckdb

duckdb.connect().execute("""
    COPY (
        SELECT * FROM read_parquet('data/food.parquet')
        WHERE list_contains(countries_tags, 'en:france')
        LIMIT 10000
    ) TO 'data/tp13_echantillon.parquet' (FORMAT PARQUET)
""")
'@ | & $python -
```

```powershell
$options = @("--source", "data/tp13_echantillon.parquet", "--dossier-donnees", "data/tp13", "--date", "2026-11-25")
& $python -m nutriscope.pipeline all @options
# Appels isolés, à utiliser pour reprendre une étape.
& $python -m nutriscope.pipeline charger @options
& $python -m nutriscope.pipeline nettoyer @options
& $python -m nutriscope.pipeline charger_base @options
& $python -m nutriscope.pipeline parquet @options
& $python -m nutriscope.pipeline exports @options
# Source complète, dans un dossier de sortie séparé.
& $python -m nutriscope.pipeline all --source data/food.parquet --dossier-donnees data/tp13-complet --date 2026-11-25
& $python -m pytest -q
```

`NUTRISCOPE_SOURCE` peut définir la source par défaut. `--source` reste prioritaire.
Pour rejouer par date, conserve la même source et change `--date` au besoin.
Un instantané brut de contenu différent et un export déjà figé sont protégés contre
l'écrasement. Pour repartir de zéro, choisis un nouveau dossier avec
`--dossier-donnees`. Pour rétablir une base de test vide, initialise le schéma dans
une nouvelle base de test. Utilise le journal `logs/pipeline.jsonl` pour identifier
l'étape en échec. L'horodatage UTC indique quand elle a tourné, tandis que
`date_donnees` détermine les noms des sorties.

## Durées mesurées

Mesures du 25 novembre 2026 issues de `logs/pipeline.jsonl`.
Windows 11 (build 22631), processeur Intel x86-64 avec 16 processeurs logiques visibles,
Python 3.12.16, DuckDB 1.5.5, pandas 3.0.5, PyArrow 25.0.0 et PostgreSQL 17 sous Docker.

| Étape | Échantillon (s) | Lignes | Source complète (s) | Lignes |
|---|---:|---:|---:|---:|
| `charger` | 0,074 | 10 000 | 23,063 | 4 811 891 |
| `nettoyer` | 0,670 | 10 000 | 81,507 | 1 273 539 |
| `charger_base` | 2,746 | 10 000 | 68,907 | 1 273 539 |
| `parquet` | 0,877 | 10 000 | 26,910 | 1 273 539 |
| `exports` | 0,236 | 5 489 | 1,630 | 461 698 |

Le chargement PostgreSQL domine sur l'échantillon. Cette étape inclut la
construction de cinq tables d'import, leur sérialisation et leur insertion dans
PostgreSQL. L'effectif exporté est inférieur car l'export ML filtre les lignes qui
ne satisfont pas ses critères nutritionnels et de grade.
Sur les 7,95 Go de la source complète, le nettoyage domine. Il inclut la projection
France et les règles TP9. Avec le chargement PostgreSQL, il représente environ
les trois quarts du temps mesuré.

## Vérification en clone neuf

Un clone local distinct et un environnement Python 3.12 neuf ont exécuté les
cinq étapes sur l'échantillon de 10 000 lignes avec une base de test dédiée.
La co-évaluation par une autre équipe reste à réaliser. Pour consigner son retour,
noter la version testée, l'environnement, chaque commande dont un prérequis a dû
être deviné et les effectifs observés dans PostgreSQL et le Parquet.

## Ce que la phase 4 lira

- `exports/features_nutriscore_<AAAAMMJJ>.parquet` contient les features, le grade et `split`.
- `exports/features_nutriscore_<AAAAMMJJ>.schema.json` décrit les colonnes, l'empreinte, les filtres et les effectifs par grade et par split.
- Préserve le split stratifié par grade avec la graine 42. Ajuste les transformations sur `train`, fais la validation croisée dans `train` et réserve `test` à l'évaluation finale.
- Exclure `nutriscore_score`, `code`, `product_name` et `brands` des variables explicatives. Le grade est la cible.
