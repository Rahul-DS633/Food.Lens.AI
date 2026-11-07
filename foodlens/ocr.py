"""
FoodLens OCR Pipeline
Image preprocessing (grayscale, CLAHE contrast enhancement, deskew, denoise)
and OCR text extraction with bounding boxes and confidence scores.

Supports:
- EasyOCR engine
- Image preprocessing pipeline using OpenCV
- Fallback mock extractor for unit tests / CPU environments
"""

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


class OCREngine:
    """
    Wrapper around EasyOCR with lazy model loading, local caching,
    image preprocessing, and 2D table row reassembly.
    """
    def __init__(self, languages: Optional[List[str]] = None, use_gpu: bool = False):
        self.languages = languages or ["en"]
        self.use_gpu = use_gpu
        self._reader = None

    def _get_reader(self):
        if self._reader is None:
            try:
                import easyocr  # type: ignore[import-untyped]
                from pathlib import Path
                model_dir = Path(__file__).resolve().parent.parent / "data" / "models" / "easyocr"
                model_dir.mkdir(parents=True, exist_ok=True)
                self._reader = easyocr.Reader(
                    self.languages,
                    gpu=self.use_gpu,
                    model_storage_directory=str(model_dir),
                    user_network_directory=str(model_dir)
                )
            except Exception:
                # If model download fails or EasyOCR unavailable, keep None
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
        Applies smart upscaling, gentle contrast enhancement, and 2D table row reassembly.
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
            return []

        # Smart upscale: if image resolution is modest, upscale so small table numbers (14.1g, 3.1g) become sharp
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

