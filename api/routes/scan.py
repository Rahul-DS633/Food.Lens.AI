"""
FoodLens Scan Routes: Barcode Lookup, OCR Label Extraction, and Confirmation
"""

import json
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas import (
    BarcodeScanRequest, BarcodeScanResponse, ConfirmScanRequest, LabelExtractionResponse
)
from db.models import Product, Nutrition, Ingredient, Scan, UserProgress, XPEvent
from foodlens.barcode import decode_barcode_from_image, clean_barcode, validate_ean13
from foodlens.off_client import OpenFoodFactsClient
from foodlens.ocr import OCREngine
from foodlens.parser import parse_ocr_text
from foodlens.validation import validate_nutrition_profile
from foodlens.scoring import calculate_foodlens_score
from foodlens.ingredients import IngredientEngine
from foodlens.gamification.xp import calculate_xp_award, get_level_for_xp
from foodlens.nutrition import Nutrient, NutritionProfile, create_nutrient

router = APIRouter(prefix="/api/scan", tags=["Scan"])

off_client = OpenFoodFactsClient()
ingredient_engine = IngredientEngine()
ocr_engine = OCREngine()


@router.post("/barcode", response_model=BarcodeScanResponse)
def scan_barcode(
    payload: Optional[BarcodeScanRequest] = None,
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Lookup product by barcode string or image.
    1. Decode from image if file is supplied.
    2. Check local database cache.
    3. Check Open Food Facts API client.
    4. Compute validation, score, ingredients, and award XP.
    """
    barcode = ""
    if isinstance(file, UploadFile):
        contents = file.file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image exceeds 10MB limit.")
        decoded, _ = decode_barcode_from_image(contents)
        if decoded:
            barcode = decoded
    elif payload and payload.barcode:
        barcode = clean_barcode(payload.barcode)

    if not barcode:
        return BarcodeScanResponse(
            found=False,
            source="none",
            message="No valid barcode detected. Please upload nutrition panel photos for OCR extraction."
        )

    # 1. Check DB first
    db_prod = db.query(Product).filter(Product.barcode == barcode).first()
    if db_prod and db_prod.nutrition:
        # Build profile from DB
        n = db_prod.nutrition
        profile = NutritionProfile(
            basis=n.basis or "per_100g",
            energy_kcal=create_nutrient(n.energy_kcal, "kcal", basis=n.basis, source="db"),
            protein_g=create_nutrient(n.protein_g, "g", basis=n.basis, source="db"),
            carbs_g=create_nutrient(n.carbs_g, "g", basis=n.basis, source="db"),
            sugars_g=create_nutrient(n.sugars_g, "g", basis=n.basis, source="db"),
            added_sugar_g=create_nutrient(n.added_sugar_g, "g", basis=n.basis, source="db"),
            fat_g=create_nutrient(n.fat_g, "g", basis=n.basis, source="db"),
            sat_fat_g=create_nutrient(n.sat_fat_g, "g", basis=n.basis, source="db"),
            trans_fat_g=create_nutrient(n.trans_fat_g, "g", basis=n.basis, source="db"),
            fibre_g=create_nutrient(n.fibre_g, "g", basis=n.basis, source="db"),
            sodium_mg=create_nutrient(n.sodium_mg, "mg", basis=n.basis, source="db"),
            serving_size_g=db_prod.serving_size_g,
            net_weight_g=db_prod.net_weight_g,
            is_beverage=(db_prod.category == "beverages" or db_prod.category == "drinks"),
        )
        validation_res = validate_nutrition_profile(profile)
        score_res = calculate_foodlens_score(profile, category=db_prod.category)

        ing_text = ", ".join([ing.name for ing in db_prod.ingredients]) if db_prod.ingredients else ""
        ing_res = ingredient_engine.analyze(ing_text)

        # Log scan and award XP (+10)
        xp_to_award = calculate_xp_award("scan")
        _award_user_xp(db, user_id=1, xp=xp_to_award, action="scan", ref_id=barcode)

        scan_record = Scan(
            user_id=1,
            product_id=db_prod.id,
            source_type="barcode",
            score=score_res.score,
            created_at=datetime.now(timezone.utc)
        )
        db.add(scan_record)
        db.commit()

        return BarcodeScanResponse(
            found=True,
            source="database",
            product={
                "id": db_prod.id,
                "barcode": db_prod.barcode,
                "name": db_prod.name,
                "brand": db_prod.brand,
                "category": db_prod.category,
                "net_weight_g": db_prod.net_weight_g,
                "serving_size_g": db_prod.serving_size_g,
                "image_url": db_prod.image_url,
                "quality_grade": db_prod.quality_grade,
            },
            nutrition_profile=profile.to_dict(),
            validation=validation_res.to_dict(),
            score=score_res.to_dict(),
            ingredients=ing_res.to_dict(),
            xp_awarded=xp_to_award,
            message=f"Product found in database! +{xp_to_award} XP awarded."
        )

    # 2. Check Open Food Facts
    prod_info, off_profile = off_client.fetch_product(barcode)
    if prod_info and off_profile:
        validation_res = validate_nutrition_profile(off_profile)
        score_res = calculate_foodlens_score(off_profile, category=prod_info.get("category"))
        ing_res = ingredient_engine.analyze(prod_info.get("ingredients_text", ""))

        # Save to DB as new product
        new_prod = Product(
            barcode=barcode,
            name=prod_info["name"],
            brand=prod_info["brand"],
            category=prod_info.get("category", "general"),
            net_weight_g=prod_info.get("net_weight_g"),
            serving_size_g=prod_info.get("serving_size_g"),
            image_url=prod_info.get("image_url"),
            source="api",
            verification_status="api",
            quality_grade=validation_res.quality_grade,
        )
        db.add(new_prod)
        db.flush()

        nutr_dict = prod_info.get("nutrients", {})
        db_nutr = Nutrition(
            product_id=new_prod.id,
            basis="per_100g",
            energy_kcal=nutr_dict.get("energy_kcal"),
            protein_g=nutr_dict.get("protein_g"),
            carbs_g=nutr_dict.get("carbs_g"),
            sugars_g=nutr_dict.get("sugars_g"),
            added_sugar_g=nutr_dict.get("added_sugar_g"),
            fat_g=nutr_dict.get("fat_g"),
            sat_fat_g=nutr_dict.get("sat_fat_g"),
            trans_fat_g=nutr_dict.get("trans_fat_g"),
            fibre_g=nutr_dict.get("fibre_g"),
            sodium_mg=nutr_dict.get("sodium_mg"),
        )
        db.add(db_nutr)

        # Save ingredients
        for ing in ing_res.ingredients:
            db.add(Ingredient(
                product_id=new_prod.id,
                position=ing.position,
                name=ing.raw_name,
                category=ing.category,
                explanation=ing.explanation,
                allergen_flag=ing.allergen_tag or "none"
            ))

        xp_to_award = calculate_xp_award("new_product")
        _award_user_xp(db, user_id=1, xp=xp_to_award, action="new_product", ref_id=barcode)

        scan_record = Scan(
            user_id=1,
            product_id=new_prod.id,
            source_type="barcode",
            score=score_res.score,
            created_at=datetime.now(timezone.utc)
        )
        db.add(scan_record)
        db.commit()

        prod_info["id"] = new_prod.id
        return BarcodeScanResponse(
            found=True,
            source="open_food_facts",
            product=prod_info,
            nutrition_profile=off_profile.to_dict(),
            validation=validation_res.to_dict(),
            score=score_res.to_dict(),
            ingredients=ing_res.to_dict(),
            xp_awarded=xp_to_award,
            message=f"Discovered new product on Open Food Facts! +{xp_to_award} XP awarded."
        )

    # 3. Not found
    return BarcodeScanResponse(
        found=False,
        source="none",
        message="Barcode not found in database or Open Food Facts. Please photograph the nutrition panel for OCR extraction."
    )


@router.post("/label", response_model=LabelExtractionResponse)
def extract_label(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None)
):
    """
    Extracts nutrition label fields from image upload or pasted raw text.
    Returns detected basis, fields, and flags low-confidence values (< 0.70).
    """
    lines: List[str] = []
    confidences: List[float] = []

    if isinstance(file, UploadFile):
        contents = file.file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image exceeds 10MB limit.")
        ocr_lines = ocr_engine.extract_text_from_image(contents)
        lines = [ol.text for ol in ocr_lines]
        confidences = [ol.confidence for ol in ocr_lines]

    if not lines and isinstance(raw_text, str) and raw_text.strip():
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        confidences = [0.90] * len(lines)

    if not lines:
        raise HTTPException(status_code=400, detail="No readable text or image provided.")

    profile, details = parse_ocr_text(lines, confidences)

    conf_scores: dict[str, float] = {}
    for k, v in details.get("field_matches", {}).items():
        if isinstance(v, dict) and "confidence" in v:
            conf_scores[k] = float(v["confidence"])

    return LabelExtractionResponse(
        detected_basis=details["detected_basis"],
        serving_size_g=details["serving_size_g"],
        nutrition_profile=profile.to_dict(),
        low_confidence_fields=details["low_confidence_fields"],
        raw_lines=lines,
        confidence_scores=conf_scores,
    )


@router.post("/confirm")
def confirm_scan(
    req: ConfirmScanRequest,
    db: Session = Depends(get_db)
):
    """
    User reviews, confirms, or edits extracted fields.
    Runs validation, saves to DB, and awards XP (+15 XP for verified data contribution).
    """
    # Build NutritionProfile from confirmed values
    nutr = req.nutrients
    profile = NutritionProfile(
        basis=req.basis,
        energy_kcal=create_nutrient(nutr.get("energy_kcal"), "kcal", basis=req.basis, source="user_confirmed"),
        protein_g=create_nutrient(nutr.get("protein_g"), "g", basis=req.basis, source="user_confirmed"),
        carbs_g=create_nutrient(nutr.get("carbs_g"), "g", basis=req.basis, source="user_confirmed"),
        sugars_g=create_nutrient(nutr.get("sugars_g"), "g", basis=req.basis, source="user_confirmed"),
        added_sugar_g=create_nutrient(nutr.get("added_sugar_g"), "g", basis=req.basis, source="user_confirmed"),
        fat_g=create_nutrient(nutr.get("fat_g"), "g", basis=req.basis, source="user_confirmed"),
        sat_fat_g=create_nutrient(nutr.get("sat_fat_g"), "g", basis=req.basis, source="user_confirmed"),
        trans_fat_g=create_nutrient(nutr.get("trans_fat_g"), "g", basis=req.basis, source="user_confirmed"),
        fibre_g=create_nutrient(nutr.get("fibre_g"), "g", basis=req.basis, source="user_confirmed"),
        sodium_mg=create_nutrient(nutr.get("sodium_mg"), "mg", basis=req.basis, source="user_confirmed"),
        serving_size_g=req.serving_size_g,
        net_weight_g=req.net_weight_g,
        is_beverage=(req.category in ("beverages", "drinks"))
    )

    val_res = validate_nutrition_profile(profile)
    score_res = calculate_foodlens_score(profile, category=req.category)
    ing_res = ingredient_engine.analyze(req.ingredients_text)

    # Save to database
    barcode_to_use = req.barcode or f"CUSTOM-{int(datetime.now().timestamp())}"
    existing_prod = db.query(Product).filter(Product.barcode == barcode_to_use).first()

    if existing_prod:
        prod = existing_prod
        prod.name = req.product_name
        prod.brand = req.brand
        prod.category = req.category
        prod.net_weight_g = req.net_weight_g
        prod.serving_size_g = req.serving_size_g
        prod.verification_status = "user_confirmed"
        prod.quality_grade = val_res.quality_grade
    else:
        prod = Product(
            barcode=barcode_to_use,
            name=req.product_name,
            brand=req.brand,
            category=req.category,
            net_weight_g=req.net_weight_g,
            serving_size_g=req.serving_size_g,
            source="ocr",
            verification_status="user_confirmed",
            quality_grade=val_res.quality_grade,
        )
        db.add(prod)
        db.flush()

    # Save or update nutrition
    if prod.nutrition:
        db.delete(prod.nutrition)
        db.flush()

    db_nutr = Nutrition(
        product_id=prod.id,
        basis=req.basis,
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

    # Save ingredients
    if prod.ingredients:
        for i in prod.ingredients:
            db.delete(i)
        db.flush()

    for ing in ing_res.ingredients:
        db.add(Ingredient(
            product_id=prod.id,
            position=ing.position,
            name=ing.raw_name,
            category=ing.category,
            explanation=ing.explanation,
            allergen_flag=ing.allergen_tag or "none"
        ))

    # Award XP (+15 XP for verified contribution)
    xp_to_award = calculate_xp_award("correction")
    _award_user_xp(db, user_id=req.user_id, xp=xp_to_award, action="correction", ref_id=barcode_to_use)

    scan_record = Scan(
        user_id=req.user_id,
        product_id=prod.id,
        source_type="ocr_confirmed",
        score=score_res.score,
        created_at=datetime.now(timezone.utc)
    )
    db.add(scan_record)
    db.commit()

    return {
        "status": "success",
        "product_id": prod.id,
        "xp_awarded": xp_to_award,
        "validation": val_res.to_dict(),
        "score": score_res.to_dict(),
        "ingredients": ing_res.to_dict(),
        "message": f"Verified product saved! +{xp_to_award} XP added to your Quest progress."
    }


def _award_user_xp(db: Session, user_id: int, xp: int, action: str, ref_id: str):
    """Helper to register XP events and update user levels."""
    progress = db.query(UserProgress).filter(UserProgress.user_id == user_id).first()
    if not progress:
        progress = UserProgress(user_id=user_id, xp=0)
        db.add(progress)

    progress.xp += xp
    lvl_name, _, _, _ = get_level_for_xp(progress.xp)
    progress.level = lvl_name

    event = XPEvent(
        user_id=user_id,
        event_type=action,
        xp=xp,
        ref_id=ref_id,
        created_at=datetime.now(timezone.utc)
    )
    db.add(event)
