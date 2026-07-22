from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncGenerator, Optional

from app.core.config import settings
from app.voice.audio_stream import (
    chunk_bytes,
    generate_tone_wav,
    normalize_text_fragments,
)


class TextToSpeechError(Exception):
    """Raised when speech synthesis fails."""


@dataclass(frozen=True)
class SpeechChunk:
    audio_bytes: bytes
    is_final: bool
    sentence: str


class BaseTextToSpeechProvider:
    async def synthesize_stream(self, text: str) -> AsyncGenerator[SpeechChunk, None]:
        raise NotImplementedError


class RuleBasedTextToSpeechProvider(BaseTextToSpeechProvider):
    async def synthesize_stream(self, text: str) -> AsyncGenerator[SpeechChunk, None]:
        sentence = normalize_text_fragments(text.replace("\n", " ").split("."))
        audio_bytes = generate_tone_wav(
            sentence or text,
            sample_rate=settings.voice_audio_sample_rate,
            channels=settings.voice_audio_channels,
        )
        frame_size = settings.voice_audio_chunk_size
        for index, chunk in enumerate(chunk_bytes(audio_bytes, frame_size)):
            yield SpeechChunk(
                audio_bytes=chunk,
                is_final=index + frame_size >= len(audio_bytes),
                sentence=sentence or text,
            )


class KokoroTextToSpeechProvider(BaseTextToSpeechProvider):
    def __init__(self) -> None:
        self._tts = None

    async def synthesize_stream(self, text: str) -> AsyncGenerator[SpeechChunk, None]:
        try:
            audio_bytes = await self._synthesize(text)
            for index, chunk in enumerate(
                chunk_bytes(audio_bytes, settings.voice_audio_chunk_size)
            ):
                yield SpeechChunk(
                    audio_bytes=chunk,
                    is_final=(index + 1) * settings.voice_audio_chunk_size
                    >= len(audio_bytes),
                    sentence=text,
                )
        except Exception as exc:
            raise TextToSpeechError("Kokoro synthesis failed.") from exc

    async def _synthesize(self, text: str) -> bytes:
        if self._tts is None:
            try:
                from kokoro import KPipeline
            except ImportError as exc:
                raise TextToSpeechError("Kokoro is not installed.") from exc

            self._tts = KPipeline()

        result = self._tts(text)
        if isinstance(result, bytes):
            return result
        if hasattr(result, "read"):
            return result.read()

        raise TextToSpeechError("Unexpected Kokoro response type.")


class PiperTextToSpeechProvider(BaseTextToSpeechProvider):
    async def synthesize_stream(self, text: str) -> AsyncGenerator[SpeechChunk, None]:
        del text
        raise TextToSpeechError("Piper TTS is not configured.")


class TextToSpeechService:
    def __init__(self, provider: Optional[BaseTextToSpeechProvider] = None) -> None:
        self.provider = provider or self._default_provider()

    async def synthesize_stream(self, text: str) -> AsyncGenerator[SpeechChunk, None]:
        async for chunk in self.provider.synthesize_stream(text):
            yield chunk

    @staticmethod
    def _default_provider() -> BaseTextToSpeechProvider:
        provider_name = settings.voice_tts_provider.lower().strip()
        if provider_name == "kokoro":
            return KokoroTextToSpeechProvider()
        if provider_name == "piper":
            return PiperTextToSpeechProvider()
        return RuleBasedTextToSpeechProvider()
