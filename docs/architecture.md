# Architecture des données NutriScope

Données : © Open Food Facts contributors — ODbL.

En une phrase : **PostgreSQL sert l'application (accès par code-barres), les Parquet servent l'analyse et le ML (balayages).** Les deux sont produits depuis le même nettoyé.

## Flux

```
data/food.parquet (OFF, 7,9 Go)
   │  src/extract_perimeter.py      filtre France (DuckDB)
   ▼
data/extracts/france_brut.parquet   1 273 567 lignes
   │  src/cleaning.py (nettoyer)    TP 9
   ▼
nettoyé (1 273 539 lignes)
   ├─► data/extracts/*.parquet ─► src/load_database.py ─► PostgreSQL     (application)
   └─► data/clean/produits_nettoyes.csv
          │  src/storage/convert_parquet.py
          ▼
       data/parquet/produits/rayon=<slug>/   (ZSTD, 12 partitions)       (analyse)
          ├─► src/storage/run_queries.py   ─► docs/data/controle.md
          ├─► src/storage/benchmark.py     ─► docs/data/benchmark.md
          └─► src/storage/export_features.py
                 ▼
              data/exports/features_nutriscore_<AAAAMMJJ>.parquet + schema.json   (ML, figé)
```

## Magasins de données

| Magasin | Contenu | Producteur | Format | Emplacement | Git |
|---|---|---|---|---|---|
| Brut | dump Open Food Facts complet | téléchargement | Parquet | `data/food.parquet` | non |
| Extrait France | colonnes utiles, produits français | `extract_perimeter.py` | Parquet | `data/extracts/france_brut.parquet` | non |
| Nettoyé | sortie de `nettoyer()`, une ligne par code | `convert_parquet.py` | CSV | `data/clean/produits_nettoyes.csv` | non |
| Base | produits, marques, catégories, nutriments (relationnel) | `load_database.py` | PostgreSQL | serveur local `nutriscope` | non (schéma : `sql/schema.sql`) |
| Parquet analytique | produits typés, partitionnés par rayon | `convert_parquet.py` | Parquet ZSTD | `data/parquet/produits/` | non (schéma : `docs/data/schema_produits.json`) |
| Export features | produits utilisables pour prédire le Nutri-Score | `export_features.py` | Parquet | `data/exports/` | non (schéma : `docs/data/schema_features.json`) |

## Qui lit quoi

| Lecteur | Lit | Pourquoi | Ne lit pas |
|---|---|---|---|
| API (fiche produit, substitution) | PostgreSQL | accès par clé `code`, index, intégrité | Parquet, exports |
| Notebooks d'EDA | Parquet `produits` via DuckDB | balayages et agrégats rapides, élagage par rayon | la base (charge inutile), le brut |
| Entraînement (TP 13-14) | export `features_nutriscore_<date>.parquet` | jeu figé, daté, reproductible | le Parquet vivant, la base |
| Contrôles qualité | Parquet `produits` (`sql/controles.sql`) | mêmes chiffres que la base, sans serveur | le brut |
| Assistant (RAG, plus tard) | PostgreSQL (fiches) | réponses sur un produit précis | Parquet |

## Règles

1. **Une source de vérité** : le nettoyé du TP 9. Base et Parquet en dérivent ; on corrige la chaîne, jamais un magasin à la main.
2. **Données hors Git** : seuls le code, les schémas JSON et les rapports sont versionnés.
3. **Parquet reconstruit à chaque exécution** : `convert_parquet.py` supprime le dossier puis le réécrit ; aucune partition orpheline.
4. **Export jamais réécrit** : un export daté est figé ; l'écraser exige `--force` et doit redonner le même SHA-256.
5. **Partition par rayon seulement** : 12 valeurs, les filtres d'analyse portent dessus. Partitionner aussi par marque ou par date créerait des milliers de petits fichiers et ralentirait les lectures plus qu'il ne les élague.

## Phases 6-7

- Parquet et exports passent en stockage objet (bucket S3 ou équivalent) ; DuckDB les lit en `s3://…` sans changer les requêtes.
- PostgreSQL passe en base managée ; `DB_CONFIG` vient de variables d'environnement.
- Le flux devient une suite de cibles orchestrées (TP 13 : `Makefile` / `python -m nutriscope.pipeline`).
