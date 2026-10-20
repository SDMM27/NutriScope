-- Contrôles qualité du TP 12, écrits contre la vue `produits` (Parquet partitionné par rayon).
-- Un marqueur `-- @nom: <nom>` ouvre chaque requête.
-- Données : © Open Food Facts contributors — ODbL.

-- @nom: comptage_par_rayon
SELECT
    rayon,
    count(*) AS nb_produits,
    round(100.0 * count(*) / sum(count(*)) OVER (), 2) AS part_pct
FROM produits
GROUP BY rayon
ORDER BY nb_produits DESC, rayon;

-- @nom: completude
SELECT
    rayon,
    count(*) AS nb_produits,
    round(100.0 * avg(CAST(nutriscore_grade IN ('a', 'b', 'c', 'd', 'e') AS INTEGER)), 2) AS nutriscore_pct,
    round(100.0 * avg(CAST(
        "energy-kcal_100g" IS NOT NULL AND fat_100g IS NOT NULL AND "saturated-fat_100g" IS NOT NULL
        AND carbohydrates_100g IS NOT NULL AND sugars_100g IS NOT NULL
        AND proteins_100g IS NOT NULL AND salt_100g IS NOT NULL AS INTEGER)), 2) AS sept_nutriments_pct,
    round(100.0 * avg(CAST(rayon <> 'unknown' AS INTEGER)), 2) AS categorie_pct
FROM produits
GROUP BY rayon
ORDER BY nb_produits DESC, rayon;

-- @nom: doublons
SELECT
    (SELECT count(*) FROM (SELECT code FROM produits GROUP BY code HAVING count(*) > 1)) AS codes_en_double_groupes,
    (SELECT coalesce(sum(n - 1), 0) FROM (SELECT count(*) AS n FROM produits GROUP BY code HAVING count(*) > 1)) AS lignes_en_trop,
    (SELECT count(*) FROM (
        SELECT 1 FROM produits
        WHERE product_name IS NOT NULL AND brand IS NOT NULL
        GROUP BY product_name, brand HAVING count(*) > 1
    )) AS couples_nom_marque_repetes_groupes;

-- @nom: bornes_coherences
SELECT 'fat_100g hors [0, 100]' AS controle, count(*) AS nb FROM produits WHERE fat_100g < 0 OR fat_100g > 100
UNION ALL
SELECT 'saturated-fat_100g hors [0, 100]', count(*) FROM produits WHERE "saturated-fat_100g" < 0 OR "saturated-fat_100g" > 100
UNION ALL
SELECT 'carbohydrates_100g hors [0, 100]', count(*) FROM produits WHERE carbohydrates_100g < 0 OR carbohydrates_100g > 100
UNION ALL
SELECT 'sugars_100g hors [0, 100]', count(*) FROM produits WHERE sugars_100g < 0 OR sugars_100g > 100
UNION ALL
SELECT 'fiber_100g hors [0, 100]', count(*) FROM produits WHERE fiber_100g < 0 OR fiber_100g > 100
UNION ALL
SELECT 'proteins_100g hors [0, 100]', count(*) FROM produits WHERE proteins_100g < 0 OR proteins_100g > 100
UNION ALL
SELECT 'salt_100g hors [0, 100]', count(*) FROM produits WHERE salt_100g < 0 OR salt_100g > 100
UNION ALL
SELECT 'sodium_100g hors [0, 40]', count(*) FROM produits WHERE sodium_100g < 0 OR sodium_100g > 40
UNION ALL
SELECT 'energy-kcal_100g hors [0, 900]', count(*) FROM produits WHERE "energy-kcal_100g" < 0 OR "energy-kcal_100g" > 900
UNION ALL
SELECT 'sucres > glucides', count(*) FROM produits WHERE sugars_100g > carbohydrates_100g
UNION ALL
SELECT 'saturés > lipides', count(*) FROM produits WHERE "saturated-fat_100g" > fat_100g
UNION ALL
SELECT 'sel ≠ sodium × 2,5 (écart > 0,1)', count(*) FROM produits WHERE abs(salt_100g - sodium_100g * 2.5) > 0.1
UNION ALL
SELECT 'énergie nulle avec macronutriments > 0', count(*) FROM produits
WHERE "energy-kcal_100g" = 0 AND (fat_100g > 0 OR carbohydrates_100g > 0 OR proteins_100g > 0);

-- @nom: distribution_nutriscore
SELECT
    coalesce(nutriscore_grade, 'null') AS grade,
    count(*) AS nb_produits,
    round(100.0 * count(*) / sum(count(*)) OVER (), 2) AS part_pct,
    round(avg(nutriscore_score), 2) AS score_moyen
FROM produits
GROUP BY grade
ORDER BY grade;
