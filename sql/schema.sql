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
