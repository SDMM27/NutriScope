"""Rapport avant / après nettoyage (TP 9, point 4).

Usage, depuis la racine du dépôt :

    python -m src.report
    python -m src.report --source data/echantillon_france.csv --sortie docs/data/rapport_nettoyage.md

Le rapport est généré, jamais édité à la main. Seule la date d'en-tête
change d'une exécution à l'autre.
"""

import argparse
from datetime import date
from pathlib import Path

import pandas as pd

from src.cleaning import (
    KCAL_MAX, NUTRIMENT_MAX_G, SEL_PAR_SODIUM, TOLERANCE_SEL_SODIUM, TOLERANCE_SOUS_TOTAL_G,
    COLONNES_0_100, CompteRendu, calcul_energie_449, lire_brut, nettoyer, typer_colonnes,
)

SOURCE_PAR_DEFAUT = Path("data/echantillon_france.csv")
SORTIE_PAR_DEFAUT = Path("docs/data/rapport_nettoyage.md")

COLONNES_CLES = [
    "product_name", "brands", "categories_tags", "pnns_groups_1", "nutriscore_grade",
    "energy-kcal_100g", "fat_100g", "saturated-fat_100g", "carbohydrates_100g",
    "sugars_100g", "fiber_100g", "proteins_100g", "salt_100g",
]


# ============================================================
# Diagnostic (mêmes définitions que la démo 3.2.1)
# ============================================================

def diagnostiquer(df: pd.DataFrame) -> pd.Series:
    """Nombre de lignes en anomalie par règle métier.

    Une valeur manquante ne viole aucune règle. Les définitions reprennent
    celles du diagnostic du matin : l'énergie incohérente ne tient pas compte
    de l'exception alcool, c'est voulu (on voit ce qu'il reste).
    """
    df = typer_colonnes(df)[0]
    kcal = df["energy-kcal_100g"]
    glucides, lipides = df["carbohydrates_100g"], df["fat_100g"]
    calcul = calcul_energie_449(df)
    macro_positif = (df[["carbohydrates_100g", "proteins_100g", "fat_100g"]] > 0).any(axis=1)

    anomalies = {
        "nutriment hors 0–100 g": ((df[COLONNES_0_100] < 0) | (df[COLONNES_0_100] > NUTRIMENT_MAX_G)).any(axis=1),
        f"énergie hors 0–{KCAL_MAX:.0f} kcal": (kcal < 0) | (kcal > KCAL_MAX),
        "énergie incohérente avec 4/4/9": (calcul >= 50) & ((kcal - calcul).abs() / calcul > 0.5),
        "énergie nulle avec macronutriments": (kcal == 0) & macro_positif,
        "sucres > glucides": df["sugars_100g"] > glucides + TOLERANCE_SOUS_TOTAL_G,
        "saturés > lipides": df["saturated-fat_100g"] > lipides + TOLERANCE_SOUS_TOTAL_G,
        "sel ≠ sodium × 2,5": (df["salt_100g"] - SEL_PAR_SODIUM * df["sodium_100g"]).abs() > TOLERANCE_SEL_SODIUM,
    }
    lignes = pd.DataFrame(anomalies)
    lignes["au moins une"] = lignes.any(axis=1)
    return lignes.sum().astype(int)


# ============================================================
# Mise en forme
# ============================================================

def _nombre(n) -> str:
    return f"{n:,}".replace(",", " ")


def _pct(n: int, total: int) -> str:
    return f"{n / total * 100:.1f} %" if total else "—"


def _tableau(entetes: list[str], lignes: list[list]) -> str:
    """Tableau Markdown (sans dépendance à tabulate)."""
    rendu = ["| " + " | ".join(entetes) + " |", "|" + "|".join("---" for _ in entetes) + "|"]
    rendu += ["| " + " | ".join(str(v) for v in ligne) + " |" for ligne in lignes]
    return "\n".join(rendu)


def _details(compte_rendu: CompteRendu) -> str:
    details = [f"{nom} : {_nombre(n)}" for nom, n in compte_rendu.details.items() if n]
    return " ; ".join(details) if details else "—"


# ============================================================
# Rapport
# ============================================================

def generer_rapport(avant: pd.DataFrame, apres: pd.DataFrame, journal: list[CompteRendu],
                    chemin: str | Path, source: str = str(SOURCE_PAR_DEFAUT),
                    jour: date | None = None) -> str:
    """Écrit le rapport Markdown dans `chemin` et renvoie son contenu."""
    jour = jour or date.today()
    s = []

    s.append("# Rapport de nettoyage NutriScope\n")
    s.append(f"- Généré le {jour.isoformat()} par `python -m src.report` — ne pas éditer à la main")
    s.append(f"- Source : `{source}`")
    s.append("- Données : Open Food Facts, © Open Food Facts contributors — licence ODbL\n")

    s.append("## Volumétrie\n")
    s.append(_tableau(["", "avant", "après", "écart"], [
        ["lignes", _nombre(len(avant)), _nombre(len(apres)), _nombre(len(apres) - len(avant))],
        ["colonnes", avant.shape[1], apres.shape[1], apres.shape[1] - avant.shape[1]],
        ["codes distincts", _nombre(avant["code"].nunique()), _nombre(apres["code"].nunique()),
         _nombre(apres["code"].nunique() - avant["code"].nunique())],
    ]) + "\n")

    s.append("## Lignes touchées par règle\n")
    s.append("Une ligne touchée par plusieurs sous-règles compte une fois dans « touchées », "
             "une fois par sous-règle dans le détail.\n")
    s.append(_tableau(["règle", "lignes avant", "lignes après", "touchées", "détail"], [
        [f"`{cr.regle}`", _nombre(cr.lignes_avant), _nombre(cr.lignes_apres),
         _nombre(cr.lignes_touchees), _details(cr)]
        for cr in journal
    ]) + "\n")

    s.append("## Anomalies métier\n")
    s.append("Lignes en anomalie, mêmes définitions que le diagnostic de la démo 3.2.1.\n")
    diag_avant, diag_apres = diagnostiquer(avant), diagnostiquer(apres)
    s.append(_tableau(["anomalie", "avant", "après"], [
        [nom, _nombre(diag_avant[nom]), _nombre(diag_apres[nom])] for nom in diag_avant.index
    ]) + "\n")

    s.append("## Manquants sur les colonnes clés\n")
    lignes = []
    for col in COLONNES_CLES:
        m_avant = int(avant[col].isna().sum()) if col in avant.columns else None
        m_apres = int(apres[col].isna().sum()) if col in apres.columns else None
        lignes.append([
            f"`{col}`",
            "—" if m_avant is None else f"{_nombre(m_avant)} ({_pct(m_avant, len(avant))})",
            "retirée" if m_apres is None else f"{_nombre(m_apres)} ({_pct(m_apres, len(apres))})",
        ])
    s.append(_tableau(["colonne", "avant", "après"], lignes) + "\n")

    s.append("## Produits par rayon après nettoyage\n")
    rayons = apres["pnns_groups_1"].fillna("(vide)").value_counts()
    rayons = rayons.sort_index().sort_values(ascending=False, kind="stable")
    s.append(_tableau(["rayon", "produits", "part"], [
        [rayon, _nombre(n), _pct(n, len(apres))] for rayon, n in rayons.items()
    ]) + "\n")

    s.append("## Colonnes ajoutées et retirées\n")
    ajoutees = [c for c in apres.columns if c not in avant.columns]
    retirees = [c for c in avant.columns if c not in apres.columns]
    s.append(f"- ajoutées : {', '.join(f'`{c}`' for c in ajoutees) or 'aucune'}")
    s.append(f"- retirées : {', '.join(f'`{c}`' for c in retirees) or 'aucune'}")

    contenu = "\n".join(s) + "\n"
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(contenu, encoding="utf-8", newline="\n")
    return contenu


def main() -> None:
    parser = argparse.ArgumentParser(description="Nettoie l'extrait brut et génère le rapport avant / après.")
    parser.add_argument("--source", type=Path, default=SOURCE_PAR_DEFAUT)
    parser.add_argument("--sortie", type=Path, default=SORTIE_PAR_DEFAUT)
    args = parser.parse_args()

    brut = lire_brut(args.source)
    propre, journal = nettoyer(brut)
    generer_rapport(brut, propre, journal, args.sortie, source=args.source.as_posix())
    print(f"{_nombre(len(brut))} lignes lues, {_nombre(len(propre))} gardées -> {args.sortie.as_posix()}")


if __name__ == "__main__":
    main()
