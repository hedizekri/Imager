import shutil
from pathlib import Path

from imager.config import PATHS
from imager.types import Scene


class CompositionError(Exception):
    pass


def organize_downloads(
    segments: list[Scene],
    downloads_dir: Path | None = None,
    output_dir: Path | None = None,
) -> list[Path]:
    downloads_dir = downloads_dir or PATHS["downloads_dir"]
    output_dir = output_dir or PATHS["output_dir"]

    if not downloads_dir.exists():
        raise CompositionError(f"Downloads folder not found: {downloads_dir}")

    video_extensions = {".mp4", ".webm", ".mov", ".mkv"}
    files = sorted(
        [f for f in downloads_dir.iterdir() if f.suffix.lower() in video_extensions],
        key=lambda p: p.stat().st_mtime,
    )

    if len(files) < len(segments):
        raise CompositionError(
            f"Not enough video files: {len(files)} in {downloads_dir}, "
            f"expected {len(segments)} (one per segment)"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    result = []

    for i, scene in enumerate(segments):
        src = files[i]
        name = _timestamp_filename(scene.start_time)
        dest = output_dir / name
        shutil.move(str(src), str(dest))
        result.append(dest)

    return result


def _timestamp_filename(start_time: float) -> str:
    seconds = int(start_time)
    millis = int((start_time - seconds) * 1000)
    return f"{seconds:06d}_{millis:03d}.mp4"
