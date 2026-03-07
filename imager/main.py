import argparse
import json
from pathlib import Path

from imager.artgrid import artgrid_search_url
from imager.config import PATHS, TRANSCRIPTION
from imager.scene_extraction import extract_scenes
from imager.transcription import transcribe_audio
from imager.video_composition import organize_downloads


def run_pipeline(
    audio_path: Path,
    output_path: Path | None = None,
    language: str | None = None,
    organize: bool = False,
) -> None:
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    data_dir = PATHS["data_dir"]
    data_dir.mkdir(parents=True, exist_ok=True)

    print(f"Processing: {audio_path}")
    print("Step 1/3: Transcribing audio...")
    lang = language or TRANSCRIPTION["default_language"]
    transcript = transcribe_audio(audio_path, lang)
    print(f"  Transcribed {len(transcript.segments)} segments")

    transcript_path = data_dir / "transcript.json"
    _save_transcript(transcript, transcript_path)
    print(f"  Saved {transcript_path}")

    print("Step 2/3: Extracting scenes and keywords...")
    scenes = extract_scenes(transcript)
    print(f"  Found {len(scenes)} scenes")

    segments_path = data_dir / "segments.json"
    _save_segments(scenes, segments_path)
    print(f"  Saved {segments_path}")

    print("Step 3/3: Artgrid search URLs (one per segment):")
    for i, scene in enumerate(scenes):
        url = artgrid_search_url(scene.keywords)
        print(f"  [{i + 1}] {url}")

    if organize:
        out_dir = output_path or PATHS["output_dir"]
        print(f"Organizing downloads into {out_dir}...")
        result = organize_downloads(scenes, output_dir=out_dir)
        print(f"  Moved and renamed {len(result)} files")
    else:
        print(
            "Download videos in Firefox (first result per URL) with Download Helper, "
            "then run with --organize to move and rename by timestamp."
        )


def _save_transcript(transcript, path: Path) -> None:
    data = [
        {
            "start": seg.start_time,
            "end": seg.end_time,
            "text": seg.text,
        }
        for seg in transcript.segments
    ]
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _save_segments(scenes: list, path: Path) -> None:
    data = [
        {
            "start": s.start_time,
            "end": s.end_time,
            "keywords": s.keywords,
        }
        for s in scenes
    ]
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="B-roll MVP: audio -> transcript -> segments -> Artgrid URLs"
    )
    parser.add_argument("audio", type=Path, help="Path to audio file")
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output directory for organized videos (default: config output_dir)",
    )
    parser.add_argument(
        "-l", "--language",
        type=str,
        default=TRANSCRIPTION["default_language"],
        help="Audio language code",
    )
    parser.add_argument(
        "--organize",
        action="store_true",
        help="Move and rename videos from downloads folder to output by timestamp",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_pipeline(args.audio, args.output, args.language, args.organize)


if __name__ == "__main__":
    main()
