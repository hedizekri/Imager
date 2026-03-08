import shutil
from pathlib import Path

from imager.config import PATHS
from imager.types import Scene


def organize_downloads(
    segments: list[Scene],
    downloads_dir: Path | None = None,
    output_dir: Path | None = None,
) -> list[Path]:
    downloads_dir = downloads_dir or PATHS["downloads_dir"]
    output_dir = output_dir or PATHS["output_dir"]

    if not downloads_dir.exists():
        raise ValueError(f"Downloads folder not found: {downloads_dir}")

    files = sorted(
        [f for f in downloads_dir.iterdir() if f.suffix.lower() == ".mp4"],
        key=lambda p: p.stat().st_mtime,
    )

    if len(files) < len(segments):
        raise ValueError(
            f"Not enough video files: {len(files)} in {downloads_dir}, "
            f"expected {len(segments)} (one per segment)"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    result = []

    for i, scene in enumerate(segments):
        src = files[i]
        dest = output_dir / src.name
        shutil.move(str(src), str(dest))
        result.append(dest)

    return result
