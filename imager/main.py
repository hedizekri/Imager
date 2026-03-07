import argparse
import json
import sys
from pathlib import Path
from urllib.parse import quote_plus

from imager.artgrid_browser import (
    connect_firefox,
    open_first_result,
    open_first_result_via_firefox,
)
from imager.config import (
    PATHS,
    TRANSCRIPTION,
    ARTGRID_SEARCH_BASE,
)
from imager.scene_extraction import extract_scenes
from imager.transcription import transcribe_audio
from imager.video_composition import organize_downloads

try:
    from selenium.common.exceptions import WebDriverException
except ImportError:
    WebDriverException = Exception


def _debug(debug: bool, msg: str) -> None:
    if debug:
        print(f"[debug] {msg}")


def run_pipeline(
    audio_path: Path,
    output_path: Path | None = None,
    language: str | None = None,
    organize: bool = False,
    open_in_browser: bool = False,
    connect_firefox_flag: bool = False,
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

    segment_urls: list[str] = []
    for scene in scenes:
        if not scene.keywords:
            url = ARTGRID_SEARCH_BASE
        else:
            params = "&".join(f"search={quote_plus(kw)}" for kw in scene.keywords) + "&sortId=1"
            url = f"{ARTGRID_SEARCH_BASE}?{params}"
        segment_urls.append(url)
        print(url)

    if open_in_browser and segment_urls:
        if connect_firefox_flag:
            try:
                driver, firefox_process = connect_firefox()
            except WebDriverException as e:
                raise ValueError(
                    f"Could not connect to Firefox: {e}. Ensure geckodriver is installed and in PATH."
                ) from e
            try:
                for url in segment_urls:
                    open_first_result_via_firefox(driver, url)
            finally:
                driver.quit()
                firefox_process.terminate()
        else:
            for url in segment_urls:
                open_first_result(url)

    if organize:
        out_dir = output_path or PATHS["output_dir"]
        result = organize_downloads(scenes, output_dir=out_dir)
        print(f"Organized {len(result)} files into {out_dir}")
    else:
        print("Download videos (first result per URL) then run with --organize.")


def _read_urls_from_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [line.strip() for line in text.splitlines() if line.strip()]


def run_urls_only(
    urls: list[str],
    open_in_browser: bool,
    connect_firefox_flag: bool,
) -> None:
    if not urls:
        raise ValueError("At least one URL required")
    if not open_in_browser and not connect_firefox_flag:
        raise ValueError("In URL mode, use --open or --connect-firefox to open the URLs")
    if connect_firefox_flag:
        try:
            driver, firefox_process = connect_firefox()
        except WebDriverException as e:
            raise ValueError(
                f"Could not connect to Firefox: {e}. Ensure geckodriver is installed and in PATH."
            ) from e
        try:
            for url in urls:
                open_first_result_via_firefox(driver, url)
        finally:
            driver.quit()
            firefox_process.terminate()
    else:
        for url in urls:
            open_first_result(url)


def parse_args() -> argparse.Namespace:
    if len(sys.argv) >= 2 and sys.argv[1] == "urls":
        parser = argparse.ArgumentParser(description="Open Artgrid search URLs in browser (no audio)")
        parser.add_argument("urls", nargs="*", help="Artgrid search URLs (or use --file)")
        parser.add_argument("-f", "--file", nargs="?", const=PATHS["urls_file"], default=None, type=Path, metavar="PATH", help="Read URLs from file (one per line). Omit PATH to use input/urls.txt")
        parser.add_argument("--open", action="store_true", dest="open_in_browser", help="Open each URL in browser")
        parser.add_argument("--connect-firefox", action="store_true", dest="connect_firefox_flag", help="Open first result per URL in Firefox")
        args = parser.parse_args(sys.argv[2:])
        if args.file is not None:
            path = args.file
            if not path.exists():
                raise ValueError(f"URLs file not found: {path}")
            args.urls = _read_urls_from_file(path)
        return args
    parser = argparse.ArgumentParser(description="B-roll MVP: audio -> transcript -> segments -> Artgrid URLs")
    parser.add_argument("audio", type=Path, help="Path to audio file")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output directory for organized videos")
    parser.add_argument("-l", "--language", type=str, default=TRANSCRIPTION["default_language"], help="Audio language code")
    parser.add_argument("--organize", action="store_true", help="Move and rename downloads to output by timestamp")
    parser.add_argument("--open", action="store_true", dest="open_in_browser", help="Open each segment in default browser (search URL only)")
    parser.add_argument("--connect-firefox", action="store_true", dest="connect_firefox_flag", help="Connect to Firefox started with -marionette -start-debugger-server 2828; opens first result per segment")
    parser.add_argument("-d", "--debug", action="store_true", help="Print concise debug summaries")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if hasattr(args, "urls"):
        run_urls_only(args.urls, args.open_in_browser, args.connect_firefox_flag)
        return
    run_pipeline(
        args.audio,
        args.output,
        args.language,
        args.organize,
        args.open_in_browser,
        args.connect_firefox_flag,
        args.debug,
    )


if __name__ == "__main__":
    main()
