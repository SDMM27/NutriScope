# **TP 17 — Classifieur d'images (mercredi 04/11, demi-journée) · jalon J4**

NutriScope doit reconnaître le rayon d'un produit à partir de sa photo. À vous de construire cette brique dans le dépôt de votre équipe, **sur vos rayons et sur les vraies photos du bucket Open Food Facts**, avec ce que nous avons vu lundi et mardi (`courses/dl/`, 001 à 004).

Aucun code de modèle n'est fourni : les choix sont les vôtres, et vous devrez les défendre.

## **L'environnement**

Python 3.12 obligatoire. Dans un environnement virtuel activé :

```
pip install -r requirements.txt
```

Si votre environnement des cours `dl/` fonctionne, gardez-le et ajoutez seulement `pytest`.

## **Les données**

`manifest_bucket.csv` référence 7 500 photos de face (15 rayons × 500, produits vendus en France) sur le bucket public `openfoodfacts-images`. Copiez ce fichier et `telecharger_images.py` dans votre dépôt, à côté l'un de l'autre, puis, depuis la racine du dépôt :

```
python telecharger_images.py --liste
python telecharger_images.py --rayons <vos 5 à 8 rayons>
```

- Prenez les rayons les plus proches de votre `docs/perimetre.md`, et notez l'écart s'il y en a un.
- Les photos arrivent dans `data/images/<rayon>/<code>.jpg`, en 400 px. Ajoutez `data/images/` à votre `.gitignore`.
- Si le script signale des échecs, relancez la même commande : il ne reprend que ce qui manque.
- Ce sont des photos de contributeurs : flous, mains, fonds variés, quelques intrus. C'est le vrai problème de l'application.
- Licence CC BY-SA : créditez « contributeurs Open Food Facts » dans vos livrables.

## **Ce qui est attendu**

1. **Un jeu maîtrisé :** photos regardées, effectifs contrôlés, découpage entraînement / validation / test.
2. **Une référence :** un CNN simple entraîné de zéro.
3. **Un modèle par transfert :** réseau pré-entraîné, augmentation de données choisie pour *ces* images, fine-tuning si vous le jugez utile. Comparez à la référence sur la même validation.
4. **Une évaluation sérieuse sur le test :** accuracy par rayon, matrice de confusion, et surtout la **planche des erreurs les plus parlantes** (les photos confondues, affichées et commentées).
5. **Une brique utilisable par l'application :** à partir du chemin d'une photo, votre code renvoie le rayon et une confiance, et sait répondre « je ne sais pas » sous un seuil que vous justifiez. L'API du TP 23 l'appellera.

## **Les règles**

- Uniquement les photos réelles : pas de données simulées.
- Le test ne sert qu'une fois, sur le modèle déjà choisi.
- Rien de ce qui est augmenté ne doit toucher la validation ni le test.
- Chaque score se lit par rapport à un plancher, que vous annoncez.

## **À committer**

| Fichier | Contenu |
|---|---|
| `notebooks/dl_images.ipynb` | le travail complet, exécuté |
| `models/` | le modèle sauvegardé et ses métadonnées (rayons, taille d'image, seuil, score de test) |
| `src/classifieur_images.py` | la brique du point 5, avec au moins un test |
| `docs/ml/limites_images.md` | deux paragraphes honnêtes sur ce que le modèle rate, puis **deux pistes d'amélioration** tirées de votre planche d'erreurs |

Tag `v0.4` sur le commit final : il clôt les travaux de modélisation des TP 14 à 17. Jalon J4 atteint.

Évaluation par compétences, sans note : `grille_evaluation_tp17.md`.
