# Journal de NutriScope

## Choix du format du fichier des données d'open food facts (29/07)
Pour commencer, le CSV est un choix à exclure étant donné le fait que ce soit un format lourd et lent sur des gros volumes, bien qu'il soit simple et lisible pour des humains. De plus, le format CSV n'est pas du tout adapté aux objets imbriqués.

Il nous reste donc à choisir entre le format JSONL et le format Parquet.
L'avantage de Parquet est qu'il est plus léger, et donc plus rapide. Si on veut lire quelques colonnes d'un fichier au format Parquet, il va lire uniquement les colonnes que l'on veut. Alors qu'en JSONL, il va parcourir chaque ligne entièrement. 
En outre, l'objectif est d'intégrer les données dans un framework SQL (DuckDB ou PostgreSQL), et JSONL n'est pas forcément adapté pour les analyses SQL ou pandas. Alors que comme le cahier des charges du TP l'indique, les fichiers Parquet sont recommandés car ils s'intègrent très bien avec DuckDB.

## EDA de référence — TP 10 (30/09)
**Fait** : EDA de référence complète (`notebooks/eda_reference.ipynb`), fonctions de calcul testées dans `src/eda_lib.py` (34 tests verts), synthèse d'une page et registre d'hypothèses dans `docs/data/`.
**Décidé** : features du TP 14 (saturés, énergie, lipides, sucres, sel, glucides ; sodium retiré ; rayon donné au modèle) ; deux nouveaux drapeaux pour le nettoyage du TP 9 ; sort du rayon `unknown` (20,5 %) renvoyé au TP 12. Tout lien nutriment ↔ score est relu par rayon (paradoxe de Simpson).
**Bloqué** : travail sur le nettoyage minimal faute du TP 9 ; les rayons `pnns_groups_1` de l'échantillon devront être retrouvés dans le Parquet complet via `food_groups_tags` (TP 12).