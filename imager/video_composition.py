from pathlib import Path

from moviepy.editor import AudioFileClip, VideoFileClip, concatenate_videoclips

from imager.config import COMPOSITION, PATHS
from imager.types import MatchedScene


class CompositionError(Exception):
    pass


def compose_video(
    matches: list[MatchedScene],
    audio_path: Path,
    output_path: Path | None = None
) -> Path:
    if not matches:
        raise CompositionError("No scenes to compose")

    if not audio_path.exists():
        raise CompositionError(f"Audio file not found: {audio_path}")

    output_path = output_path or _default_output_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    audio = AudioFileClip(str(audio_path))
    clips = [_load_and_trim_clip(match) for match in matches]
    video = concatenate_videoclips(clips, method="compose")

    video = _match_duration_to_audio(video, audio.duration)
    final = video.set_audio(audio)

    final.write_videofile(
        str(output_path),
        fps=COMPOSITION["fps"],
        codec="libx264",
        audio_codec="aac"
    )

    _cleanup(clips, video, audio, final)
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


def _match_duration_to_audio(video: VideoFileClip, audio_duration: float):
    if video.duration > audio_duration:
        return video.subclip(0, audio_duration)

    if video.duration < audio_duration:
        return video.loop(duration=audio_duration)

    return video


def _default_output_path() -> Path:
    return PATHS["output_dir"] / f"output.{COMPOSITION['output_format']}"


def _cleanup(
    clips: list[VideoFileClip],
    video: VideoFileClip,
    audio: AudioFileClip,
    final: VideoFileClip
) -> None:
    for clip in clips:
        clip.close()
    video.close()
    audio.close()
    final.close()
