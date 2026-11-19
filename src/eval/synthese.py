"""Compte les verdicts posés à la main et rend le chiffre du tour de table.

Usage : python -m src.eval.synthese resultats/eval_sans_rag.csv [resultats/eval_avec_rag.csv ...]
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

from src.eval.mesurer import CONFORMES, ERREURS, VERDICTS


def synthese(chemin: Path) -> dict:
    with open(chemin, encoding="utf-8", newline="") as f:
        lignes = list(csv.DictReader(f, delimiter=";"))
    verdicts = Counter(l["verdict"].strip() for l in lignes)
    non_poses = verdicts.pop("", 0)
    inconnus = {v: n for v, n in verdicts.items() if v not in VERDICTS}
    conformes = sum(n for v, n in verdicts.items() if v in CONFORMES)
    erreurs = sum(n for v, n in verdicts.items() if v in ERREURS)
    latences = [float(l["latence_s"]) for l in lignes if l.get("latence_s")]
    return {
        "fichier": str(chemin), "questions": len(lignes), "conformes": conformes, "erreurs": erreurs,
        "non_poses": non_poses, "inconnus": inconnus, "detail": dict(verdicts),
        "latence_moyenne_s": round(sum(latences) / len(latences), 1) if latences else None,
    }


def main() -> None:
    for chemin in sys.argv[1:]:
        s = synthese(Path(chemin))
        print(f"\n{s['fichier']}")
        print(f"  conformes : {s['conformes']} / {s['questions']}   "
              f"erreurs (inventé, non sourcé, outil détourné) : {s['erreurs']}   "
              f"latence moyenne : {s['latence_moyenne_s']} s")
        for verdict in VERDICTS:
            if s["detail"].get(verdict):
                print(f"  {verdict:<20} {s['detail'][verdict]}")
        if s["non_poses"]:
            print(f"  ATTENTION : {s['non_poses']} verdict(s) non posé(s)")
        if s["inconnus"]:
            print(f"  ATTENTION : verdicts hors liste {s['inconnus']}")


if __name__ == "__main__":
    main()
