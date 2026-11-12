"""Contrat de rejet et chargement ; intégration TensorFlow si disponible."""
import importlib.util
import json
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.classifieur_images import (
    ClassifieurImages, _verifier_metadonnees, interpreter_probabilites,
    pretraiter_image,
)


def metadonnees():
    return {"rayons": ["eaux", "sodas"], "taille_image": 16, "seuil": 0.8,
            "pretraitement": "rgb_resize_with_pad_uint8_0_255"}


def test_accepte_au_seuil_et_respecte_ordre_rayons():
    assert interpreter_probabilites([0.2, 0.8], ["eaux", "sodas"], 0.8) == {
        "rayon": "sodas", "confiance": 0.8, "statut": "ok"}


def test_rejette_sous_le_seuil():
    assert interpreter_probabilites([0.7, 0.3], ["eaux", "sodas"], 0.8) == {
        "rayon": None, "confiance": 0.7, "statut": "je ne sais pas"}


@pytest.mark.parametrize("scores", [[float("nan"), 0.2], [0.2], [0.9, 0.9],
                                   [-0.1, 1.1], [float("inf"), 0]])
def test_refuse_sorties_incoherentes(scores):
    with pytest.raises(ValueError):
        interpreter_probabilites(scores, ["eaux", "sodas"], 0.8)


@pytest.mark.parametrize("champ,valeur", [
    ("rayons", ["eaux", "eaux"]), ("taille_image", 0), ("taille_image", True),
    ("seuil", float("nan")), ("seuil", 1.1), ("seuil", True),
    ("pretraitement", "division_par_255"),
])
def test_refuse_metadonnees_incompatibles(champ, valeur):
    meta = metadonnees()
    meta[champ] = valeur
    with pytest.raises(ValueError):
        _verifier_metadonnees(meta)


def test_photo_absente(tmp_path):
    with pytest.raises(FileNotFoundError):
        pretraiter_image(tmp_path / "absente.jpg", 16)


def test_charge_une_seule_fois_et_verifie_sorties(tmp_path, monkeypatch):
    modele = tmp_path / "modele.keras"
    modele.touch()
    modele.with_suffix(".json").write_text(json.dumps(metadonnees()), encoding="utf-8")
    reseau = SimpleNamespace(input_shape=(None, 16, 16, 3), output_shape=(None, 2))
    charger = Mock(return_value=reseau)
    monkeypatch.setitem(sys.modules, "keras", SimpleNamespace(models=SimpleNamespace(load_model=charger)))
    instance = ClassifieurImages(modele)
    assert instance.modele is reseau
    charger.assert_called_once_with(modele, compile=False)
    reseau.output_shape = (None, 3)
    with pytest.raises(ValueError, match="sorties"):
        ClassifieurImages(modele)


def test_refuse_modele_remplace(tmp_path):
    modele = tmp_path / "modele.keras"
    modele.write_bytes(b"modele modifie")
    meta = metadonnees()
    meta["sha256_fichier_modele"] = "0" * 64
    modele.with_suffix(".json").write_text(json.dumps(meta), encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256"):
        ClassifieurImages(modele)


@pytest.mark.skipif(importlib.util.find_spec("tensorflow") is None,
                    reason="Intégration : nécessite l'environnement TensorFlow du TP 17")
def test_integration_sauvegarde_pretraitement_et_prediction(tmp_path):
    import keras
    import tensorflow as tf

    # Fixture technique uniquement : aucun entraînement ni score sur ces pixels.
    photo = tmp_path / "photo.png"
    pixels = tf.fill((8, 4, 3), tf.constant(200, dtype=tf.uint8))
    tf.io.write_file(str(photo), tf.io.encode_png(pixels))
    image = pretraiter_image(photo, 16)
    assert image.dtype == tf.uint8
    assert tuple(image.shape) == (16, 16, 3)
    assert int(tf.reduce_max(image)) == 200  # pas de normalisation externe
    assert int(tf.reduce_max(image[:, :4])) == 0  # bandes noires

    entree = keras.Input((16, 16, 3))
    x = keras.layers.GlobalAveragePooling2D()(entree)
    sortie = keras.layers.Dense(2, activation="softmax", kernel_initializer="zeros",
                               bias_initializer=keras.initializers.Constant([0., 2.]))(x)
    chemin = tmp_path / "modele.keras"
    keras.Model(entree, sortie).save(chemin)
    chemin.with_suffix(".json").write_text(json.dumps(metadonnees()), encoding="utf-8")
    classifieur = ClassifieurImages(chemin)
    assert classifieur.predire(photo)["rayon"] == "sodas"
    classifieur.metadonnees["seuil"] = 0.99
    assert classifieur.predire(photo)["rayon"] is None
    photo.write_bytes(b"pas une image")
    with pytest.raises(ValueError, match="illisible"):
        classifieur.predire(photo)
