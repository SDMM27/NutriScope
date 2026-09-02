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
    ingredients           TEXT,
    url_image             VARCHAR,
    nutriscore_lettre     VARCHAR(20)
        CHECK (nutriscore_lettre IN ('a','b','c','d','e','not-applicable','unknown')),
    nutriscore_score      INTEGER,
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
    sel_100g                              NUMERIC(5,2) CHECK (sel_100g BETWEEN 0 AND 100),
);