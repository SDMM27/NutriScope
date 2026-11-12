# Analyse visuelle des erreurs du test — TP 17

Revue des 12 photos sélectionnées dans `models/erreurs_images_test.png`, après
choix définitif du modèle et du seuil. Les observations ci-dessous décrivent les
photos ; les explications du comportement du réseau restent des hypothèses.
Aucun réétiquetage, réglage ou nouvel entraînement n'a été effectué sur le test.

| Code | Vrai rayon → prédiction ; confiance | Observation et interprétation |
|---|---|---|
| `3123930771059` | fromages → cereales ; 98,6 % | Sachet de comté Entremont photographié en rayon. Le nom du fromage est lisible, mais une grande photo de plat garni occupe le bas du sachet et le fond comporte le rayon du magasin. C'est une erreur très confiante sur un produit identifiable ; le visuel de recette et le contexte sont des indices parasites possibles, sans preuve causale. Le seuil laisse passer l'erreur. |
| `3242272270355` | pates → cereales ; 97,0 % | Gobelet Sodebo PastaBox, photographié en gros plan. « Pâtes fraîches » est visible ; la forme du gobelet diffère des sachets de pâtes courants. Le modèle échoue sur la diversité des contenants du rayon, sans ambiguïté manifeste sur le produit. Erreur acceptée malgré la forte confiance. |
| `3329770083233` | fromages → yaourts ; 96,7 % | Pack Yoplait Skyr vanille, sur fond blanc. Son aspect ressemble à un pack de yaourts ; son classement dans le manifest est `fromages`. C'est une frontière de taxonomie à expliciter pour le skyr, pas une preuve d'étiquette erronée. La photo est nette : améliorer seulement la qualité des images ne résoudrait pas ce cas. Erreur acceptée selon la cible actuelle. |
| `3124480185082` | sodas → yaourts ; 95,6 % | Pack Orangina Zero de six canettes, vu de face. Le nom de la boisson est lisible, mais la silhouette du multipack pourrait rappeler celle de desserts lactés. Il s'agit d'une limite du modèle sur un soda identifiable, plutôt que d'une ambiguïté de classe. Erreur acceptée. |
| `3256223022375` | sodas → eaux ; 93,9 % | Limonade U dans une bouteille transparente, avec liquide clair et bouchon bleu. La silhouette ressemble à celle d'une eau ; le mot « limonade » permet de distinguer les deux. Ambiguïté visuelle entre boissons, sans erreur d'étiquette démontrée. Erreur acceptée. |
| `0667803000707` | sauces → sodas ; 90,9 % | Boîte jaune de moutarde Colman's photographiée en magasin, principalement de côté, avec des inscriptions verticales et peu de face produit. Cadrage et contenant atypique constituent une difficulté concrète. La classe `sauces` reste cohérente avec un condiment. Erreur acceptée. |
| `5000128583954` | sauces → pates ; 88,7 % | Étiquette de houmous Co-op en gros plan, avec visuel de pain et tableau nutritionnel. Le produit est identifiable comme tartinable ; son inclusion parmi les sauces doit être documentée dans la taxonomie. Le gros plan et la composition de l'étiquette sont des difficultés possibles, sans pouvoir attribuer l'erreur à une zone précise. Erreur acceptée. |
| `3179730101329` | eaux → sodas ; 86,0 % | Canette de Perrier photographiée à l'horizontale. La canette est un contenant partagé avec les sodas ; l'orientation est éloignée des rotations d'environ ±15° utilisées à l'entraînement. Limite visuelle et de couverture des augmentations, sans erreur de cible manifeste. Erreur acceptée. |
| `3033491638367` | yaourts → cereales ; 82,5 % | Pack Activia aux céréales, avec le mot « céréales » et des grains très visibles sur le décor. Le produit reste un yaourt ; l'ingrédient et son illustration peuvent concurrencer la catégorie du produit. C'est une confusion entre contenu annoncé et rayon, pas une preuve de mauvais étiquetage. Erreur acceptée de justesse. |
| `5013803000028` | cereales → pates ; 81,8 % | Sachet de granola Eat Natural, photographié debout, avec une fenêtre transparente montrant son contenu. Les céréales sont identifiables ; la forme du sachet peut être commune aux pâtes. Limite du modèle sur des contenants proches. Erreur acceptée de justesse. |
| `4002359011887` | pates → fromages ; 80,4 % | Sachet de nouilles de riz Suzi Wan, avec une fenêtre montrant des bandes blanches et un visuel de plat préparé. Le texte permet d'identifier les nouilles ; l'apparence du contenu et du sachet peut rappeler d'autres produits. Aucun problème de cible n'est établi. Erreur acceptée, à seulement 0,4 point au-dessus du seuil. |
| `5412971116072` | yaourts → sauces ; 78,8 % | Pot de yaourt Pur Natur nature, beige, photographié près d'un autre objet. La forme du pot peut évoquer une sauce ou un condiment ; le mot « yaourt » est visible sur l'étiquette. Erreur du modèle, mais le seuil fonctionne ici : la brique répond « je ne sais pas ». |

## Deux pistes d'amélioration issues de cette planche

1. **Clarifier les frontières de catégorie avant d'ajouter des données.** Définir
   explicitement le classement du skyr (`3329770083233`) et des tartinables tels
   que le houmous (`5000128583954`), puis auditer des exemples supplémentaires
   d'entraînement et de validation. Cette clarification doit être décidée selon
   les besoins de NutriScope, sans modifier rétrospectivement les cibles ni le
   score du test présent.
2. **Enrichir les vues et les contenants réellement difficiles.** Collecter des
   photos supplémentaires hors du test : multipacks Orangina, gobelets PastaBox,
   boîtes de condiment vues de côté, canettes horizontales et sachets à fenêtre.
   Comparer sur une future validation des augmentations couvrant mieux ces
   orientations et des cadrages centrés sur le produit, tout en gardant le texte
   lisible. Les photos de comté et d'Activia justifient aussi de varier les fonds
   et les visuels de recette pour limiter les raccourcis possibles.

La sélection privilégie la confiance et la diversité des paires de confusion :
ses proportions ne décrivent donc pas toutes les erreurs. Onze erreurs sur les
douze affichées sont acceptées, contre **24 erreurs parmi 373 réponses acceptées**
sur le test entier. La confiance élevée n'est pas une certitude de justesse.

Photos : **contributeurs Open Food Facts**, licence **CC BY-SA**.
