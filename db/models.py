"""
FoodLens SQLAlchemy Database Models
Covers Products, Nutrition, Ingredients, Extractions, Scans, Users,
and the FoodLens Quest Gamification Layer.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Boolean, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utcnow():
    return datetime.now(timezone.utc)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    barcode = Column(String(32), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    brand = Column(String(128), default="")
    category = Column(String(64), default="general")
    net_weight_g = Column(Float, nullable=True)
    serving_size_g = Column(Float, nullable=True)
    image_url = Column(String(512), nullable=True)
    source = Column(String(32), default="manual")  # api, ocr, manual
    retrieved_at = Column(DateTime, default=utcnow)
    verification_status = Column(String(32), default="unverified")  # api, ocr, user_confirmed, manual
    quality_grade = Column(String(4), default="B")  # A, B, C

    # Relationships
    nutrition = relationship("Nutrition", back_populates="product", uselist=False, cascade="all, delete-orphan")
    ingredients = relationship("Ingredient", back_populates="product", order_by="Ingredient.position", cascade="all, delete-orphan")
    scans = relationship("Scan", back_populates="product")
    revisions = relationship("ProductRevision", back_populates="product", cascade="all, delete-orphan")
    reports = relationship("DataReport", back_populates="product")


class Nutrition(Base):
    __tablename__ = "nutrition"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    basis = Column(String(32), default="per_100g")
    energy_kcal = Column(Float, nullable=True)
    protein_g = Column(Float, nullable=True)
    carbs_g = Column(Float, nullable=True)
    sugars_g = Column(Float, nullable=True)
    added_sugar_g = Column(Float, nullable=True)
    fat_g = Column(Float, nullable=True)
    sat_fat_g = Column(Float, nullable=True)
    trans_fat_g = Column(Float, nullable=True)
    fibre_g = Column(Float, nullable=True)
    sodium_mg = Column(Float, nullable=True)

    raw_label_json = Column(JSON, nullable=True)
    normalised_json = Column(JSON, nullable=True)
    field_sources_json = Column(JSON, nullable=True)

    product = relationship("Product", back_populates="nutrition")


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    position = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(64), default="ingredient")
    explanation = Column(Text, default="")
    allergen_flag = Column(String(64), default="none")

    product = relationship("Product", back_populates="ingredients")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    display_name = Column(String(64), default="Guest User")
    language = Column(String(8), default="en")  # en, hi
    created_at = Column(DateTime, default=utcnow)

    scans = relationship("Scan", back_populates="user")
    progress = relationship("UserProgress", back_populates="user", uselist=False, cascade="all, delete-orphan")
    xp_events = relationship("XPEvent", back_populates="user")
    achievements = relationship("UserAchievement", back_populates="user")
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    household = relationship("Household", back_populates="owner", uselist=False, cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)          # Display only, never sent to external AI
    age = Column(Integer, nullable=False)               # 1 to 120
    weight_kg = Column(Float, nullable=True)            # Optional: 5.0 to 300.0 kg
    allergies_json = Column(JSON, nullable=False)       # List[str]: ["milk", "peanut", ...]
    custom_allergens_text = Column(Text, default="")    # Freeform comma-separated custom triggers
    language = Column(String(8), default="en")          # "en" or "hi"
    consent_given = Column(Boolean, default=False)      # Must be True
    parental_consent_given = Column(Boolean, default=False) # Required if age < 18
    consent_timestamp = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="profile")


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    source_type = Column(String(32), default="barcode")  # barcode, ocr, manual
    consumed_g = Column(Float, nullable=True)
    score = Column(Integer, nullable=True)
    scoring_version = Column(String(16), default="1.0.0")
    created_at = Column(DateTime, default=utcnow, index=True)

    product = relationship("Product", back_populates="scans")
    user = relationship("User", back_populates="scans")
    extraction = relationship("Extraction", back_populates="scan", uselist=False, cascade="all, delete-orphan")


class Extraction(Base):
    __tablename__ = "extractions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False, index=True)
    ocr_engine = Column(String(32), default="easyocr")
    raw_text = Column(Text, default="")
    avg_confidence = Column(Float, default=1.0)
    field_confidence_json = Column(JSON, nullable=True)
    user_corrections_json = Column(JSON, nullable=True)

    scan = relationship("Scan", back_populates="extraction")


# --- Game Layer Tables (FoodLens Quest) ---

class UserProgress(Base):
    __tablename__ = "user_progress"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    xp = Column(Integer, default=0)
    level = Column(String(64), default="Label Rookie")
    current_streak = Column(Integer, default=1)
    longest_streak = Column(Integer, default=1)
    last_active_date = Column(String(16), default="")  # YYYY-MM-DD
    streak_freezes = Column(Integer, default=1)

    user = relationship("User", back_populates="progress")


class XPEvent(Base):
    __tablename__ = "xp_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)  # scan, correction, first_scan, compare, minigame
    xp = Column(Integer, nullable=False)
    ref_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="xp_events")


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, index=True, nullable=False)
    title = Column(String(128), nullable=False)
    description = Column(String(255), nullable=False)
    icon = Column(String(16), default="🏅")
    rule_json = Column(JSON, nullable=True)


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), primary_key=True)
    earned_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement")


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(16), nullable=False, index=True)  # YYYY-MM-DD
    type = Column(String(64), nullable=False)
    config_json = Column(JSON, nullable=True)


class ChallengeAttempt(Base):
    __tablename__ = "challenge_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    result_json = Column(JSON, nullable=True)
    xp = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)


# --- Data Report & Audit Trail (Wrong Data & Admin Review) ---

class DataReport(Base):
    __tablename__ = "data_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    field = Column(String(64), nullable=False)             # "name", "barcode", "protein_g", "ingredients", etc.
    current_value = Column(Text, nullable=True)
    proposed_value = Column(Text, nullable=False)
    evidence_image_path = Column(String(512), nullable=True) # Stored outside web root
    comment = Column(String(500), default="")
    reporter_hash = Column(String(64), nullable=True, index=True) # SHA-256 of session/IP
    status = Column(String(32), default="pending", index=True)    # pending, approved, rejected, needs_info, duplicate
    priority_score = Column(Float, default=1.0)
    auto_checks_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utcnow, index=True)
    reviewed_by = Column(String(64), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewer_note = Column(Text, default="")

    product = relationship("Product", back_populates="reports")
    revisions = relationship("ProductRevision", back_populates="report")


class ProductRevision(Base):
    __tablename__ = "product_revisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    field = Column(String(64), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=False)
    source = Column(String(32), default="user_report")  # user_report, admin_edit
    report_id = Column(Integer, ForeignKey("data_reports.id"), nullable=True)
    changed_by = Column(String(64), default="admin")
    changed_at = Column(DateTime, default=utcnow)

    product = relationship("Product", back_populates="revisions")
    report = relationship("DataReport", back_populates="revisions")


# --- Family Profiles & Households ---

class Household(Base):
    __tablename__ = "households"

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=utcnow)

    owner = relationship("User", back_populates="household")
    members = relationship("HouseholdMember", back_populates="household", cascade="all, delete-orphan", order_by="HouseholdMember.id")


class HouseholdMember(Base):
    __tablename__ = "household_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    household_id = Column(Integer, ForeignKey("households.id"), nullable=False, index=True)
    display_name = Column(String(128), nullable=False)
    emoji_avatar = Column(String(16), default="👤")
    age = Column(Integer, nullable=False)
    weight_kg = Column(Float, nullable=True)
    allergies_json = Column(JSON, nullable=False)         # List[str]
    dietary_prefs_json = Column(JSON, default=list)       # List[str]: "vegetarian", "vegan", "jain", "halal"
    is_minor = Column(Boolean, nullable=False)            # Derived from age < 18
    consent_by_owner = Column(Boolean, default=False)     # Verifiable parental consent under DPDP Act
    consent_at = Column(DateTime, default=utcnow)
    created_at = Column(DateTime, default=utcnow)

    household = relationship("Household", back_populates="members")


Index("idx_reports_prod_status", DataReport.product_id, DataReport.status)
Index("idx_revisions_product", ProductRevision.product_id, ProductRevision.changed_at)
Index("idx_scans_user_created", Scan.user_id, Scan.created_at)
Index("idx_products_barcode", Product.barcode)

