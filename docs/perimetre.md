# Périmètre alimentaire au lancement : 6 rayons.

## Objectif

Ce document fixe le périmètre de lancement de NutriScope : sur quels produits Open Food Facts l'application va porter, quelles colonnes du dataset sont retenues pour chaque fonctionnalité, et à quelles conditions de qualité (complétude, cohérence, absence de fuite de cible).

Il s'appuie sur le profiling systématique du dataset `food.parquet` (périmètre France, 1 247 336 produits) réalisé au TP2 — distributions, cardinalités, doublons de codes-barres, incohérences d'unités, valeurs impossibles — et sur la décision d'équipe qui en découle : 6 rayons de lancement, des colonnes conservées ou écartées, et un seuil de complétude minimal par produit.

Le périmètre couvre 5 fonctionnalités : prédiction du Nutri-Score, moteur de substitution, classification d'images, assistant RAG et application (recherche/affichage), plus l'usage transverse des données par le machine learning.

## Rayons couverts
Voici les 6 rayons qui ont été retenu à la fin du TP2 comme candidats potentiels :

- Boissons
- Produits laitiers
- Céréales et petit-déjeuner
- Biscuits et snacks
- Plats préparés et conserves
- Sauces et condiments

Ce choix vise à maintenir un compromis entre couverture du catalogue et spécialisation du dataset. Les six rayons présentent des profils nutritionnels, des compositions et des caractéristiques visuelles suffisamment différents pour limiter les ambiguïtés de classification tout en couvrant une diversité importante de produits.

Le choix définitif des catégories Open Food Facts associées à chaque rayon sera validé à partir du profiling du dataset, notamment du volume disponible, de la complétude nutritionnelle, de la présence du Nutri-Score, de la disponibilité des images et du chevauchement entre catégories.

## Pourquoi ces 6 ?

Ils couvrent des profils nutritionnels très différents :

                       NUTRITION
                          │
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
    Boissons          Produits          Sauces
    (sucre/énergie)    (laitiers)       (sel/graisses)
        │                 │                 │
        └────────────┬────┴────┬────────────┘
                     ↓         ↓
                  Céréales   Snacks
               (sucre fibres) (sucre gras)
                     │         │
                     └────┬────┘
                          ↓
                    Plats préparés
                  (profil très varié)

Cela donne à notre dataset un espace nutritionnel assez large sans essayer de couvrir tout le supermarché.

## Fonctionnalités

### Nutri-Score

Prédiction/calcul du Nutri-Score à partir des nutriments essentiels (`energy`/`energy-kcal`, `sugars`, `salt`, `saturated-fat`, `proteins`, `carbohydrates`). Les colonnes `nutrition_grade_fr`, `nutriscore_grade`, `nutriscore_score` sont conservées comme cible/référence mais **jamais** comme feature (cf. [Fuite de cible](#fuite-de-cible)).

### Substitution

Recherche d'un produit comparable et potentiellement meilleur sur le plan nutritionnel. S'appuie sur les données nutritionnelles, les catégories (`categories`, `categories_tags`), les marques et la composition (ingrédients, additifs, `ingredients_analysis_tags`, `ingredients_from_palm_oil_n`).

### Images

Exploitation des photographies produit (`image_url`, `image_small_url`) pour un futur classifieur d'images entraîné avec Keras, et pour l'affichage dans l'application. 

### RAG / Assistant

Informations utilisées par l'assistant pour répondre aux questions sur un produit : identification, nutrition, ingrédients/additifs, labels, origine, et informations secondaires de contextualisation (packaging, lieux de fabrication, pays).

### Application

Recherche et affichage des produits dans l'application : identification (`code`, `product_name`, `brands`, `categories_tags`, `quantity`), images, et informations secondaires.

### Machine Learning

Variables numériques et catégorielles utilisables comme features par les modèles (Nutri-Score, classification de rayon, etc.), en excluant explicitement toute colonne dérivée de la cible.

## Profiling

Profiling réalisé sur le périmètre France du dataset `food.parquet` : **1 247 336 produits**. Détail complet dans `notebooks/tp2_profiling.ipynb`.

### Colonnes conservées

**Identification et catalogue**

```text
code, product_name, generic_name, brands, brands_tags,
categories, categories_tags, quantity, url
```

**Nutrition** (cœur du projet : Nutri-Score, comparaison, substitution, RAG, ML)

```text
nutriments, energy_100g, energy-kj_100g, energy-kcal_100g,
proteins_100g, carbohydrates_100g, sugars_100g, fat_100g,
saturated-fat_100g, fiber_100g, sodium_100g, salt_100g,
fruits-vegetables-nuts_100g
```

ainsi que les autres vitamines/minéraux/nutriments disponibles lorsqu'ils présentent une qualité de données suffisante.

**Composition et ingrédients** (RAG, substitution, comparaison, NLP/ML)

```text
ingredients_text, traces, traces_tags,
additives_n, additives, additives_tags,
ingredients_from_palm_oil_n, ingredients_from_palm_oil, ingredients_from_palm_oil_tags,
ingredients_that_may_be_from_palm_oil_n, ingredients_that_may_be_from_palm_oil,
ingredients_that_may_be_from_palm_oil_tags
```

**Images** (classifieur Keras, affichage app)

```text
image_url, image_small_url
```

`code` est particulièrement important puisqu'il permet d'identifier le produit de manière quasi unique (cf. [Gestion des valeurs aberrantes](#gestion-des-valeurs-aberrantes) pour les 27 exceptions).

### Colonnes secondaires

Conservées avec une priorité faible (`KEEP_LOW`) : utiles au RAG, à la substitution, à l'app et à la contextualisation, mais non indispensables au calcul du Nutri-Score.

```text
packaging, packaging_tags,
labels, labels_tags, labels_fr,
completeness,
origins, origins_tags,
manufacturing_places, manufacturing_places_tags,
countries, countries_tags, countries_fr,
serving_size
```

### Colonnes écartées

Métadonnées et informations logistiques n'apportant pas de valeur directe aux fonctionnalités de NutriScope — écartées pour réduire le bruit et la complexité du dataset.

```text
creator, created_t, created_datetime,
last_modified_t, last_modified_datetime,
emb_codes, emb_codes_tags,
first_packaging_code_geo,
cities, cities_tags,
purchase_places, stores
```

### Critères de sélection

La sélection des colonnes repose sur quatre critères :

1. **Utilité métier** — la colonne sert-elle une des 6 fonctionnalités ci-dessus ?
2. **Qualité des données** — cohérence des valeurs, des unités, absence d'anomalies majeures.
3. **Complétude** — taux de valeurs renseignées suffisant pour être exploitable.
4. **Risque de fuite de cible** — la colonne dérive-t-elle directement de ce que le modèle doit prédire ?

Les colonnes sont réparties en quatre catégories : `KEEP` (indispensable ou fortement utile), `KEEP_LOW` (utile mais secondaire), `ANALYSIS_ONLY` (conservée pour l'analyse/l'évaluation, jamais en feature) et `DROP` (bruit).

### Seuil de complétude

`completeness` est un score entre 0 et 1 : plus une fiche a de champs renseignés (nom, marque, quantité, nutriments, ingrédients, photo, catégories...), plus il se rapproche de 1.

Le seuil est défini **par fonctionnalité**, car les besoins diffèrent :

- **Modèle Nutri-Score** : pas de seuil sur `completeness` (trop englobant — il inclut des champs sans rapport avec le calcul, comme les photos ou le packaging). On exige à la place la **présence effective des nutriments nécessaires** (`energy`/`energy-kcal`, `sugars`, `salt`, `saturated-fat`, `proteins`, `carbohydrates`), déjà mesurés à ~70 % de couverture. `fiber` n'est **pas** exigé (seulement 30 % de couverture, non obligatoire sur l'étiquette européenne) : l'imposer exclurait inutilement 70 % du catalogue.
- **RAG / App / Substitution (usage général)** : seuil sur `completeness` ≥ **0,3**.
- **Images** : critère binaire indépendant de `completeness` — présence d'une `image_url`/`image_small_url` exploitable.

**Décision finale — seuil retenu (usage général) : 0,3.** Justification : le 1er quartile de `completeness` sur le périmètre France est de 0,275 (arrondi à 0,3). Ce seuil n'exclut que le quart des fiches les moins renseignées tout en conservant environ 75 % du catalogue :

| Seuil `completeness` | Produits conservés | % du catalogue |
|---|---|---|
| ≥ 0,3 | 807 665 | 64,8 % |
| ≥ 0,4 | 582 380 | 46,7 % |
| ≥ 0,5 | 416 069 | 33,4 % |
| ≥ 0,6 | 298 400 | 23,9 % |
| ≥ 0,7 | 202 905 | 16,3 % |

Pour le modèle Nutri-Score, ce seuil générique n'est pas utilisé : voir la règle spécifique sur la présence des nutriments ci-dessus.

### Gestion des valeurs aberrantes

**Complétude hors bornes.** `completeness` dépasse sa borne documentée (1,0) pour 11 737 produits (0,94 %), avec des valeurs observées jusqu'à 1,10 — impossible au regard de sa propre définition.

**Doublons de codes-barres.** 27 codes distincts apparaissent en double (54 lignes sur 1 247 336, soit 0,004 %), tous en groupes de taille 2. Trois cas de figure identifiés : (1) même produit ré-importé sous deux fiches distinctes → fusionner en gardant la plus complète ; (2) code interne préfixé « 200x » (réservé Open Food Facts, non unique par construction) réattribué à deux produits différents → exclure du scan ou désambiguïser via d'autres champs ; (3) doublons de fiches vides (`completeness` = 0) → supprimer.

**Incohérences d'unités.** La colonne `unit` de `nutriments` est une chaîne libre : `energy` (censé être en kJ) est déclaré en `kcal` sur 97 lignes et en `kj` (casse différente) sur 3 lignes ; `salt` (censé être en g) est déclaré en `mg` sur 9 lignes — un calcul naïf sans normaliser par `unit` sous-estimerait le sel d'un facteur 1000 sur ces lignes. La cohérence croisée `energy` (kJ) / `energy-kcal` (ratio attendu 1 kcal = 4,184 kJ) s'écarte de plus de 20 % pour 55 124 produits sur 870 111 renseignés (6,34 %) — trop pour n'être que du bruit d'arrondi, à traiter par un contrôle de ratio systématique plutôt qu'en faisant confiance à une seule des deux colonnes. Enfin, `quantity`/`serving_size` (texte libre) exposent au moins 11 unités différentes (`g`, `kg`, `ml`, `l`, `cl`, `oz`, `mg`, `unité`...) sans compter les quantités multi-lots (`"4 x 100 g"`) : à ne pas parser à la main, privilégier `product_quantity`/`product_quantity_unit` déjà normalisés par Open Food Facts.

**Valeurs impossibles.** Pour les nutriments en g/100g, une valeur ne peut être ni négative ni dépasser 100 g pour 100 g de produit :

| Nutriment | Valeurs renseignées | Négatives | > 100 g/100g |
|---|---|---|---|
| sugars | 880 782 | 0 | 47 |
| salt | 826 467 | 0 | 54 |
| proteins | 882 511 | 1 | 31 |
| carbohydrates | 881 125 | 0 | 77 |
| fat | 880 864 | 1 | 44 |
| saturated-fat | 879 680 | 1 | 17 |
| fiber | 379 988 | 58 | 20 |

Pour `energy`/`energy-kcal` : 8 et 1 valeurs négatives (strictement impossibles) ; 17 773 (2,0 %) et 17 734 valeurs nulles — volume non négligeable, à distinguer d'un vrai produit à 0 kcal.

**Décision de nettoyage (réalisé au TP9, pas au TP2) :** valeur aberrante isolée → mettre à `NULL` (le produit reste, seul le nutriment devient manquant) ; motif systématique identifiable (ex. mg confondu avec g) → corriger par conversion ; anomalie sur un nutriment essentiel au score sans correction fiable → exclure la ligne.

### Fuite de cible

Les colonnes `nutrition_grade_fr`, `nutriscore_grade`, `nutriscore_score` sont traitées séparément : elles sont **conservées** pour mesurer la couverture du Nutri-Score, analyser sa distribution, constituer la cible et évaluer les performances du modèle, mais elles ne doivent **jamais** être utilisées comme variables explicatives du modèle de prédiction. Ces colonnes contiennent directement le résultat que le modèle doit prédire (ou une information qui en dérive) ; les utiliser comme entrée créerait une fuite de cible (*target leakage*).

## Limites du périmètre

- **Couverture nutritionnelle partielle.** Les nutriments essentiels au Nutri-Score sont renseignés pour ~70 % des produits France (66 % pour le sel seul), et `fiber` seulement pour 30 % — insuffisant pour l'imposer comme critère de complétude.
- **Nutri-Score et NOVA peu renseignés.** `nutriscore_grade` est manquant ou non applicable pour une large part du catalogue (717 597 `unknown` + 40 942 `not-applicable` + 25 040 NaN sur 1 247 336) ; `nova_group` est manquant pour 73,26 % des produits — limite la taille du jeu d'entraînement/évaluation exploitable pour la cible.
- **Cardinalité élevée sur les champs texte libre.** `brands` (113 784 valeurs, 86 322 une fois normalisée en `brands_tags`), `categories_tags` (37 442 tags distincts, 46,98 % de valeurs manquantes), `quantity` (28 870 valeurs) et `serving_size` (18 010 valeurs) nécessitent un travail de normalisation/mapping (marques, catégories → rayons) avant tout usage en filtre ou en feature.
- **Incohérence `energy`/`energy-kcal` non négligeable** (~6,3 % des produits ayant les deux champs renseignés) : nécessite un contrôle de ratio systématique plutôt qu'une confiance aveugle en une seule des deux colonnes.
- **Doublons et anomalies marginaux en proportion mais réels** : 0,004 % de lignes dupliquées, 0,94 % de `completeness` hors bornes, quelques dizaines à ~18 000 lignes selon le nutriment sur des valeurs impossibles — ne remettent pas en cause le périmètre mais imposent un nettoyage ciblé au TP9 avant tout entraînement de modèle.
- **Mapping catégories → rayons non finalisé.** Le choix définitif des catégories Open Food Facts associées à chacun des 6 rayons reste à valider (volume, complétude nutritionnelle, présence du Nutri-Score, disponibilité des images, chevauchement entre catégories) ; les 6 rayons eux-mêmes restent des candidats à confirmer par l'équipe.