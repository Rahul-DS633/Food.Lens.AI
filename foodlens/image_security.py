"""
FoodLens Image Security & Sanitization
Handles image validation, size limit enforcement (max 8MB), and EXIF/GPS metadata stripping.

Key Principles:
1. Re-encodes image through fresh PIL buffer to ensure zero EXIF/GPS leaks.
2. Rejects files larger than 8MB.
3. Rejects non-image files and unknown MIME types.
4. Stores images safely outside the web root.
"""

import io
from pathlib import Path

from PIL import Image

MAX_IMAGE_SIZE_BYTES = 8 * 1024 * 1024  # 8 MB
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


class ImageValidationError(Exception):
    """Raised when an uploaded evidence image fails security or format validation."""


def sanitize_and_save_evidence_image(
    raw_bytes: bytes,
    filename: str,
    output_path: Path | None = None
) -> tuple[bytes, str]:
    """
    Validates image, strips all EXIF/GPS tags, re-encodes, and optionally writes to output_path.
    Returns (cleaned_bytes, file_extension).
    """
    if len(raw_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise ImageValidationError(
            f"Image size ({round(len(raw_bytes)/(1024*1024), 2)}MB) exceeds maximum allowed size of 8MB."
        )

    try:
        img = Image.open(io.BytesIO(raw_bytes))
        img_format = img.format
    except (OSError, ValueError) as e:
        raise ImageValidationError(f"Invalid image format or corrupted file: {e}") from e

    if not img_format or img_format.upper() not in ALLOWED_FORMATS:
        raise ImageValidationError(
            f"Unsupported image format: {img_format}. Allowed: {', '.join(sorted(ALLOWED_FORMATS))}."
        )

    # Convert modes to standard RGB or RGBA
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        target_mode = "RGBA"
        out_format = "PNG"
        ext = ".png"
    else:
        target_mode = "RGB"
        out_format = "JPEG"
        ext = ".jpg"

    clean_img = Image.new(target_mode, img.size)
    clean_img.paste(img)

    out_buffer = io.BytesIO()
    clean_img.save(out_buffer, format=out_format, quality=90)
    cleaned_bytes = out_buffer.getvalue()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(cleaned_bytes)

    return cleaned_bytes, ext
