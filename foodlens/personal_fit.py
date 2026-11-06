"""
FoodLens Personal Fit Engine
Pure Python calculation of dietary alignment against standard ICMR-NIN & FSSAI daily reference intakes.

Guarantees:
1. 100% deterministic arithmetic. LLM never calculates numbers.
2. Missing nutrients remain None; never zero-filled.
3. Under-18 safety rules: disables calorie guidance and weight-based targets.
4. Allergen alert always overrides nutritional verdict.
5. All outputs cite portion grams, reference denominator, and standard source.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml

from foodlens.nutrition import NutritionProfile, Nutrient, scale
from foodlens.allergens import AllergenEngine, AllergenAnalysisResult, AllergenStatus

REF_INTAKES_PATH = Path(__file__).parent / "config" / "reference_intakes.yaml"

DISCLAIMER_TEXT = "General information, not medical advice. Verify on the pack."


class PersonalFitVerdict(str, Enum):
    ALLERGEN_ALERT = "Allergen alert"
    FITS_WELL = "Fits well"
    FITS_IN_MODERATION = "Fits in moderation"
    BETTER_OCCASIONALLY = "Better occasionally"
    NOT_ENOUGH_DATA = "Not enough data"


@dataclass(frozen=True)
class UserProfileData:
    name: str = "User"
    age: int = 25
    weight_kg: Optional[float] = None
    allergies: List[str] = field(default_factory=list)
    custom_allergens: List[str] = field(default_factory=list)
    language: str = "en"
    consent_given: bool = True
    parental_consent_given: bool = False


@dataclass(frozen=True)
class NutrientFlag:
    nutrient: str
    display_name: str
    portion_value: float
    reference_value: float
    pct_of_reference: float
    unit: str
    severity: str  # "green", "amber", "red"
    reason: str


@dataclass(frozen=True)
class PersonalFit:
    allergen_check: AllergenAnalysisResult
    nutrient_flags: List[NutrientFlag]
    verdict: PersonalFitVerdict
    confidence: float
    missing_data: List[str]
    guidance_notes: List[str]
    portion_grams: float
    disclaimer: str = DISCLAIMER_TEXT

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "portion_grams": self.portion_grams,
            "confidence": self.confidence,
            "disclaimer": self.disclaimer,
            "allergen_check": self.allergen_check.to_dict(),
            "nutrient_flags": [
                {
                    "nutrient": f.nutrient,
                    "display_name": f.display_name,
                    "portion_value": f.portion_value,
                    "reference_value": f.reference_value,
                    "pct_of_reference": f.pct_of_reference,
                    "unit": f.unit,
                    "severity": f.severity,
                    "reason": f.reason,
                }
                for f in self.nutrient_flags
            ],
            "missing_data": self.missing_data,
            "guidance_notes": self.guidance_notes,
        }


class PersonalFitEngine:
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or REF_INTAKES_PATH
        self.allergen_engine = AllergenEngine()
        self.ref_data: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        if not self.config_path.exists():
            return
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.ref_data = yaml.safe_load(f) or {}

    def calculate_fit(
        self,
        profile: NutritionProfile,
        user: UserProfileData,
        portion_grams: float,
        ingredients_text: Optional[str] = None,
        ocr_confidence: float = 1.0,
    ) -> PersonalFit:
        """
        Determines personal food fit deterministically.
        """
        # 1. Allergen Cross-Check (Always priority 1)
        allergen_res = self.allergen_engine.check_allergens(
            ingredients_text=ingredients_text,
            user_allergies=user.allergies,
            custom_allergens=user.custom_allergens,
            ocr_confidence=ocr_confidence,
        )

        # 2. Scale nutrition profile linearly to target portion
        portion_prof = self._scale_to_grams(profile, portion_grams)

        adult_ref = self.ref_data.get("adult_general", {})
        flags: List[NutrientFlag] = []
        missing_data: List[str] = []
        guidance_notes: List[str] = []

        is_minor = user.age < 18

        if is_minor:
            guidance_notes.append(
                "Notice: Caloric and weight-based dietary guidance are disabled for individuals under 18 under safety guidelines. Please involve a parent or guardian."
            )

        # Helper to safely evaluate nutrient % of reference
        def _check_nutrient(
            key: str,
            disp_name: str,
            ref_key: str,
            amber_pct: float,
            red_pct: float,
            unit: str = "g",
            higher_is_concerning: bool = True
        ):
            nutr: Optional[Nutrient] = getattr(portion_prof, key, None)
            if nutr is None or nutr.value is None:
                missing_data.append(key)
                return

            ref_info = adult_ref.get(ref_key, {})
            ref_val = ref_info.get("value")
            if not ref_val or ref_val <= 0:
                return

            pct = round((nutr.value / ref_val) * 100.0, 1)

            if higher_is_concerning:
                if pct >= red_pct:
                    sev = "red"
                    sev_text = "high share"
                elif pct >= amber_pct:
                    sev = "amber"
                    sev_text = "moderate share"
                else:
                    sev = "green"
                    sev_text = "modest share"
            else:
                # E.g. Protein / Fibre where higher is beneficial
                if pct >= amber_pct:
                    sev = "green"
                    sev_text = "good contribution"
                else:
                    sev = "green"
                    sev_text = "modest contribution"

            flags.append(
                NutrientFlag(
                    nutrient=key,
                    display_name=disp_name,
                    portion_value=round(nutr.value, 2),
                    reference_value=ref_val,
                    pct_of_reference=pct,
                    unit=unit,
                    severity=sev,
                    reason=f"Provides {pct}% of standard adult daily reference ({ref_val} {unit}) in this {portion_grams}g portion ({sev_text}).",
                )
            )

        # 3. Evaluate Nutrients
        # Calorie check: disabled for minors
        if not is_minor:
            _check_nutrient("energy_kcal", "Energy", "energy_kcal", amber_pct=15.0, red_pct=30.0, unit="kcal")

        # Added sugar / Total sugar
        added_sug = getattr(portion_prof, "added_sugar_g", None)
        if added_sug and added_sug.value is not None:
            _check_nutrient("added_sugar_g", "Added Sugar", "added_sugar_g", amber_pct=20.0, red_pct=40.0)
        else:
            _check_nutrient("sugars_g", "Total Sugar", "total_sugar_g", amber_pct=15.0, red_pct=30.0)

        # Saturated fat
        _check_nutrient("sat_fat_g", "Saturated Fat", "sat_fat_g", amber_pct=20.0, red_pct=35.0)

        # Sodium
        _check_nutrient("sodium_mg", "Sodium", "sodium_mg", amber_pct=20.0, red_pct=35.0, unit="mg")

        # Protein (Demographic-aware: adult with weight vs adult default)
        prot_nutr: Optional[Nutrient] = getattr(portion_prof, "protein_g", None)
        if prot_nutr is None or prot_nutr.value is None:
            missing_data.append("protein_g")
        else:
            if not is_minor and user.weight_kg and user.weight_kg > 0:
                ref_prot = round(user.weight_kg * 0.83, 1)
                prot_source_note = f"based on your {user.weight_kg} kg weight @ 0.83 g/kg ICMR RDA"
            else:
                ref_prot = adult_ref.get("protein_g_default", {}).get("value", 54.0)
                prot_source_note = "standard reference adult"

            pct_prot = round((prot_nutr.value / ref_prot) * 100.0, 1)
            flags.append(
                NutrientFlag(
                    nutrient="protein_g",
                    display_name="Protein",
                    portion_value=round(prot_nutr.value, 2),
                    reference_value=ref_prot,
                    pct_of_reference=pct_prot,
                    unit="g",
                    severity="green",
                    reason=f"Provides {round(prot_nutr.value, 1)} g ({pct_prot}% of {ref_prot} g daily target, {prot_source_note}) in this {portion_grams}g portion.",
                )
            )

        # Fibre
        _check_nutrient("fibre_g", "Dietary Fibre", "fibre_g", amber_pct=10.0, red_pct=25.0, higher_is_concerning=False)

        # 4. Determine Overall Verdict
        # Allergen Alert ALWAYS overrides everything
        if allergen_res.overall_status in (AllergenStatus.CONTAINS_YOUR_ALLERGEN, AllergenStatus.MAY_CONTAIN_TRACES):
            verdict = PersonalFitVerdict.ALLERGEN_ALERT
        elif allergen_res.overall_status == AllergenStatus.UNKNOWN and len(user.allergies) > 0:
            verdict = PersonalFitVerdict.NOT_ENOUGH_DATA
        elif len(flags) < 2 and len(missing_data) >= 3:
            verdict = PersonalFitVerdict.NOT_ENOUGH_DATA
        else:
            red_count = sum(1 for f in flags if f.severity == "red")
            amber_count = sum(1 for f in flags if f.severity == "amber")

            if red_count >= 1:
                verdict = PersonalFitVerdict.BETTER_OCCASIONALLY
            elif amber_count >= 2:
                verdict = PersonalFitVerdict.FITS_IN_MODERATION
            else:
                verdict = PersonalFitVerdict.FITS_WELL

        confidence = max(0.2, min(1.0, ocr_confidence * (1.0 - (len(missing_data) * 0.1))))

        return PersonalFit(
            allergen_check=allergen_res,
            nutrient_flags=flags,
            verdict=verdict,
            confidence=round(confidence, 2),
            missing_data=missing_data,
            guidance_notes=guidance_notes,
            portion_grams=portion_grams,
            disclaimer=DISCLAIMER_TEXT,
        )

    def _scale_to_grams(self, profile: NutritionProfile, grams: float) -> NutritionProfile:
        """Scales profile from 100g basis to portion grams linearly."""
        return NutritionProfile(
            basis="custom_portion",
            energy_kcal=scale(profile.energy_kcal, grams, target_basis="custom"),
            protein_g=scale(profile.protein_g, grams, target_basis="custom"),
            carbs_g=scale(profile.carbs_g, grams, target_basis="custom"),
            sugars_g=scale(profile.sugars_g, grams, target_basis="custom"),
            added_sugar_g=scale(profile.added_sugar_g, grams, target_basis="custom"),
            fat_g=scale(profile.fat_g, grams, target_basis="custom"),
            sat_fat_g=scale(profile.sat_fat_g, grams, target_basis="custom"),
            trans_fat_g=scale(profile.trans_fat_g, grams, target_basis="custom"),
            fibre_g=scale(profile.fibre_g, grams, target_basis="custom"),
            sodium_mg=scale(profile.sodium_mg, grams, target_basis="custom"),
            serving_size_g=profile.serving_size_g,
            net_weight_g=profile.net_weight_g,
            is_beverage=profile.is_beverage,
        )
