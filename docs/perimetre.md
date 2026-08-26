# Périmètre alimentaire au lancement : 6 rayons.
Voici les 6 rayons qui ont été retenu à la fin du TP2 comme candidats potentiels :

+ Boissons
+ Produits laitiers
+ Céréales et petit-déjeuner
+ Biscuits et snacks
+ Plats préparés et conserves
+ Sauces et condiments

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

## Profiling
A suivre ....