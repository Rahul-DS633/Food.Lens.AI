"""
FoodLens Barcode Engine
Validation, checksum calculation, Indian EAN-13 prefix detection, and image decoding.

Rules:
1. Validate EAN-13 / UPC checksums before querying databases.
2. Flag Indian packaged foods (prefix 890).
3. Robust handling of whitespace, dashes, and malformed inputs.
4. Image decoding via OpenCV BarcodeDetector.
"""

import re
from typing import Optional, Tuple
import cv2
import numpy as np


def clean_barcode(code: str) -> str:
    """Strip whitespace, dashes, and non-digit characters."""
    if not code:
        return ""
    return re.sub(r"[^\d]", "", str(code).strip())


def calculate_ean13_checksum(digits12: str) -> int:
    """
    Computes the 13th check digit for a 12-digit string.
    Odd-index digits (1st, 3rd, 5th...) weight = 1
    Even-index digits (2nd, 4th, 6th...) weight = 3
    Check digit = (10 - (sum % 10)) % 10
    """
    if len(digits12) != 12 or not digits12.isdigit():
        raise ValueError(f"Expected 12 numeric digits, got: {digits12}")

    total = 0
    for idx, char in enumerate(digits12):
        digit = int(char)
        # 0-indexed: index 0 is 1st digit (odd), index 1 is 2nd digit (even)
        weight = 1 if (idx % 2 == 0) else 3
        total += digit * weight

    remainder = total % 10
    return (10 - remainder) % 10


def validate_ean13(code: str) -> bool:
    """
    Validates an EAN-13 barcode including length and check digit.
    Also handles 12-digit UPC-A by prepending a 0.
    """
    cleaned = clean_barcode(code)

    # Convert UPC-A (12 digits) to EAN-13
    if len(cleaned) == 12:
        cleaned = "0" + cleaned

    if len(cleaned) != 13:
        return False

    expected_check = calculate_ean13_checksum(cleaned[:12])
    return int(cleaned[12]) == expected_check


def is_indian_product(code: str) -> bool:
    """
    GS1 Country Code for India is 890.
    Returns True if the barcode begins with 890.
    """
    cleaned = clean_barcode(code)
    if len(cleaned) == 12:
        cleaned = "0" + cleaned
    return cleaned.startswith("890")


def decode_barcode_from_image(image_input) -> Tuple[Optional[str], Optional[str]]:
    """
    Attempts to detect and decode a barcode from an image (file path, bytes, or numpy array).
    Returns (barcode_str, barcode_type) or (None, None).
    """
    img = None
    if isinstance(image_input, str):
        img = cv2.imread(image_input)
    elif isinstance(image_input, (bytes, bytearray)):
        nparr = np.frombuffer(image_input, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    elif isinstance(image_input, np.ndarray):
        img = image_input

    if img is None:
        return None, None

    # Use OpenCV's BarcodeDetector
    try:
        detector = cv2.barcode.BarcodeDetector()
        ok, decoded_info, decoded_type, _ = detector.detectAndDecode(img)
        if ok and decoded_info:
            # decoded_info might be a tuple or string depending on OpenCV version
            info = decoded_info[0] if isinstance(decoded_info, (list, tuple)) else decoded_info
            btype = decoded_type[0] if isinstance(decoded_type, (list, tuple)) else decoded_type
            if info:
                cleaned = clean_barcode(info)
                return cleaned, str(btype)
    except Exception:
        pass

    # Fallback with grayscale and thresholding if direct detection missed it
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        detector = cv2.barcode.BarcodeDetector()
        ok, decoded_info, decoded_type, _ = detector.detectAndDecode(gray)
        if ok and decoded_info:
            info = decoded_info[0] if isinstance(decoded_info, (list, tuple)) else decoded_info
            btype = decoded_type[0] if isinstance(decoded_type, (list, tuple)) else decoded_type
            if info:
                cleaned = clean_barcode(info)
                return cleaned, str(btype)
    except Exception:
        pass

    return None, None

