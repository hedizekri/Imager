import argparse
import json
from pathlib import Path
from urllib.parse import quote_plus

from imager.config import PATHS, TRANSCRIPTION, ARTGRID_SEARCH_BASE
from imager.scene_extraction import extract_scenes
from imager.transcription import transcribe_audio
from imager.video_composition import organize_downloads


def _debug(debug: bool, msg: str) -> None:
    if debug:
        print(f"[debug] {msg}")


def run_pipeline(
    audio_path: Path,
    output_path: Path | None = None,
    language: str | None = None,
    organize: bool = False,
    debug: bool = False,
) -> None:
    if not audio_path.exists():
        raise ValueError(f"Audio file not found: {audio_path}")

    data_dir = PATHS["data_dir"]
    data_dir.mkdir(parents=True, exist_ok=True)
    lang = language or TRANSCRIPTION["default_language"]

    print("Transcribing...")
    transcript = transcribe_audio(audio_path, lang)
    _debug(debug, "full text (transcribed):")
    if debug:
        print(transcript.full_text)
    if transcript.segments:
        s0, sL = transcript.segments[0], transcript.segments[-1]
        preview = f"{len(transcript.segments)} segments, {s0.start_time:.1f}s–{sL.end_time:.1f}s"
        _debug(debug, f"transcript: {preview} | first: \"{s0.text[:50]}{'…' if len(s0.text) > 50 else ''}\" ({s0.start_time:.1f}–{s0.end_time:.1f}s) | last: \"{sL.text[:50]}{'…' if len(sL.text) > 50 else ''}\"")
    transcript_path = data_dir / "transcript.json"
    transcript_path.write_text(
        json.dumps(
            [{"start": s.start_time, "end": s.end_time, "text": s.text} for s in transcript.segments],
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Saved {transcript_path}")

    print("Extracting scenes...")
    scenes = extract_scenes(transcript, debug=debug)
    if scenes:
        _debug(debug, f"scenes: {len(scenes)} | first keywords: {scenes[0].keywords[:3]} | last: {scenes[-1].keywords[:3]}")
    segments_path = data_dir / "segments.json"
    segments_path.write_text(
        json.dumps(
            [{"start": s.start_time, "end": s.end_time, "keywords": s.keywords} for s in scenes],
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Saved {segments_path}")

    for scene in scenes:
        if not scene.keywords:
            print(ARTGRID_SEARCH_BASE)
            continue
        params = "&".join(f"search={quote_plus(kw)}" for kw in scene.keywords) + "&sortId=1"
        print(f"{ARTGRID_SEARCH_BASE}?{params}")

    if organize:
        out_dir = output_path or PATHS["output_dir"]
        result = organize_downloads(scenes, output_dir=out_dir)
        print(f"Organized {len(result)} files into {out_dir}")
    else:
        print("Download videos (first result per URL) then run with --organize.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="B-roll MVP: audio -> transcript -> segments -> Artgrid URLs")
    parser.add_argument("audio", type=Path, help="Path to audio file")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output directory for organized videos")
    parser.add_argument("-l", "--language", type=str, default=TRANSCRIPTION["default_language"], help="Audio language code")
    parser.add_argument("--organize", action="store_true", help="Move and rename downloads to output by timestamp")
    parser.add_argument("-d", "--debug", action="store_true", help="Print concise debug summaries")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_pipeline(args.audio, args.output, args.language, args.organize, args.debug)


if __name__ == "__main__":
    main()
