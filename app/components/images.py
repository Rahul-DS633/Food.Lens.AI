"""
FoodLens AI — Realistic Image & Product Card System
Loads and converts realistic product photography and nutrition visuals
to high-performance base64 data URIs for instantaneous, offline-ready rendering.
"""

import base64
from pathlib import Path
from typing import Optional, Dict

_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "images"

# Map brands/categories to downloaded realistic high-res photography
_PRODUCT_IMAGE_MAP: Dict[str, str] = {
    "parle-g": "biscuits.jpg",
    "parle": "biscuits.jpg",
    "biscuits": "biscuits.jpg",
    "maggi": "noodles.jpg",
    "noodles": "noodles.jpg",
    "instant_noodles": "noodles.jpg",
    "haldiram": "bhujia.jpg",
    "haldiram's": "bhujia.jpg",
    "aloo bhujia": "bhujia.jpg",
    "bhujia": "bhujia.jpg",
    "namkeen": "bhujia.jpg",
    "amul": "butter.jpg",
    "butter": "butter.jpg",
    "spreads": "butter.jpg",
    "frooti": "mango_drink.jpg",
    "parle agro": "mango_drink.jpg",
    "beverages": "mango_drink.jpg",
    "drinks": "mango_drink.jpg",
}


def get_image_base64(filename: str) -> str:
    """
    Reads a local image and encodes it into a base64 data URI.
    """
    img_path = _ASSETS_DIR / filename
    if img_path.exists():
        ext = img_path.suffix.lstrip(".").lower()
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
        try:
            with open(img_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                return f"data:{mime};base64,{b64}"
        except Exception:
            return ""
    return ""


def get_product_image(
    product_name: str = "",
    brand: str = "",
    category: str = "",
    fallback_url: Optional[str] = None
) -> str:
    """
    Resolves the best real packaging image for a product.
    1. Prioritizes verified Open Food Facts / CDN image URL (fallback_url).
    2. Falls back to local authentic packaging photography base64 data URI.
    3. Falls back to nutrition hero visual.
    """
    # 1. Prioritize real Open Food Facts / CDN image URL if provided
    if fallback_url and fallback_url.startswith("http"):
        return fallback_url

    # 2. Match against local packaging photography assets
    search_keys = [
        product_name.lower(),
        brand.lower(),
        category.lower()
    ]

    for key in search_keys:
        for pattern, filename in _PRODUCT_IMAGE_MAP.items():
            if pattern in key:
                data_uri = get_image_base64(filename)
                if data_uri:
                    return data_uri

    # 3. Default category fallback
    data_uri = get_image_base64("hero_nutrition.jpg")
    return data_uri or ""

