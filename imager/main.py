import argparse
from pathlib import Path

from imager.config import TRANSCRIPTION
from imager.scene_extraction import extract_scenes
from imager.transcription import transcribe_audio
from imager.video_composition import compose_video
from imager.video_matching import load_video_index, match_scenes_to_videos


def run_pipeline(
    audio_path: Path,
    output_path: Path | None = None,
    language: str | None = None
) -> Path:
    print(f"Processing: {audio_path}")

    print("Step 1/4: Transcribing audio...")
    transcript = transcribe_audio(audio_path, language)
    print(f"  Transcribed {len(transcript.segments)} segments")

    print("Step 2/4: Extracting scenes...")
    scenes = extract_scenes(transcript)
    print(f"  Found {len(scenes)} scenes")

    print("Step 3/4: Matching videos...")
    index = load_video_index()
    matches = match_scenes_to_videos(scenes, index)
    placeholder_count = sum(1 for m in matches if m.is_placeholder)
    print(f"  Matched {len(matches) - placeholder_count}/{len(matches)} scenes")

    print("Step 4/4: Composing video...")
    result = compose_video(matches, audio_path, output_path)
    print(f"  Output saved to: {result}")

    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate video from audio narration"
    )
    parser.add_argument("audio", type=Path, help="Path to audio file")
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output video path"
    )
    parser.add_argument(
        "-l", "--language",
        type=str,
        default=TRANSCRIPTION["default_language"],
        help="Audio language code (default: fr)"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_pipeline(args.audio, args.output, args.language)


if __name__ == "__main__":
    main()
