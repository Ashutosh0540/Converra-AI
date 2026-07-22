from __future__ import annotations

import tempfile
from dataclasses import dataclass
from typing import Dict, Optional
from uuid import UUID

from app.core.config import settings
from app.voice.audio_stream import decode_audio_base64


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    is_final: bool
    confidence: float = 1.0


class SpeechToTextError(Exception):
    """Raised when transcription fails."""


class BaseSpeechToTextProvider:
    async def transcribe(
        self,
        audio_bytes: bytes,
        is_final: bool,
    ) -> TranscriptionResult:
        raise NotImplementedError


class RuleBasedSpeechToTextProvider(BaseSpeechToTextProvider):
    async def transcribe(
        self,
        audio_bytes: bytes,
        is_final: bool,
    ) -> TranscriptionResult:
        del is_final
        try:
            text = audio_bytes.decode("utf-8").strip()
        except UnicodeDecodeError:
            text = ""
        return TranscriptionResult(text=text, is_final=True, confidence=1.0)


class FasterWhisperSpeechToTextProvider(BaseSpeechToTextProvider):
    def __init__(self, model_name: str = "base", device: str = "cpu") -> None:
        self.model_name = model_name
        self.device = device
        self._model = None

    async def transcribe(
        self,
        audio_bytes: bytes,
        is_final: bool,
    ) -> TranscriptionResult:
        del is_final
        try:
            model = self._get_model()
            with tempfile.NamedTemporaryFile(suffix=".audio", delete=True) as temp_file:
                temp_file.write(audio_bytes)
                temp_file.flush()
                segments, info = model.transcribe(temp_file.name, language="en")
                text = " ".join(segment.text.strip() for segment in segments).strip()
                confidence = max(
                    0.0, min(1.0, float(getattr(info, "probability", 0.8)))
                )
                return TranscriptionResult(
                    text=text, is_final=True, confidence=confidence
                )
        except Exception as exc:
            raise SpeechToTextError("Failed to transcribe audio.") from exc

    def _get_model(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise SpeechToTextError("faster-whisper is not installed.") from exc

            self._model = WhisperModel(
                self.model_name, device=self.device, compute_type="int8"
            )

        return self._model


class SpeechToTextService:
    def __init__(self, provider: Optional[BaseSpeechToTextProvider] = None) -> None:
        self.provider = provider or self._default_provider()
        self._buffers: Dict[UUID, bytearray] = {}

    async def transcribe_chunk(
        self,
        session_id: Optional[UUID] = None,
        audio_base64: Optional[str] = None,
        audio_bytes: Optional[bytes] = None,
        is_final: bool = False,
        text: Optional[str] = None,
    ) -> TranscriptionResult:
        if text is not None:
            return TranscriptionResult(
                text=text.strip(),
                is_final=is_final,
                confidence=1.0 if is_final else 0.65,
            )

        chunk = audio_bytes or b""
        if audio_base64:
            chunk = decode_audio_base64(audio_base64)

        buffer = self._get_buffer(session_id)
        buffer.extend(chunk)
        if not is_final:
            return TranscriptionResult(
                text=self._safe_decode(buffer),
                is_final=False,
                confidence=0.65,
            )

        transcript = await self.provider.transcribe(bytes(buffer), is_final=True)
        buffer.clear()
        return transcript

    def reset_buffer(self, session_id: Optional[UUID] = None) -> None:
        if session_id is None:
            self._buffers.clear()
            return

        self._buffers.pop(session_id, None)

    @staticmethod
    def _safe_decode(buffer: bytearray) -> str:
        try:
            return bytes(buffer).decode("utf-8").strip()
        except UnicodeDecodeError:
            return ""

    def _get_buffer(self, session_id: Optional[UUID]) -> bytearray:
        if session_id is None:
            return bytearray()

        buffer = self._buffers.get(session_id)
        if buffer is None:
            buffer = bytearray()
            self._buffers[session_id] = buffer
        return buffer

    @staticmethod
    def _default_provider() -> BaseSpeechToTextProvider:
        provider_name = settings.voice_stt_provider.lower().strip()
        if provider_name == "faster_whisper":
            return FasterWhisperSpeechToTextProvider()
        return RuleBasedSpeechToTextProvider()
