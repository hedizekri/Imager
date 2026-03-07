from dataclasses import dataclass


@dataclass
class TranscriptSegment:
    text: str
    start_time: float
    end_time: float


@dataclass
class Transcript:
    full_text: str
    segments: list[TranscriptSegment]


@dataclass
class Scene:
    keywords: list[str]
    start_time: float
    end_time: float
