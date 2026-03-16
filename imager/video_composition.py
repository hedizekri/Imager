import re
import shutil
from pathlib import Path

from imager.config import PATHS
from imager.types import Scene

TIMELINE_FROM_FILENAME = re.compile(r"^\d{2}-\d{2}-\d{2}-\d{2}-(\d+)-")


def organize_downloads(
    segments: list[Scene],
    downloads_dir: Path | None = None,
    output_dir: Path | None = None,
    timeline_count: int = 1,
) -> list[Path]:
    downloads_dir = downloads_dir or PATHS["downloads_dir"]
    output_dir = output_dir or PATHS["output_dir"]

    if not downloads_dir.exists():
        raise ValueError(f"Downloads folder not found: {downloads_dir}")

    files = [f for f in downloads_dir.iterdir() if f.suffix.lower() == ".mp4"]
    expected = len(segments) * timeline_count
    if len(files) == 0:
        raise ValueError(f"No video files in {downloads_dir}")
    if len(files) < expected:
        print(
            f"Warning: {len(files)} files, expected {expected}. Organizing available files."
        )

    result = []
    if timeline_count == 1:
        files_sorted = sorted(files, key=lambda p: p.stat().st_mtime)
        output_dir.mkdir(parents=True, exist_ok=True)
        for i in range(min(len(segments), len(files))):
            src = files_sorted[i]
            dest = output_dir / src.name
            shutil.move(str(src), str(dest))
            result.append(dest)
        return result

    for ti in range(1, timeline_count + 1):
        (output_dir / str(ti)).mkdir(parents=True, exist_ok=True)
    for src in files:
        match = TIMELINE_FROM_FILENAME.match(src.name)
        timeline = match.group(1) if match else "1"
        dest = output_dir / timeline / src.name
        shutil.move(str(src), str(dest))
        result.append(dest)
    return result
