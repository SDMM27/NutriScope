# Journal de bord — NutriScope

Ce journal sert à garder une trace de l'évolution de NutriScope au fil du projet.

L'objectif n'est pas de refaire la documentation technique. On y note plutôt ce que nous avons fait, comment nous nous sommes réparti le travail, les problèmes rencontrés, les solutions trouvées et les décisions qui ont fait évoluer le projet.

---

# Juillet — Démarrage

## Semaine du 29 juillet

### Ce qu'on fait

Le projet NutriScope commence avec la constitution de l'équipe et la découverte du sujet.

Nous partons sur l'idée d'une application capable de donner rapidement des informations sur un produit alimentaire, mais aussi d'aller plus loin qu'un simple Nutri-Score : explication du score, comparaison avec d'autres produits, substitution et, plus tard, assistant basé sur un RAG.

Pour commencer, nous devons surtout comprendre les données Open Food Facts et mettre en place le dépôt du projet.

### Répartition

* **Clément** : mise en place du dépôt, premières réflexions sur l'architecture et exploration technique.
* **Sacha** : exploration des données Open Food Facts et premières recherches sur les formats disponibles.

### Ce qui nous pose problème

Le dataset est beaucoup plus important que ce que nous avions imaginé. Il ne s'agit pas simplement d'un CSV que l'on peut charger tranquillement avec pandas.

Nous devons donc rapidement réfléchir à une manière de travailler avec beaucoup de données sans essayer de tout charger en mémoire.

### Ce qu'on décide

Nous allons travailler avec le format Parquet et utiliser DuckDB pour pouvoir interroger les données directement.

C'est un premier choix important : plutôt que de réduire immédiatement les données simplement parce qu'elles sont volumineuses, nous cherchons d'abord une manière de les exploiter correctement.

---

# Août — Comprendre les données

## Semaine suivante

### Ce qu'on fait

Nous passons beaucoup de temps à explorer le contenu du dataset.

Au début, nous pensions surtout chercher les colonnes dont nous aurions besoin. En réalité, nous découvrons progressivement que certaines informations sont beaucoup moins simples qu'elles n'en ont l'air.

Les nutriments sont notamment regroupés dans des structures particulières et certaines informations existent sous plusieurs formes.

### Répartition

* **Sacha** continue principalement l'exploration et l'extraction des données.
* **Clément** travaille davantage sur la façon dont les données pourront être exploitées ensuite par la base et les futures fonctionnalités.

### Problème rencontré

Une difficulté apparaît assez vite : il est facile de sélectionner des colonnes simplement parce qu'elles semblent intéressantes, mais beaucoup plus difficile de savoir si elles seront réellement utiles au projet.

Nous commençons donc à regarder les fonctionnalités une par une pour éviter de conserver énormément de données sans raison.

### Ce qu'on apprend

Le projet va finalement être autant un travail de **compréhension et de préparation des données** qu'un projet d'IA.

C'est un point qui n'était pas forcément aussi évident au début.

---

# Fin août — Définir le périmètre

## Semaine du 25 août

### Ce qu'on fait

Nous essayons maintenant de répondre à une question simple : **sur quels produits NutriScope doit-il réellement travailler ?**

Le catalogue Open Food Facts est trop large pour essayer de tout couvrir.

Après exploration, nous retenons six grands rayons comme base du projet :

* boissons ;
* produits laitiers ;
* céréales et petit-déjeuner ;
* biscuits et snacks ;
* plats préparés et conserves ;
* sauces et condiments.

Ce choix doit nous permettre d'avoir des produits suffisamment différents tout en gardant un projet raisonnable.

### Répartition

À ce stade, la séparation des tâches commence à être plus claire :

* **Sacha** prend principalement en charge le travail d'extraction et de manipulation du dataset ;
* **Clément** prend davantage en charge la partie structure du projet, base de données, nettoyage et organisation technique.

Cette répartition n'est pas totalement rigide : nous continuons à discuter ensemble des décisions qui ont un impact sur l'ensemble du projet.

### Problème

Les catégories Open Food Facts ne correspondent pas directement à nos six rayons.

Il faut donc éviter de faire un mapping arbitraire.

### Décision

Nous gardons les six rayons comme objectif, mais nous voulons valider leur contenu à partir des données réelles : quantité de produits disponibles, qualité des informations nutritionnelles, images disponibles et chevauchement entre catégories.

---

# Semaine suivante — Le profiling change notre vision

### Ce qu'on fait

Nous commençons à mesurer réellement la qualité des données.

Le périmètre France représente environ **1,25 million de produits**.

Nous regardons notamment les valeurs manquantes, les doublons, les valeurs aberrantes et la disponibilité des informations dont nous aurons besoin plus tard.

### Ce qui nous surprend

Nous trouvons des valeurs impossibles dans plusieurs nutriments : valeurs négatives, valeurs supérieures à 100 g pour 100 g de produit, incohérences entre les différentes valeurs d'énergie, etc.

Nous découvrons également que certaines informations que nous pensions pouvoir utiliser facilement sont en réalité très incomplètes.

### Pourquoi c'est important

Cela change notre façon de voir la suite du projet.

Au départ, nous pensions pouvoir rapidement passer de l'extraction au machine learning.

Nous comprenons maintenant qu'il faut d'abord construire une donnée suffisamment fiable pour que les modèles aient un sens.

---

# Début septembre — Jalon J1

## Semaine du 1er septembre

### Ce qu'on fait

Nous finalisons le premier jalon du projet.

Le dépôt commence à prendre sa structure définitive et nous avons maintenant une meilleure vision de ce que nous voulons faire avec les données.

Nous commençons également à formaliser nos choix dans les différents documents plutôt que de les garder uniquement dans nos discussions.

### Répartition

* **Clément** : architecture, organisation du dépôt et réflexion sur la future base.
* **Sacha** : données et extraction.
* **Ensemble** : validation du périmètre et des grandes fonctionnalités.

### Ce qu'on retient

Nous décidons notamment de ne pas utiliser directement le Nutri-Score comme variable d'entrée des futurs modèles.

Il doit rester une référence ou une cible, et non une information permettant de donner indirectement la réponse au modèle.

Cette décision est importante car elle évite de construire un modèle qui semblerait performant uniquement parce qu'on lui donne déjà une partie de la réponse.

---

# Septembre — Structurer le projet

## Semaine du 8 septembre

### Ce qu'on fait

Nous passons progressivement de l'exploration à la conception du projet.

Il faut maintenant réfléchir à la manière dont les données vont circuler entre les différentes parties de NutriScope.

On commence notamment à réfléchir à la séparation entre les produits, les marques, les catégories et les informations nutritionnelles.

### Problème

Le fichier Open Food Facts est pratique pour stocker beaucoup d'informations, mais il n'est pas forcément adapté tel quel à la base de données de notre application.

Certaines informations sont répétées et certaines colonnes contiennent plusieurs valeurs.

### Solution

Nous décidons de transformer progressivement ces données avant de les charger en base.

L'objectif n'est pas de reproduire exactement le fichier Open Food Facts, mais de construire une structure qui correspond mieux à notre projet.

---

# Semaine du 15 septembre — Jalon J2

### Ce qu'on fait

Nous travaillons sur le cadrage du projet et sur le backlog.

Nous commençons à avoir une vision plus concrète de la suite : nettoyage des données, base, machine learning, RAG puis application.

### Répartition

La répartition des tâches devient progressivement plus naturelle.

**Sacha** reste principalement concentré sur l'extraction et les données sources.

**Clément** travaille davantage sur le traitement des données, la base et la coordination des différentes briques.

Cette organisation permet d'avancer en parallèle plutôt que de travailler systématiquement sur les mêmes fichiers.

### Difficulté

Nous constatons que certaines décisions prises au début doivent être réexaminées lorsque nous regardons les données de plus près.

C'est parfois frustrant, mais cela évite de construire trop tôt quelque chose sur de mauvaises hypothèses.

---

# Fin septembre — Préparer le nettoyage

## Semaine du 22 septembre

### Ce qu'on fait

Nous préparons le travail de nettoyage des données.

Nous savons maintenant que nous ne pouvons pas simplement supprimer toutes les lignes contenant une anomalie.

Un produit peut être parfaitement exploitable même si une seule de ses informations nutritionnelles est incorrecte ou absente.

### Décision

Nous décidons donc de raisonner **règle par règle**.

Lorsqu'une valeur est manifestement fausse mais que le produit reste intéressant, nous préférons corriger ou supprimer uniquement cette valeur plutôt que supprimer tout le produit.

Lorsqu'une erreur peut être corrigée de manière fiable, nous la corrigeons.

Et lorsqu'une information essentielle est trop incertaine pour être corrigée, le produit peut finalement être écarté.

Cette stratégie est directement liée à ce que nous avons observé pendant le profiling.

---

# Fin septembre / début octobre — TP9

## Semaine du 29 septembre

### Ce qu'on fait

Nous passons réellement à l'implémentation du nettoyage.

C'est une étape importante parce que nous devons maintenant transformer les décisions prises précédemment en règles concrètes et vérifiables.

Nous ajoutons également des tests pour vérifier que les règles fonctionnent dans les cas normaux, mais aussi dans les cas un peu tordus que nous avons rencontrés pendant l'exploration.

### Problèmes rencontrés

Certains cas sont moins simples qu'ils en ont l'air.

Par exemple, une valeur aberrante ne signifie pas forcément que tout le produit est mauvais. Il faut déterminer si le problème vient d'une seule donnée, d'une unité mal interprétée ou d'un produit réellement inexploitable.

Nous avons également rencontré des problèmes de doublons : deux fiches peuvent correspondre au même produit, mais certaines fiches sont plus complètes que d'autres.

### Solution

Nous décidons de privilégier la fiche la plus complète lorsqu'il s'agit simplement d'un doublon.

Pour certains codes internes qui ne permettent pas d'identifier correctement le produit, nous préférons ne pas les conserver plutôt que de créer une fausse unicité.

Ces choix permettent ensuite à la base de garder une structure cohérente.

---

# Semaine du 6 octobre — Repenser le chemin des données

### Ce qu'on comprend

Une nouvelle question apparaît alors que nous avançons dans le TP9 :

**à quel moment doit-on découper les données en plusieurs fichiers ?**

Au début, nous pensions pouvoir extraire directement plusieurs fichiers depuis le Parquet puis les nettoyer séparément.

En avançant, cela paraît moins intéressant.

Nous préférons maintenant avoir une chaîne plus claire :

**Open Food Facts → extraction France → nettoyage → données propres → découpage → chargement en base**

Cela permet de faire le nettoyage sur une base commune avant de créer les différentes tables nécessaires à la base de données.

### Pourquoi ce changement

Cette organisation évite de nettoyer plusieurs fois les mêmes données et surtout de risquer d'avoir des incohérences entre les différents fichiers.

Le fichier propre intermédiaire devient donc une étape importante du pipeline, même s'il ne s'agit pas forcément d'un fichier définitif du projet.

---

# Semaine du 6 octobre — Aujourd'hui

### Où nous en sommes

Nous sommes encore dans la partie data du projet.

La base commence à avoir une structure claire, avec une séparation entre les produits, les marques, les catégories et les nutriments.

Mais nous n'avons pas encore fini de stabiliser toute la chaîne de données.

C'est probablement la partie du projet qui nous aura demandé le plus de réflexion jusqu'ici, alors qu'elle est assez peu visible lorsqu'on imagine simplement l'application finale.

### Ce qui reste à faire

La priorité est maintenant de terminer proprement le pipeline :

1. récupérer le périmètre France ;
2. appliquer le nettoyage ;
3. produire le jeu de données propre ;
4. préparer les données nécessaires à la base ;
5. charger la base ;
6. vérifier que les résultats sont cohérents.

Ensuite seulement, nous pourrons réellement nous concentrer sur les modèles et les fonctionnalités IA.

---

# Bilan provisoire

Après plusieurs semaines, NutriScope est assez différent de l'idée que nous avions au départ.

Nous pensions surtout construire une application autour de la nutrition et de l'IA.

Pour l'instant, une grande partie du travail consiste à comprendre les données, se mettre d'accord sur ce qu'on veut réellement garder et trouver une manière fiable de les faire circuler dans le projet.

Ce n'est pas forcément la partie la plus spectaculaire, mais elle conditionne tout ce qui viendra ensuite.

Et surtout, nous avons déjà appris quelque chose d'important : **une bonne idée d'IA ne suffit pas si les données sur lesquelles elle repose ne sont pas maîtrisées.**

La suite du projet permettra de voir si tout ce travail de préparation nous fait réellement gagner du temps lorsque nous commencerons le machine learning et le RAG.
