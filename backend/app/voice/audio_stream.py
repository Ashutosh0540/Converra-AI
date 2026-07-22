from __future__ import annotations

import base64
import math
import struct
import wave
from io import BytesIO
from typing import Generator, Iterable


def decode_audio_base64(audio_base64: str) -> bytes:
    return base64.b64decode(audio_base64.encode("utf-8"))


def encode_audio_base64(audio_bytes: bytes) -> str:
    return base64.b64encode(audio_bytes).decode("utf-8")


def chunk_bytes(data: bytes, chunk_size: int) -> Generator[bytes, None, None]:
    for start in range(0, len(data), chunk_size):
        yield data[start : start + chunk_size]


def generate_tone_wav(
    text: str,
    sample_rate: int = 16000,
    channels: int = 1,
) -> bytes:
    duration_seconds = max(0.35, min(0.12 * max(len(text), 1), 3.0))
    frequency = 440.0 + (len(text) % 9) * 35.0
    amplitude = 0.25
    total_frames = int(sample_rate * duration_seconds)

    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        frames = bytearray()
        for index in range(total_frames):
            sample = int(
                amplitude
                * 32767
                * math.sin(2.0 * math.pi * frequency * (index / sample_rate))
            )
            packed = struct.pack("<h", sample)
            frames.extend(packed * channels)
        wav_file.writeframes(bytes(frames))

    return buffer.getvalue()


def normalize_text_fragments(fragments: Iterable[str]) -> str:
    return " ".join(
        fragment.strip() for fragment in fragments if fragment and fragment.strip()
    )
