"""
FoodLens TTS Provider Base Interface
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TTSResult:
    audio_bytes: Optional[bytes]
    provider_type: str
    cached: bool = False
    error: Optional[str] = None


class TTSProvider(ABC):
    @abstractmethod
    def synthesize(self, text: str, language: str = "en") -> TTSResult:
        """Synthesizes text into audio."""
        pass
