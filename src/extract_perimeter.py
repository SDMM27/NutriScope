"""Extrait, nettoie et prépare les cinq fichiers utilisés par PostgreSQL."""

try:
    from src.etl_pipeline import preparer_pipeline
except ModuleNotFoundError:
    from etl_pipeline import preparer_pipeline


if __name__ == "__main__":
    brut, propre, journal, tables = preparer_pipeline()
    print(f"France : {len(brut):,} lignes projetées ; {len(propre):,} produits après TP9.")
    print("Fichiers Parquet produits : " + ", ".join(f"{nom}={len(df):,}" for nom, df in tables.items()))
    print("Rapport : docs/data/rapport_nettoyage.md")
