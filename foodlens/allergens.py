"""
FoodLens Allergen Engine
100% deterministic allergen cross-checking against declared ingredients and precautionary statements.

Safety Invariants:
1. Pure Python deterministic matching. Never LLM-decided.
2. Allergen statuses are strictly:
   - CONTAINS_YOUR_ALLERGEN
   - MAY_CONTAIN_TRACES
   - NONE_DETECTED_IN_READABLE_TEXT
   - UNKNOWN
3. Never output 'safe' or 'allergen-free'.
4. If OCR confidence is low (< 0.60) or ingredients text is absent, status is UNKNOWN.
5. Always appends mandatory warning: 'Verify on the pack.'
"""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml

CONFIG_PATH = Path(__file__).parent / "config" / "allergen_synonyms.yaml"

DISCLAIMER_SUFFIX = "Verify on the pack."


class AllergenStatus(str, Enum):
    CONTAINS_YOUR_ALLERGEN = "CONTAINS_YOUR_ALLERGEN"
    MAY_CONTAIN_TRACES = "MAY_CONTAIN_TRACES"
    NONE_DETECTED_IN_READABLE_TEXT = "NONE_DETECTED_IN_READABLE_TEXT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class AllergenCheckResult:
    allergen: str
    display_name: str
    status: AllergenStatus
    matched_terms: List[str]
    location: str  # "ingredients", "precautionary_statement", "none", "unreadable"


@dataclass(frozen=True)
class AllergenAnalysisResult:
    overall_status: AllergenStatus
    allergen_results: List[AllergenCheckResult]
    banner_text: str
    has_alert: bool
    ocr_confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_status.value,
            "banner_text": self.banner_text,
            "has_alert": self.has_alert,
            "ocr_confidence": self.ocr_confidence,
            "allergen_results": [
                {
                    "allergen": r.allergen,
                    "display_name": r.display_name,
                    "status": r.status.value,
                    "matched_terms": r.matched_terms,
                    "location": r.location,
                }
                for r in self.allergen_results
            ],
        }


# Regex to separate precautionary allergen advisory statements from direct ingredients
PRECAUTIONARY_PATTERN = re.compile(
    r"(?:may contain(?:\s+traces of)?|processed in a facility that also handles|manufactured on equipment that processes|packed in a facility that handles|traces of)\s*[:\-]?\s*([^.]+)",
    re.IGNORECASE
)


class AllergenEngine:
    """
    Deterministic allergen identification engine with regional and chemical synonym resolution.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or CONFIG_PATH
        self.categories: Dict[str, Dict[str, Any]] = {}
        self._load_config()

    def _load_config(self):
        if not self.config_path.exists():
            return
        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            self.categories = data.get("categories", {})

    def _match_synonyms(self, text: str, synonyms: List[str]) -> List[str]:
        """Finds whole-word synonym matches in text."""
        lowered = text.lower()
        matched = []
        for syn in synonyms:
            syn_clean = syn.strip().lower()
            if not syn_clean:
                continue
            # Use word boundaries for clean matching
            pattern = rf"(?<!\w){re.escape(syn_clean)}(?!\w)"
            if re.search(pattern, lowered):
                matched.append(syn)
        return matched

    def check_allergens(
        self,
        ingredients_text: Optional[str],
        user_allergies: List[str],
        custom_allergens: Optional[List[str]] = None,
        ocr_confidence: float = 1.0,
    ) -> AllergenAnalysisResult:
        """
        Cross-checks declared allergens against package text and returns structured status.
        """
        custom_allergens = custom_allergens or []
        user_allergies = [a.lower().strip() for a in user_allergies if a.strip()]

        # Safety Check 1: Missing ingredients text or low OCR confidence
        if not ingredients_text or not ingredients_text.strip() or ocr_confidence < 0.60:
            results: List[AllergenCheckResult] = []
            for alg in user_allergies:
                disp = self.categories.get(alg, {}).get("display_name", alg.replace("_", " ").title())
                results.append(
                    AllergenCheckResult(
                        allergen=alg,
                        display_name=disp,
                        status=AllergenStatus.UNKNOWN,
                        matched_terms=[],
                        location="unreadable",
                    )
                )
            for c_alg in custom_allergens:
                results.append(
                    AllergenCheckResult(
                        allergen=f"custom:{c_alg.lower()}",
                        display_name=c_alg,
                        status=AllergenStatus.UNKNOWN,
                        matched_terms=[],
                        location="unreadable",
                    )
                )

            banner = (
                f"⚠️ Allergen status UNKNOWN due to missing or unreadable ingredient text. {DISCLAIMER_SUFFIX}"
            )
            return AllergenAnalysisResult(
                overall_status=AllergenStatus.UNKNOWN,
                allergen_results=results,
                banner_text=banner,
                has_alert=True,
                ocr_confidence=ocr_confidence,
            )

        # Separate precautionary statement from main ingredient text
        precautionary_text = ""
        main_ingredients_text = ingredients_text

        precautionary_matches = list(PRECAUTIONARY_PATTERN.finditer(ingredients_text))
        if precautionary_matches:
            precautionary_text = " ".join(m.group(0) for m in precautionary_matches)
            main_ingredients_text = PRECAUTIONARY_PATTERN.sub(" ", ingredients_text)

        results = []
        has_direct_allergen = False
        has_precautionary_trace = False

        # 1. Standard predefined categories
        for alg in user_allergies:
            cat_data = self.categories.get(alg, {})
            disp = cat_data.get("display_name", alg.replace("_", " ").title())
            synonyms = cat_data.get("synonyms", [alg])

            direct_matched = self._match_synonyms(main_ingredients_text, synonyms)
            trace_matched = self._match_synonyms(precautionary_text, synonyms)

            if direct_matched:
                results.append(
                    AllergenCheckResult(
                        allergen=alg,
                        display_name=disp,
                        status=AllergenStatus.CONTAINS_YOUR_ALLERGEN,
                        matched_terms=direct_matched,
                        location="ingredients",
                    )
                )
                has_direct_allergen = True
            elif trace_matched:
                results.append(
                    AllergenCheckResult(
                        allergen=alg,
                        display_name=disp,
                        status=AllergenStatus.MAY_CONTAIN_TRACES,
                        matched_terms=trace_matched,
                        location="precautionary_statement",
                    )
                )
                has_precautionary_trace = True
            else:
                results.append(
                    AllergenCheckResult(
                        allergen=alg,
                        display_name=disp,
                        status=AllergenStatus.NONE_DETECTED_IN_READABLE_TEXT,
                        matched_terms=[],
                        location="none",
                    )
                )

        # 2. Custom freeform user allergens
        for c_alg in custom_allergens:
            c_clean = c_alg.strip()
            if not c_clean:
                continue
            direct_c = self._match_synonyms(main_ingredients_text, [c_clean])
            trace_c = self._match_synonyms(precautionary_text, [c_clean])

            if direct_c:
                results.append(
                    AllergenCheckResult(
                        allergen=f"custom:{c_clean.lower()}",
                        display_name=c_clean,
                        status=AllergenStatus.CONTAINS_YOUR_ALLERGEN,
                        matched_terms=direct_c,
                        location="ingredients",
                    )
                )
                has_direct_allergen = True
            elif trace_c:
                results.append(
                    AllergenCheckResult(
                        allergen=f"custom:{c_clean.lower()}",
                        display_name=c_clean,
                        status=AllergenStatus.MAY_CONTAIN_TRACES,
                        matched_terms=trace_c,
                        location="precautionary_statement",
                    )
                )
                has_precautionary_trace = True
            else:
                results.append(
                    AllergenCheckResult(
                        allergen=f"custom:{c_clean.lower()}",
                        display_name=c_clean,
                        status=AllergenStatus.NONE_DETECTED_IN_READABLE_TEXT,
                        matched_terms=[],
                        location="none",
                    )
                )

        # Determine overall status & build neutral banner
        if has_direct_allergen:
            overall = AllergenStatus.CONTAINS_YOUR_ALLERGEN
            matched_items = [
                f"{r.display_name} ({', '.join(r.matched_terms)})"
                for r in results
                if r.status == AllergenStatus.CONTAINS_YOUR_ALLERGEN
            ]
            banner = f"🚨 CONTAINS YOUR ALLERGEN: Found {'; '.join(matched_items)} in ingredient list. {DISCLAIMER_SUFFIX}"
            has_alert = True
        elif has_precautionary_trace:
            overall = AllergenStatus.MAY_CONTAIN_TRACES
            matched_items = [
                f"{r.display_name} ({', '.join(r.matched_terms)})"
                for r in results
                if r.status == AllergenStatus.MAY_CONTAIN_TRACES
            ]
            banner = f"⚠️ MAY CONTAIN TRACES: Pack states {'; '.join(matched_items)} handled in facility. {DISCLAIMER_SUFFIX}"
            has_alert = True
        else:
            overall = AllergenStatus.NONE_DETECTED_IN_READABLE_TEXT
            banner = f"ℹ️ None of your selected allergens detected in readable label text. {DISCLAIMER_SUFFIX}"
            has_alert = False

        return AllergenAnalysisResult(
            overall_status=overall,
            allergen_results=results,
            banner_text=banner,
            has_alert=has_alert,
            ocr_confidence=ocr_confidence,
        )

