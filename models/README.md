# Modèle d'images — TP 17

Le modèle entraîné et évalué est livré avec ses métadonnées et les diagnostics.
Sur 525 photos : **81,5 % d'accuracy**, **71,0 % de couverture** au seuil 0,80,
et **93,6 % de justesse parmi les réponses**. Les résultats proviennent de
l'évaluation enregistrée dans [`dl_images.ipynb`](../notebooks/dl_images.ipynb).

- `images_efficientnetb0.keras` : modèle retenu, augmentation et prétraitement
  EfficientNet inclus, entrée RGB 224 × 224 en pixels 0–255 avec bandes noires.
- `images_efficientnetb0.json` : rayons ordonnés, seuil choisi sur la validation,
  empreintes et scores. `etat_evaluation` vaut `en_attente` avant le test, puis
  `terminee` après la sauvegarde du bilan.
- `evaluation_images_test.json` : probabilités de l'évaluation unique et contexte.
- `confusion_images_test.png`, `erreurs_images_test.png` et
  `erreurs_images_test.csv` : diagnostics du test, si des erreurs sont présentes.

Conserver ensemble le modèle, ses métadonnées et la trace du test. La brique
`src/classifieur_images.py` vérifie l'empreinte SHA-256 avant le chargement.

La procédure d'exécution et de reprise est décrite dans
[`tp17_execution.md`](../docs/ml/tp17_execution.md).

Photos : **contributeurs Open Food Facts**, licence **CC BY-SA**.
