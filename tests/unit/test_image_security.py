"""
Unit Tests for Image Security, Validation, and EXIF Stripping
Rules:
1. Validate file size (max 8MB).
2. Validate image format (PNG, JPEG, WebP).
3. EXIF and GPS coordinates must be stripped before storage.
"""

import io
import pytest
from PIL import Image
from foodlens.image_security import sanitize_and_save_evidence_image, ImageValidationError


def test_exif_stripping():
    # Create an in-memory image with dummy EXIF metadata
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    exif = img.getexif()
    exif[0x010E] = "Secret GPS and Camera Info"  # ImageDescription tag
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    raw_bytes = buf.getvalue()

    # Sanitize and re-encode
    cleaned_bytes, extension = sanitize_and_save_evidence_image(raw_bytes, "test_upload.jpg")
    
    # Read cleaned image and verify EXIF is stripped
    cleaned_img = Image.open(io.BytesIO(cleaned_bytes))
    cleaned_exif = cleaned_img.getexif()
    assert 0x010E not in cleaned_exif
    assert extension in [".jpg", ".jpeg", ".png", ".webp"]


def test_reject_oversized_images():
    oversized_bytes = b"0" * (9 * 1024 * 1024)  # 9 MB
    with pytest.raises(ImageValidationError) as exc:
        sanitize_and_save_evidence_image(oversized_bytes, "huge.jpg")
    assert "exceeds maximum allowed size" in str(exc.value)


def test_reject_non_image_polyglot():
    fake_script = b"<html><script>alert('XSS')</script></html>"
    with pytest.raises(ImageValidationError) as exc:
        sanitize_and_save_evidence_image(fake_script, "exploit.html")
    assert "invalid image format" in str(exc.value).lower()
