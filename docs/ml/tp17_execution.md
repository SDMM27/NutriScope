# Exécution et livraison du TP 17

## État vérifié

Le notebook est exécuté jusqu'à la section 7, sans sortie d'erreur. Le modèle,
ses métadonnées, les prédictions finales et les deux planches sont présents.
L'analyse visuelle finale est en section 5.4 du notebook et dans
[analyse_erreurs_images.md](analyse_erreurs_images.md).

| Mesure | Résultat du test |
|---|---:|
| Photos | 525, soit 75 par rayon |
| Accuracy sans rejet | 81,5 % — 428 / 525 |
| Seuil choisi sur la validation | 0,80 |
| Couverture | 71,0 % — 373 / 525 |
| Justesse parmi les réponses | 93,6 % — 349 / 373 |
| Erreurs acceptées | 24 |
| Abstentions | 152 |
| IC de Wilson à 95 % sur la justesse parmi les réponses | 90,6–95,6 % |

Les 18 tests passent dans la sortie enregistrée de la section 7, dont le test
TensorFlow de sauvegarde/rechargement, de prétraitement et de rejet. Deux
avertissements de dépréciation Keras/NumPy sont consignés, sans échec.

La vérification finale a recalculé les métriques à partir des probabilités
sauvegardées, contrôlé les 525 affectations au test, l'empreinte des images et le
SHA-256 du fichier du modèle. Aucun nouvel entraînement, choix de seuil ou
nouvelle évaluation comparative sur le test n'a été effectué.

## Utiliser la brique

Depuis la racine du dépôt, dans un environnement Python 3.12 :

```bash
python -m pip install -r requirements.txt
python -m pytest tests/test_classifieur_images.py -q
```

Le modèle a été sauvegardé avec Python 3.12.3, TensorFlow 2.20.0, Keras 3.13.2
et NumPy 2.5.4, comme indiqué dans ses métadonnées. Les trois dernières versions
sont fixées dans `requirements.txt`.

```python
from src.classifieur_images import ClassifieurImages

classifieur = ClassifieurImages()  # une instance au démarrage du service
resultat = classifieur.predire("chemin/produit.jpg")
# {"rayon": "sodas", "confiance": 0.91, "statut": "ok"}
# ou {"rayon": None, "confiance": 0.62, "statut": "je ne sais pas"}
```

Ces valeurs illustrent le contrat de sortie, pas une nouvelle mesure du modèle.
Le prétraitement est RGB, redimensionnement avec bandes noires puis conversion
uint8, sans division externe par 255. Le fichier Keras contient le prétraitement
EfficientNet ; les augmentations sont inactives pendant l'inférence.

## Revoir les résultats sans réentraîner

Le test a déjà été ouvert. Conserver `models/evaluation_images_test.json` : les
cellules de métriques et de planches réutilisent ses probabilités. Tout changement
de poids, de seuil, de vocabulaire ou d'images est refusé par le contrôle du
contexte. Ne pas supprimer cette trace pour comparer de nouveaux modèles.

Pour une reprise après redémarrage du kernel, exécuter les sections 0 à 2.1
(jusqu'à la création des datasets), puis :

```python
import json

chemin_modele = MODELES / "images_efficientnetb0.keras"
meta = json.loads(chemin_modele.with_suffix(".json").read_text(encoding="utf-8"))
modele = keras.models.load_model(chemin_modele, compile=False)
nom_retenu = meta["version_retenue"]
candidats = {nom_retenu: (meta["accuracy_validation"], None)}
y_val = val_df["rayon"].map(NUM).to_numpy()
```

Exécuter ensuite les sections 4 à 7. Le seuil est recalculé sur la même validation
et doit correspondre au contexte enregistré ; les prédictions du test sont relues.
La génération des limites produit un diagnostic automatique. La revue visuelle
finale indépendante reste dans `docs/ml/analyse_erreurs_images.md` et en section
5.4 ; conserver ses observations lors d'une régénération du document de limites.

## Livrables

- `notebooks/dl_images.ipynb`, avec sorties et analyse visuelle finale.
- `models/images_efficientnetb0.keras` et `models/images_efficientnetb0.json`.
- `models/evaluation_images_test.json`, trace de l'évaluation.
- `models/confusion_images_test.png`, `models/erreurs_images_test.png` et CSV.
- `src/classifieur_images.py` et `tests/test_classifieur_images.py`.
- `docs/ml/limites_images.md` et `docs/ml/analyse_erreurs_images.md`.
- `docs/ml/manifest_images.csv` et `docs/ml/decoupage_images.csv`.

Les photos sont ignorées par Git. Si elles manquent pour revoir le notebook :

```bash
python src/telecharger_images.py --rayons eaux sodas yaourts fromages cereales pates sauces
```

Une source distante peut avoir évolué : le contrôle des empreintes empêche de
confondre des photos modifiées avec le test livré. Le tag `v0.4` désigne le jalon
TP 14 à 17 ; il se pose après vérification des autres travaux du jalon. Le présent
contrôle porte sur le TP 17.

Photos : **contributeurs Open Food Facts**, licence **CC BY-SA**.
