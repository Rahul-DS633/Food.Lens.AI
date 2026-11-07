"""
Unit tests for foodlens/barcode.py and foodlens/off_client.py
"""

from foodlens.barcode import (
    clean_barcode, validate_ean13, is_indian_product
)
from foodlens.off_client import OpenFoodFactsClient


def test_clean_barcode():
    assert clean_barcode(" 890-1719-101052 ") == "8901719101052"
    assert clean_barcode("") == ""
    assert clean_barcode(None) == ""


def test_ean13_checksum_and_validation():
    # Valid Indian barcode for Parle-G: 8901719101052
    assert validate_ean13("8901719101052") is True
    assert is_indian_product("8901719101052") is True

    # Valid Maggi barcode: 8901058852349
    assert validate_ean13("8901058852349") is True
    assert is_indian_product("8901058852349") is True

    # Corrupt last digit
    assert validate_ean13("8901719101059") is False

    # Too short
    assert validate_ean13("890171910") is False


def test_off_client_preseeded_and_none_retention():
    client = OpenFoodFactsClient()
    info, profile = client.fetch_product("8901719101052")

    assert info is not None
    assert profile is not None
    assert info["brand"] == "Parle"
    assert info["name"] == "Parle-G Original Gluco Biscuits"

    # Check nutrients
    assert profile.energy_kcal.value == 454.0
    assert profile.protein_g.value == 6.5
    assert profile.sugars_g.value == 26.5
    assert profile.sodium_mg.value == 280.0
    assert profile.serving_size_g == 21.6
    assert profile.net_weight_g == 65.0


def test_off_client_unknown_barcode():
    client = OpenFoodFactsClient(timeout=1)
    info, profile = client.fetch_product("0000000000000")
    assert info is None
    assert profile is None
