from dataclasses import dataclass
from pathlib import Path


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
    description: str
    keywords: list[str]
    start_time: float
    end_time: float


@dataclass
class MatchedScene:
    scene: Scene
    video_path: Path
    is_placeholder: bool


@dataclass
class VideoMetadata:
    filename: str
    tags: list[str]
    description: str
