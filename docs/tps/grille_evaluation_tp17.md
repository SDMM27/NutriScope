# **Grille d'évaluation par compétences — TP 17, Classifieur d'images**

Évaluation formative, par équipe, sans note : chaque compétence est située sur un niveau, d'après les livrables committés.

| # | Compétence | Maîtrisée si… |
|---|---|---|
| 1 | **Préparer un jeu d'images** | photos regardées et commentées, effectifs contrôlés, découpage fait avant l'augmentation, rayons reliés au périmètre de l'équipe |
| 2 | **Poser une référence** | CNN de zéro cohérent, score de validation lu par rapport au plancher annoncé |
| 3 | **Mettre en œuvre le transfert et l'augmentation** | choix justifiés (réseau, taille d'image, transformations adaptées à des emballages, couches dégelées ou non), comparaison sur la même validation |
| 4 | **Évaluer un modèle sur le test** | test ouvert une seule fois, accuracy par rayon, confusions principales nommées |
| 5 | **Analyser les erreurs du modèle** | erreurs variées et confiantes, commentées en mots propres (données ambiguës, erreur d'étiquette, limite du modèle) |
| 6 | **Livrer une brique réutilisable** | `src/classifieur_images.py` testé, chargé hors du notebook, seuil de confiance justifié par des chiffres |
| 7 | **Documenter les limites et les pistes** | deux paragraphes honnêtes, deux pistes qui découlent de la planche, crédit Open Food Facts, tag `v0.4` |

## **Lecture des niveaux**

| Niveau | Signification |
|---|---|
| Maîtrisé | attendus remplis et justifiés |
| En cours | fait, mais sans justification ou avec un défaut mineur |
| À reprendre | absent, ou erreur de méthode |

## **Erreurs de méthode**

| Erreur | Conséquence |
|---|---|
| Augmentation appliquée à la validation ou au test | compétence 3 à reprendre |
| Modèle choisi d'après le test | compétence 4 à reprendre |
| Photos réelles remplacées par des données simulées | jalon J4 non validé |
