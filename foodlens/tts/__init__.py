"""
FoodLens TTS Providers Package
"""

from foodlens.tts.base import TTSProvider, TTSResult
from foodlens.tts.browser import BrowserSpeechProvider
from foodlens.tts.server import ServerTTSProvider

__all__ = ["TTSProvider", "TTSResult", "BrowserSpeechProvider", "ServerTTSProvider"]
