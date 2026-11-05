"""
FoodLens Quest Routes: Progress, Daily Challenges, and Mini-Games
"""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.deps import get_db
from api.schemas import QuestProgressResponse, QuestAttemptRequest, QuestAttemptResponse
from db.models import User, UserProgress, Achievement, UserAchievement, XPEvent
from foodlens.gamification.xp import get_level_for_xp, calculate_xp_award
from foodlens.gamification.streaks import update_user_streak
from foodlens.gamification.badges import check_new_achievements
from foodlens.gamification.challenges import (
    get_daily_challenge, evaluate_sugar_guess, evaluate_serving_trap_answer
)

router = APIRouter(prefix="/api/quest", tags=["Quest"])


@router.get("/progress")
def get_quest_progress(user_id: int = 1, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    progress = user.progress
    if not progress:
        progress = UserProgress(user_id=user_id, xp=0)
        db.add(progress)
        db.commit()

    # Update streak
    today = date.today()
    new_streak, new_longest, new_freezes, streak_msg = update_user_streak(
        progress.last_active_date,
        progress.current_streak,
        progress.longest_streak,
        progress.streak_freezes,
        today=today
    )
    progress.current_streak = new_streak
    progress.longest_streak = new_longest
    progress.streak_freezes = new_freezes
    progress.last_active_date = today.isoformat()

    lvl_name, lvl_icon, base_xp, next_xp = get_level_for_xp(progress.xp)
    progress.level = lvl_name

    # Check achievements
    all_achievements = db.query(Achievement).all()
    earned_ids = {ua.achievement_id for ua in user.achievements} if user.achievements else set()

    # Calculate user activity counts
    scan_count = len(user.scans) if user.scans else 0
    stats = {
        "total_scans": scan_count,
        "corrections_count": db.query(XPEvent).filter(XPEvent.user_id == user_id, XPEvent.event_type == "correction").count(),
        "comparisons_count": db.query(XPEvent).filter(XPEvent.user_id == user_id, XPEvent.event_type == "compare").count(),
        "used_sugar_cubes": True,
        "checked_whole_packet": True,
    }
    earned_codes = [a.code for a in all_achievements if a.id in earned_ids]
    newly_earned = check_new_achievements(stats, earned_codes)
    for code in newly_earned:
        ach_obj = db.query(Achievement).filter(Achievement.code == code).first()
        if ach_obj:
            db.add(UserAchievement(user_id=user_id, achievement_id=ach_obj.id))

    db.commit()

    badges_list = []
    for a in all_achievements:
        is_earned = a.id in earned_ids or a.code in newly_earned
        badges_list.append({
            "code": a.code,
            "title": a.title,
            "description": a.description,
            "icon": a.icon,
            "unlocked": is_earned,
        })

    return {
        "user_id": user_id,
        "xp": progress.xp,
        "level": progress.level,
        "level_icon": lvl_icon,
        "current_level_base": base_xp,
        "next_level_xp": next_xp,
        "current_streak": progress.current_streak,
        "longest_streak": progress.longest_streak,
        "streak_freezes": progress.streak_freezes,
        "streak_message": streak_msg,
        "badges": badges_list,
    }


@router.get("/daily")
def get_daily_quest():
    today = date.today()
    challenge = get_daily_challenge(today)
    return {
        "status": "success",
        "challenge": challenge
    }


@router.post("/attempt")
def submit_minigame_attempt(
    req: QuestAttemptRequest,
    db: Session = Depends(get_db)
):
    """
    Submits a mini-game guess:
    - 'guess_sugar': Guess Before You Scan
    - 'serving_trap': How Many Servings in this Packet?
    Awards XP and updates user level.
    """
    if req.game_type == "guess_sugar":
        awarded_xp, msg = evaluate_sugar_guess(req.actual_value, req.user_guess)
    elif req.game_type == "serving_trap":
        awarded_xp, msg = evaluate_serving_trap_answer(req.actual_value, req.user_guess)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown game type: {req.game_type}")

    # Register XP
    progress = db.query(UserProgress).filter(UserProgress.user_id == req.user_id).first()
    if not progress:
        progress = UserProgress(user_id=req.user_id, xp=0)
        db.add(progress)

    progress.xp += awarded_xp
    lvl_name, _, _, _ = get_level_for_xp(progress.xp)
    progress.level = lvl_name

    db.add(XPEvent(
        user_id=req.user_id,
        event_type=f"minigame_{req.game_type}",
        xp=awarded_xp,
        ref_id=str(req.actual_value)
    ))
    db.commit()

    return {
        "status": "success",
        "xp_awarded": awarded_xp,
        "message": msg,
        "total_xp": progress.xp,
        "level": progress.level,
    }
