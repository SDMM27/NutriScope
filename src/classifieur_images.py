"""Inférence du TP 17. Photos : CC BY-SA, contributeurs Open Food Facts.

Le modèle reçoit des pixels RGB 0–255, redimensionnés avec bandes noires.
Le prétraitement EfficientNet est déjà inclus dans le fichier Keras.
"""
from __future__ import annotations

import json
import math
import hashlib
from pathlib import Path


MODELES = Path(__file__).resolve().parents[1] / "models"


def _verifier_metadonnees(meta):
    rayons = meta.get("rayons")
    if (not isinstance(rayons, list) or len(rayons) < 2
            or not all(isinstance(r, str) and r for r in rayons)
            or len(set(rayons)) != len(rayons)):
        raise ValueError("Les métadonnées doivent contenir des rayons uniques et ordonnés.")
    taille = meta.get("taille_image")
    if type(taille) is not int or taille <= 0:
        raise ValueError("taille_image doit être un entier positif.")
    seuil = meta.get("seuil")
    if (isinstance(seuil, bool) or not isinstance(seuil, (int, float))
            or not math.isfinite(seuil) or not 0 <= seuil <= 1):
        raise ValueError("seuil doit être un nombre entre 0 et 1.")
    if meta.get("pretraitement") != "rgb_resize_with_pad_uint8_0_255":
        raise ValueError("Prétraitement absent ou incompatible avec cette brique.")


def interpreter_probabilites(probabilites, rayons, seuil):
    """Applique le seuil ; la confiance est un score softmax non calibré."""
    if (isinstance(seuil, bool) or not isinstance(seuil, (int, float))
            or not math.isfinite(seuil) or not 0 <= seuil <= 1):
        raise ValueError("Seuil invalide.")
    scores = [float(p) for p in probabilites]
    if (len(scores) != len(rayons) or not scores
            or any(not math.isfinite(p) or not 0 <= p <= 1 for p in scores)
            or not math.isclose(sum(scores), 1.0, abs_tol=1e-4)):
        raise ValueError("Sortie du modèle invalide : probabilités attendues par rayon.")
    indice = max(range(len(scores)), key=scores.__getitem__)
    confiance = scores[indice]
    accepte = confiance >= seuil
    return {
        "rayon": rayons[indice] if accepte else None,
        "confiance": confiance,
        "statut": "ok" if accepte else "je ne sais pas",
    }


def pretraiter_image(chemin, taille):
    """Même décodage, padding et conversion uint8 que le notebook, sans /255."""
    chemin = Path(chemin)
    if not chemin.is_file():
        raise FileNotFoundError(f"Photo introuvable : {chemin}")
    import tensorflow as tf

    try:
        # JPEG et PNG sont acceptés ; une éventuelle animation n'est pas développée.
        image = tf.io.decode_image(tf.io.read_file(str(chemin)), channels=3,
                                   expand_animations=False)
        image = tf.image.resize_with_pad(image, taille, taille)
        return tf.cast(image, tf.uint8)
    except tf.errors.OpError as exc:
        raise ValueError(f"Photo illisible : {chemin}") from exc


class ClassifieurImages:
    """Charger une instance au démarrage de l'API, puis appeler predire(photo)."""

    def __init__(self, modele=None, metadonnees=None):
        modele = Path(modele) if modele is not None else MODELES / "images_efficientnetb0.keras"
        metadonnees = (Path(metadonnees) if metadonnees is not None
                       else modele.with_suffix(".json"))
        self.metadonnees = json.loads(metadonnees.read_text(encoding="utf-8"))
        _verifier_metadonnees(self.metadonnees)
        if not modele.is_file():
            raise FileNotFoundError(f"Modèle introuvable : {modele}")
        empreinte_attendue = self.metadonnees.get("sha256_fichier_modele")
        if empreinte_attendue is not None:
            if hashlib.sha256(modele.read_bytes()).hexdigest() != empreinte_attendue:
                raise ValueError("Le fichier du modèle ne correspond pas aux métadonnées (SHA-256).")
        import keras

        self.modele = keras.models.load_model(modele, compile=False)
        taille = self.metadonnees["taille_image"]
        if tuple(self.modele.input_shape[1:]) != (taille, taille, 3):
            raise ValueError("La taille d'entrée du modèle ne correspond pas aux métadonnées.")
        if self.modele.output_shape[-1] != len(self.metadonnees["rayons"]):
            raise ValueError("Le nombre de sorties ne correspond pas aux rayons.")

    def predire(self, chemin):
        image = pretraiter_image(chemin, self.metadonnees["taille_image"])
        probabilites = self.modele.predict(image[None, ...], verbose=0)[0]
        return interpreter_probabilites(
            probabilites, self.metadonnees["rayons"], self.metadonnees["seuil"]
        )

