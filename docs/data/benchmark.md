# Benchmark : pandas, SQLite, DuckDB

Données : © Open Food Facts contributors — ODbL 1.0 (https://opendatacommons.org/licenses/odbl/1-0/)

## Machine et versions

- Système : Windows-11-10.0.22631-SP0
- Processeur : Intel64 Family 6 Model 167 Stepping 1, GenuineIntel (8 cœurs physiques, 16 logiques)
- Mémoire vive : 31.7 Go
- Python 3.12.10, pandas 2.3.3, DuckDB 1.5.6
- SQLite 3.49.1, pyarrow 25.0.1

## Jeu mesuré

- 1,273,539 lignes (sortie du nettoyage, TP 9)
- CSV nettoyé : 238.8 Mo
- Parquet partitionné par rayon (ZSTD) : 47.9 Mo
- SQLite sans index : 174.2 Mo

## Coût de construction

| Support | Durée (s) | Remarque |
|---|---:|---|
| CSV nettoyé | 0 | sortie du nettoyage, pas de construction propre |
| SQLite | 9.26 | construit depuis le CSV, sans index |
| Parquet | 1.35 | `convertir` relancé sur une copie temporaire |

## Méthode

- Chaque mesure tourne dans un sous-processus neuf ; 3 répétition(s), médiane des temps, maximum des pics mémoire.
- Temps = lecture + requête, imports exclus ; SQLite : connexion + requête (la base est déjà construite).
- pandas lit le CSV avec `dtype={'code': 'string'}` et `usecols` limité aux colonnes utiles à chaque requête (agrégat : 4 colonnes, filtre et tri : 6, forte cardinalité : 2).
- DuckDB/Parquet lit une vue sur le dossier partitionné ; DuckDB/CSV relit le CSV avec types explicites.
- Pic mémoire : pic de mémoire résidente du processus ; la ligne `imports` donne le poids de l'interpréteur et des bibliothèques seuls.
- Avant de chronométrer, tous les moteurs rendent le même nombre de lignes et la même clé en première ligne.

## Résultats

| Requête | Moteur | Temps médian (s) | Pic mémoire (Mo) |
|---|---|---:|---:|
| agregat_rayon | pandas_csv | 1.835 | 169 |
| agregat_rayon | sqlite | 0.715 | 38 |
| agregat_rayon | duckdb_parquet | 0.031 | 110 |
| agregat_rayon | duckdb_csv | 0.258 | 353 |
| filtre_tri | pandas_csv | 2.448 | 365 |
| filtre_tri | sqlite | 0.169 | 36 |
| filtre_tri | duckdb_parquet | 0.041 | 109 |
| filtre_tri | duckdb_csv | 0.266 | 330 |
| forte_cardinalite | pandas_csv | 1.845 | 147 |
| forte_cardinalite | sqlite | 0.485 | 39 |
| forte_cardinalite | duckdb_parquet | 0.059 | 137 |
| forte_cardinalite | duckdb_csv | 0.275 | 311 |
| (référence) imports | pandas_csv | – | 92 |
| (référence) imports | sqlite | – | 35 |
| (référence) imports | duckdb_parquet | – | 35 |
| (référence) imports | duckdb_csv | – | 35 |

### Ratio pandas_csv / duckdb_parquet

| Requête | Ratio des temps |
|---|---:|
| agregat_rayon | ×59.4 |
| filtre_tri | ×60.0 |
| forte_cardinalite | ×31.1 |

## Élagage de partitions (EXPLAIN DuckDB)

```
WHERE rayon = 'beverages' (12 partitions) :

┌───────────────────────────┐
│    UNGROUPED_AGGREGATE    │
│    ────────────────────   │
│        Aggregates:        │
│        count_star()       │
│          avg(#0)          │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│CAST(sugars_100g AS DOUBLE)│
│                           │
│        ~18,012 rows       │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│        READ_PARQUET       │
│    ────────────────────   │
│         Function:         │
│        READ_PARQUET       │
│                           │
│        Projections:       │
│        sugars_100g        │
│                           │
│       File Filters:       │
│   (rayon = 'beverages')   │
│                           │
│    Scanning Files: 1/12   │
│                           │
│        ~18,012 rows       │
└───────────────────────────┘

```

## Lecture

« Honnête » veut dire : même nettoyé pour tous les moteurs, résultats vérifiés identiques avant chronométrage, lecture comprise dans le temps, sous-processus neuf par mesure, médiane de trois essais, poids des imports affiché à part, et aucun index ajouté pour SQLite.

- **DuckDB sur Parquet est 30 à 60 fois plus rapide que pandas sur CSV** (0,03-0,06 s contre 1,8-2,4 s). On n'atteint pas les trois ordres de grandeur annoncés : pandas ne lit ici que 2 à 6 colonnes (`usecols`). Lire tout le CSV avec pandas coûterait bien plus cher en temps et en mémoire.
- **Le format compte autant que le moteur** : DuckDB sur le CSV est 5 à 8 fois plus lent que sur le Parquet. Le Parquet lit seulement les colonnes utiles et saute 11 partitions sur 12 quand on filtre par rayon (EXPLAIN ci-dessus).
- **SQLite garde la mémoire la plus basse** (≈ 38 Mo, il lit depuis le disque) mais il est 4 à 23 fois plus lent que DuckDB sur ces balayages. La base reste faite pour l'accès par code-barres, le Parquet pour l'analyse (voir `docs/architecture.md`).
