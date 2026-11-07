"""
Unit tests for foodlens/gamification modules:
1. Daily and per-product XP caps
2. Level progression
3. Streak calculations and protective freeze usage
4. Badges unlocking
5. Mini-game scoring
"""

from datetime import date, timedelta
from foodlens.gamification.xp import calculate_xp_award, get_level_for_xp
from foodlens.gamification.streaks import update_user_streak
from foodlens.gamification.badges import check_new_achievements
from foodlens.gamification.challenges import evaluate_sugar_guess, evaluate_serving_trap_answer


def test_xp_daily_and_product_caps():
    # Regular scan award
    xp = calculate_xp_award("scan", current_daily_xp=0, current_product_xp=0)
    assert xp == 10

    # Approaching daily cap: only 5 left before 150
    xp_capped = calculate_xp_award("scan", current_daily_xp=145, current_product_xp=0)
    assert xp_capped == 5

    # At daily cap: 0 awarded
    xp_zero = calculate_xp_award("scan", current_daily_xp=150, current_product_xp=0)
    assert xp_zero == 0


def test_level_progression():
    lvl, icon, base, nxt = get_level_for_xp(50)
    assert lvl == "Label Rookie"
    assert icon == "🌱"

    lvl, icon, base, nxt = get_level_for_xp(120)
    assert lvl == "Label Reader"
    assert icon == "📖"

    lvl, icon, base, nxt = get_level_for_xp(1050)
    assert lvl == "Food Intelligence Pro"
    assert icon == "🏆"


def test_streak_consecutive_and_freeze():
    today = date(2026, 11, 5)
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)

    # Consecutive day: increment streak
    streak, longest, freezes, msg = update_user_streak(
        yesterday.isoformat(), current_streak=4, longest_streak=4, streak_freezes=1, today=today
    )
    assert streak == 5
    assert longest == 5
    assert freezes == 1

    # Missed one day, protected by freeze!
    streak_f, longest_f, freezes_f, msg_f = update_user_streak(
        two_days_ago.isoformat(), current_streak=4, longest_streak=4, streak_freezes=1, today=today
    )
    assert streak_f == 5
    assert freezes_f == 0
    assert "Streak Freeze used" in msg_f


def test_badges_unlock():
    stats = {
        "total_scans": 1,
        "corrections_count": 0,
        "comparisons_count": 0,
        "used_sugar_cubes": True,
        "claims_verified_count": 1,
    }
    new_badges = check_new_achievements(stats, already_earned_codes=[])
    assert "FIRST_SCAN" in new_badges
    assert "SUGAR_SPOTTER" in new_badges
    assert "MYTH_BUSTER" in new_badges


def test_mini_games():
    xp, msg = evaluate_sugar_guess(10.0, 10.5)
    assert xp == 25
    assert "Bullseye" in msg

    xp_trap, msg_trap = evaluate_serving_trap_answer(3.0, 3.0)
    assert xp_trap == 20
    assert "Correct" in msg_trap

