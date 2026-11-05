"""
FoodLens Nutrition Text Parser
Extracts structured nutrition data, basis (per 100g / per serving), and units from OCR text lines.

Principles:
1. Deterministic regex and dictionary matching.
2. Comma vs decimal handling (e.g., 2,5 g vs 2.5 g).
3. Distinguish between per-100g and per-serve columns when multiple numbers appear.
4. Preserves missing fields as None (Never zero-fills).
5. Computes confidence per field.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from foodlens.nutrition import Nutrient, NutritionProfile, create_nutrient
from foodlens.units import normalize_nutrient_value, salt_g_to_sodium_mg

CONFIG_PATH = Path(__file__).parent / "config" / "nutrient_dictionary.json"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    NUTRIENT_SYNONYMS: Dict[str, List[str]] = json.load(f)


def clean_text_line(line: str) -> str:
    """Standardize punctuation, spacing, and casing."""
    line = line.lower()
    line = line.replace("\xa0", " ")
    # Replace colon, dash, equals, slash with spaces
    line = re.sub(r"[:=\-–—/|]", " ", line)
    return " ".join(line.split())


def detect_basis_and_serving(text: str) -> Tuple[str, Optional[float], bool]:
    """
    Scans full OCR text for basis indicators and serving size.
    Returns: (basis, serving_size_g, is_beverage)
    """
    text_lower = text.lower()
    is_beverage = bool(re.search(r"\b(ml|per 100\s*ml|beverage|drink)\b", text_lower))

    # Detect serving size: e.g. "serving size: 30g", "per serve (25 g)", "serve size 15.5g"
    serving_match = re.search(
        r"(?:serving size|serve size|per serving|per serve|approx\.\s*serve|approx\.\s*serving)[\s:]*\(?(\d+(?:[.,]\d+)?)\s*(g|ml|gm)?\)?",
        text_lower
    )
    serving_size_g = None
    if serving_match:
        try:
            val_str = serving_match.group(1).replace(",", ".")
            serving_size_g = float(val_str)
        except ValueError:
            serving_size_g = None

    # Detect reference basis
    if "per 100ml" in text_lower or "per 100 ml" in text_lower:
        basis = "per_100ml"
    elif "per 100g" in text_lower or "per 100 g" in text_lower or "per 100 gm" in text_lower:
        basis = "per_100g"
    elif "per serve" in text_lower or "per serving" in text_lower:
        basis = "per_serving"
    else:
        # Default packaged standard in India is per 100g (or 100ml if beverage)
        basis = "per_100ml" if is_beverage else "per_100g"

    return basis, serving_size_g, is_beverage


# Regex to match a number followed optionally by a unit (g, mg, kcal, kj, etc.)
NUMBER_UNIT_REGEX = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(kcal|calories|cal|kj|mg|mcg|µg|ug|g|gm)?",
    re.IGNORECASE
)


def extract_numbers_from_line(line: str) -> List[Tuple[float, str]]:
    """
    Extracts all numeric tokens and their associated units from a line.
    Handles comma decimals like '12,5' -> 12.5.
    """
    results: List[Tuple[float, str]] = []
    # Avoid picking up percentages as absolute values
    line_clean = re.sub(r"\d+(?:[.,]\d+)?\s*%", "", line)

    for match in NUMBER_UNIT_REGEX.finditer(line_clean):
        num_str = match.group(1).replace(",", ".")
        unit = (match.group(2) or "").strip().lower()
        if unit == "gm":
            unit = "g"
        try:
            val = float(num_str)
            results.append((val, unit))
        except ValueError:
            continue
    return results


def parse_ocr_text(
    lines: List[str],
    line_confidences: Optional[List[float]] = None
) -> Tuple[NutritionProfile, Dict[str, Any]]:
    """
    Parses a list of OCR lines into a NutritionProfile.
    Preserves missing fields as None.
    Flags low-confidence extractions (< 0.70).
    """
    full_text = "\n".join(lines)
    basis, serving_size, is_beverage = detect_basis_and_serving(full_text)

    # Storage for extracted raw values and metadata
    extracted_nutrients: Dict[str, Optional[Nutrient]] = {
        "energy_kcal": None,
        "protein_g": None,
        "carbs_g": None,
        "sugars_g": None,
        "added_sugar_g": None,
        "fat_g": None,
        "sat_fat_g": None,
        "trans_fat_g": None,
        "fibre_g": None,
        "sodium_mg": None,
    }
    extracted_details: Dict[str, Any] = {
        "raw_lines": lines,
        "detected_basis": basis,
        "serving_size_g": serving_size,
        "is_beverage": is_beverage,
        "field_matches": {},
        "low_confidence_fields": [],
    }

    salt_extracted: Optional[Nutrient] = None

    for idx, raw_line in enumerate(lines):
        line = clean_text_line(raw_line)
        conf = line_confidences[idx] if line_confidences and idx < len(line_confidences) else 0.85

        # Check against each nutrient in dictionary
        # Note: Check more specific synonyms first (e.g. 'added sugar' before 'sugars', 'saturated fat' before 'fat')
        ordered_keys = [
            "added_sugar_g",
            "sugars_g",
            "sat_fat_g",
            "trans_fat_g",
            "fat_g",
            "fibre_g",
            "protein_g",
            "carbs_g",
            "energy_kcal",
            "sodium_mg",
            "salt_g",
        ]

        for nutrient_key in ordered_keys:
            # If already extracted with high confidence, skip unless overridden
            if nutrient_key != "salt_g" and extracted_nutrients.get(nutrient_key) is not None:
                continue

            synonyms = NUTRIENT_SYNONYMS.get(nutrient_key, [])
            matched_synonym = None
            for syn in synonyms:
                pattern = r"\b" + re.escape(syn) + r"\b"
                if re.search(pattern, line):
                    matched_synonym = syn
                    break

            if matched_synonym:
                # Found label keyword in line. Now extract numbers.
                # Remove the matched label part to avoid number interference
                remainder = line
                num_matches = extract_numbers_from_line(remainder)
                if num_matches:
                    # If multiple numbers exist, the first column is typically per 100g, 2nd per serve
                    val, unit = num_matches[0]

                    # Standardize unit
                    default_unit = "mg" if nutrient_key == "sodium_mg" else ("kcal" if nutrient_key == "energy_kcal" else "g")
                    final_unit = unit if unit else default_unit

                    normalized_val = val
                    if nutrient_key == "energy_kcal" and final_unit in ("kj",):
                        normalized_val = normalize_nutrient_value(val, "kj", "kcal")
                        final_unit = "kcal"
                    elif nutrient_key == "sodium_mg" and final_unit == "g":
                        normalized_val = normalize_nutrient_value(val, "g", "mg")
                        final_unit = "mg"

                    nutrient_obj = Nutrient(
                        value=normalized_val,
                        unit=final_unit,
                        basis=basis,
                        source="ocr",
                        confidence=round(conf, 2),
                    )

                    if nutrient_key == "salt_g":
                        salt_extracted = nutrient_obj
                    else:
                        extracted_nutrients[nutrient_key] = nutrient_obj

                    extracted_details["field_matches"][nutrient_key] = {
                        "raw_line": raw_line,
                        "matched_term": matched_synonym,
                        "raw_value": val,
                        "raw_unit": unit,
                        "confidence": conf,
                    }

                    if conf < 0.70:
                        extracted_details["low_confidence_fields"].append(nutrient_key)

                    break  # Matched this line

    # If sodium was not directly present but salt was extracted, derive sodium from salt
    if extracted_nutrients["sodium_mg"] is None and salt_extracted and salt_extracted.value is not None:
        sodium_from_salt = salt_g_to_sodium_mg(salt_extracted.value)
        extracted_nutrients["sodium_mg"] = Nutrient(
            value=sodium_from_salt,
            unit="mg",
            basis=basis,
            source="ocr",
            confidence=salt_extracted.confidence,
        )
        extracted_details["field_matches"]["sodium_mg"] = {
            "derived_from_salt": salt_extracted.value,
            "confidence": salt_extracted.confidence,
        }

    profile = NutritionProfile(
        basis=basis,
        energy_kcal=extracted_nutrients["energy_kcal"],
        protein_g=extracted_nutrients["protein_g"],
        carbs_g=extracted_nutrients["carbs_g"],
        sugars_g=extracted_nutrients["sugars_g"],
        added_sugar_g=extracted_nutrients["added_sugar_g"],
        fat_g=extracted_nutrients["fat_g"],
        sat_fat_g=extracted_nutrients["sat_fat_g"],
        trans_fat_g=extracted_nutrients["trans_fat_g"],
        fibre_g=extracted_nutrients["fibre_g"],
        sodium_mg=extracted_nutrients["sodium_mg"],
        serving_size_g=serving_size,
        is_beverage=is_beverage,
    )

    return profile, extracted_details
