from pathlib import Path

from faster_whisper import WhisperModel

from imager.config import TRANSCRIPTION
from imager.types import Transcript, TranscriptSegment


def transcribe_audio(audio_path: Path, language: str | None = None) -> Transcript:
    lang = language or TRANSCRIPTION["default_language"]
    model = WhisperModel(
        TRANSCRIPTION["model_size"],
        device=TRANSCRIPTION["device"],
        compute_type=TRANSCRIPTION["compute_type"],
    )
    segments_gen, _ = model.transcribe(str(audio_path), language=lang)
    segments_list = list(segments_gen)
    segments = [
        TranscriptSegment(text=s.text.strip(), start_time=s.start, end_time=s.end)
        for s in segments_list
    ]
    full_text = " ".join(s.text for s in segments_list).strip()
    return Transcript(full_text=full_text, segments=segments)
