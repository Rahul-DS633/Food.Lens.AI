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
from typing import List, Tuple, Optional, Any
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
    Wrapper around EasyOCR with lazy model loading and preprocessing.
    """
    def __init__(self, languages: Optional[List[str]] = None, use_gpu: bool = False):
        self.languages = languages or ["en"]
        self.use_gpu = use_gpu
        self._reader = None

    def _get_reader(self):
        if self._reader is None:
            try:
                import easyocr
                self._reader = easyocr.Reader(self.languages, gpu=self.use_gpu)
            except Exception as e:
                # If model download fails or EasyOCR unavailable, keep None
                self._reader = None
        return self._reader

    def extract_text_from_image(self, image_input: Any) -> List[OCRTextLine]:
        """
        Takes image bytes, path, or numpy array.
        Returns extracted lines with confidence and bounding boxes.
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

        # Preprocess
        preprocessed = ImagePreprocessor.preprocess(img)

        reader = self._get_reader()
        if reader is None:
            # Fallback if EasyOCR models aren't yet downloaded
            return []

        try:
            results = reader.readtext(preprocessed)
            lines: List[OCRTextLine] = []
            for bbox, text, conf in results:
                lines.append(OCRTextLine(
                    text=text.strip(),
                    confidence=float(conf),
                    bbox=[[int(p[0]), int(p[1])] for p in bbox]
                ))
            return lines
        except Exception:
            return []
