import json
import time
from datetime import datetime
from pathlib import Path

from moviepy.editor import AudioFileClip, VideoFileClip, concatenate_videoclips

from imager.config import COMPOSITION, PATHS
from imager.types import MatchedScene

# #region agent log
DEBUG_LOG_PATH = "/Users/hedizekri/Perso/Imager/.cursor/debug.log"
def _debug_log(loc, msg, data, hyp):
    with open(DEBUG_LOG_PATH, "a") as f:
        f.write(json.dumps({"location": loc, "message": msg, "data": data, "hypothesisId": hyp, "timestamp": int(time.time()*1000), "sessionId": "debug-session"}) + "\n")
# #endregion


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
    # #region agent log
    _debug_log("video_composition.py:compose_video", "clips_created", {"count": len(clips), "clip_durations": [c.duration for c in clips]}, "H4")
    # #endregion

    clips = _extend_clips_to_audio(clips, audio.duration)

    video = concatenate_videoclips(clips, method="compose")
    # #region agent log
    _debug_log("video_composition.py:compose_video", "after_concatenate", {"concatenated_duration": video.duration, "audio_duration": audio.duration}, "H4")
    # #endregion

    video = _trim_to_audio(video, audio.duration)
    # #region agent log
    _debug_log("video_composition.py:compose_video", "after_duration_match", {"final_video_duration": video.duration}, "H5")
    # #endregion
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
    # #region agent log
    _debug_log("video_composition.py:_load_and_trim_clip", "clip_processing", {"video": match.video_path.name, "original_duration": clip.duration, "target_duration": target_duration, "scene_start": match.scene.start_time, "scene_end": match.scene.end_time}, "H3")
    # #endregion

    if target_duration <= 0:
        return clip

    if clip.duration >= target_duration:
        return clip.subclip(0, target_duration)

    return clip.loop(duration=target_duration)


def _extend_clips_to_audio(
    clips: list[VideoFileClip],
    audio_duration: float
) -> list[VideoFileClip]:
    total_duration = sum(c.duration for c in clips)

    if total_duration >= audio_duration:
        return clips

    remaining = audio_duration - total_duration
    last_clip = clips[-1]
    extended_last = last_clip.loop(duration=last_clip.duration + remaining)
    return clips[:-1] + [extended_last]


def _trim_to_audio(video: VideoFileClip, audio_duration: float):
    if video.duration > audio_duration:
        return video.subclip(0, audio_duration)
    return video


def _default_output_path() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return PATHS["output_dir"] / f"output_{timestamp}.{COMPOSITION['output_format']}"


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
