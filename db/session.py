"""
FoodLens Database Session and Initialization
Handles SQLite database connection, sessionmaker, and table seeding.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from db.models import (
    Base, User, UserProgress, Achievement, Product, Nutrition, Ingredient
)
from foodlens.off_client import PRESEEDED_INDIAN_PRODUCTS

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_DB_PATH = DATA_DIR / "foodlens.db"
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
]


def init_db():
    """Creates tables and populates default demo data if missing."""
    Base.metadata.create_all(bind=engine)
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
            demo_user = User(id=1, display_name="Curious Eater", language="en")
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

        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


# Ensure DB is initialized when session module is loaded
init_db()
