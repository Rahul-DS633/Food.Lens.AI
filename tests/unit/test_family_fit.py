"""
Unit Tests for Family Profiles & Household Fit Engine
Rules:
1. Reuses personal_fit and allergens engine.
2. Severity ranking: CONTAINS_YOUR_ALLERGEN > MAY_CONTAIN_TRACES > UNKNOWN > NONE_DETECTED_IN_READABLE_TEXT.
3. Household banner mirrors worst status among selected members.
4. Minors under 18 strictly never receive calorie or weight guidance.
5. Never outputs 'safe for everyone'.
6. 8-member limit per household.
7. Dietary preferences (vegetarian, vegan, Jain, halal) evaluated deterministically.
"""

import pytest
from foodlens.family_fit import (
    FamilyMemberInput,
    HouseholdFitEngine,
    HouseholdFitResult,
    check_dietary_preference,
)
from foodlens.allergens import AllergenStatus
from foodlens.nutrition import create_nutrient, NutritionProfile


@pytest.fixture
def sample_nutrition():
    return NutritionProfile(
        basis="per_100g",
        energy_kcal=create_nutrient(400.0, "kcal", "per_100g"),
        protein_g=create_nutrient(6.0, "g", "per_100g"),
        carbs_g=create_nutrient(70.0, "g", "per_100g"),
        sugars_g=create_nutrient(25.0, "g", "per_100g"),
        added_sugar_g=create_nutrient(20.0, "g", "per_100g"),
        fat_g=create_nutrient(12.0, "g", "per_100g"),
        sat_fat_g=create_nutrient(5.0, "g", "per_100g"),
        trans_fat_g=create_nutrient(0.0, "g", "per_100g"),
        fibre_g=create_nutrient(2.0, "g", "per_100g"),
        sodium_mg=create_nutrient(350.0, "mg", "per_100g"),
        serving_size_g=25.0,
    )


def test_severity_ordering_and_household_banner(sample_nutrition):
    engine = HouseholdFitEngine()
    ingredients_text = "Wheat flour (atta), milk solids, sugar, palm oil, salt."

    # Member 1: allergic to milk -> CONTAINS_YOUR_ALLERGEN
    m1 = FamilyMemberInput(
        id=1, display_name="Aarav", age=12, allergies=["milk"], is_minor=True, consent_by_owner=True
    )
    # Member 2: allergic to peanut -> NONE_DETECTED_IN_READABLE_TEXT
    m2 = FamilyMemberInput(
        id=2, display_name="Pooja", age=35, allergies=["peanut"], is_minor=False, consent_by_owner=True
    )

    result = engine.check_household(
        members=[m1, m2],
        portions_by_member={1: 25.0, 2: 50.0},
        nutrition=sample_nutrition,
        ingredients_text=ingredients_text,
    )

    # Invariant: Worst status wins
    assert result.worst_allergen_status == AllergenStatus.CONTAINS_YOUR_ALLERGEN
    assert "Aarav" in result.top_alert_banner
    assert "contains milk" in result.top_alert_banner.lower()
    assert "safe for everyone" not in result.top_alert_banner.lower()


def test_minors_never_receive_calorie_or_weight_guidance(sample_nutrition):
    engine = HouseholdFitEngine()
    ingredients_text = "Rolled oats, almonds, honey, cinnamon."

    minor = FamilyMemberInput(
        id=3, display_name="Vihaan", age=10, weight_kg=32.0, allergies=[], is_minor=True, consent_by_owner=True
    )
    adult = FamilyMemberInput(
        id=4, display_name="Ramesh", age=42, weight_kg=78.0, allergies=[], is_minor=False, consent_by_owner=True
    )

    result = engine.check_household(
        members=[minor, adult],
        portions_by_member={3: 20.0, 4: 50.0},
        nutrition=sample_nutrition,
        ingredients_text=ingredients_text,
    )

    minor_fit = result.per_member_fits[3]
    adult_fit = result.per_member_fits[4]

    # Invariant: Minors under 18 have calorie and weight-based guidance disabled
    assert minor_fit.calorie_guidance is None
    assert minor_fit.weight_guidance is None
    assert any("under 18" in note.lower() or "pediatrician" in note.lower() or "parent" in note.lower() for note in minor_fit.guidance_notes)

    # Adults have normal guidance
    assert adult_fit.calorie_guidance is not None


def test_eight_member_cap_enforcement(sample_nutrition):
    engine = HouseholdFitEngine()
    members = [
        FamilyMemberInput(id=i, display_name=f"Member {i}", age=20+i, allergies=[], is_minor=False, consent_by_owner=True)
        for i in range(1, 10)  # 9 members
    ]

    with pytest.raises(ValueError) as exc:
        engine.check_household(
            members=members,
            portions_by_member={m.id: 25.0 for m in members},
            nutrition=sample_nutrition,
            ingredients_text="Flour, water, yeast.",
        )
    assert "cannot exceed 8 members" in str(exc.value).lower()


def test_dietary_preferences_evaluation():
    # 1. Pure veg ingredients
    veg_ing = "Wheat flour, sugar, cardamom, salt, baking powder."
    assert check_dietary_preference("vegetarian", veg_ing) == "CONFIRMED"
    assert check_dietary_preference("vegan", veg_ing) == "CONFIRMED"
    assert check_dietary_preference("jain", veg_ing) == "CONFIRMED"

    # 2. Contains milk -> Vegetarian: Yes, Vegan: No
    milk_ing = "Wheat flour, butter, milk solids, sugar."
    assert check_dietary_preference("vegetarian", milk_ing) == "CONFIRMED"
    assert check_dietary_preference("vegan", milk_ing) == "NOT_MET"

    # 3. Contains root vegetables (onion, garlic, potato) -> Jain: No
    jain_violating = "Potato starch, dehydrated garlic powder, sunflower oil, salt."
    assert check_dietary_preference("vegetarian", jain_violating) == "CONFIRMED"
    assert check_dietary_preference("jain", jain_violating) == "NOT_MET"

    # 4. Empty or missing text -> UNKNOWN
    assert check_dietary_preference("vegetarian", "") == "UNKNOWN"
