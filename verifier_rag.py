"""Six contrôles avant le TP 19 : Ollama, modèle, dimensions, norme, Chroma, collection.

Usage, à la racine de votre dépôt :  python verifier_rag.py
Chaque ligne doit finir en [OK]. Une ligne [KO] dit quoi faire. Rien n'est écrit dans votre dépôt.
"""

from __future__ import annotations

import json
import math
import os
import shutil
import sys
import tempfile
import urllib.request

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

BASE = os.environ.get("NUTRISCOPE_EMBED_BASE_URL", "http://localhost:11434/v1").rstrip("/")
RACINE_OLLAMA = BASE[:-3] if BASE.endswith("/v1") else BASE
MODELE = os.environ.get("NUTRISCOPE_MODELE_EMBEDDINGS", "qwen3-embedding:0.6b")
DIMENSION = 1024
VERSION_CHROMA = "1.5.9"

resultats: list[bool] = []


def ligne(ok: bool, intitule: str, detail: str = "") -> bool:
    resultats.append(ok)
    print(f"[{'OK' if ok else 'KO'}] {intitule}" + (f" — {detail}" if detail else ""))
    return ok


def verifier_ollama() -> list[str] | None:
    try:
        with urllib.request.urlopen(f"{RACINE_OLLAMA}/api/tags", timeout=5) as reponse:
            modeles = [m["name"] for m in json.load(reponse).get("models", [])]
    except Exception as e:  # noqa: BLE001
        ligne(False, "1. Ollama joignable",
              f"{RACINE_OLLAMA} ne répond pas ({type(e).__name__}) : lancez Ollama ou corrigez NUTRISCOPE_EMBED_BASE_URL")
        ligne(False, f"2. modèle {MODELE} présent", "impossible à vérifier sans Ollama")
        return None
    ligne(True, "1. Ollama joignable", RACINE_OLLAMA)
    present = MODELE in modeles or f"{MODELE}:latest" in modeles
    ligne(present, f"2. modèle {MODELE} présent", "" if present else f"lancez : ollama pull {MODELE}")
    return modeles


def verifier_vecteur() -> list[float] | None:
    vecteur = None
    try:
        from openai import OpenAI

        client = OpenAI(base_url=BASE, api_key=os.environ.get("NUTRISCOPE_EMBED_API_KEY", "ollama"))
        reponse = client.embeddings.create(model=MODELE, input=["Pâte à tartiner aux noisettes et au cacao"])
        vecteur = list(reponse.data[0].embedding)
        ligne(len(vecteur) == DIMENSION, f"3. {DIMENSION} dimensions", f"{len(vecteur)} reçues")
    except Exception as e:  # noqa: BLE001
        ligne(False, f"3. {DIMENSION} dimensions", f"appel impossible ({type(e).__name__} : {str(e)[:120]})")
    if vecteur:
        norme = math.sqrt(sum(x * x for x in vecteur))
        ligne(abs(norme - 1) < 1e-3, "4. norme proche de 1", f"{norme:.4f}")
    else:
        ligne(False, "4. norme proche de 1", "aucun vecteur à mesurer")
    return vecteur


def verifier_chroma(vecteur: list[float] | None) -> None:
    dossier = tempfile.mkdtemp(prefix="verifier_rag_")
    try:
        import chromadb
    except ImportError:
        ligne(False, "5. collection cosinus créée", f"lancez : pip install chromadb=={VERSION_CHROMA}")
        ligne(False, "6. vecteur inséré puis retrouvé", "Chroma absent")
        return
    try:
        version_ok = chromadb.__version__ == VERSION_CHROMA
        client = chromadb.PersistentClient(path=dossier)
        collection = client.create_collection("verification", configuration={"hnsw": {"space": "cosine"}},
                                              embedding_function=None)
        espace = (collection.configuration.get("hnsw") or {}).get("space")
        detail = f"chromadb {chromadb.__version__}, espace {espace}"
        if not version_ok:
            detail += f" : la promo travaille en chromadb=={VERSION_CHROMA}"
        ligne(espace == "cosine" and version_ok, "5. collection cosinus créée", detail)
        if not vecteur:
            ligne(False, "6. vecteur inséré puis retrouvé", "aucun vecteur à insérer")
            return
        collection.upsert(ids=["fiche:verification"], embeddings=[vecteur], documents=["vérification"],
                          metadatas=[{"code": "verification"}])
        r = collection.query(query_embeddings=[vecteur], n_results=1, include=["distances"])
        distance = r["distances"][0][0]
        ligne(r["ids"][0] == ["fiche:verification"] and abs(distance) < 1e-3,
              "6. vecteur inséré puis retrouvé", f"distance {abs(distance):.4f}")
    except Exception as e:  # noqa: BLE001
        ligne(False, "5-6. Chroma", f"{type(e).__name__} : {str(e)[:160]}")
    finally:
        shutil.rmtree(dossier, ignore_errors=True)


def main() -> int:
    print(f"Vérification RAG — serveur {BASE}, modèle {MODELE}\n")
    verifier_ollama()
    verifier_chroma(verifier_vecteur())
    n_ok = sum(resultats)
    total = len(resultats)
    print(f"\n{n_ok} / {total} au vert." + (" Vous pouvez partir en TP." if n_ok == total else
                                           " Corrigez les lignes [KO] avant le TP."))
    return 0 if n_ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
