"""
FoodLens Quest Badges Engine
Evaluates milestone achievements based on user literacy and engagement activities.
"""

from typing import List, Dict, Any


def check_new_achievements(stats: Dict[str, Any], already_earned_codes: List[str]) -> List[str]:
    """
    Checks if user qualifies for new achievements based on current statistics.
    Returns list of newly unlocked badge codes.
    """
    already_set = set(already_earned_codes)
    newly_earned: List[str] = []

    total_scans = stats.get("total_scans", 0)
    corrections = stats.get("corrections_count", 0)
    comparisons = stats.get("comparisons_count", 0)
    sugar_spotter = stats.get("used_sugar_cubes", False)
    serving_sleuth = stats.get("checked_whole_packet", False)
    hindi_explorer = stats.get("used_hindi", False)

    if total_scans >= 1 and "FIRST_SCAN" not in already_set:
        newly_earned.append("FIRST_SCAN")

    if total_scans >= 10 and "BARCODE_HUNTER" not in already_set:
        newly_earned.append("BARCODE_HUNTER")

    if corrections >= 5 and "SHARP_EYES" not in already_set:
        newly_earned.append("SHARP_EYES")

    if comparisons >= 1 and "COMPARISON_CHAMPION" not in already_set:
        newly_earned.append("COMPARISON_CHAMPION")

    if sugar_spotter and "SUGAR_SPOTTER" not in already_set:
        newly_earned.append("SUGAR_SPOTTER")

    if serving_sleuth and "SERVING_SIZE_SLEUTH" not in already_set:
        newly_earned.append("SERVING_SIZE_SLEUTH")

    if hindi_explorer and "HINDI_EXPLORER" not in already_set:
        newly_earned.append("HINDI_EXPLORER")

    profile_set_up = stats.get("profile_set_up", False)
    if profile_set_up and "PROFILE_SET_UP" not in already_set:
        newly_earned.append("PROFILE_SET_UP")

    return newly_earned

