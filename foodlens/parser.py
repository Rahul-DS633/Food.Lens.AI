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


def clean_ocr_line_for_nutrition(line: str) -> str:
    """
    Cleans OCR-specific character confusions in nutrition tables:
    - 'Energy 579 6 kcal' -> 'Energy 579.6 kcal'
    - 'Protein 14.la' -> 'Protein 14.1 g'
    - 'Total Carbohydrate 39.09' -> 'Total Carbohydrate 39.0 g'
    - '40 89' / '40.8g' -> '40.8 g'
    - '6.79' -> '6.7 g'
    - 'Sodium 754 Onia' -> 'Sodium 754.0 mg'
    - '0.0q' -> '0.0 g'
    - '<0.1#g' -> '0.1 g'
    """
    # Remove # and <
    line = re.sub(r"[#<>]", " ", line)

    # 'Energy 579 6 kcal' -> 'Energy 579.6 kcal'
    line = re.sub(r"(\d+)\s+(\d)\s*(?:kcal|calories)", r"\1.\2 kcal", line, flags=re.I)

    # '14.la' / '14.l' -> '14.1 g'
    line = re.sub(r"(\d+)\.[lI]([a-zA-Z]?)", r"\1.1 \2", line)

    # '39.09' or '39.0q' or '6.79' (where 9 or q is misread 'g')
    line = re.sub(r"(\d+\.\d)[9q](?!\d)", r"\1 g", line)
    line = re.sub(r"(\d+)\s+8[9q](?!\d)", r"\1.8 g", line)
    line = re.sub(r"(\d+)\s+6[9q](?!\d)", r"\1.6 g", line)

    # '754 Onia' -> '754.0 mg'
    line = re.sub(r"(\d+)\s+O[a-z]+", r"\1.0 mg", line, flags=re.I)

    # Clean isolated 'q' or 'a' after numbers to 'g'
    line = re.sub(r"(\d+(?:\.\d+)?)\s*[qa]\b", r"\1 g", line, flags=re.I)

    # 'slze' -> 'size'
    line = re.sub(r"\bslze\b", "size", line, flags=re.I)

    # '209;' in serving size line -> '20 g;'
    line = re.sub(r"(\d+)9(?=\s*;|\s*$|\s+serving|\s+serve)", r"\1 g", line, flags=re.I)

    # '5 0 Serving' -> '5.0 Serving'
    line = re.sub(r"(\d+)\s+0\s+(?:serving|serve)", r"\1.0 serving", line, flags=re.I)

    return line


def detect_net_weight(text: str, serving_size_g: Optional[float] = None) -> Optional[float]:
    """
    Estimates net weight from 'Net Wt: 100g' or '5 servings in this pack' * serving_size_g.
    """
    text_lower = clean_ocr_line_for_nutrition(text.lower())
    # Explicit net weight: e.g. "Net Wt: 100g", "Net Weight 150 g"
    net_wt_match = re.search(
        r"(?:net\s*wt|net\s*weight|net\s*quantity)[\s.:]*(\d+(?:[.,]\d+)?)\s*(?:g|ml|gm)",
        text_lower
    )
    if net_wt_match:
        try:
            return float(net_wt_match.group(1).replace(",", "."))
        except ValueError:
            pass

    # Multiply servings per pack by serving size: e.g. "5.0 serving in this pack", "5 0 serving"
    servings_per_pack_match = re.search(
        r"(\d+(?:[.,\s]\d+)?)\s*(?:servings?|serves?)\s*(?:in\s*this\s*pack|per\s*pack)?",
        text_lower
    )
    if servings_per_pack_match and serving_size_g:
        try:
            cnt_str = servings_per_pack_match.group(1).replace(",", ".").replace(" ", ".")
            servings_cnt = float(cnt_str)
            if servings_cnt > 0:
                return round(serving_size_g * servings_cnt, 1)
        except ValueError:
            pass

    return None


def detect_basis_and_serving(text: str) -> Tuple[str, Optional[float], bool]:
    """
    Scans full OCR text for basis indicators and serving size.
    Returns: (basis, serving_size_g, is_beverage)
    """
    text_lower = clean_ocr_line_for_nutrition(text.lower())
    is_beverage = bool(re.search(r"\b(ml|per 100\s*ml|beverage|drink)\b", text_lower))

    # Detect serving size: e.g. "serving size: 30g", "per serve (25 g)", "serve size is 20g"
    serving_match = re.search(
        r"(?:serving size|serve size|per serving|per serve|approx\.\s*serve|approx\.\s*serving)[\s:]*(?:is\s*)?\(?(\d+(?:[.,]\d+)?)\s*(?:g|ml|gm|9)?\)?",
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
    Handles comma decimals like '12,5' -> 12.5 and cleans OCR glitches.
    """
    cleaned_line = clean_ocr_line_for_nutrition(line)
    results: List[Tuple[float, str]] = []
    # Avoid picking up percentages as absolute values
    line_clean = re.sub(r"\d+(?:[.,]\d+)?\s*%", "", cleaned_line)

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
    detected_net_wt = detect_net_weight(full_text, serving_size)

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
        "detected_net_weight_g": detected_net_wt,
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
                remainder = line
                num_matches = extract_numbers_from_line(remainder)

                # Lookahead: if no number on current line, inspect the next line
                if not num_matches:
                    for lookahead in (1, 2):
                        if idx + lookahead < len(lines):
                            cand_line = clean_text_line(lines[idx + lookahead])
                            is_another_label = any(
                                re.search(r"\b" + re.escape(s) + r"\b", cand_line)
                                for k, s_list in NUTRIENT_SYNONYMS.items() for s in s_list
                            )
                            if not is_another_label:
                                cand_nums = extract_numbers_from_line(cand_line)
                                if cand_nums:
                                    num_matches = cand_nums
                                    break

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


def extract_ingredients_from_lines(lines: List[str]) -> str:
    """
    Scans OCR lines to locate and extract the ingredients statement block.
    Matches starting keywords like 'INGREDIENTS:', 'सामग्री:', 'INGRÉDIENTS'
    and stops at packaging boundaries like 'NUTRITIONAL INFORMATION', 'MFG BY', etc.
    """
    start_idx = -1
    start_prefix_len = 0

    ingredient_start_pattern = re.compile(
        r"^(?:(?:list\s+of\s+)?ingredients?|सामग्री|ingrédients?)\s*[:\-—]?",
        re.IGNORECASE
    )

    for i, line in enumerate(lines):
        match = ingredient_start_pattern.search(line.strip())
        if match:
            start_idx = i
            start_prefix_len = match.end()
            break

    if start_idx == -1:
        # Check if any line has 'ingredients' anywhere in it
        for i, line in enumerate(lines):
            match = re.search(r"\b(?:ingredients?|सामग्री)\s*[:\-—]", line, re.IGNORECASE)
            if match:
                start_idx = i
                start_prefix_len = match.end()
                break

    if start_idx == -1:
        return ""

    collected: List[str] = []
    # Take remainder of first line
    first_rem = lines[start_idx][start_prefix_len:].strip()
    if first_rem:
        collected.append(first_rem)

    stop_pattern = re.compile(
        r"\b(?:nutritional|nutrition\s+facts|mfg|manufactured|marketed|pkg|fssai|batch\s+no|best\s+before|customer\s+care|net\s+wt|net\s+weight|keep\s+in\s+a\s+cool)\b",
        re.IGNORECASE
    )

    for line in lines[start_idx + 1:]:
        clean = line.strip()
        if not clean:
            continue
        if stop_pattern.search(clean):
            break
        collected.append(clean)

    return " ".join(collected).strip()


def extract_product_and_brand(lines: List[str]) -> Tuple[str, str, str]:
    """
    Intelligently extracts the brand, product name, and category from OCR packaging lines.
    Rejects generic table titles ('Nutritional Information', 'Ingredients', etc.)
    """
    detected_brand = "Custom Brand"
    detected_name = "Scanned Packaged Food"
    detected_category = "general"

    KNOWN_BRANDS = [
        ("Haldiram's", ["haldiram", "haldirams", "haldiram's"]),
        ("Bikaji", ["bikaji"]),
        ("Bikano", ["bikano"]),
        ("Balaji", ["balaji"]),
        ("Parle", ["parle", "parle-g"]),
        ("Parle Agro", ["parle agro", "frooti", "appy"]),
        ("Britannia", ["britannia", "good day", "marie gold", "bourbon", "treat", "nutrichoice"]),
        ("Nestle", ["nestle", "nestlé", "maggi", "kitkat", "munch", "nescafe"]),
        ("PepsiCo", ["pepsico", "lay's", "lays", "kurkure", "doritos"]),
        ("ITC", ["sunfeast", "dark fantasy", "bingo", "yippee", "aashirvaad"]),
        ("Amul", ["amul"]),
        ("Mother Dairy", ["mother dairy"]),
        ("Cadbury", ["cadbury", "dairy milk", "oreo", "bournvita", "5 star", "perk"]),
        ("Tata", ["tata", "tata tea", "tata sampann"]),
        ("Dabur", ["dabur", "real"]),
        ("MTR", ["mtr"]),
        ("Coca-Cola", ["coca cola", "coca-cola", "thums up", "sprite", "limca", "maaza"]),
    ]

    full_blob = " ".join(lines).lower()

    # Match brand
    for brand_name, aliases in KNOWN_BRANDS:
        for alias in aliases:
            if re.search(r"\b" + re.escape(alias) + r"\b", full_blob):
                detected_brand = brand_name
                break
        if detected_brand != "Custom Brand":
            break

    # Common food product names in Indian packaging
    FOOD_KEYWORDS = [
        ("Aloo Bhujia", ["aloo bhujia", "bhujia", "bikaneri bhujia"]),
        ("Sev", ["ratlami sev", "sev", "nylon sev", "bhujia sev"]),
        ("Moong Dal", ["moong dal", "salted moong"]),
        ("Khatta Meetha", ["khatta meetha", "chana chur", "navratan"]),
        ("Nut Cracker", ["nut cracker", "coated peanuts", "peanuts"]),
        ("Maggi Masala Noodles", ["2-minute noodles", "masala noodles", "maggi noodles", "noodles"]),
        ("Gluco Biscuits", ["gluco biscuits", "parle-g", "glucose biscuits"]),
        ("Butter Cookies", ["good day", "butter cookies", "butter cookies"]),
        ("Marie Biscuits", ["marie gold", "marie"]),
        ("Chocolate Cream Biscuits", ["dark fantasy", "bourbon", "choco fills", "oreo"]),
        ("Potato Chips", ["potato chips", "magic masala", "cream & onion", "salted chips"]),
        ("Corn Puffs", ["kurkure", "masala munch", "puffcorn", "mad angles"]),
        ("Butter", ["amul butter", "pasteurised butter", "table butter"]),
        ("Mango Drink", ["frooti", "mango drink", "mango juice", "maaza", "slice"]),
    ]

    for prod_name, keywords in FOOD_KEYWORDS:
        for kw in keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", full_blob):
                detected_name = prod_name
                if "bhujia" in kw or "sev" in kw or "khatta" in kw or "dal" in kw:
                    detected_category = "namkeen"
                elif "chips" in kw or "kurkure" in kw or "puffs" in kw:
                    detected_category = "snacks"
                elif "biscuits" in kw or "cookies" in kw or "marie" in kw:
                    detected_category = "biscuits"
                elif "noodles" in kw:
                    detected_category = "instant_noodles"
                elif "drink" in kw or "juice" in kw:
                    detected_category = "beverages"
                elif "butter" in kw:
                    detected_category = "spreads"
                break
        if detected_name != "Scanned Packaged Food":
            break

    # If product name is still generic, scan lines for a clean title candidate
    if detected_name == "Scanned Packaged Food":
        UNWANTED_WORDS = {
            "nutritional", "nutrition", "information", "approximate", "values",
            "ingredients", "ingredient", "table", "per", "100g", "serve",
            "serving", "mfg", "manufactured", "marketed", "fssai", "batch",
            "date", "mrp", "net", "wt", "weight", "best", "before", "customer",
            "care", "keep", "cool", "dry", "place", "packed", "by", "lic",
            "no", "india", "pvt", "ltd", "snack", "snacks", "contribution", "rda",
            "relish", "goodness", "delightful", "savoury", "treats"
        }
        for line in lines:
            clean_words = [w for w in re.sub(r"[^a-zA-Z\s]", " ", line).split() if len(w) > 2]
            non_unwanted = [w for w in clean_words if w.lower() not in UNWANTED_WORDS]
            if 1 <= len(non_unwanted) <= 4:
                cand = " ".join(non_unwanted).title()
                if 3 <= len(cand) <= 30:
                    detected_name = cand
                    break

    return detected_name, detected_brand, detected_category


