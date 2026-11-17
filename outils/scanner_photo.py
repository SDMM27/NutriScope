"""Entrée photo de l'assistant, utilisable depuis la racine du dépôt."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.assistant.client_ollama import ClientOllama
from src.assistant.scanner import repondre_photo


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("photo", type=Path)
    p.add_argument("--catalogue-json", type=Path)
    p.add_argument("--modele", default="qwen3:8b")
    p.add_argument("--json", action="store_true", help="Affiche aussi les données et la trace OCR/LLM")
    args = p.parse_args()
    if args.catalogue_json:
        catalogue = json.loads(args.catalogue_json.read_text(encoding="utf-8-sig"))
    else:
        from src.scanner.catalogue import CatalogueParquet
        catalogue = CatalogueParquet()
    r = repondre_photo(args.photo, catalogue, ClientOllama(modele=args.modele))
    print(json.dumps(r, ensure_ascii=False, indent=2) if args.json else r["reponse"])


if __name__ == "__main__":
    main()
