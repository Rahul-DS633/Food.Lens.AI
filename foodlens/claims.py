"""
FoodLens AI — Marketing Claim Detection & Verification Engine
Evaluates front-of-pack claims against verified label nutrition, ordered ingredients,
and sugar detector reports.

Strict Legal Neutrality Rules:
- Never say 'false', 'misleading', or 'fraud'.
- Say 'the label values do not appear to support this claim'.
- Always include category disclaimer and statutory benchmark citations.
- Pure Python domain logic: Zero UI imports.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple
import yaml

from foodlens.nutrition import NutritionProfile
from foodlens.sugar_detector import SugarDetector


class ClaimStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTLY_SUPPORTED = "PARTLY_SUPPORTED"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    CANNOT_VERIFY = "CANNOT_VERIFY"
    NOT_CHECKABLE = "NOT_CHECKABLE"


@dataclass(frozen=True)
class ClaimEvidence:
    field: str
    value: Any
    basis: str


@dataclass(frozen=True)
class ClaimResult:
    claim_text: str
    rule_id: str
    status: ClaimStatus
    evidence: List[ClaimEvidence] = field(default_factory=list)
    threshold_value: Optional[float] = None
    threshold_operator: Optional[str] = None
    threshold_source: str = ""
    confidence: float = 1.0
    missing_fields: List[str] = field(default_factory=list)
    neutral_explanation: str = ""
    disclaimer: str = "Based on the label data we have; claim rules can differ by product category."


@dataclass(frozen=True)
class ClaimCheckSummary:
    results: List[ClaimResult]
    total_claims: int
    supported_count: int
    partly_supported_count: int
    not_supported_count: int
    cannot_verify_count: int
    not_checkable_count: int
    summary_sentence: str


class ClaimChecker:
    """
    Deterministic rule engine verifying front-of-pack marketing claims against
    nutrition facts and ordered ingredients.
    """

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent / "config" / "claims.yaml"

        self.config_path = config_path
        self._rules: Dict[str, Any] = {}
        self._vague_terms: List[str] = []
        self._vague_explanation: str = ""
        self._sugar_detector = SugarDetector()
        self._load_config()

    def _load_config(self) -> None:
        if not self.config_path.exists():
            return

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        rules_dict = data.get("rules", {})
        self._rules = {k: v for k, v in rules_dict.items() if k != "vague_marketing_terms"}
        
        vague_cfg = rules_dict.get("vague_marketing_terms", {})
        self._vague_terms = [t.lower() for t in vague_cfg.get("terms", []) + vague_cfg.get("hindi_terms", [])]
        self._vague_explanation = vague_cfg.get(
            "explanation",
            "Marketing terms do not have fixed statutory nutrition thresholds under food labelling regulations."
        )

    def _match_claim(self, claim_text: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        clean = claim_text.strip().lower()
        # Clean punctuation
        clean_norm = re.sub(r"[^\w\s\u0900-\u097F]", " ", clean)
        clean_norm = re.sub(r"\s+", " ", clean_norm).strip()

        # 1. Check vague buzzwords
        for v in self._vague_terms:
            v_norm = re.sub(r"[^\w\s\u0900-\u097F]", " ", v)
            v_norm = re.sub(r"\s+", " ", v_norm).strip()
            if v_norm == clean_norm or v == clean or v in clean:
                return "vague_terms", None

        # 2. Check rule claim_names and hindi_names
        for rule_id, rule_data in self._rules.items():
            aliases = rule_data.get("claim_names", []) + rule_data.get("hindi_names", [])
            for alias in aliases:
                a_clean = alias.strip().lower()
                a_norm = re.sub(r"[^\w\s\u0900-\u097F]", " ", a_clean)
                a_norm = re.sub(r"\s+", " ", a_norm).strip()
                if clean == a_clean or clean_norm == a_norm:
                    return rule_id, rule_data
                if len(a_norm) > 4 and a_norm in clean_norm:
                    return rule_id, rule_data

        return None, None

    def _get_nutrient_val_per_100g(
        self,
        profile: NutritionProfile,
        field_name: str
    ) -> Tuple[Optional[float], Optional[str], Optional[str]]:
        """
        Returns (scaled_val_100g, basis_desc, error_code).
        If basis is per_serving:
          - If serving_size_g > 0: linear conversion to 100g
          - Else: error_code="serving_size_missing"
        """
        nut = None
        if hasattr(profile, field_name):
            nut = getattr(profile, field_name)
        elif hasattr(profile, "nutrients") and isinstance(profile.nutrients, dict):
            nut = profile.nutrients.get(field_name)

        if nut is None or nut.value is None:
            return None, None, "nutrient_missing"

        if profile.basis == "per_serving":
            if profile.serving_size_g is None or profile.serving_size_g <= 0:
                return None, None, "serving_size_missing"
            scaled = (nut.value * 100.0) / profile.serving_size_g
            return round(scaled, 2), "scaled_to_100g_from_serving", None

        return round(nut.value, 2), "per_100g", None

    def check_claims(
        self,
        claim_texts: List[str],
        profile: NutritionProfile,
        ingredients_text: Optional[str] = None
    ) -> ClaimCheckSummary:
        results: List[ClaimResult] = []
        if ingredients_text is None:
            ingredients_text = getattr(profile, "ingredients_text", "") or ""

        for text in claim_texts:
            rule_id, rule_data = self._match_claim(text)

            if rule_id == "vague_terms":
                results.append(
                    ClaimResult(
                        claim_text=text,
                        rule_id="vague_marketing_terms",
                        status=ClaimStatus.NOT_CHECKABLE,
                        neutral_explanation=self._vague_explanation,
                    )
                )
                continue

            if not rule_id or not rule_data:
                results.append(
                    ClaimResult(
                        claim_text=text,
                        rule_id="unrecognized",
                        status=ClaimStatus.NOT_CHECKABLE,
                        neutral_explanation=(
                            f"'{text}' does not correspond to a recognized statutory nutrition category in our database."
                        ),
                    )
                )
                continue

            rule_type = rule_data.get("type", "nutrient_content")

            if rule_type == "process_claim":
                results.append(
                    ClaimResult(
                        claim_text=text,
                        rule_id=rule_id,
                        status=ClaimStatus.CANNOT_VERIFY,
                        threshold_source=rule_data.get("source", ""),
                        neutral_explanation=rule_data.get(
                            "explanation",
                            "Processing methods cannot be independently verified from the nutrition panel alone."
                        ),
                    )
                )
                continue

            if rule_type == "ingredient_exclusion":
                banned_words = rule_data.get("banned_keywords", [])
                ing_lower = ingredients_text.lower()
                found = [w for w in banned_words if w.lower() in ing_lower]
                if found:
                    status = ClaimStatus.NOT_SUPPORTED
                    expl = (
                        f"The label values do not appear to support this claim: declared ingredients list '{found[0]}'."
                    )
                else:
                    status = ClaimStatus.SUPPORTED
                    expl = "Refined flour (maida) does not appear anywhere in declared ingredients text."

                results.append(
                    ClaimResult(
                        claim_text=text,
                        rule_id=rule_id,
                        status=status,
                        threshold_source=rule_data.get("source", ""),
                        neutral_explanation=expl,
                    )
                )
                continue

            if rule_type == "ingredient_position":
                if rule_id == "whole_grain":
                    ing_text = ingredients_text
                    # Split ingredients
                    tokens = [t.strip() for t in re.split(r"[,;]+", ing_text) if t.strip()]
                    targets = [t.lower() for t in rule_data.get("target_ingredients", [])]
                    disquals = [d.lower() for d in rule_data.get("disqualifying_ingredients", [])]

                    target_idx = None
                    disqual_idx = None

                    for idx, tok in enumerate(tokens):
                        t_lower = tok.lower()
                        if target_idx is None and any(t in t_lower for t in targets):
                            target_idx = idx
                        if disqual_idx is None and any(d in d_lower for d in disquals for d_lower in [t_lower]):
                            disqual_idx = idx

                    if target_idx is None:
                        status = ClaimStatus.NOT_SUPPORTED
                        expl = "The label values do not appear to support this claim: no whole grain flour detected in readable ingredients."
                    elif target_idx == 0 and (disqual_idx is None or disqual_idx > 0):
                        status = ClaimStatus.SUPPORTED
                        expl = "Whole grain is the primary flour declared at ingredient position #1."
                    else:
                        status = ClaimStatus.PARTLY_SUPPORTED
                        pos_str = f"position #{target_idx + 1}"
                        expl = f"Whole grain is present at ingredient {pos_str}, but refined flour or other ingredients appear earlier in the ingredient statement."

                    evidence = []
                    if target_idx is not None:
                        evidence.append(ClaimEvidence(field="ingredient_position", value=target_idx + 1, basis="ordered_ingredients"))

                    results.append(
                        ClaimResult(
                            claim_text=text,
                            rule_id=rule_id,
                            status=status,
                            evidence=evidence,
                            threshold_source=rule_data.get("source", ""),
                            neutral_explanation=expl,
                        )
                    )
                    continue

                if rule_id == "multigrain":
                    ing_text = ingredients_text.lower()
                    grains = rule_data.get("grains", [])
                    min_count = rule_data.get("min_grains_count", 2)
                    detected = [g for g in grains if g in ing_text]
                    if len(detected) >= min_count:
                        status = ClaimStatus.SUPPORTED
                        expl = f"Contains {len(detected)} distinct edible grains ({', '.join(detected)})."
                    else:
                        status = ClaimStatus.NOT_SUPPORTED
                        expl = f"The label values do not appear to support this claim: fewer than {min_count} distinct grains detected in ingredients."

                    results.append(
                        ClaimResult(
                            claim_text=text,
                            rule_id=rule_id,
                            status=status,
                            evidence=[ClaimEvidence(field="distinct_grains_count", value=len(detected), basis="ordered_ingredients")],
                            threshold_source=rule_data.get("source", ""),
                            neutral_explanation=expl,
                        )
                    )
                    continue

            if rule_type in ("nutrient_content", "ingredient_and_nutrient"):
                nutrient_field = rule_data.get("nutrient_field", "")
                val_100g, basis_desc, err = self._get_nutrient_val_per_100g(profile, nutrient_field)

                if err == "serving_size_missing":
                    results.append(
                        ClaimResult(
                            claim_text=text,
                            rule_id=rule_id,
                            status=ClaimStatus.CANNOT_VERIFY,
                            threshold_source=rule_data.get("source", ""),
                            missing_fields=["serving_size_g"],
                            neutral_explanation=f"Cannot verify '{text}' because serving size in grams is not declared on the label.",
                        )
                    )
                    continue

                if err == "nutrient_missing" and rule_id != "no_added_sugar":
                    results.append(
                        ClaimResult(
                            claim_text=text,
                            rule_id=rule_id,
                            status=ClaimStatus.CANNOT_VERIFY,
                            threshold_source=rule_data.get("source", ""),
                            missing_fields=[nutrient_field],
                            neutral_explanation=f"The label does not declare {nutrient_field}; cannot verify '{text}'.",
                        )
                    )
                    continue

                # Specific check for no_added_sugar
                if rule_id == "no_added_sugar":
                    sugar_report = self._sugar_detector.detect_sugars(ingredients_text)
                    matches_count = len(sugar_report.matches)
                    has_sugar_ingredients = matches_count > 0
                    added_val = val_100g if val_100g is not None else 0.0

                    if added_val > 0.0 or has_sugar_ingredients:
                        status = ClaimStatus.NOT_SUPPORTED
                        if has_sugar_ingredients:
                            first_name = sugar_report.matches[0].ingredient_text or sugar_report.matches[0].normalized_alias
                            expl = f"The label values do not appear to support this claim: declared ingredients list {matches_count} sugar/syrup item(s) (e.g., {first_name})."
                        else:
                            expl = f"The label values do not appear to support this claim: nutrition panel declares {added_val} g added sugar."
                    else:
                        status = ClaimStatus.SUPPORTED
                        expl = "No added sugars, syrups, or concentrates detected in declared ingredients, and added sugar is 0 g on label."

                    evidence = [
                        ClaimEvidence(
                            field="sugar_detector_matches",
                            value=matches_count,
                            basis="ingredient_analysis"
                        )
                    ]
                    if val_100g is not None:
                        evidence.append(ClaimEvidence(field=nutrient_field, value=val_100g, basis=basis_desc or "per_100g"))

                    results.append(
                        ClaimResult(
                            claim_text=text,
                            rule_id=rule_id,
                            status=status,
                            evidence=evidence,
                            threshold_value=0.0,
                            threshold_operator="<=",
                            threshold_source=rule_data.get("source", ""),
                            neutral_explanation=expl,
                        )
                    )
                    continue

                # Standard numeric threshold evaluation
                is_liquid = getattr(profile, "is_beverage", False) or getattr(profile, "category", "") in ("beverage", "liquid") or "ml" in getattr(profile, "basis", "")
                thresh = (
                    rule_data.get("threshold_liquid") if is_liquid and "threshold_liquid" in rule_data
                    else rule_data.get("threshold_solid", rule_data.get("threshold"))
                )
                op = rule_data.get("operator", "<=")
                unit = "mg" if "mg" in nutrient_field else "g"

                if val_100g is None:
                    status = ClaimStatus.CANNOT_VERIFY
                    expl = f"The label does not declare {nutrient_field}; cannot verify '{text}'."
                elif thresh is not None:
                    passed = (val_100g <= thresh) if op == "<=" else (val_100g >= thresh)
                    if passed:
                        status = ClaimStatus.SUPPORTED
                        expl = f"Declared {nutrient_field} ({val_100g} {unit} / 100 g) meets the statutory threshold ({op} {thresh} {unit})."
                    else:
                        status = ClaimStatus.NOT_SUPPORTED
                        expl = f"The label values do not appear to support this claim ({val_100g} {unit} / 100 g vs statutory threshold {op} {thresh} {unit})."
                else:
                    status = ClaimStatus.CANNOT_VERIFY
                    expl = f"No statutory benchmark threshold defined for {text}."

                evidence = [
                    ClaimEvidence(
                        field=nutrient_field,
                        value=val_100g,
                        basis=basis_desc or "per_100g"
                    )
                ]

                results.append(
                    ClaimResult(
                        claim_text=text,
                        rule_id=rule_id,
                        status=status,
                        evidence=evidence,
                        threshold_value=float(thresh) if thresh is not None else None,
                        threshold_operator=op,
                        threshold_source=rule_data.get("source", ""),
                        neutral_explanation=expl,
                    )
                )

        # Calculate aggregates
        total = len(results)
        sup = sum(1 for r in results if r.status == ClaimStatus.SUPPORTED)
        part = sum(1 for r in results if r.status == ClaimStatus.PARTLY_SUPPORTED)
        not_sup = sum(1 for r in results if r.status == ClaimStatus.NOT_SUPPORTED)
        cannot = sum(1 for r in results if r.status == ClaimStatus.CANNOT_VERIFY)
        not_check = sum(1 for r in results if r.status == ClaimStatus.NOT_CHECKABLE)

        summary_sentence = (
            f"{sup} of {total} claims supported by label data." if total > 0
            else "No claims evaluated."
        )

        return ClaimCheckSummary(
            results=results,
            total_claims=total,
            supported_count=sup,
            partly_supported_count=part,
            not_supported_count=not_sup,
            cannot_verify_count=cannot,
            not_checkable_count=not_check,
            summary_sentence=summary_sentence,
        )
