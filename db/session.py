"""
FoodLens Database Session and Initialization
Handles SQLite database connection, sessionmaker, and table seeding.
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from db.models import (
    Base, User, UserProgress, Achievement, Product, Nutrition, Ingredient, Scan, XPEvent, UserAchievement,
    Household
)
from foodlens.off_client import PRESEEDED_INDIAN_PRODUCTS
from foodlens.ingredients import IngredientEngine
from foodlens.auth import hash_password

ingredient_engine = IngredientEngine()

DATA_DIR = Path(__file__).parent.parent / "data"

# On Vercel / Serverless environments, /var/task is read-only; use /tmp for SQLite unless external DATABASE_URL provided
is_serverless = bool(
    os.getenv("VERCEL")
    or os.getenv("VERCEL_ENV")
    or os.getenv("VERCEL_REGION")
    or os.getenv("AWS_LAMBDA_FUNCTION_NAME")
    or os.getenv("LAMBDA_TASK_ROOT")
)

if is_serverless and "DATABASE_URL" not in os.environ:
    DEFAULT_DB_PATH = Path("/tmp/foodlens.db")
else:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        DEFAULT_DB_PATH = DATA_DIR / "foodlens.db"
    except OSError:
        DEFAULT_DB_PATH = Path("/tmp/foodlens.db")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI & Streamlit database dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


INITIAL_ACHIEVEMENTS = [
    {
        "code": "FIRST_SCAN",
        "title": "First Scan",
        "description": "Scanned your very first food product label.",
        "icon": "🎉",
    },
    {
        "code": "BARCODE_HUNTER",
        "title": "Barcode Hunter",
        "description": "Scanned 10 distinct food products.",
        "icon": "🎯",
    },
    {
        "code": "SHARP_EYES",
        "title": "Sharp Eyes",
        "description": "Corrected or verified extracted label fields.",
        "icon": "👁️",
    },
    {
        "code": "SUGAR_SPOTTER",
        "title": "Sugar Spotter",
        "description": "Used the sugar-in-teaspoons visualization.",
        "icon": "🧊",
    },
    {
        "code": "SERVING_SIZE_SLEUTH",
        "title": "Serving Size Sleuth",
        "description": "Checked 'Eat the Whole Packet' portion multiplier.",
        "icon": "🕵️",
    },
    {
        "code": "COMPARISON_CHAMPION",
        "title": "Comparison Champion",
        "description": "Compared two packaged foods side-by-side.",
        "icon": "⚖️",
    },
    {
        "code": "HINDI_EXPLORER",
        "title": "Hindi Explorer",
        "description": "Switched FoodLens to Hindi label mode.",
        "icon": "🇮🇳",
    },
    {
        "code": "PROFILE_SET_UP",
        "title": "Dietary Guardian",
        "description": "Set up your personalized food profile and allergen preferences.",
        "icon": "🛡️",
    },
    {
        "code": "FAMILY_PIONEER",
        "title": "Family Pioneer",
        "description": "Configured family members for multi-person food fit.",
        "icon": "👨‍👩‍👧‍👦",
    },
    {
        "code": "MYTH_BUSTER",
        "title": "Myth Buster",
        "description": "Inspected marketing claims and verified real label evidence.",
        "icon": "🔬",
    },
]


def init_db():
    """Creates tables and populates default demo data if missing."""
    try:
        Base.metadata.create_all(bind=engine)
        # Migrate optional columns on users table if SQLite table already existed
        with engine.connect() as conn:
            res = conn.execute(text("PRAGMA table_info(users)"))
            cols = {row[1] for row in res.fetchall()}
            if cols:
                if "username" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR(64)"))
                if "email" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(128)"))
                if "password_hash" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(256)"))
                if "role" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(16) DEFAULT 'user'"))
                conn.commit()
    except Exception as e:
        print(f"Warning: Base.metadata.create_all or migration failed: {e}")

    db: Session = SessionLocal()
    try:
        # 1. Seed Achievements
        for ach in INITIAL_ACHIEVEMENTS:
            existing = db.query(Achievement).filter(Achievement.code == ach["code"]).first()
            if not existing:
                db.add(Achievement(**ach))

        # 2. Ensure default demo user exists
        demo_user = db.query(User).filter(User.id == 1).first()
        if not demo_user:
            demo_user = User(
                id=1,
                username="curious",
                display_name="Curious Eater",
                role="user",
                password_hash=hash_password("demo123"),
                language="en"
            )
            db.add(demo_user)
            db.flush()

            progress = UserProgress(
                user_id=demo_user.id,
                xp=25,
                level="Label Rookie",
                current_streak=1,
                longest_streak=1,
                streak_freezes=1,
            )
            db.add(progress)
        else:
            if not demo_user.username:
                demo_user.username = "curious"
            if not demo_user.password_hash:
                demo_user.password_hash = hash_password("demo123")
            if not demo_user.role:
                demo_user.role = "user"

        # 2b. Ensure default admin user exists
        admin_user = db.query(User).filter(User.role == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                display_name="FoodLens Admin",
                role="admin",
                password_hash=hash_password("foodlens_admin_secret"),
                language="en"
            )
            db.add(admin_user)
            db.flush()

        # 3. Seed verified Indian products for offline resilience
        for code, prod in PRESEEDED_INDIAN_PRODUCTS.items():
            existing_prod = db.query(Product).filter(Product.barcode == code).first()
            if not existing_prod:
                db_prod = Product(
                    barcode=prod["barcode"],
                    name=prod["name"],
                    brand=prod["brand"],
                    category=prod["category"],
                    net_weight_g=prod.get("net_weight_g"),
                    serving_size_g=prod.get("serving_size_g"),
                    image_url=prod.get("image_url"),
                    source="api",
                    verification_status="verified",
                    quality_grade="A",
                )
                db.add(db_prod)
                db.flush()

                nutr = prod.get("nutrients", {})
                db_nutr = Nutrition(
                    product_id=db_prod.id,
                    basis="per_100g",
                    energy_kcal=nutr.get("energy_kcal"),
                    protein_g=nutr.get("protein_g"),
                    carbs_g=nutr.get("carbs_g"),
                    sugars_g=nutr.get("sugars_g"),
                    added_sugar_g=nutr.get("added_sugar_g"),
                    fat_g=nutr.get("fat_g"),
                    sat_fat_g=nutr.get("sat_fat_g"),
                    trans_fat_g=nutr.get("trans_fat_g"),
                    fibre_g=nutr.get("fibre_g"),
                    sodium_mg=nutr.get("sodium_mg"),
                )
                db.add(db_nutr)
                target_prod = db_prod
            else:
                target_prod = existing_prod

            # Seed ingredients if missing
            if target_prod and not target_prod.ingredients and prod.get("ingredients_text"):
                try:
                    ing_analysis = ingredient_engine.analyze(prod["ingredients_text"])
                    for ing in ing_analysis.ingredients:
                        db.add(Ingredient(
                            product_id=target_prod.id,
                            position=ing.position,
                            name=ing.cleaned_name,
                            category=ing.category,
                            explanation=ing.explanation,
                            allergen_flag=ing.allergen_tag or "none",
                        ))
                except Exception as ex:
                    print(f"Warning: could not seed ingredients for {prod.get('name')}: {ex}")

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Warning: init_db database seeding encountered: {e}")
    finally:
        db.close()



def export_user_data(user_id: int, db: Session) -> Dict[str, Any]:
    """
    Exports all personal data related to a user (DPDP Act right to data portability).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found"}

    profile = user.profile
    profile_data = None
    if profile:
        profile_data = {
            "name": profile.name,
            "age": profile.age,
            "weight_kg": profile.weight_kg,
            "allergies": profile.allergies_json or [],
            "custom_allergens": profile.custom_allergens_text,
            "language": profile.language,
            "consent_given": profile.consent_given,
            "parental_consent_given": profile.parental_consent_given,
            "consent_timestamp": profile.consent_timestamp.isoformat() if profile.consent_timestamp else None,
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
        }

    scans = db.query(Scan).filter(Scan.user_id == user_id).all()
    achievements = db.query(UserAchievement).filter(UserAchievement.user_id == user_id).all()

    return {
        "user_id": user.id,
        "display_name": user.display_name,
        "language": user.language,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "profile": profile_data,
        "total_scans": len(scans),
        "achievements_count": len(achievements),
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def delete_user_data(user_id: int, db: Session) -> bool:
    """
    Deletes all personal profile and activity data for a user (DPDP Act right to erasure).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    if user.profile:
        db.delete(user.profile)

    # Clear user scans and xp events
    db.query(Scan).filter(Scan.user_id == user_id).delete()
    db.query(XPEvent).filter(XPEvent.user_id == user_id).delete()
    db.query(UserAchievement).filter(UserAchievement.user_id == user_id).delete()

    # Reset user display name to default guest
    user.display_name = "Guest User"
    db.commit()
    return True


def export_household_data(user_id: int, db: Session) -> Optional[Dict[str, Any]]:
    """
    Exports all household and member data for a given user account (DPDP Act right to portability).
    """
    household = db.query(Household).filter(Household.owner_user_id == user_id).first()
    if not household:
        return None

    members_data = []
    for m in household.members:
        members_data.append({
            "id": m.id,
            "display_name": m.display_name,
            "emoji_avatar": m.emoji_avatar,
            "age": m.age,
            "weight_kg": m.weight_kg,
            "allergies": m.allergies_json or [],
            "dietary_prefs": m.dietary_prefs_json or [],
            "is_minor": m.is_minor,
            "consent_by_owner": m.consent_by_owner,
            "consent_at": m.consent_at.isoformat() if m.consent_at else None,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        })

    return {
        "household_id": household.id,
        "owner_user_id": household.owner_user_id,
        "created_at": household.created_at.isoformat() if household.created_at else None,
        "member_count": len(members_data),
        "members": members_data,
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def delete_household_data(user_id: int, db: Session) -> bool:
    """
    Deletes the user's household and all attached members (cascade delete).
    """
    household = db.query(Household).filter(Household.owner_user_id == user_id).first()
    if not household:
        return False

    db.delete(household)
    db.commit()
    return True


