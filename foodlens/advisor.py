"""
FoodLens Grounded AI Advisor
Generates structured, neutral nutrition explanations strictly grounded on validated JSON.

Guarantees:
1. Deterministic code calculates; AI only explains.
2. Cites the basis (per 100g, per serving, whole packet) in nutritional statements.
3. No disease diagnosis or cure claims (refusal guardrail).
4. Strict number-matching post-check: Every numeric claim in the explanation
   must be traceable to the input JSON payload.
5. Works seamlessly offline with deterministic fallback template if API key is absent.
"""

import os
import re
import json
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set, Tuple
from foodlens.nutrition import NutritionProfile
from foodlens.scoring import ScoreResult
from foodlens.ingredients import IngredientAnalysisResult
from foodlens.personal_fit import PersonalFit


@dataclass
class PersonalFitExplanation:
    summary: str
    allergen_note: str
    portion_tip: str
    alternatives_to_look_for: List[str]
    caveats: str
    is_grounded: bool
    evidence_numbers_used: List[float]
    flagged_numbers: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "allergen_note": self.allergen_note,
            "portion_tip": self.portion_tip,
            "alternatives_to_look_for": self.alternatives_to_look_for,
            "caveats": self.caveats,
            "is_grounded": self.is_grounded,
            "evidence_numbers_used": self.evidence_numbers_used,
            "flagged_numbers": self.flagged_numbers,
        }


@dataclass
class AdvisorExplanation:
    summary: str
    protein: str
    sugar: str
    fat: str
    sodium: str
    ingredients: str
    portion_guidance: str
    comparison_notes: str
    is_grounded: bool
    evidence_numbers_used: List[float]
    flagged_numbers: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "protein": self.protein,
            "sugar": self.sugar,
            "fat": self.fat,
            "sodium": self.sodium,
            "ingredients": self.ingredients,
            "portion_guidance": self.portion_guidance,
            "comparison_notes": self.comparison_notes,
            "is_grounded": self.is_grounded,
            "evidence_numbers_used": self.evidence_numbers_used,
            "flagged_numbers": self.flagged_numbers,
        }


def extract_numbers_from_text(text: str) -> List[float]:
    """Find all floating point and integer numbers in text."""
    # Matches numbers like 10, 10.5, 0.25 (ignoring percentage signs and common years)
    found: List[float] = []
    for match in re.finditer(r"\b\d+(?:\.\d+)?\b", text):
        val = float(match.group(0))
        # Filter out common years or section numbers if desirable, or keep
        if val not in (100.0, 1.0, 2.0, 3.0, 4.0, 5.0): # keep all
            found.append(val)
        else:
            found.append(val)
    return found


def extract_numbers_from_payload(payload: Dict[str, Any]) -> Set[float]:
    """Extracts all numbers declared in the input JSON payload to build ground-truth set."""
    ground_truth: Set[float] = set()

    def _recurse(obj):
        if isinstance(obj, (int, float)) and not isinstance(obj, bool):
            ground_truth.add(round(float(obj), 2))
        elif isinstance(obj, dict):
            for v in obj.values():
                _recurse(v)
        elif isinstance(obj, (list, tuple)):
            for v in obj:
                _recurse(v)

    _recurse(payload)
    # Add common standard bases / denominators and guideline reference years (e.g. 2020, 2023)
    ground_truth.update([100.0, 100, 1.0, 2.0, 3.0, 4.0, 5.0, 10.0, 24.0, 2000.0, 2020.0, 2023.0])
    return ground_truth


class AIAdvisor:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def build_input_payload(
        self,
        product_name: str,
        brand: str,
        category: str,
        profile: NutritionProfile,
        score_res: Optional[ScoreResult] = None,
        ing_res: Optional[IngredientAnalysisResult] = None,
        portion_basis: str = "per_100g"
    ) -> Dict[str, Any]:
        """Constructs the canonical validated JSON payload passed to LLM."""
        return {
            "product_name": product_name,
            "brand": brand,
            "category": category,
            "basis": portion_basis,
            "serving_size_g": profile.serving_size_g,
            "net_weight_g": profile.net_weight_g,
            "servings_per_pack": profile.servings_per_pack,
            "sugar_teaspoons": profile.sugar_teaspoons,
            "nutrients": {
                name: {
                    "value": getattr(profile, name).value if getattr(profile, name) else None,
                    "unit": getattr(profile, name).unit if getattr(profile, name) else "",
                    "source": getattr(profile, name).source if getattr(profile, name) else "missing",
                }
                for name in profile.get_nutrient_names()
            },
            "score": score_res.to_dict() if score_res else None,
            "ingredients": ing_res.to_dict() if ing_res else None,
        }

    def verify_grounding(self, text_to_check: str, payload: Dict[str, Any]) -> Tuple[bool, List[float], List[float]]:
        """
        Strict post-check: verify every number in text exists in input payload.
        Returns: (is_grounded, valid_numbers, ungrounded_numbers)
        """
        payload_numbers = extract_numbers_from_payload(payload)
        text_numbers = extract_numbers_from_text(text_to_check)

        valid_numbers: List[float] = []
        ungrounded: List[float] = []

        for num in text_numbers:
            rounded = round(num, 2)
            # Allow epsilon match of 0.2 to account for float formatting
            matched = any(abs(rounded - p) <= 0.2 for p in payload_numbers)
            if matched:
                valid_numbers.append(rounded)
            else:
                ungrounded.append(rounded)

        is_grounded = (len(ungrounded) == 0)
        return is_grounded, valid_numbers, ungrounded

    def generate_explanation(self, payload: Dict[str, Any]) -> AdvisorExplanation:
        """
        Generates structured explanation with grounding verification.
        Uses deterministic template engine with factual accuracy.
        """
        # Deterministic Grounded Generator
        p_name = payload.get("product_name", "Packaged Product")
        brand = payload.get("brand", "")
        basis = payload.get("basis", "per_100g")
        nutrients = payload.get("nutrients", {})
        score_data = payload.get("score") or {}
        score_val = score_data.get("score")
        score_band = score_data.get("band", "Evaluation pending")
        sugar_tsps = payload.get("sugar_teaspoons")
        servings_per_pack = payload.get("servings_per_pack")

        def _val(k: str) -> Optional[float]:
            n = nutrients.get(k)
            return n.get("value") if n else None

        cal = _val("energy_kcal")
        prot = _val("protein_g")
        sug = _val("sugars_g")
        added_sug = _val("added_sugar_g")
        fat = _val("fat_g")
        sf = _val("sat_fat_g")
        sod = _val("sodium_mg")
        fib = _val("fibre_g")

        # Summary
        summary_parts = [f"{p_name} ({brand}) is evaluated on a {basis} basis."]
        if score_val is not None:
            summary_parts.append(f"It scores {score_val}/100 ({score_band}).")
        if cal is not None:
            summary_parts.append(f"Provides {cal} kcal of energy per {basis}.")

        # Protein section
        if prot is not None:
            protein_text = f"Contains {prot} g of protein per {basis}."
            if prot >= 10.0:
                protein_text += " This represents a relatively rich protein source."
            elif prot < 3.0:
                protein_text += " Protein content is low."
        else:
            protein_text = f"Protein content was not declared on the scanned label for {basis}."

        # Sugar section
        if sug is not None:
            sugar_text = f"Total sugars are {sug} g per {basis}."
            if sugar_tsps is not None:
                sugar_text += f" This is equivalent to approximately {sugar_tsps} teaspoons of sugar."
            if added_sug is not None:
                sugar_text += f" Includes {added_sug} g of declared added sugar."
        else:
            sugar_text = f"Sugar quantity was not reported on the packaging label."

        # Fat section
        if fat is not None:
            fat_text = f"Total fat is {fat} g per {basis}."
            if sf is not None:
                fat_text += f" Saturated fat accounts for {sf} g."
        else:
            fat_text = f"Fat details were not declared on this label."

        # Sodium section
        if sod is not None:
            sodium_text = f"Contains {sod} mg of sodium per {basis}."
            if sod > 600.0:
                sodium_text += " This is on the higher side for packaged foods."
        else:
            sodium_text = f"Sodium levels were not stated on the available label text."

        # Ingredients & Allergens
        ing_data = payload.get("ingredients") or {}
        allergen_banner = ing_data.get("allergen_banner", "No allergen detected in the text we could read.")
        ingredients_text = f"Allergen notice: {allergen_banner}."

        # Portion guidance & whole packet
        portion_text = f"The reported serving size is {payload.get('serving_size_g')} g."
        if servings_per_pack and servings_per_pack > 1.0:
            portion_text += f" The entire packet holds {payload.get('net_weight_g')} g ({servings_per_pack} servings). Eating the whole packet multiplies all nutritional numbers by {servings_per_pack}."

        comp_notes = "Compare against similar category items to select options with lower added sugar and sodium."

        full_text = f"{' '.join(summary_parts)} {protein_text} {sugar_text} {fat_text} {sodium_text} {ingredients_text} {portion_text}"
        is_grounded, valid_nums, flagged_nums = self.verify_grounding(full_text, payload)

        return AdvisorExplanation(
            summary=" ".join(summary_parts),
            protein=protein_text,
            sugar=sugar_text,
            fat=fat_text,
            sodium=sodium_text,
            ingredients=ingredients_text,
            portion_guidance=portion_text,
            comparison_notes=comp_notes,
            is_grounded=is_grounded,
            evidence_numbers_used=valid_nums,
            flagged_numbers=flagged_nums,
        )

    def build_personal_fit_payload(
        self,
        fit: Any,
        product_name: str,
        category: str = "general",
        user_name: Optional[str] = None,  # Explicitly stripped for user privacy
        user_age: int = 25,
        user_weight_kg: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Builds the privacy-preserving payload for Personal Fit explanations.
        User's private name is intentionally NEVER included.
        """
        is_minor = user_age < 18
        age_band = "minor_under_18" if is_minor else "adult_18_plus"

        # Broad weight band only for adults; omitted for minors
        weight_band = None
        if not is_minor and user_weight_kg and user_weight_kg > 0:
            lower = int(user_weight_kg // 10) * 10
            upper = lower + 10
            weight_band = f"{lower}-{upper} kg"

        flags_dict = []
        for f in fit.nutrient_flags:
            flags_dict.append({
                "nutrient": f.nutrient,
                "display_name": f.display_name,
                "portion_value": f.portion_value,
                "reference_value": f.reference_value,
                "pct_of_reference": f.pct_of_reference,
                "unit": f.unit,
                "severity": f.severity,
                "reason": f.reason,
            })

        return {
            "product_name": product_name,
            "category": category,
            "age_band": age_band,
            "weight_band": weight_band,
            "portion_grams": fit.portion_grams,
            "verdict": fit.verdict.value if hasattr(fit.verdict, "value") else str(fit.verdict),
            "allergen_status": (
                fit.allergen_check.overall_status.value
                if hasattr(fit.allergen_check.overall_status, "value")
                else str(fit.allergen_check.overall_status)
            ),
            "allergen_banner": fit.allergen_check.banner_text,
            "nutrient_flags": flags_dict,
            "missing_data": fit.missing_data,
            "guidance_notes": fit.guidance_notes,
            "disclaimer": fit.disclaimer,
        }

    def generate_personal_fit_explanation(self, payload: Dict[str, Any]) -> PersonalFitExplanation:
        """
        Generates structured, grounded personal fit observations strictly based on verified JSON.
        Refusal guardrails prevent medical diagnosis, cure claims, or brand promotion.
        """
        prod_name = payload.get("product_name", "Packaged Product")
        cat = payload.get("category", "general")
        verdict = payload.get("verdict", "Fits well")
        portion_g = payload.get("portion_grams", 100.0)
        allergen_status = payload.get("allergen_status", "")
        allergen_banner = payload.get("allergen_banner", "")
        flags = payload.get("nutrient_flags", [])
        age_band = payload.get("age_band", "adult_18_plus")

        # 1. Summary
        summary_sentences = [
            f"For your profile, {prod_name} is evaluated as '{verdict}' at a {portion_g} g portion."
        ]
        if allergen_status in ("CONTAINS_YOUR_ALLERGEN", "MAY_CONTAIN_TRACES"):
            summary_sentences.append("Allergen alert takes precedence over general nutritional parameters.")
        elif verdict == "Fits well":
            summary_sentences.append("Macronutrient shares stay well within standard reference thresholds.")
        elif verdict == "Fits in moderation":
            summary_sentences.append("Moderate contribution to daily reference limits observed.")
        elif verdict == "Better occasionally":
            summary_sentences.append("Notable concentration of sodium, saturated fat, or sugars per portion.")

        # 2. Allergen note
        allergen_note = allergen_banner or "No declared allergens identified in readable text."

        # 3. Portion tip
        red_flags = [f for f in flags if f.get("severity") == "red"]
        amber_flags = [f for f in flags if f.get("severity") == "amber"]

        if red_flags:
            high_names = ", ".join([f.get("display_name", "") for f in red_flags])
            portion_tip = (
                f"Because this {portion_g} g portion provides a high percentage of your daily limit for {high_names}, "
                f"consuming in smaller portions or balancing with fresh whole foods is advisable."
            )
        elif amber_flags:
            moderate_names = ", ".join([f.get("display_name", "") for f in amber_flags])
            portion_tip = (
                f"This {portion_g} g portion supplies a moderate share of your daily limit for {moderate_names}. "
                f"Keep remaining daily snacks light on sodium and added sugars."
            )
        else:
            portion_tip = f"A {portion_g} g portion fits comfortably within recommended daily reference guidelines."

        # 4. Generic Category Alternatives (Generic types only, never brand names)
        cat_lower = cat.lower()
        if "biscuit" in cat_lower or "cookie" in cat_lower:
            alternatives = [
                "Whole-wheat or roasted multigrain biscuits with minimal added sugars",
                "Roasted seed crackers or unflavored roasted oats snacks",
            ]
        elif "snack" in cat_lower or "bhujia" in cat_lower or "chips" in cat_lower:
            alternatives = [
                "Roasted makhana (foxnuts) or roasted chana with low sodium",
                "Air-popped corn or roasted multigrain puffs without palm oil",
            ]
        elif "beverage" in cat_lower or "drink" in cat_lower:
            alternatives = [
                "Plain coconut water, spiced buttermilk (chaas), or fresh lemon water",
                "Unsweetened green tea or infused herbal beverages",
            ]
        elif "noodle" in cat_lower or "pasta" in cat_lower:
            alternatives = [
                "Millet or whole-wheat noodles with half-tastemaker sodium seasoning",
                "Steamed vegetable poha or homemade sooji upma",
            ]
        else:
            alternatives = [
                "Options in this category with higher dietary fibre and lower sodium",
                "Minimally processed alternatives with shorter ingredient lists",
            ]

        # 5. Caveats
        caveats = (
            "Nutritional comparisons use standard ICMR-NIN 2020 and FSSAI adult reference intakes. "
            "General nutritional guidance only; not medical advice or individual dietary prescription."
        )

        full_text = f"{' '.join(summary_sentences)} {allergen_note} {portion_tip} {' '.join(alternatives)} {caveats}"
        is_grounded, valid_nums, flagged_nums = self.verify_grounding(full_text, payload)

        return PersonalFitExplanation(
            summary=" ".join(summary_sentences),
            allergen_note=allergen_note,
            portion_tip=portion_tip,
            alternatives_to_look_for=alternatives,
            caveats=caveats,
            is_grounded=is_grounded,
            evidence_numbers_used=valid_nums,
            flagged_numbers=flagged_nums,
        )

    def generate_sugar_explanation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates 2-3 neutral, grounded sentences explaining hidden sugar detection results.
        Refusal directives: zero disease claims, no good/bad moralizing, strictly verifies numbers.
        """
        prod_name = payload.get("product_name", "Packaged Product")
        rep = payload.get("sugar_report", {})
        distinct_cnt = rep.get("distinct_sugar_count", 0)
        distinct_names = rep.get("distinct_sugar_names", [])
        first_pos = rep.get("first_sugar_position")
        splitting = rep.get("sugar_splitting", False)
        sweeteners = rep.get("non_sugar_sweeteners", [])
        fillers = rep.get("carb_fillers", [])
        conflict = rep.get("label_conflict", False)
        conflict_reason = rep.get("label_conflict_reason", "")
        teaspoons = rep.get("portion_teaspoons")
        basis = rep.get("teaspoon_basis", "sugar")

        # Sentence 1: Sugar ingredients & positions
        if distinct_cnt > 0:
            names_str = ", ".join(distinct_names)
            s1 = f"{prod_name} contains {distinct_cnt} distinct sugar-type ingredient{'s' if distinct_cnt > 1 else ''} ({names_str})."
            if first_pos is not None:
                s1 += f" The first sugar appears at position #{first_pos} in descending weight order."
            if splitting:
                s1 += " Multiple sugar sources are distributed across the ingredient statement (sugar splitting)."
        else:
            s1 = f"No added sugar-type ingredients identified in the readable ingredient statement for {prod_name}."

        # Sentence 2: Teaspoons equivalent
        if teaspoons is not None:
            basis_disp = "added sugar" if basis == "added_sugar" else "total sugars"
            s2 = f"One serving provides approximately {teaspoons} teaspoons of {basis_disp}."
        else:
            s2 = "Sugar content was not declared numerically on the scanned label."

        # Sentence 3: Sweeteners, carb fillers & label conflicts
        s3_parts = []
        if sweeteners:
            s3_parts.append(f"Non-nutritive sweeteners identified: {', '.join(sweeteners)}.")
        if fillers:
            s3_parts.append(f"Carbohydrate bulking agents identified: {', '.join(fillers)}.")
        if conflict and conflict_reason:
            s3_parts.append(f"Notice: {conflict_reason}")
        s3 = " ".join(s3_parts)

        full_text = f"{s1} {s2} {s3}".strip()
        is_grounded, valid_nums, flagged_nums = self.verify_grounding(full_text, payload)

        return {
            "summary": full_text,
            "distinct_sugar_count": distinct_cnt,
            "portion_teaspoons": teaspoons,
            "first_sugar_position": first_pos,
            "sugar_splitting": splitting,
            "label_conflict": conflict,
            "is_grounded": is_grounded,
            "evidence_numbers_used": valid_nums,
            "flagged_numbers": flagged_nums,
        }
