"""
FoodLens Server TTS Provider
Optional server-side speech synthesis with local file caching by SHA-256 hash.
Enabled exclusively when ENABLE_SERVER_TTS=true.
"""

import os
import hashlib
from pathlib import Path
from foodlens.tts.base import TTSProvider, TTSResult

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "audio_cache"


class ServerTTSProvider(TTSProvider):
    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.enabled = os.getenv("ENABLE_SERVER_TTS", "false").lower() == "true"
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def synthesize(self, text: str, language: str = "en") -> TTSResult:
        if not self.enabled:
            return TTSResult(
                audio_bytes=None,
                provider_type="server_tts",
                cached=False,
                error="Server TTS is disabled. Set ENABLE_SERVER_TTS=true to enable server-side audio synthesis."
            )

        # Compute deterministic cache key
        voice = "hi_in_neural" if language == "hi" else "en_us_neural"
        cache_key = hashlib.sha256(f"{text}:{language}:{voice}".encode("utf-8")).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.mp3"

        if cache_file.exists():
            with open(cache_file, "rb") as f:
                return TTSResult(
                    audio_bytes=f.read(),
                    provider_type="server_tts",
                    cached=True,
                )

        # Placeholder for external cloud speech provider (when flag enabled)
        dummy_audio = b"ID3\x04\x00\x00\x00\x00\x00#TSSE\x00\x00\x00\x0f\x00\x00\x03Lavf58.29.100"
        with open(cache_file, "wb") as f:
            f.write(dummy_audio)

        return TTSResult(
            audio_bytes=dummy_audio,
            provider_type="server_tts",
            cached=False,
        )
