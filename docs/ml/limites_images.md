# Limites du classifieur d'images — TP 17

Sur les 525 photos du test, le fine-tuning nº2 d'EfficientNetB0 classe correctement
428 photos : **81,5 % d'accuracy**, contre un plancher de 14,3 %. Les fromages
(72,0 %) et les yaourts (73,3 %) sont moins bien reconnus que les céréales
(90,7 %). Les confusions dominantes sont fromages → yaourts (9 photos), sodas →
eaux (8) et yaourts → sauces (7). La planche montre des emballages partagés
entre rayons, des images de recettes et des vues atypiques. Le pack de skyr
classé `fromages` par le manifest illustre aussi une frontière de taxonomie :
la prédiction `yaourts` est comptée comme fausse sans que cela démontre une
étiquette erronée. Les photos ne permettent pas de prouver quels indices le
réseau utilise. La [revue des 12 erreurs](analyse_erreurs_images.md) distingue
les observations visibles des hypothèses.

Au seuil **0,80**, choisi uniquement sur la validation, le modèle accepte
373 photos sur 525 (**71,0 % de couverture**) et en classe correctement 349
(**93,6 % de justesse parmi les réponses** ; IC de Wilson à 95 % : 90,6–95,6 %).
Il reste donc 24 erreurs acceptées et 152 abstentions. Le score softmax n'est
pas calibré ; même une erreur à 98,6 % passe le seuil. Le rejet des photos hors
des sept rayons n'est pas évalué. Les 75 photos par rayon, les variantes
proches d'un même produit et le mélange de photos studio et smartphone limitent
la généralisation. Les biscuits et snacks ne sont pas couverts, et les pâtes
représentent imparfaitement les plats préparés. Le modèle et le seuil n'ont pas
été modifiés après consultation du test.

## Deux pistes issues de la planche d'erreurs

1. **Clarifier la taxonomie et auditer des exemples hors du test.** Définir le
   classement du skyr (`3329770083233`) et des tartinables comme le houmous
   (`5000128583954`), puis vérifier la cohérence des futures données
   d'entraînement et de validation. Conserver les cibles du test présent.
2. **Enrichir les vues et les emballages difficiles.** Collecter des exemples
   supplémentaires hors du test : gobelets PastaBox, multipacks Orangina, boîte
   de moutarde vue de côté, canette Perrier horizontale et sachets à fenêtre.
   Comparer sur une future validation des augmentations d'orientation et des
   cadrages adaptés, tout en conservant le texte lisible. Varier aussi les fonds
   et les visuels de recettes, difficiles sur le comté et le pack Activia.

## Traçabilité

- Modèle : `models/images_efficientnetb0.keras` et métadonnées JSON associées.
- Scores et probabilités : `models/evaluation_images_test.json`.
- Matrice : `models/confusion_images_test.png`.
- Sélection illustrée : `models/erreurs_images_test.png` et CSV associé.
- Analyse photo par photo : [analyse_erreurs_images.md](analyse_erreurs_images.md).

Photos : **contributeurs Open Food Facts**, licence **CC BY-SA**.
