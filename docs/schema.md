# Schéma relationnel — proposition pour discussion (TP4, jalon J1)

## Vue d'ensemble

Quatre entités demandées par le sujet + une table de liaison pour `categories_tags` (multi-valué) :

```text
        marques                    categories
      ┌──────────┐               ┌──────────────┐
      │ id  PK    │               │ id   PK       │
      │ nom UQ    │               │ tag  UQ       │
      └────┬─────┘               └──────┬────────┘
           │ 0..1                       │ 0..N
           │                    ┌───────┴─────────────┐
           │                    │ produits_categories  │  (liaison)
           │                    │ code         FK,PK    │
           │                    │ categorie_id FK,PK    │
           │                    └───────┬─────────────┘
           │                            │ 0..N
      ┌────┴────────────────────────────┴───┐
      │              produits                │
      │ code (PK, code-barres)               │
      │ nom, quantite, ...                   │
      │ marque_id FK → marques(id)           │
      └───────────────┬───────────────────────┘
                       │ 1..1
                 ┌─────┴──────┐
                 │ nutriments │
                 │ code PK,FK │
                 └────────────┘
```

- `produits` → `marques` : plusieurs produits pour une marque (1..N), une marque par produit
- `produits` ↔ `categories` : many-to-many via `produits_categories`, parce que `categories_tags` est une
  liste dans la source.
- `produits` → `nutriments` : relation 1-1 (une ligne de nutriments par produit), séparée de `produits`
  pour isoler les colonnes nutritionnelles typées/contraintes du reste des métadonnées.

## Tables détaillées

### `produits`

| Colonne parquet | Colonne (base) | Type | Contrainte | Notes |
|---|---|---|---|---|
| `code` | `code` | `VARCHAR` | **PK**, NOT NULL | code-barres OFF ; texte car certains codes internes (`200x...`) ne sont pas numériques |
| `product_name` | `nom` | `VARCHAR` | | nom retenu pour le périmètre France |
| `brands_tags[1]` | `marque_id` | `INTEGER` | FK → `marques(id)`, NULL possible | marque absente pour une partie du catalogue |
| `quantity` | `quantite` | `VARCHAR` | | texte brut déclaré (ex. `"500 g"`) |
| `product_quantity` | `quantite_normalisee` | `NUMERIC` | | quantité normalisée par OFF (à privilégier plutôt que de parser `quantity`) |
| `product_quantity_unit` | `unite_quantite` | `VARCHAR` | | unité normalisée associée |
| `ingredients_text` | `ingredients` | `TEXT` | | texte des ingrédients (RAG) |
| `images` (construit à partir de `code` + `imgid`) | `url_image` | `VARCHAR` | | pas de colonne `image_url` directe dans le parquet — à construire depuis la structure `images` |
| `images` (idem, taille réduite) | `url_image_miniature` | `VARCHAR` | | idem |
| `nutriscore_grade` | `nutriscore_lettre` | `VARCHAR(20)` | CHECK dans `('a','b','c','d','e','not-applicable','unknown')` | conservé en référence, **jamais en feature** (fuite de cible) |
| `nutriscore_score` | `nutriscore_score` | `INTEGER` | | idem, référence uniquement |
| `nova_group` | `groupe_nova` | `SMALLINT` | CHECK entre 1 et 4, NULL possible | 73 % de valeurs manquantes |
| `completeness` | `completude` | `NUMERIC(4,3)` | CHECK entre 0 et 1 | valeurs > 1 mises à NULL au chargement |

`image_url`/`image_small_url` n'existent pas comme colonnes du parquet (vérifié via `DESCRIBE`) — seule la
colonne `images` (struct détaillant imgid/tailles) existe. Il faudra reconstruire l'URL au chargement
(pattern OFF `.../images/products/<code>/<imgid>.<taille>.jpg`), ou revoir cette colonne si trop complexe
pour le J1.

### `marques`

| Colonne parquet | Colonne (base) | Type | Contrainte |
|---|---|---|---|
| — | `id` | `INTEGER` | **PK** |
| `brands_tags[1]` | `nom` | `VARCHAR` | **UNIQUE**, NOT NULL |

Une ligne par valeur distincte de `brands_tags[1]` (dédupliquée par construction via l'UNIQUE).

### `categories`

| Colonne parquet | Colonne (base) | Type | Contrainte |
|---|---|---|---|
| — | `id` | `INTEGER` | **PK** |
| `categories_tags` (un élément) | `tag` | `VARCHAR` | **UNIQUE**, NOT NULL |

Une ligne par tag distinct de `categories_tags` (ex. `en:dairies`).

### `produits_categories` (liaison)

| Colonne parquet | Colonne (base) | Type | Contrainte |
|---|---|---|---|
| `code` | `code` | `VARCHAR` | FK → `produits(code)` |
| `categories_tags` (un élément, résolu vers `categories.id`) | `categorie_id` | `INTEGER` | FK → `categories(id)` |

**PK** composite `(code, category_id)`. Une ligne par (produit, catégorie) — porte la multi-valuation de
`categories_tags`.

### `nutriments`

Table large (une colonne par nutriment retenu au TP2). Le parquet n'a pas de colonnes `xxx_100g` à plat :
chaque valeur est extraite de la colonne struct `nutriments` (liste de `{name, "100g", ...}`), filtrée sur
le `name` correspondant.

| Colonne parquet (`nutriments`, filtré sur `name=`) | Colonne (base) | Type | Contrainte |
|---|---|---|---|
| `code` | `code` | `VARCHAR` | **PK**, FK → `produits(code)` |
| `'energy'` | `energie_100g` | `NUMERIC(7,2)` | CHECK ≥ 0 (kJ, pas de borne à 100) |
| `'energy-kcal'` | `energie_kcal_100g` | `NUMERIC(7,2)` | CHECK ≥ 0 |
| `'proteins'` | `proteines_100g` | `NUMERIC(5,2)` | CHECK entre 0 et 100 |
| `'carbohydrates'` | `glucides_100g` | `NUMERIC(5,2)` | CHECK entre 0 et 100 |
| `'sugars'` | `sucres_100g` | `NUMERIC(5,2)` | CHECK entre 0 et 100 |
| `'fat'` | `lipides_100g` | `NUMERIC(5,2)` | CHECK entre 0 et 100 |
| `'saturated-fat'` | `acides_gras_satures_100g` | `NUMERIC(5,2)` | CHECK entre 0 et 100 |
| `'fiber'` | `fibres_100g` | `NUMERIC(5,2)` | CHECK entre 0 et 100, NULL fréquent (30 % de couverture, non exigé) |
| `'sodium'` | `sodium_100g` | `NUMERIC(5,2)` | CHECK entre 0 et 100 |
| `'salt'` | `sel_100g` | `NUMERIC(5,2)` | CHECK entre 0 et 100 |
| `'fruits-vegetables-nuts'` | `fruits_legumes_noix_100g` | `NUMERIC(5,2)` | CHECK entre 0 et 100 |

Reprend exactement l'ensemble de nutriments « cœur du projet » retenu dans perimetre.md.
Les valeurs négatives ou hors bornes détectées au TP2 sont mises à `NULL` au chargement (règle déjà
actée dans perimetre.md, appliquée dès maintenant plutôt qu'au TP9 pour pouvoir poser des `CHECK` propres).

## Contraintes et clés

- **Unicité du code-barres** : `produits.code` en clé primaire. Nécessite une déduplication préalable au
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
  `nutriments`/`produits_categories` avant `produits`).
- **Types corrects sur les nutriments** : `NUMERIC` (pas `FLOAT`, pour éviter les imprécisions binaires sur
  des bornes strictes 0–100) + `CHECK` par colonne reprenant les bornes physiques documentées au TP2.

## DDL indicatif (DuckDB)

```sql
CREATE SEQUENCE seq_marques START 1;
CREATE TABLE marques (
    id  INTEGER PRIMARY KEY DEFAULT nextval('seq_marques'),
    nom VARCHAR NOT NULL UNIQUE
);

CREATE SEQUENCE seq_categories START 1;
CREATE TABLE categories (
    id  INTEGER PRIMARY KEY DEFAULT nextval('seq_categories'),
    tag VARCHAR NOT NULL UNIQUE
);

CREATE TABLE produits (
    code                  VARCHAR PRIMARY KEY,
    nom                   VARCHAR,
    marque_id             INTEGER REFERENCES marques(id),
    quantite              VARCHAR,
    quantite_normalisee   NUMERIC,
    unite_quantite        VARCHAR,
    ingredients           TEXT,
    url_image             VARCHAR,
    url_image_miniature   VARCHAR,
    nutriscore_lettre     VARCHAR(20)
        CHECK (nutriscore_lettre IN ('a','b','c','d','e','not-applicable','unknown')),
    nutriscore_score      INTEGER,
    groupe_nova           SMALLINT CHECK (groupe_nova BETWEEN 1 AND 4),
    completude            NUMERIC(4,3) CHECK (completude BETWEEN 0 AND 1)
);

CREATE TABLE produits_categories (
    code         VARCHAR REFERENCES produits(code),
    categorie_id INTEGER REFERENCES categories(id),
    PRIMARY KEY (code, categorie_id)
);

CREATE TABLE nutriments (
    code                       VARCHAR PRIMARY KEY REFERENCES produits(code),
    energie_100g                NUMERIC(7,2) CHECK (energie_100g >= 0),
    energie_kcal_100g            NUMERIC(7,2) CHECK (energie_kcal_100g >= 0),
    proteines_100g                 NUMERIC(5,2) CHECK (proteines_100g BETWEEN 0 AND 100),
    glucides_100g                   NUMERIC(5,2) CHECK (glucides_100g BETWEEN 0 AND 100),
    sucres_100g                      NUMERIC(5,2) CHECK (sucres_100g BETWEEN 0 AND 100),
    lipides_100g                      NUMERIC(5,2) CHECK (lipides_100g BETWEEN 0 AND 100),
    acides_gras_satures_100g           NUMERIC(5,2) CHECK (acides_gras_satures_100g BETWEEN 0 AND 100),
    fibres_100g                         NUMERIC(5,2) CHECK (fibres_100g BETWEEN 0 AND 100),
    sodium_100g                          NUMERIC(5,2) CHECK (sodium_100g BETWEEN 0 AND 100),
    sel_100g                              NUMERIC(5,2) CHECK (sel_100g BETWEEN 0 AND 100),
    fruits_legumes_noix_100g               NUMERIC(5,2) CHECK (fruits_legumes_noix_100g BETWEEN 0 AND 100)
);
```
