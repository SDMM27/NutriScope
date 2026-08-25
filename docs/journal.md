# Journal de NutriScope

## Choix du format du fichier des données d'open food facts (29/07)
Pour commencer, le CSV est un choix à exclure étant donné le fait que ce soit un format lourd et lent sur des gros volumes, bien qu'il soit simple et lisible pour des humains. De plus, le format CSV n'est pas du tout adapté aux objets imbriqués.

Il nous reste donc à choisir entre le format JSONL et le format Parquet.
L'avantage de Parquet est qu'il est plus léger, et donc plus rapide. Si on veut lire quelques colonnes d'un fichier au format Parquet, il va lire uniquement les colonnes que l'on veut. Alors qu'en JSONL, il va parcourir chaque ligne entièrement. 
En outre, l'objectif est d'intégrer les données dans un framework SQL (DuckDB ou PostgreSQL), et JSONL n'est pas forcément adapté pour les analyses SQL ou pandas. Alors que comme le cahier des charges du TP l'indique, les fichiers Parquet sont recommandés car ils s'intègrent très bien avec DuckDB.