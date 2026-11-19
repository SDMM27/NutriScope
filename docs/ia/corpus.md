# Corpus de l'assistant NutriScope

Ce document liste toutes les sources que le RAG a le droit d'utiliser. Une source n'entre dans le corpus que si sa licence est établie et permet l'usage prévu. Les fichiers eux-mêmes restent hors du dépôt (`data/corpus/`, ignoré par Git) ; ils sont régénérés par `src/corpus/fiches.py` et `src/corpus/telecharger.py`.

## Famille 1 — fiches produits

| id | titre | éditeur | origine | mis à jour le | consulté le | licence et conditions | utilisé pour |
|---|---|---|---|---|---|---|---|
| `fiche:<code>` | une fiche texte par produit du catalogue (22 dans le lot) | Open Food Facts | catalogue de l'équipe, généré par `python -m src.corpus.fiches` | export du 2026-11-11 | 2026-11-15 | ODbL : créditer Open Food Facts, repartager la base dérivée dans les mêmes conditions | questions produit, comparaison, explication de score |

## Famille 2 — documents de référence

| id | titre | éditeur | URL | mis à jour le | consulté le | licence et conditions | statut | utilisé pour |
|---|---|---|---|---|---|---|---|---|
| `viepub-ns` | Le Nutri-Score en cinq questions | Vie publique (DILA) | https://www.vie-publique.fr/questions-reponses/286134-le-nutri-score-en-cinq-questions | à relever sur la page | 2026-11-15 | Licence Ouverte 2.0 : citer « Vie publique » et la date ; ne pas modifier le contenu | autorisé | fonctionnement du Nutri-Score |
| `santefr-ns` | Ce qu'il faut savoir sur le nouveau Nutri-Score | Santé.fr | https://www.sante.fr/ce-quil-faut-savoir-sur-le-nouveau-nutri-score | à relever sur la page | 2026-11-15 | CGU de Santé.fr à lire | à vérifier | nouveau calcul, boissons, caractère volontaire |
| `spf-ns` | Nutri-Score | Santé publique France | https://www.santepubliquefrance.fr/determinants-de-sante/nutrition-et-activite-physique/articles/nutri-score | à relever sur la page | 2026-11-15 | mentions légales de santepubliquefrance.fr à lire | à vérifier | composantes du score |
| `pnns-adultes` | Recommandations relatives à l'alimentation, à l'activité physique et à la sédentarité pour les adultes | Santé publique France | https://santepubliquefrance.fr/content/download/197811/2365735 | à relever dans le PDF | 2026-11-15 | mentions légales de santepubliquefrance.fr à lire | à vérifier | repères de consommation (fruits et légumes, légumes secs, charcuterie, produits laitiers) |
| `ciqual` | Table de composition nutritionnelle des aliments Ciqual | Anses | https://ciqual.anses.fr/ | à relever sur la fiche data.gouv.fr | — | Licence Ouverte : citer la source et la date de mise à jour | autorisé, non retenu | bonus : questions sur des aliments génériques (non indexé dans ce corrigé) |
| `hcsp-2017` | Avis relatif à la révision des repères alimentaires pour les adultes | HCSP | https://www.hcsp.fr/ | 2017 | — | « doit être diffusé dans sa totalité, sans ajout ni modification » | **exclu** | lien seulement : le découper en morceaux serait le modifier |

## Décisions

- **Statut « à vérifier ».** Les trois sources de Santé publique France et Santé.fr ne sont indexées qu'après lecture de leurs mentions légales par l'équipe (`python -m src.corpus.telecharger --inclure-a-verifier`). La décision et sa date sont reportées dans la colonne statut.
- **Vie publique, « ne pas modifier le contenu ».** Le découpage en morceaux ne réécrit pas le texte : chaque morceau garde le texte d'origine mot pour mot, et la réponse cite la page source et sa date. L'équipe considère que ce n'est pas une modification ; si le formateur en juge autrement, la source passe en « lien seulement ».
- **HCSP exclu.** La condition de diffusion intégrale interdit d'en extraire des morceaux. Le lien peut figurer dans la documentation, pas dans le corpus.
- **Ciqual non retenu.** Source tabulaire : elle relève d'un outil de recherche (comme `chercher_produit`), pas d'un découpage en texte. Piste pour la suite.
