"""Entrée photo de l'assistant : formulation déterministe des données contrôlées."""
from src.scanner import scanner_photo


def repondre_photo(photo, catalogue, client, **options):
    scan = scanner_photo(photo, catalogue, client, **options)
    if scan["statut"] == "illisible":
        texte = "Je ne peux pas lire suffisamment le tableau nutritionnel. Reprenez une photo nette du tableau, avec la base pour 100 g ou 100 ml."
    else:
        if scan["statut"] == "verifie":
            p = scan["produit"]
            texte = f"Produit concordant avec le catalogue : {p['nom']} — {p['marque']} (code {p['code']})."
            texte += f" Nutri-Score : {p['nutriscore'] or 'non renseigné'}. Source : Open Food Facts (ODbL)."
        else:
            texte = "Étiquette non vérifiée : je ne peux pas confirmer une fiche du catalogue ni son Nutri-Score."
        texte += f" Lecture OCR pour {scan['base']} (à contrôler sur l'emballage) : "
        texte += "; ".join(f"{k} : non renseigné" if v is None else
                           f"{k} : {v:g} {'kcal' if k == 'kcal' else 'g'}"
                           for k, v in scan["nutriments"].items()) + "."
    return {"reponse": texte, "scanner": scan}
