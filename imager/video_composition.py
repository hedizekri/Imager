from pathlib import Path

from moviepy.editor import VideoFileClip, concatenate_videoclips

from imager.config import COMPOSITION, PATHS
from imager.types import MatchedScene


class CompositionError(Exception):
    pass


def compose_video(
    matches: list[MatchedScene],
    output_path: Path | None = None
) -> Path:
    if not matches:
        raise CompositionError("No scenes to compose")

    output_path = output_path or _default_output_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    clips = [_load_and_trim_clip(match) for match in matches]
    final = concatenate_videoclips(clips, method="compose")

    final.write_videofile(
        str(output_path),
        fps=COMPOSITION["fps"],
        codec="libx264",
        audio_codec="aac"
    )

    _cleanup_clips(clips, final)
    return output_path


def _load_and_trim_clip(match: MatchedScene) -> VideoFileClip:
    if not match.video_path.exists():
        raise CompositionError(f"Video not found: {match.video_path}")

    clip = VideoFileClip(str(match.video_path))
    target_duration = match.scene.end_time - match.scene.start_time

    if target_duration <= 0:
        return clip

    if clip.duration >= target_duration:
        return clip.subclip(0, target_duration)

    return clip.loop(duration=target_duration)


def _default_output_path() -> Path:
    return PATHS["output_dir"] / f"output.{COMPOSITION['output_format']}"


def _cleanup_clips(clips: list[VideoFileClip], final: VideoFileClip) -> None:
    for clip in clips:
        clip.close()
    final.close()
