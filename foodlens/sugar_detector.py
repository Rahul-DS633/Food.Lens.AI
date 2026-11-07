"""
FoodLens Hidden Sugar & Sweetener Detector
Pure Python deterministic engine for detecting sugar aliases, syrups, concentrates,
carbohydrate fillers, and non-sugar sweeteners in ingredient lists.

Safety & Architectural Guarantees:
1. Deterministic code calculates; AI only explains.
2. Ingredient position indicates descending weight order only; never estimates quantities.
3. RapidFuzz handles OCR typographical variants with explicit 'fuzzy' tagging and lower confidence.
4. Identifies 'sugar splitting' (>= 3 distinct added sugar aliases).
5. Cross-checks nutrition table for 0g added sugar conflicts.
6. Teaspoons rounded to nearest 0.5 step, citing basis (added vs total sugars).
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
import yaml

try:
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover
    from difflib import SequenceMatcher

    class _FuzzFallback:
        @staticmethod
        def token_sort_ratio(s1: str, s2: str) -> float:
            t1 = " ".join(sorted(s1.split()))
            t2 = " ".join(sorted(s2.split()))
            return SequenceMatcher(None, t1, t2).ratio() * 100.0

    fuzz = _FuzzFallback()  # type: ignore[assignment]

from foodlens.units import sugar_g_to_teaspoons_rounded

CONFIG_PATH = Path(__file__).parent / "config" / "sugar_aliases.yaml"


@dataclass(frozen=True)
class SugarMatch:
    ingredient_text: str          # Original token text from label
    normalized_alias: str         # Canonical alias ID (e.g. "invert_sugar")
    sugar_class: str              # "sugars", "syrups", "concentrates", "carb_fillers", "non_sugar_sweeteners", "ambiguous"
    position: int                 # 1-based index in ordered ingredients
    confidence: float             # 1.0 (exact) or ~0.8 (fuzzy)
    match_type: str               # "exact" or "fuzzy"
    is_added: str                 # "yes", "no", "ambiguous"
    explanation: str              # Neutral plain-English description


@dataclass(frozen=True)
class SugarReport:
    matches: List[SugarMatch]
    distinct_sugar_names: List[str]
    first_sugar_position: Optional[int]
    sugars_in_top3: bool
    sugar_splitting: bool
    non_sugar_sweeteners: List[str]
    carb_fillers: List[str]
    label_conflict: bool
    label_conflict_reason: Optional[str]
    portion_teaspoons: Optional[float]
    teaspoon_basis: Optional[str]
    total_sugar_grams: Optional[float]
    added_sugar_grams: Optional[float]
    missing_data: List[str]
    status: str  # "OK" or "UNKNOWN"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "distinct_sugar_count": len(self.distinct_sugar_names),
            "distinct_sugar_names": self.distinct_sugar_names,
            "first_sugar_position": self.first_sugar_position,
            "sugars_in_top3": self.sugars_in_top3,
            "sugar_splitting": self.sugar_splitting,
            "non_sugar_sweeteners": self.non_sugar_sweeteners,
            "carb_fillers": self.carb_fillers,
            "label_conflict": self.label_conflict,
            "label_conflict_reason": self.label_conflict_reason,
            "portion_teaspoons": self.portion_teaspoons,
            "teaspoon_basis": self.teaspoon_basis,
            "total_sugar_grams": self.total_sugar_grams,
            "added_sugar_grams": self.added_sugar_grams,
            "missing_data": self.missing_data,
            "matches": [
                {
                    "ingredient_text": m.ingredient_text,
                    "normalized_alias": m.normalized_alias,
                    "sugar_class": m.sugar_class,
                    "position": m.position,
                    "confidence": m.confidence,
                    "match_type": m.match_type,
                    "is_added": m.is_added,
                    "explanation": m.explanation,
                }
                for m in self.matches
            ],
        }


class SugarDetector:
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or CONFIG_PATH
        self.alias_map: Dict[str, Dict[str, Any]] = {}
        self.exclusion_terms: Set[str] = set()
        self._load_config()

    def _load_config(self):
        if not self.config_path.exists():
            return
        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        classes = data.get("classes", {})
        for c_key, c_data in classes.items():
            is_added = c_data.get("is_added", "yes")
            entries = c_data.get("entries", [])
            for entry in entries:
                e_id = entry.get("id", "")
                explanation = entry.get("explanation", "")
                aliases = entry.get("aliases", [])
                for alias in aliases:
                    alias_clean = alias.strip().lower()
                    if alias_clean:
                        self.alias_map[alias_clean] = {
                            "id": e_id,
                            "class": c_key,
                            "is_added": is_added,
                            "explanation": explanation,
                            "canonical": aliases[0],
                        }

        exclusions = data.get("exclusions", {}).get("terms", [])
        self.exclusion_terms = {t.strip().lower() for t in exclusions if t.strip()}

    def split_ingredients(self, text: str) -> List[str]:
        """
        Splits ingredient text on commas outside brackets and parentheses.
        """
        if not text:
            return []

        # Remove prefix like "Ingredients:" or "INGREDIENTS :"
        clean_text = re.sub(r"^(?:ingredients|ingrédients|सामग्री)\s*[:\-]?\s*", "", text.strip(), flags=re.IGNORECASE)

        tokens: List[str] = []
        current: List[str] = []
        depth = 0

        for char in clean_text:
            if char in "([{":
                depth += 1
                current.append(char)
            elif char in ")]}":
                depth = max(0, depth - 1)
                current.append(char)
            elif char == "," and depth == 0:
                token = "".join(current).strip()
                if token:
                    tokens.append(token)
                current = []
            elif char == "." and depth == 0 and len(tokens) > 0 and len(current) == 0:
                # Trailing period after last ingredient
                continue
            else:
                current.append(char)

        last_token = "".join(current).strip().rstrip(".")
        if last_token:
            tokens.append(last_token)

        return tokens

    def _clean_token_for_matching(self, token: str) -> str:
        """Strips percentages and common parenthetical qualifiers for candidate evaluation."""
        # E.g. "Jaggery (Gur 35%)" -> "jaggery gur"
        cleaned = re.sub(r"\b\d+(?:\.\d+)?\s*%\b", " ", token)
        cleaned = re.sub(r"[()\[\]{}]", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
        return cleaned

    def detect_sugars(
        self,
        ingredients_text: Optional[str],
        added_sugar_g: Optional[float] = None,
        total_sugars_g: Optional[float] = None,
        portion_g: float = 100.0,
        ocr_confidence: float = 1.0,
    ) -> SugarReport:
        """
        Analyzes ingredient statement to find and classify all sugar-like items.
        """
        missing_data: List[str] = []

        # Safety Check 1: Missing ingredients or low OCR confidence
        if not ingredients_text or not ingredients_text.strip() or ocr_confidence < 0.60:
            return SugarReport(
                matches=[],
                distinct_sugar_names=[],
                first_sugar_position=None,
                sugars_in_top3=False,
                sugar_splitting=False,
                non_sugar_sweeteners=[],
                carb_fillers=[],
                label_conflict=False,
                label_conflict_reason=None,
                portion_teaspoons=None,
                teaspoon_basis=None,
                total_sugar_grams=total_sugars_g,
                added_sugar_grams=added_sugar_g,
                missing_data=["ingredients_text"],
                status="UNKNOWN",
            )

        tokens = self.split_ingredients(ingredients_text)
        matches: List[SugarMatch] = []
        distinct_sugars_set: Set[str] = set()
        sweeteners_list: List[str] = []
        carb_fillers_list: List[str] = []

        # Sort aliases by length descending so longer phrases match first
        sorted_aliases = sorted(self.alias_map.keys(), key=len, reverse=True)

        for pos, raw_token in enumerate(tokens, start=1):
            lowered_token = raw_token.lower()

            # Check exclusion terms (e.g. "sugarcane vinegar", "cane vinegar")
            if any(exc in lowered_token for exc in self.exclusion_terms):
                continue

            cleaned_cand = self._clean_token_for_matching(raw_token)
            matched_entry: Optional[Tuple[str, Dict[str, Any], str, float]] = None

            # 1. Exact / Substring Alias Search (prioritize longest matching phrase)
            for alias in sorted_aliases:
                # Word-boundary match in lowered_token or cleaned candidate
                pattern = rf"(?<!\w){re.escape(alias)}(?!\w)"
                if re.search(pattern, lowered_token) or re.search(pattern, cleaned_cand):
                    matched_entry = (alias, self.alias_map[alias], "exact", 1.0)
                    break

            # 2. Fuzzy Matching for Typographical / OCR Errors (Rapidfuzz)
            if not matched_entry:
                # Split candidate into words to check against short single-word aliases or evaluate full token
                for alias in sorted_aliases:
                    if len(alias) < 4:
                        continue  # Avoid fuzzy matching short 3-letter codes

                    score = fuzz.token_sort_ratio(cleaned_cand, alias)
                    if score >= 85:
                        conf = round(score / 100.0, 2)
                        matched_entry = (alias, self.alias_map[alias], "fuzzy", conf)
                        break

            if matched_entry:
                alias_str, entry_data, m_type, conf = matched_entry
                sugar_match = SugarMatch(
                    ingredient_text=raw_token,
                    normalized_alias=entry_data["canonical"],
                    sugar_class=entry_data["class"],
                    position=pos,
                    confidence=conf,
                    match_type=m_type,
                    is_added=entry_data["is_added"],
                    explanation=entry_data["explanation"],
                )
                matches.append(sugar_match)

                if entry_data["is_added"] == "yes":
                    distinct_sugars_set.add(entry_data["canonical"])
                elif entry_data["class"] == "non_sugar_sweeteners":
                    sweeteners_list.append(entry_data["canonical"])
                elif entry_data["class"] == "carb_fillers":
                    carb_fillers_list.append(entry_data["canonical"])

        distinct_sugars = sorted(list(distinct_sugars_set))

        # First sugar position and sugars in top 3
        added_matches = [m for m in matches if m.is_added == "yes"]
        first_pos = min([m.position for m in added_matches]) if added_matches else None
        sugars_in_top3 = (first_pos is not None and first_pos <= 3)

        # Sugar splitting: >= 3 distinct added sugar aliases
        sugar_splitting = len(distinct_sugars) >= 3

        # Label conflict cross-check: 0g added sugar on label, but added sugar ingredients present
        label_conflict = False
        conflict_reason = None
        if added_sugar_g is not None and added_sugar_g <= 0.1 and len(distinct_sugars) > 0:
            label_conflict = True
            conflict_reason = (
                f"Nutrition table reports 0g added sugar, but the ingredient statement lists: "
                f"{', '.join(distinct_sugars)}. Both facts are shown for consumer transparency."
            )

        # Teaspoon conversion
        portion_teaspoons = None
        teaspoon_basis = None
        if added_sugar_g is not None:
            portion_teaspoons = sugar_g_to_teaspoons_rounded(added_sugar_g)
            teaspoon_basis = "added_sugar"
        elif total_sugars_g is not None:
            portion_teaspoons = sugar_g_to_teaspoons_rounded(total_sugars_g)
            teaspoon_basis = "total_sugars"
        else:
            missing_data.append("added_sugar_g")
            missing_data.append("total_sugars_g")

        return SugarReport(
            matches=matches,
            distinct_sugar_names=distinct_sugars,
            first_sugar_position=first_pos,
            sugars_in_top3=sugars_in_top3,
            sugar_splitting=sugar_splitting,
            non_sugar_sweeteners=sorted(list(set(sweeteners_list))),
            carb_fillers=sorted(list(set(carb_fillers_list))),
            label_conflict=label_conflict,
            label_conflict_reason=conflict_reason,
            portion_teaspoons=portion_teaspoons,
            teaspoon_basis=teaspoon_basis,
            total_sugar_grams=total_sugars_g,
            added_sugar_grams=added_sugar_g,
            missing_data=missing_data,
            status="OK",
        )
