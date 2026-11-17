"""Mesures réelles OCR + modèle ; attentes lues seulement pour calculer les scores.

python outils/mesurer_scanner.py --historique
python outils/mesurer_scanner.py --manifest data/scanner_demo/manifest.json --palier 3
python outils/mesurer_scanner.py --manifest data/scanner_demo/manifest.json --palier 6 --catalogue-json outils/fixtures_scanner/catalogue.json
"""
import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from src.assistant.client_ollama import ClientOllama
from src.assistant.scanner import repondre_photo
from src.scanner.scanner import VERSION, scanner_photo


def empreinte(chemin):
    return hashlib.sha256(Path(chemin).read_bytes()).hexdigest()


def mesurer(manifest, catalogue, client, palier):
    description = json.loads(Path(manifest).read_text(encoding="utf-8-sig"))
    lignes = []
    for cas in description["cas"]:
        photo = Path(manifest).resolve().parent / cas["photo"]
        debut = time.perf_counter()
        print(f"{cas['id']} : OCR + {client.modele}...", flush=True)
        ligne = {"id": cas["id"], "photo_sha256": empreinte(photo),
                 "attendu": cas["statut_attendu"], "code_attendu": cas.get("code_attendu"),
                 "erreur": "", "reponse": ""}
        try:
            if palier == 6:
                r = repondre_photo(photo, catalogue, client)
                scan, ligne["reponse"] = r["scanner"], r["reponse"]
            else:
                scan = scanner_photo(photo, catalogue, client)
            ligne.update(statut=scan["statut"], resultat=scan)
            code = (scan.get("produit") or {}).get("code")
            ligne["mauvais_rattachement"] = scan["statut"] == "verifie" and (
                cas["statut_attendu"] != "verifie" or code != cas.get("code_attendu"))
            ligne["correct"] = scan["statut"] == cas["statut_attendu"] and not ligne["mauvais_rattachement"]
        except (RuntimeError, ConnectionError, ValueError, OSError, subprocess.SubprocessError) as e:
            ligne.update(statut="erreur_technique", erreur=str(e), correct=False,
                         mauvais_rattachement=False, resultat=None)
        ligne["latence_s"] = round(time.perf_counter() - debut, 3)
        lignes.append(ligne)
        print(f"  {ligne['statut']} / attendu {ligne['attendu']} ; {ligne['latence_s']} s", flush=True)
    return description, lignes


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--historique", action="store_true")
    p.add_argument("--manifest", type=Path)
    p.add_argument("--catalogue-json", type=Path, help="Snapshot de catalogue (liste de lignes), sinon Parquets TP18")
    p.add_argument("--palier", type=int, choices=[3, 6], default=3)
    p.add_argument("--modele", default="qwen3:8b")
    p.add_argument("--sortie", type=Path, default=RACINE / "resultats/scanner")
    args = p.parse_args()
    historique = args.sortie / "historique.jsonl"
    if args.historique:
        print(historique.read_text(encoding="utf-8") if historique.exists() else "Aucune mesure enregistrée.")
        return
    if not args.manifest:
        p.error("--manifest est obligatoire pour mesurer")
    if args.catalogue_json:
        catalogue = json.loads(args.catalogue_json.read_text(encoding="utf-8-sig"))
        signature_catalogue = empreinte(args.catalogue_json)
    else:
        from src.scanner.catalogue import CatalogueParquet
        catalogue = CatalogueParquet()
        signature_catalogue = {f: empreinte(RACINE / "data/extracts" / f)
                               for f in ("products.parquet", "nutrients.parquet")}
    client = ClientOllama(modele=args.modele, temperature=0, timeout=180)
    description, lignes = mesurer(args.manifest, catalogue, client, args.palier)
    if not lignes:
        p.error("Le jeu de mesure est vide")
    args.sortie.mkdir(parents=True, exist_ok=True)
    date = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    fichier = args.sortie / f"{date}_palier{args.palier}.json"
    bilan = {"date_utc": date, "version": VERSION, "palier_exerce": args.palier,
             "modele": args.modele, "temperature": 0, "ocr": "Windows.Media.Ocr",
             "python": platform.python_version(), "type_images": description["type_images"],
             "provenance": description["provenance"], "manifest_sha256": empreinte(args.manifest),
             "catalogue_sha256": signature_catalogue, "total": len(lignes),
             "catalogue": {"type": "snapshot_json" if args.catalogue_json else "parquets_complets_duckdb",
                           **getattr(catalogue, "statistiques", {})},
             "code_sha256": {f: empreinte(RACINE / f) for f in
                             ("src/scanner/scanner.py", "src/scanner/catalogue.py", "src/scanner/ocr.py", "src/scanner/ocr_windows.ps1",
                              "src/assistant/scanner.py", "src/assistant/client_ollama.py")},
             "corrects": sum(l["correct"] for l in lignes),
             "mauvais_rattachements": sum(l["mauvais_rattachement"] for l in lignes),
             "erreurs_techniques": sum(bool(l["erreur"]) for l in lignes),
             "details": str(fichier)}
    fichier.write_text(json.dumps({"bilan": bilan, "cas": lignes}, ensure_ascii=False, indent=2), encoding="utf-8")
    with fichier.with_suffix(".csv").open("w", encoding="utf-8-sig", newline="") as f:
        colonnes = ["id", "attendu", "statut", "correct", "mauvais_rattachement", "latence_s", "reponse", "erreur"]
        writer = csv.DictWriter(f, fieldnames=colonnes, delimiter=";", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(lignes)
    with historique.open("a", encoding="utf-8") as f:
        f.write(json.dumps(bilan, ensure_ascii=False) + "\n")
    print(json.dumps(bilan, ensure_ascii=False, indent=2))
    if bilan["corrects"] != bilan["total"] or bilan["mauvais_rattachements"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
