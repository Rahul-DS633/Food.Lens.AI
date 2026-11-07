"""
FoodLens OCR Pipeline
Image preprocessing (grayscale, CLAHE contrast enhancement, deskew, denoise)
and OCR text extraction with bounding boxes and confidence scores.

Supports:
- EasyOCR engine
- Image preprocessing pipeline using OpenCV
- Fallback mock extractor for unit tests / CPU environments
"""

import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Any, Dict
import cv2
import numpy as np


@dataclass
class OCRTextLine:
    text: str
    confidence: float
    bbox: Optional[List[List[int]]] = None


class ImagePreprocessor:
    """
    OpenCV preprocessing pipeline for nutrition labels:
    - Grayscale
    - Contrast Limited Adaptive Histogram Equalization (CLAHE)
    - Bilateral filter denoising
    - Deskewing
    """

    @staticmethod
    def to_grayscale(image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image

    @staticmethod
    def enhance_contrast_clahe(gray: np.ndarray, clip_limit: float = 2.0) -> np.ndarray:
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
        return clahe.apply(gray)

    @staticmethod
    def denoise(gray: np.ndarray) -> np.ndarray:
        return cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)

    @staticmethod
    def deskew(gray: np.ndarray) -> np.ndarray:
        """Estimates text orientation angle and deskews image."""
        try:
            coords = np.column_stack(np.where(gray < 128))
            if len(coords) < 100:
                return gray
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            elif angle > 45:
                angle = 90 - angle
            else:
                angle = -angle

            if abs(angle) > 0.5 and abs(angle) < 45.0:
                (h, w) = gray.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                return cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        except Exception:
            pass
        return gray

    @classmethod
    def preprocess(cls, image: np.ndarray) -> np.ndarray:
        """Full enhancement pipeline."""
        gray = cls.to_grayscale(image)
        denoised = cls.denoise(gray)
        enhanced = cls.enhance_contrast_clahe(denoised)
        deskewed = cls.deskew(enhanced)
        return deskewed


def _get_gemini_api_key() -> Optional[str]:
    """Resolves Gemini API key across os.environ, Streamlit Cloud secrets, and .env."""
    # 1. Environment variable
    key = os.getenv("GEMINI_API_KEY")
    if key and "your_gemini" not in key.lower() and len(key.strip()) > 10:
        return key.strip()

    # 2. Streamlit Cloud Secrets (handles direct navigation to /Scan or any page)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            k = str(st.secrets["GEMINI_API_KEY"]).strip()
            if k and "your_gemini" not in k.lower() and len(k) > 10:
                os.environ["GEMINI_API_KEY"] = k
                return k
    except Exception:
        pass

    # 3. python-dotenv fallback
    try:
        from dotenv import load_dotenv
        load_dotenv()
        key = os.getenv("GEMINI_API_KEY")
        if key and "your_gemini" not in key.lower() and len(key.strip()) > 10:
            return key.strip()
    except Exception:
        pass

    return None


class OCREngine:
    """
    Multi-engine OCR processor with intelligent fallback:
    1. Gemini Vision OCR (if GEMINI_API_KEY is available: 0 MB server RAM, ultra accurate on Indian packaged foods)
    2. System Tesseract OCR (if installed on server: ~25 MB RAM, fast, preinstalled on Streamlit Cloud)
    3. EasyOCR with table row reassembly (local PyTorch fallback with memory safety)
    """
    def __init__(self, languages: Optional[List[str]] = None, use_gpu: bool = False):
        self.languages = languages or ["en"]
        self.use_gpu = use_gpu
        self._reader = None

    def _extract_with_gemini_vision(self, img_bytes: bytes) -> List[OCRTextLine]:
        """
        Uses Google Gemini Vision to perform cloud-based OCR directly from packaging.
        Tries both Google GenAI SDK and direct HTTPS REST API fallback.
        Zero server RAM overhead and exceptional accuracy on Indian food labels and small tables.
        """
        api_key = _get_gemini_api_key()
        if not api_key:
            return []

        prompt = (
            "You are an OCR extraction engine for packaged food labels. "
            "Read this packaging image carefully and extract all printed text verbatim. "
            "Include: Product Title, Brand, Net Weight, Serving Size, "
            "all rows in the Nutrition Facts table with their exact values, units, and basis (e.g. Energy, Protein, Carbohydrate, Total Sugar, Added Sugar, Dietary Fibre, Total Fat, Saturated Fat, Trans Fat, Sodium), "
            "and the complete Ingredients list. "
            "Output one line per extracted item. Do not include markdown formatting or commentary."
        )

        # Method 1: Google GenAI SDK
        try:
            import io
            from PIL import Image
            from google import genai

            pil_img = Image.open(io.BytesIO(img_bytes))
            client = genai.Client(api_key=api_key)

            for model_name in ["gemini-2.0-flash", "gemini-1.5-flash"]:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=[pil_img, prompt]
                    )
                    if response and response.text:
                        clean_lines = [
                            l.strip()
                            for l in response.text.replace("```", "").splitlines()
                            if l.strip() and not l.strip().startswith("#")
                        ]
                        if clean_lines:
                            return [OCRTextLine(text=l, confidence=0.96) for l in clean_lines]
                except Exception:
                    continue
        except Exception:
            pass

        # Method 2: Direct HTTPS REST API (guaranteed to work across all Python versions and platforms)
        try:
            import base64
            import requests

            b64_image = base64.b64encode(img_bytes).decode("utf-8")
            mime_type = "image/jpeg"
            if img_bytes.startswith(b"\x89PNG"):
                mime_type = "image/png"
            elif img_bytes.startswith(b"RIFF") and b"WEBP" in img_bytes[:16]:
                mime_type = "image/webp"

            for model_name in ["gemini-1.5-flash", "gemini-2.0-flash"]:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": prompt},
                            {"inline_data": {"mime_type": mime_type, "data": b64_image}}
                        ]
                    }]
                }
                resp = requests.post(url, json=payload, timeout=25)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        text_content = "".join(p.get("text", "") for p in parts)
                        clean_lines = [
                            l.strip()
                            for l in text_content.replace("```", "").splitlines()
                            if l.strip() and not l.strip().startswith("#")
                        ]
                        if clean_lines:
                            return [OCRTextLine(text=l, confidence=0.96) for l in clean_lines]
        except Exception:
            pass

        return []

    def _extract_with_tesseract(self, img_bytes: bytes) -> List[OCRTextLine]:
        """
        Uses system Tesseract OCR binary (C++).
        Lightweight (~25 MB RAM), fast, and pre-installed on Linux Streamlit Cloud.
        """
        import tempfile

        tess = shutil.which("tesseract")
        if not tess:
            return []
        try:
            suffix = ".jpg"
            if img_bytes.startswith(b"\x89PNG"):
                suffix = ".png"

            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tf:
                tf.write(img_bytes)
                tmp_path = tf.name

            try:
                proc = subprocess.run(
                    [tess, tmp_path, "stdout", "-l", "eng"],
                    capture_output=True,
                    timeout=20
                )
                if proc.returncode == 0:
                    text = proc.stdout.decode("utf-8", errors="ignore")
                    lines = [l.strip() for l in text.splitlines() if l.strip()]
                    if lines:
                        return [OCRTextLine(text=l, confidence=0.85) for l in lines]
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        except Exception:
            pass
        return []

    def _get_reader(self):
        if self._reader is None:
            from pathlib import Path
            model_dir = Path(__file__).resolve().parent.parent / "data" / "models" / "easyocr"
            cached_models = list(model_dir.glob("*.pth")) if model_dir.exists() else []

            # Check if running in a cloud/container environment
            is_cloud = bool(
                os.getenv("STREAMLIT_SERVER_PORT") or
                "/mount/" in str(__file__) or
                "/home/adminuser/" in str(__file__)
            )

            # If running in cloud and models are not cached, do NOT download 130MB (prevents OOM crashes)
            if is_cloud and not cached_models:
                return None

            try:
                import easyocr  # type: ignore[import-untyped]
                model_dir.mkdir(parents=True, exist_ok=True)
                self._reader = easyocr.Reader(
                    self.languages,
                    gpu=self.use_gpu,
                    model_storage_directory=str(model_dir),
                    user_network_directory=str(model_dir),
                    download_enabled=not is_cloud
                )
            except BaseException:
                # Catch BaseException (MemoryError, SystemExit, socket errors) to prevent app crash
                self._reader = None
        return self._reader

    @staticmethod
    def reassemble_table_rows(results: List[Any], y_tolerance_ratio: float = 0.5) -> List[OCRTextLine]:
        """
        Groups bounding boxes that lie on the same horizontal band into coherent table rows.
        Within each row, tokens are ordered from left to right by their X coordinates.
        This turns columnar OCR outputs like ['Protein', '14.1g'] into 'Protein 14.1g'.
        """
        if not results:
            return []

        items = []
        for bbox, text, conf in results:
            t = text.strip()
            if not t:
                continue
            xs = [p[0] for p in bbox]
            ys = [p[1] for p in bbox]
            y_min, y_max = min(ys), max(ys)
            x_min, x_max = min(xs), max(xs)
            y_center = (y_min + y_max) / 2.0
            height = max(1.0, y_max - y_min)
            items.append({
                "text": t,
                "conf": float(conf),
                "bbox": bbox,
                "x_min": x_min,
                "x_max": x_max,
                "y_min": y_min,
                "y_max": y_max,
                "y_center": y_center,
                "height": height,
            })

        if not items:
            return []

        # Sort top to bottom by y_center
        items.sort(key=lambda it: it["y_center"])

        rows = []
        current_row: List[Dict[str, Any]] = []
        current_y = None
        current_h = None

        for it in items:
            if not current_row:
                current_row.append(it)
                current_y = it["y_center"]
                current_h = it["height"]
            else:
                threshold = max(current_h, it["height"]) * y_tolerance_ratio
                if abs(it["y_center"] - current_y) <= threshold:
                    current_row.append(it)
                    current_y = sum(x["y_center"] for x in current_row) / len(current_row)
                    current_h = max(x["height"] for x in current_row)
                else:
                    rows.append(current_row)
                    current_row = [it]
                    current_y = it["y_center"]
                    current_h = it["height"]

        if current_row:
            rows.append(current_row)

        reassembled: List[OCRTextLine] = []
        for row in rows:
            # Sort left to right
            row.sort(key=lambda it: it["x_min"])
            merged_text = " ".join(it["text"] for it in row).strip()
            avg_conf = sum(it["conf"] for it in row) / len(row)
            min_x = min(it["x_min"] for it in row)
            max_x = max(it["x_max"] for it in row)
            min_y = min(it["y_min"] for it in row)
            max_y = max(it["y_max"] for it in row)
            box = [[int(min_x), int(min_y)], [int(max_x), int(min_y)], [int(max_x), int(max_y)], [int(min_x), int(max_y)]]
            reassembled.append(OCRTextLine(text=merged_text, confidence=round(avg_conf, 2), bbox=box))

        return reassembled

    def extract_text_from_image(self, image_input: Any) -> List[OCRTextLine]:
        """
        Takes image bytes, path, or numpy array.
        Uses a resilient multi-tier OCR strategy:
        1. Gemini Vision OCR (if API key available - 0 MB server RAM, ultra accurate)
        2. System Tesseract OCR (if installed on server - 25 MB RAM, ultra lightweight)
        3. Local EasyOCR (with memory & crash protection)
        """
        raw_bytes: Optional[bytes] = None
        img = None

        if isinstance(image_input, (bytes, bytearray)):
            raw_bytes = bytes(image_input)
            nparr = np.frombuffer(raw_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        elif isinstance(image_input, str):
            try:
                with open(image_input, "rb") as f:
                    raw_bytes = f.read()
            except Exception:
                pass
            img = cv2.imread(image_input)
        elif isinstance(image_input, np.ndarray):
            img = image_input
            try:
                success, enc = cv2.imencode(".jpg", img)
                if success:
                    raw_bytes = enc.tobytes()
            except Exception:
                pass

        # Tier 1: Gemini Vision OCR (cloud, 0 MB server RAM, highest accuracy)
        if raw_bytes:
            gemini_results = self._extract_with_gemini_vision(raw_bytes)
            if gemini_results:
                return gemini_results

        # Tier 2: System Tesseract OCR (lightweight, ~25 MB RAM, native C++)
        if raw_bytes:
            tess_results = self._extract_with_tesseract(raw_bytes)
            if tess_results:
                return tess_results

        if img is None:
            return []

        # Tier 3: Local EasyOCR
        # Smart upscale: if image resolution is modest, upscale so small table numbers become sharp
        h, w = img.shape[:2]
        if max(h, w) < 2000:
            scale = min(2.2, 2000.0 / max(h, w))
            if scale > 1.2:
                img = cv2.resize(img, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        gray = ImagePreprocessor.to_grayscale(img)
        enhanced = ImagePreprocessor.enhance_contrast_clahe(gray, clip_limit=1.5)

        reader = self._get_reader()
        if reader is None:
            return []

        try:
            results = reader.readtext(enhanced)
            if len(results) < 3:
                results = reader.readtext(gray)

            # Reassemble rows from 2D coordinates for table coherence
            merged_rows = self.reassemble_table_rows(results, y_tolerance_ratio=0.6)

            # Also collect individual raw items
            raw_items = [
                OCRTextLine(
                    text=text.strip(),
                    confidence=float(conf),
                    bbox=[[int(p[0]), int(p[1])] for p in bbox]
                )
                for bbox, text, conf in results if text.strip()
            ]

            seen_texts = {r.text.lower() for r in merged_rows}
            extra_lines = [item for item in raw_items if item.text.lower() not in seen_texts]

            return merged_rows + extra_lines
        except Exception:
            return []

