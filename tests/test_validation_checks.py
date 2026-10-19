import duckdb
import pandas as pd
import pytest

from src.validation.checks import check_product_codes_unique


def ecrire_parquet_codes(chemin, codes):
    pd.DataFrame({"code": pd.Series(codes, dtype="string")}).to_parquet(
        chemin,
        index=False,
    )


def test_check_product_codes_unique_accepte_les_codes_uniques(tmp_path):
    parquet = tmp_path / "products.parquet"
    ecrire_parquet_codes(parquet, ["0001", "0002"])
    connexion = duckdb.connect()

    try:
        check_product_codes_unique(connexion, parquet)
    finally:
        connexion.close()


@pytest.mark.parametrize(
    ("codes", "erreur"),
    [
        (["0001", "0001"], "1 ligne en doublon"),
        (["0001", None], "1 code nul ou vide"),
        (["0001", ""], "1 code nul ou vide"),
    ],
)
def test_check_product_codes_unique_refuse_les_cles_invalides(
    tmp_path,
    codes,
    erreur,
):
    parquet = tmp_path / "products.parquet"
    ecrire_parquet_codes(parquet, codes)
    connexion = duckdb.connect()

    try:
        with pytest.raises(ValueError, match=erreur):
            check_product_codes_unique(connexion, parquet)
    finally:
        connexion.close()
