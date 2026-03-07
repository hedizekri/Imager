from pathlib import Path

import whisper

from imager.config import TRANSCRIPTION
from imager.types import Transcript, TranscriptSegment


class TranscriptionError(Exception):
    pass


def transcribe_audio(audio_path: Path, language: str | None = None) -> Transcript:
    if not audio_path.exists():
        raise TranscriptionError(f"Audio file not found: {audio_path}")

    lang = language or TRANSCRIPTION["default_language"]

    model = whisper.load_model(
        TRANSCRIPTION["model_size"],
        device=TRANSCRIPTION["device"]
    )

    result = model.transcribe(
        str(audio_path),
        language=lang,
        word_timestamps=True
    )

    segments = _parse_segments(result["segments"])
    return Transcript(full_text=result["text"], segments=segments)


def _parse_segments(raw_segments: list[dict]) -> list[TranscriptSegment]:
    return [
        TranscriptSegment(
            text=seg["text"].strip(),
            start_time=seg["start"],
            end_time=seg["end"]
        )
        for seg in raw_segments
    ]
