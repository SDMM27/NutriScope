"""Point d'entrée du pipeline de données du TP13."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

import pandas as pd
from pyarrow.parquet import read_metadata

from src.cleaning import lire_brut
from src.cleaning import nettoyer as nettoyer_tp9
from src.config.settings import POSTGRES_DB_ALIAS
from src.etl_pipeline import extraire_brut, vers_tables_sql
from src.report import generer_rapport
from src.storage.commun import LICENCE
from src.storage.convert_parquet import convertir
from src.storage.export_features import chemin_schema, exporter, sha256
from src.storage.preparer_csv import preparer

RACINE = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Configuration:
    source: Path
    dossier_donnees: Path
    date_execution: date


@dataclass(frozen=True)
class ResultatEtape:
    duree_s: float
    lignes: int
    fichiers: tuple[Path, ...]


def charger(config: Configuration) -> ResultatEtape:
    """Fige le CSV ou le Parquet source et produit son manifeste daté."""
    debut = perf_counter()
    source = config.source
    extension = source.suffix.lower()
    if extension not in {".csv", ".parquet"}:
        raise ValueError(f"Format source non pris en charge : {source.name}")

    dossier = config.dossier_donnees / "raw"
    copie = dossier / f"produits_bruts_{config.date_execution:%Y%m%d}{source.suffix}"
    chemin_manifeste = copie.with_suffix(f"{copie.suffix}.manifest.json")
    dossier.mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory(dir=dossier) as temporaire:
        copie_temporaire = Path(temporaire) / copie.name
        if copie.exists():
            instantane = copie
            empreinte = sha256(copie)
            if sha256(source) != empreinte:
                raise FileExistsError(f"L'instantané {copie} existe avec un contenu différent.")
        else:
            shutil.copyfile(source, copie_temporaire)
            instantane = copie_temporaire
            empreinte = sha256(instantane)

        if extension == ".csv":
            with instantane.open(encoding="utf-8-sig", newline="") as fichier:
                enregistrements = csv.reader(fichier)
                next(enregistrements, None)
                lignes = sum(1 for enregistrement in enregistrements if enregistrement)
        else:
            lignes = read_metadata(instantane).num_rows

        if instantane == copie_temporaire:
            # Publie la copie complète sans écraser une copie créée entre-temps.
            try:
                os.link(copie_temporaire, copie)
            except FileExistsError:
                if sha256(copie) != empreinte:
                    raise FileExistsError(f"L'instantané {copie} existe avec un contenu différent.") from None

        manifeste = {
            "statut": "termine",
            "licence": LICENCE,
            "chemin_source": str(source),
            "nom_copie": copie.name,
            "date": config.date_execution.isoformat(),
            "SHA_256": empreinte,
        }
        manifeste_temporaire = Path(temporaire) / chemin_manifeste.name
        with manifeste_temporaire.open("w", encoding="utf-8") as fichier:
            json.dump(manifeste, fichier, indent=4, ensure_ascii=False)
        os.replace(manifeste_temporaire, chemin_manifeste)

    return ResultatEtape(perf_counter() - debut, lignes, (copie, chemin_manifeste))



def nettoyer(config: Configuration) -> ResultatEtape:
    """Produit le jeu nettoyé commun et les traces du nettoyage TP9."""
    debut = perf_counter()
    date_demandee = f"{config.date_execution:%Y%m%d}"
    dossier_brut = config.dossier_donnees / "raw"
    extension = config.source.suffix.lower()

    if extension not in {".csv", ".parquet"}:
        raise ValueError(f"Format du brut non pris en charge : {extension}")

    # TODO 1 — Retrouver un instantané et vérifier son intégrité.
    candidats = []
    for fichier in dossier_brut.glob("produits_bruts_????????.*"):
        if fichier.suffix.lower() != extension or not fichier.is_file():
            continue

        chemin_manifeste = fichier.with_suffix(f"{fichier.suffix}.manifest.json")
        if chemin_manifeste.is_file():
            candidats.append((fichier, chemin_manifeste))

    if not candidats:
        raise FileNotFoundError(
            f"Aucun brut {extension} avec manifeste dans {dossier_brut}. "
            "Lance d'abord l'étape charger."
        )

    nom_demande = f"produits_bruts_{date_demandee}"
    brut, chemin_manifeste = max(
        candidats,
        key=lambda candidat: (
            candidat[0].stem == nom_demande,
            candidat[0].stem,
        ),
    )

    with chemin_manifeste.open(encoding="utf-8") as fichier:
        manifeste = json.load(fichier)

    if manifeste.get("SHA_256") != sha256(brut):
        raise ValueError(f"L'empreinte du brut ne correspond pas au manifeste : {brut}")

    # TODO 2 — Préparer le DataFrame d'entrée, puis appliquer le TP9.
    if extension == ".csv":
        df_brut = lire_brut(brut)
        if "food_groups_tags" not in df_brut.columns:
            df_brut["food_groups_tags"] = None
    else:
        colonnes = set(read_metadata(brut).schema.to_arrow_schema().names)
        if {"countries_tags", "nutriments"} & colonnes:
            destination = (
                config.dossier_donnees / "extracts" / f"france_{brut.stem}.parquet"
            )
            df_brut = extraire_brut(brut, destination)
        else:
            df_brut = pd.read_parquet(brut)

    manquantes = {"code", "food_groups_tags"}.difference(df_brut.columns)
    if manquantes:
        raise ValueError(f"Colonnes manquantes dans {brut.name} : {sorted(manquantes)}")

    propre, journal = nettoyer_tp9(df_brut)

    # TODO 3 — Écrire les trois sorties datées et retourner le résultat.
    dossier_clean = config.dossier_donnees / "clean"
    dossier_clean.mkdir(parents=True, exist_ok=True)

    chemin_propre = dossier_clean / f"produits_propres_{date_demandee}.parquet"
    chemin_rapport = dossier_clean / f"rapport_nettoyage_{date_demandee}.md"
    chemin_journal = dossier_clean / f"journal_regles_{date_demandee}.json"

    propre.to_parquet(chemin_propre, index=False)

    generer_rapport(
        df_brut,
        propre,
        journal,
        chemin_rapport,
        source=str(brut),
        jour=config.date_execution,
    )

    with chemin_journal.open("w", encoding="utf-8") as fichier:
        json.dump([asdict(regle) for regle in journal], fichier, ensure_ascii=False, indent=2)
        fichier.write("\n")

    return ResultatEtape(
        duree_s=perf_counter() - debut,
        lignes=len(propre),
        fichiers=(chemin_propre, chemin_rapport, chemin_journal),
    )


def _chercher_nettoye(config: Configuration) -> Path:
    dossier_clean = config.dossier_donnees / "clean"
    chemin_propre = (
        dossier_clean / f"produits_propres_{config.date_execution:%Y%m%d}.parquet"
    )

    if not chemin_propre.is_file():
        candidats = (
            fichier
            for fichier in dossier_clean.glob("produits_propres_[0-9]" + "[0-9]" * 7 + ".parquet")
            if fichier.is_file()
        )
        chemin_propre = max(candidats, key=lambda fichier: fichier.name, default=None)
        if chemin_propre is None:
            raise FileNotFoundError(
                f"Aucun Parquet nettoyé dans {dossier_clean}. "
                "Lance d'abord l'étape nettoyer."
            )
    return chemin_propre


def charger_base(config: Configuration) -> ResultatEtape:
    """Recharge PostgreSQL à partir du Parquet nettoyé commun."""
    from src.database.connection import create_duckdb_connection
    from src.etl.brands import insert_brands
    from src.etl.categories import insert_categories
    from src.etl.nutrients import insert_nutrients
    from src.etl.products import insert_products
    from src.etl.products_categories import insert_products_categories
    from src.validation.checks import check_product_codes_unique, final_check

    debut = perf_counter()
    propre = pd.read_parquet(_chercher_nettoye(config))
    tables = vers_tables_sql(propre)
    lignes_attendues = len(propre)
    if len(tables["products"]) != lignes_attendues:
        raise ValueError("La projection SQL a changé le nombre de produits.")

    with TemporaryDirectory() as temporaire:
        dossier_import = Path(temporaire)
        for nom, table in tables.items():
            table.to_parquet(dossier_import / f"{nom}.parquet", index=False)

        connection = create_duckdb_connection()
        try:
            check_product_codes_unique(
                connection,
                parquet_path=dossier_import / "products.parquet",
            )

            connection.execute("BEGIN TRANSACTION")
            try:
                connection.execute(
                    "CALL postgres_execute(?, ?)",
                    [
                        POSTGRES_DB_ALIAS,
                        """
                        TRUNCATE TABLE
                            public.nutrients,
                            public.products_categories,
                            public.products,
                            public.categories,
                            public.brands
                        """,
                    ],
                )

                insert_brands(connection, dossier_import)
                insert_categories(connection, dossier_import)
                insert_products(connection, dossier_import)
                insert_products_categories(connection, dossier_import)
                insert_nutrients(connection, dossier_import)

                lignes = connection.execute(
                    f"SELECT COUNT(*) FROM {POSTGRES_DB_ALIAS}.public.products"
                ).fetchone()[0]
                if lignes != lignes_attendues:
                    raise ValueError(
                        f"PostgreSQL contient {lignes} produits, "
                        f"alors que {lignes_attendues} étaient attendus."
                    )

                final_check(connection)
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        finally:
            connection.close()

    return ResultatEtape(
        duree_s=perf_counter() - debut,
        lignes=lignes,
        fichiers=(),
    )


def parquet(config: Configuration) -> ResultatEtape:
    """Convertit le jeu nettoyé commun en Parquet partitionné."""
    debut = perf_counter()
    propre = pd.read_parquet(_chercher_nettoye(config))
    lignes_attendues = len(propre)
    if lignes_attendues == 0:
        raise ValueError("Le jeu nettoyé est vide. Aucune partition à écrire.")

    racine_parquet = (config.dossier_donnees / "parquet").resolve()
    racine_parquet.mkdir(parents=True, exist_ok=True)
    destination = racine_parquet / f"produits_{config.date_execution:%Y%m%d}"
    nom_schema = "schema_produits.json"
    nom_marqueur = "_SUCCESS"

    with TemporaryDirectory(prefix=".conversion-", dir=racine_parquet) as temporaire:
        travail = Path(temporaire)
        csv_propre = travail / "produits.csv"
        preparer(propre).to_csv(csv_propre, index=False)

        partitions = travail / destination.name
        lignes = convertir(csv_propre, partitions, partitions / nom_schema)
        if lignes != lignes_attendues:
            raise ValueError(f"Le Parquet partitionné contient {lignes} lignes, contre {lignes_attendues} attendues.")
        (partitions / nom_marqueur).touch()

        # Garde une sauvegarde à côté du dossier temporaire si la restauration échoue.
        sauvegarde = racine_parquet / f"{travail.name}.sauvegarde"
        if destination.exists():
            if not destination.is_dir() or destination.resolve() != destination:
                raise ValueError(f"La destination Parquet doit être un dossier local : {destination}")
            destination.rename(sauvegarde)
        try:
            partitions.rename(destination)
        except OSError:
            if sauvegarde.exists():
                sauvegarde.rename(destination)
            raise
        if sauvegarde.exists():
            sauvegarde.rename(travail / "ancienne_sortie")

    return ResultatEtape(
        duree_s=perf_counter() - debut,
        lignes=lignes,
        fichiers=(destination, destination / nom_schema, destination / nom_marqueur),
    )


def exports(config: Configuration) -> ResultatEtape:
    """Produit l'export ML daté et son schéma à partir du Parquet complet."""
    debut = perf_counter()
    racine_parquet = config.dossier_donnees / "parquet"
    nom_demande = f"produits_{config.date_execution:%Y%m%d}"
    candidats = sorted(
        racine_parquet.glob("produits_" + "[0-9]" * 8),
        key=lambda dossier: (dossier.name == nom_demande, dossier.name),
        reverse=True,
    )
    dossier_parquet = next(
        (
            dossier
            for dossier in candidats
            if (dossier / "_SUCCESS").is_file()
            and (dossier / "schema_produits.json").is_file()
            and any(partition.is_file() for partition in dossier.glob("rayon=*/*.parquet"))
        ),
        None,
    )
    if dossier_parquet is None:
        raise FileNotFoundError(
            f"Aucun jeu Parquet complet dans {racine_parquet}. Lance d'abord l'étape parquet."
        )

    fichier = exporter(dossier_parquet, config.dossier_donnees / "exports", config.date_execution)
    schema = chemin_schema(fichier)
    with schema.open(encoding="utf-8") as entree:
        lignes = json.load(entree)["lignes"]

    return ResultatEtape(
        duree_s=perf_counter() - debut,
        lignes=lignes,
        fichiers=(fichier, schema),
    )


ETAPES = {
    "charger": charger,
    "nettoyer": nettoyer,
    "charger_base": charger_base,
    "parquet": parquet,
    "exports": exports,
}


def executer(etape: str, config: Configuration) -> None:
    """Exécute une étape choisie ou le pipeline complet."""
    if etape == "all":
        for nom in ETAPES:
            executer(nom, config)
        return

    dossier_logs = config.dossier_donnees / "logs"
    dossier_logs.mkdir(parents=True, exist_ok=True)
    journal = dossier_logs / "pipeline.jsonl"
    entree: dict[str, object] = {
        "horodatage": datetime.now(UTC).isoformat(),
        "date_donnees": config.date_execution.isoformat(),
        "etape": etape,
    }

    def journaliser() -> None:
        with journal.open("a", encoding="utf-8") as fichier:
            fichier.write(json.dumps(entree, ensure_ascii=False) + "\n")

    debut = perf_counter()
    try:
        resultat = ETAPES[etape](config)
    except Exception as erreur:
        entree.update(statut="echec", duree_s=perf_counter() - debut, erreur=str(erreur))
        try:
            journaliser()
        except OSError as erreur_journal:
            erreur.add_note(f"Impossible d'écrire dans {journal} : {erreur_journal}")
        raise

    entree.update(
        statut="succes",
        duree_s=resultat.duree_s,
        lignes=resultat.lignes,
        fichiers=[str(chemin) for chemin in resultat.fichiers],
    )
    journaliser()
    print(f"{etape} : {resultat.lignes} lignes en {resultat.duree_s:.2f} s")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("etape", choices=[*ETAPES, "all"], help="Étape à exécuter ou all pour le flux complet")
    parser.add_argument(
        "--source",
        type=Path,
        default=os.environ.get("NUTRISCOPE_SOURCE", "data/food.parquet"),
        help="CSV ou Parquet source. Prioritaire sur NUTRISCOPE_SOURCE.",
    )
    parser.add_argument("--dossier-donnees", type=Path, default=Path("data"), help="Dossier des sorties")
    parser.add_argument("--date", type=date.fromisoformat, default=date.today(), help="Date des sorties (AAAA-MM-JJ)")
    args = parser.parse_args()

    config = Configuration(
        source=(RACINE / args.source).resolve(),
        dossier_donnees=(RACINE / args.dossier_donnees).resolve(),
        date_execution=args.date,
    )
    try:
        executer(args.etape, config)
    except (NotImplementedError, ValueError, OSError) as erreur:
        parser.exit(1, f"Erreur : {erreur}\n")


if __name__ == "__main__":
    main()
