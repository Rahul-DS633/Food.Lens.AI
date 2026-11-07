"""
FoodLens Family Profiles & Household Fit Engine
Multi-person food fit evaluation, allergen matrix synthesis, and DPDP Act minor protection.

Key Architectural Guarantees:
1. Pure Python deterministic engine; reuses personal_fit and allergens engine.
2. Severity Order:
   CONTAINS_YOUR_ALLERGEN > MAY_CONTAIN_TRACES > UNKNOWN > NONE_DETECTED_IN_READABLE_TEXT.
3. Top household alert banner always mirrors worst status among selected members.
4. Minors under 18 strictly never receive calorie or weight-based guidance.
5. Never outputs 'safe for everyone'.
6. 8-member limit per household enforced.
7. Dietary preferences (vegetarian, vegan, Jain, halal) evaluated deterministically.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from foodlens.allergens import AllergenEngine, AllergenStatus, AllergenCheckResult
from foodlens.personal_fit import (
    PersonalFitEngine,
    UserProfileData,
    PersonalFit,
    PersonalFitVerdict,
)
from foodlens.nutrition import NutritionProfile

SEVERITY_ORDER = {
    AllergenStatus.CONTAINS_YOUR_ALLERGEN: 4,
    AllergenStatus.MAY_CONTAIN_TRACES: 3,
    AllergenStatus.UNKNOWN: 2,
    AllergenStatus.NONE_DETECTED_IN_READABLE_TEXT: 1,
}

NON_VEG_KEYWORDS = [
    "chicken", "mutton", "beef", "pork", "fish", "meat", "prawn", "shrimp",
    "crab", "gelatin", "gelatine", "carmine", "cochineal", "egg", "eggs", "albumin", "albumen"
]

ANIMAL_DERIVED_KEYWORDS = NON_VEG_KEYWORDS + [
    "milk", "dairy", "butter", "cheese", "whey", "casein", "lactose", "curd", "paneer",
    "ghee", "honey", "beeswax", "shellac"
]

ROOT_VEGETABLES_KEYWORDS = [
    "onion", "garlic", "potato", "carrot", "radish", "ginger", "beetroot", "turnip", "sweet potato"
]


@dataclass(frozen=True)
class FamilyMemberInput:
    id: int
    display_name: str
    age: int
    allergies: List[str]
    weight_kg: Optional[float] = None
    emoji_avatar: str = "👤"
    dietary_prefs: List[str] = field(default_factory=list)
    is_minor: bool = False
    consent_by_owner: bool = False


@dataclass(frozen=True)
class MemberFitSummary:
    member_id: int
    display_name: str
    emoji_avatar: str
    is_minor: bool
    portion_g: float
    allergen_status: AllergenStatus
    allergen_banner: str
    calorie_guidance: Optional[Dict[str, Any]]
    weight_guidance: Optional[Dict[str, Any]]
    dietary_pref_status: Dict[str, str]
    guidance_notes: List[str]
    personal_fit: PersonalFit


@dataclass(frozen=True)
class HouseholdFitResult:
    worst_allergen_status: AllergenStatus
    top_alert_banner: str
    allergen_matrix: Dict[str, Dict[str, str]]  # member_id -> {allergen: status}
    per_member_fits: Dict[int, MemberFitSummary]
    summary_sentence: str
    disclaimer: str = (
        "Based on readable packaging text. Never assume a product is safe for everyone. Always verify on the pack."
    )


def check_dietary_preference(pref: str, ingredients_text: str) -> str:
    """
    Evaluates dietary preference deterministically against ingredients list.
    Returns: 'CONFIRMED', 'NOT_MET', or 'UNKNOWN'.
    """
    if not ingredients_text or not ingredients_text.strip():
        return "UNKNOWN"

    text = ingredients_text.lower()
    p = pref.lower().strip()

    if p == "vegetarian":
        for kw in NON_VEG_KEYWORDS:
            if re.search(rf"\b{re.escape(kw)}\b", text):
                return "NOT_MET"
        return "CONFIRMED"

    if p == "vegan":
        for kw in ANIMAL_DERIVED_KEYWORDS:
            if re.search(rf"\b{re.escape(kw)}\b", text):
                return "NOT_MET"
        return "CONFIRMED"

    if p == "jain":
        # Jain must be veg AND free of root vegetables
        for kw in NON_VEG_KEYWORDS + ROOT_VEGETABLES_KEYWORDS:
            if re.search(rf"\b{re.escape(kw)}\b", text):
                return "NOT_MET"
        return "CONFIRMED"

    if p == "halal":
        # Pork and alcohol forbidden
        if re.search(r"\b(pork|bacon|ham|lard|alcohol|wine|beer)\b", text):
            return "NOT_MET"
        # Without explicit halal mark, return UNKNOWN
        return "UNKNOWN"

    return "UNKNOWN"


class HouseholdFitEngine:
    def __init__(self):
        self.personal_fit_engine = PersonalFitEngine()
        self.allergen_engine = AllergenEngine()

    def check_household(
        self,
        members: List[FamilyMemberInput],
        portions_by_member: Dict[int, float],
        nutrition: NutritionProfile,
        ingredients_text: str = "",
    ) -> HouseholdFitResult:
        """
        Runs comprehensive multi-member household food fit evaluation.
        """
        if len(members) > 8:
            raise ValueError(f"Household evaluation cannot exceed 8 members. Provided: {len(members)}")

        worst_status = AllergenStatus.NONE_DETECTED_IN_READABLE_TEXT
        worst_member_name = ""
        worst_trigger = ""

        per_member_fits: Dict[int, MemberFitSummary] = {}
        allergen_matrix: Dict[str, Dict[str, str]] = {}

        for m in members:
            portion_g = portions_by_member.get(m.id, 25.0)
            is_minor = m.age < 18 or m.is_minor

            # Build UserProfileData for this member
            profile_data = UserProfileData(
                name=m.display_name,
                age=m.age,
                weight_kg=m.weight_kg if not is_minor else None,  # Suppress weight for minor
                allergies=m.allergies,
                custom_allergens=[],
                language="en",
                consent_given=m.consent_by_owner,
                parental_consent_given=m.consent_by_owner if is_minor else False,
            )

            # Evaluate personal fit
            fit_res = self.personal_fit_engine.calculate_fit(
                profile=nutrition,
                user=profile_data,
                portion_grams=portion_g,
                ingredients_text=ingredients_text,
            )

            # Allergen status for this member
            m_status = fit_res.allergen_check.overall_status
            if SEVERITY_ORDER.get(m_status, 0) > SEVERITY_ORDER.get(worst_status, 0):
                worst_status = m_status
                worst_member_name = m.display_name
                worst_trigger = ", ".join(m.allergies)

            # Dietary preference statuses
            diet_status = {p: check_dietary_preference(p, ingredients_text) for p in m.dietary_prefs}

            # Populate matrix
            allergen_status_map = {
                res.allergen.lower(): res.status.value
                for res in fit_res.allergen_check.allergen_results
            }
            allergen_matrix[str(m.id)] = {
                a: allergen_status_map.get(a.lower(), AllergenStatus.NONE_DETECTED_IN_READABLE_TEXT.value)
                for a in m.allergies
            }

            # Minor guidance suppression
            guidance_notes = list(fit_res.guidance_notes)
            calorie_guidance = None
            weight_guidance = None

            if is_minor:
                calorie_guidance = None
                weight_guidance = None
                guidance_notes.append("Child profile (under 18): Calorie and weight guidance disabled per pediatric guidelines. Consult a pediatrician.")
            else:
                calorie_guidance = {
                    "energy_kcal": nutrition.energy_kcal.value if nutrition.energy_kcal else None,
                    "portion_g": portion_g,
                }
                if m.weight_kg:
                    weight_guidance = {"weight_kg": m.weight_kg}

            summary = MemberFitSummary(
                member_id=m.id,
                display_name=m.display_name,
                emoji_avatar=m.emoji_avatar,
                is_minor=is_minor,
                portion_g=portion_g,
                allergen_status=m_status,
                allergen_banner=fit_res.allergen_check.banner_text,
                calorie_guidance=calorie_guidance,
                weight_guidance=weight_guidance,
                dietary_pref_status=diet_status,
                guidance_notes=guidance_notes,
                personal_fit=fit_res,
            )
            per_member_fits[m.id] = summary

        # Formulate household top alert banner
        if worst_status == AllergenStatus.CONTAINS_YOUR_ALLERGEN:
            top_banner = f"⚠️ Alert for {worst_member_name}: Contains {worst_trigger} or related ingredients. Verify on the pack."
        elif worst_status == AllergenStatus.MAY_CONTAIN_TRACES:
            top_banner = f"⚠️ Trace Alert for {worst_member_name}: Pack may contain trace cross-contact for {worst_trigger}. Verify on the pack."
        elif worst_status == AllergenStatus.UNKNOWN:
            top_banner = "⚠️ Allergen Status Unknown: Ingredients list could not be verified. Verify on the pack."
        else:
            top_banner = "✓ No selected allergens detected in readable text for the selected members. Verify on the pack."

        summary_sentence = f"Checked for {len(members)} family members. Overall status: {worst_status.value}."

        return HouseholdFitResult(
            worst_allergen_status=worst_status,
            top_alert_banner=top_banner,
            allergen_matrix=allergen_matrix,
            per_member_fits=per_member_fits,
            summary_sentence=summary_sentence,
        )
