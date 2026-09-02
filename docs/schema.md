# Schéma relationnel — proposition pour discussion (TP4, jalon J1)

## Vue d'ensemble

Quatre entités demandées par le sujet + une table de liaison pour `categories_tags` (multi-valué) :

```text
        brands                     categories
      ┌──────────┐               ┌──────────────┐
      │ id   PK   │               │ id   PK       │
      │ name UQ   │               │ tag  UQ       │
      └────┬─────┘               └──────┬────────┘
           │ 0..1                       │ 0..N
           │                    ┌────────┴───────────────┐
           │                    │ products_categories     │  (liaison)
           │                    │ code        FK,PK       │
           │                    │ category_id FK,PK       │
           │                    └────────┬───────────────┘
           │                             │ 0..N
      ┌────┴─────────────────────────────┴───┐
      │              products                 │
      │ code (PK, code-barres)                │
      │ name, quantity, ...                   │
      │ brand_id FK → brands(id)              │
      └───────────────┬────────────────────────┘
                       │ 1..1
                 ┌─────┴──────┐
                 │ nutrients  │
                 │ code PK,FK │
                 └────────────┘
```

- `products` → `brands` : plusieurs produits pour une marque (1..N), une marque par produit
- `products` ↔ `categories` : many-to-many via `products_categories`, parce que `categories_tags` est une
  liste dans la source.
- `products` → `nutrients` : relation 1-1 (une ligne de nutriments par produit), séparée de `products`
  pour isoler les colonnes nutritionnelles typées/contraintes du reste des métadonnées.

## Tables détaillées

### `products`

| Colonne parquet | Colonne (base) | Type | Contrainte | Notes |
|---|---|---|---|---|
| `code` | `code` | `VARCHAR` | **PK**, NOT NULL | code-barres OFF ; texte car certains codes internes (`200x...`) ne sont pas numériques |
| `product_name` | `name` | `VARCHAR` | | nom retenu pour le périmètre France |
| `brands_tags[1]` | `brand_id` | `INTEGER` | FK → `brands(id)`, NULL possible | marque absente pour une partie du catalogue |
| `nutriscore_grade` | `nutriscore_grade` | `VARCHAR(20)` | CHECK dans `('a','b','c','d','e','not-applicable','unknown')` | conservé en référence, **jamais en feature** (fuite de cible) |
| `nutriscore_score` | `nutriscore_score` | `INTEGER` | | idem, référence uniquement |

### `brands`

| Colonne parquet | Colonne (base) | Type | Contrainte |
|---|---|---|---|
| — | `id` | `INTEGER` | **PK** |
| `brands_tags[1]` | `name` | `VARCHAR` | **UNIQUE**, NOT NULL |

Une ligne par valeur distincte de `brands_tags[1]` (dédupliquée par construction via l'UNIQUE).

### `categories`

| Colonne parquet | Colonne (base) | Type | Contrainte |
|---|---|---|---|
| — | `id` | `INTEGER` | **PK** |
| `categories_tags` (un élément) | `tag` | `VARCHAR` | **UNIQUE**, NOT NULL |

Une ligne par tag distinct de `categories_tags` (ex. `en:dairies`).

### `products_categories` (liaison)

| Colonne parquet | Colonne (base) | Type | Contrainte |
|---|---|---|---|
| `code` | `code` | `VARCHAR` | FK → `products(code)` |
| `categories_tags` (un élément, résolu vers `categories.id`) | `category_id` | `INTEGER` | FK → `categories(id)` |

**PK** composite `(code, category_id)`. Une ligne par (produit, catégorie) — porte la multi-valuation de
`categories_tags`.

### `nutrients`

Table large (une colonne par nutriment retenu au TP2). Le parquet n'a pas de colonnes `xxx_100g` à plat :
chaque valeur est extraite de la colonne struct `nutriments` (liste de `{name, "100g", ...}`), filtrée sur
le `name` correspondant.

| Colonne parquet (`nutriments`, filtré sur `name=`) | Colonne (base) | Type | Contrainte |
|---|---|---|---|
| `code` | `code` | `VARCHAR` | **PK**, FK → `products(code)` |
| `'energy'` | `energy` | `NUMERIC(7,2)` | CHECK ≥ 0 (kJ, pas de borne à 100) |
| `'energy-kcal'` | `energy_kcal` | `NUMERIC(7,2)` | CHECK ≥ 0 |
| `'proteins'` | `proteins` | `NUMERIC(5,2)` | CHECK entre 0 et 100 |
| `'carbohydrates'` | `carbohydrates` | `NUMERIC(5,2)` | CHECK entre 0 et 100 |
| `'sugars'` | `sugars` | `NUMERIC(5,2)` | CHECK entre 0 et 100 |
| `'fat'` | `fat` | `NUMERIC(5,2)` | CHECK entre 0 et 100 |
| `'saturated-fat'` | `saturated_fat` | `NUMERIC(5,2)` | CHECK entre 0 et 100 |
| `'fiber'` | `fiber` | `NUMERIC(5,2)` | CHECK entre 0 et 100, NULL fréquent (30 % de couverture, non exigé) |
| `'salt'` | `salt` | `NUMERIC(5,2)` | CHECK entre 0 et 100 |

Reprend exactement l'ensemble de nutriments « cœur du projet » retenu dans perimetre.md.
Les valeurs négatives ou hors bornes détectées au TP2 sont mises à `NULL` au chargement (règle déjà
actée dans perimetre.md, appliquée dès maintenant plutôt qu'au TP9 pour pouvoir poser des `CHECK` propres).

## Contraintes et clés

- **Unicité du code-barres** : `products.code` en clé primaire. Nécessite une déduplication préalable au
  chargement (27 codes en double sur le périmètre France, 3 cas identifiés dans perimetre.md) :
  1. même produit ré-importé deux fois → on garde la fiche la plus complète (`completeness` la plus haute) ;
  2. code interne `200x…` réattribué à deux produits différents → **exclu du périmètre chargé**, ce code
     n'étant par construction pas un identifiant fiable ;
  3. doublon de fiche vide (`completeness = 0`) → supprimé.
- **Intégrité référentielle** : toutes les FK ci-dessus. DuckDB ne supporte pas `ON DELETE CASCADE`/`SET
  NULL`/`SET DEFAULT` sur les clés étrangères (contrairement à PostgreSQL, testé et confirmé) : pas de
  cascade automatique en base. Ce n'est pas gênant ici puisque le script de chargement fait un
  `DROP ... ` + recréation complète à chaque exécution plutôt que des suppressions ciblées ; si un besoin
  de suppression ciblée apparaît plus tard, il faudra l'écrire à la main dans le script (supprimer
  `nutrients`/`products_categories` avant `products`).
- **Types corrects sur les nutriments** : `NUMERIC` (pas `FLOAT`, pour éviter les imprécisions binaires sur
  des bornes strictes 0–100) + `CHECK` par colonne reprenant les bornes physiques documentées au TP2.

## DDL indicatif (DuckDB)

```sql
CREATE SEQUENCE seq_brands START 1;
CREATE TABLE brands (
    id  INTEGER PRIMARY KEY DEFAULT nextval('seq_brands'),
    name VARCHAR NOT NULL UNIQUE
);

CREATE SEQUENCE seq_categories START 1;
CREATE TABLE categories (
    id  INTEGER PRIMARY KEY DEFAULT nextval('seq_categories'),
    tag VARCHAR NOT NULL UNIQUE
);

CREATE TABLE products (
    code                  VARCHAR PRIMARY KEY,
    name                  VARCHAR,
    brand_id              INTEGER REFERENCES brands(id),
    nutriscore_grade      VARCHAR(20)
        CHECK (nutriscore_grade IN ('a','b','c','d','e','not-applicable','unknown')),
    nutriscore_score      INTEGER
);

CREATE TABLE products_categories (
    code        VARCHAR REFERENCES products(code),
    category_id INTEGER REFERENCES categories(id),
    PRIMARY KEY (code, category_id)
);

CREATE TABLE nutrients (
    code VARCHAR PRIMARY KEY REFERENCES products(code),
    energy NUMERIC(7,2) CHECK (energy >= 0),
    energy_kcal NUMERIC(7,2) CHECK (energy_kcal >= 0),
    proteins NUMERIC(5,2) CHECK (proteins BETWEEN 0 AND 100),
    carbohydrates NUMERIC(5,2) CHECK (carbohydrates BETWEEN 0 AND 100),
    sugars NUMERIC(5,2) CHECK (sugars BETWEEN 0 AND 100),
    fat NUMERIC(5,2) CHECK (fat BETWEEN 0 AND 100),
    saturated_fat NUMERIC(5,2) CHECK (saturated_fat BETWEEN 0 AND 100),
    fiber NUMERIC(5,2) CHECK (fiber BETWEEN 0 AND 100),
    salt NUMERIC(5,2) CHECK (salt BETWEEN 0 AND 100)
);

```
