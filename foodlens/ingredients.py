"""
FoodLens Ingredient Intelligence Engine
Parses ordered ingredient lists, explains additives neutrally, and identifies allergens.

Key Rules:
1. Ordered ingredients list preserved (order denotes descending weight).
2. Approved additives are explained neutrally, not condemned.
3. Detects allergens from both ingredients and explicit "Contains / May contain" statements.
4. Allergen safety rule: Never say "allergen-free"; use "No allergen detected in the text we could read."
"""

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

TABLE_PATH = Path(__file__).parent / "config" / "ingredient_table.csv"

COMMON_ALLERGEN_KEYWORDS = {
    "gluten": ["wheat", "gluten", "barley", "rye", "maida", "atta", "spelt"],
    "milk": ["milk", "dairy", "butter", "whey", "casein", "cheese", "cream", "lactose", "curd"],
    "soy": ["soy", "soya", "soybean", "lecithin"],
    "peanut": ["peanut", "groundnut", "peanuts"],
    "tree_nuts": ["almond", "cashew", "walnut", "pistachio", "hazelnut", "pecan"],
    "egg": ["egg", "eggs", "albumin", "albumen", "ovalbumin"],
    "fish": ["fish", "tuna", "salmon", "cod", "anchovy"],
    "crustacean": ["shrimp", "prawn", "crab", "lobster"],
    "sulphites": ["sulphite", "sulfite", "metabisulphite", "metabisulfite", "223", "220"],
    "sesame": ["sesame", "til"],
}


@dataclass
class ParsedIngredient:
    position: int
    raw_name: str
    cleaned_name: str
    category: str
    explanation: str
    allergen_tag: Optional[str] = None


@dataclass
class IngredientAnalysisResult:
    ingredients: List[ParsedIngredient]
    detected_allergens: List[str]
    allergen_banner: str
    has_allergens: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "detected_allergens": self.detected_allergens,
            "allergen_banner": self.allergen_banner,
            "has_allergens": self.has_allergens,
            "ingredients": [
                {
                    "position": ing.position,
                    "raw_name": ing.raw_name,
                    "cleaned_name": ing.cleaned_name,
                    "category": ing.category,
                    "explanation": ing.explanation,
                    "allergen_tag": ing.allergen_tag,
                }
                for ing in self.ingredients
            ],
        }


class IngredientEngine:
    def __init__(self):
        self.lookup_table: Dict[str, Dict[str, str]] = {}
        self._load_table()

    def _load_table(self):
        if not TABLE_PATH.exists():
            return
        with open(TABLE_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row["code_or_name"].strip().lower()
                self.lookup_table[key] = {
                    "common_name": row.get("common_name", key),
                    "category": row.get("category", "ingredient"),
                    "explanation": row.get("explanation", ""),
                    "allergen_flag": row.get("allergen_flag", "none"),
                }

    def split_ingredients_text(self, text: str) -> List[str]:
        """
        Splits an ingredient string on commas that are outside parentheses/brackets.
        Example: "Wheat Flour (68%), Sugar, Raising Agents [503(ii), 500(ii)], Salt"
        -> ["Wheat Flour (68%)", "Sugar", "Raising Agents [503(ii), 500(ii)]", "Salt"]
        """
        if not text:
            return []

        tokens: List[str] = []
        current: List[str] = []
        paren_depth = 0
        bracket_depth = 0

        for char in text:
            if char == "(":
                paren_depth += 1
            elif char == ")":
                if paren_depth > 0:
                    paren_depth -= 1
            elif char == "[":
                bracket_depth += 1
            elif char == "]":
                if bracket_depth > 0:
                    bracket_depth -= 1

            if char in (",", ";") and paren_depth == 0 and bracket_depth == 0:
                token = "".join(current).strip()
                if token:
                    tokens.append(token)
                current = []
            else:
                current.append(char)

        token = "".join(current).strip()
        if token:
            tokens.append(token)

        # Remove trailing period if present
        return [re.sub(r"\.\s*$", "", t).strip() for t in tokens if t]

    def _match_lookup(self, text: str) -> Dict[str, str]:
        t_lower = text.lower()

        # 1. Exact match
        if t_lower in self.lookup_table:
            return self.lookup_table[t_lower]

        # 2. Check INS code in parentheses or brackets e.g. 503(ii) or 322
        ins_match = re.search(r"\b(\d{3,4}(?:\([a-z0-9]+\))?)\b", t_lower)
        if ins_match:
            ins_code = ins_match.group(1)
            if ins_code in self.lookup_table:
                return self.lookup_table[ins_code]

        # 3. Substring match against known keys
        for key, val in self.lookup_table.items():
            if key in t_lower:
                return val

        return {
            "common_name": text,
            "category": "ingredient",
            "explanation": "Standard food-grade packaged ingredient.",
            "allergen_flag": "none",
        }

    def analyze(self, ingredients_text: str, declared_allergens_text: Optional[str] = None) -> IngredientAnalysisResult:
        """
        Analyzes ingredients, maps explanations, and performs comprehensive allergen detection.
        """
        raw_items = self.split_ingredients_text(ingredients_text)
        parsed_list: List[ParsedIngredient] = []
        detected_allergens: set[str] = set()

        combined_text = (ingredients_text + " " + (declared_allergens_text or "")).lower()

        # Check allergen keywords
        for allergen_category, keywords in COMMON_ALLERGEN_KEYWORDS.items():
            for kw in keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", combined_text):
                    detected_allergens.add(allergen_category)
                    break

        for pos, item in enumerate(raw_items, start=1):
            info = self._match_lookup(item)
            allergen_tag = info.get("allergen_flag")
            if allergen_tag and allergen_tag.lower() != "none":
                detected_allergens.add(allergen_tag.lower())

            # Clean percentage markings for cleaner display
            clean_name = re.sub(r"\(\s*\d+(?:\.\d+)?\s*%\s*\)", "", item).strip()

            parsed_list.append(
                ParsedIngredient(
                    position=pos,
                    raw_name=item,
                    cleaned_name=clean_name,
                    category=info.get("category", "ingredient"),
                    explanation=info.get("explanation", "Standard food ingredient."),
                    allergen_tag=allergen_tag if allergen_tag != "none" else None,
                )
            )

        allergen_list = sorted(list(detected_allergens))
        if allergen_list:
            banner = f"Contains / May Contain: {', '.join(allergen_list).title()}"
            has_allergens = True
        else:
            # Strict safety principle: never state 'allergen-free'
            banner = "No allergen detected in the text we could read."
            has_allergens = False

        return IngredientAnalysisResult(
            ingredients=parsed_list,
            detected_allergens=allergen_list,
            allergen_banner=banner,
            has_allergens=has_allergens,
        )

