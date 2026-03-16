import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

from imager.artgrid_browser import (
    connect_chromium,
    open_first_result,
    open_first_result_via_chromium,
    open_nth_result_via_chromium,
)
from imager.artgrid_download import (
    build_download_filename,
    download_video,
    get_video_url_from_page,
)
from imager.config import (
    DEFAULT_PROJECT_NAME,
    PATHS,
    TRANSCRIPTION,
    ARTGRID_SEARCH_BASE,
)
from imager.scene_extraction import extract_scenes
from imager.transcription import transcribe_audio
from imager.video_composition import organize_downloads


def _debug(debug: bool, msg: str) -> None:
    if debug:
        print(f"[debug] {msg}")


def _project_name(audio_path: Path) -> str:
    name = Path(audio_path).stem.lower().replace(" ", "_")
    return name if name else DEFAULT_PROJECT_NAME


def run_pipeline(
    audio_path: Path,
    output_path: Path | None = None,
    language: str | None = None,
    organize: bool = False,
    open_in_browser: bool = False,
    connect_flag: bool = False,
    download_flag: bool = False,
    timelines: int = 1,
    debug: bool = False,
) -> None:
    if not audio_path.exists():
        raise ValueError(f"Audio file not found: {audio_path}")

    base = _project_name(audio_path)
    project_name = f"{base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    project_downloads = PATHS["downloads_dir"] / project_name
    project_output = (output_path or PATHS["output_dir"]) / project_name

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

    if download_flag and not connect_flag:
        raise ValueError("--download requires --connect")

    if (open_in_browser or download_flag) and segment_urls:
        if connect_flag:
            try:
                playwright, browser, page = connect_chromium()
            except Exception as e:
                raise ValueError(
                    f"Could not connect to Chromium/Chrome: {e}. Start the browser with "
                    "--remote-debugging-port=9222 (e.g. macOS: /Applications/Chromium.app/Contents/MacOS/Chromium "
                    "--remote-debugging-port=9222 or Google Chrome with the same flag)."
                ) from e
            try:
                context = page.context
                if download_flag:
                    project_downloads.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(audio_path, project_downloads / audio_path.name)
                for scene, url in zip(scenes, segment_urls):
                    for ti in range(1, timelines + 1):
                        tab = context.new_page()
                        try:
                            open_nth_result_via_chromium(tab, url, ti - 1)
                            if download_flag:
                                video_url = get_video_url_from_page(tab)
                                if video_url:
                                    dest = project_downloads / build_download_filename(
                                        scene, None, timeline_index=ti
                                    )
                                    download_video(tab, video_url, dest)
                                else:
                                    print("[download] Skipped (no video URL)")
                        finally:
                            tab.close()
            finally:
                browser.close()
                playwright.stop()
        else:
            for url in segment_urls:
                open_first_result(url)

    if organize:
        result = organize_downloads(
            scenes,
            downloads_dir=project_downloads,
            output_dir=project_output,
            timeline_count=timelines,
        )
        if timelines > 1:
            for ti in range(1, timelines + 1):
                shutil.copy2(audio_path, project_output / str(ti) / audio_path.name)
            print(f"Organized {len(result)} files and audio into {project_output}/1..{timelines}")
        else:
            shutil.copy2(audio_path, project_output / audio_path.name)
            print(f"Organized {len(result)} files and audio into {project_output}")
        if project_downloads.exists():
            shutil.rmtree(project_downloads)
    else:
        print("Download videos (first result per URL) then run with --organize.")


def _read_urls_from_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [line.strip() for line in text.splitlines() if line.strip()]


def run_urls_only(
    urls: list[str],
    open_in_browser: bool,
    connect_flag: bool,
    download_flag: bool = False,
) -> None:
    if not urls:
        raise ValueError("At least one URL required")
    if not open_in_browser and not connect_flag:
        raise ValueError("In URL mode, use --open or --connect to open the URLs")
    if download_flag and not connect_flag:
        raise ValueError("--download requires --connect")
    if connect_flag:
        try:
            playwright, browser, page = connect_chromium()
        except Exception as e:
            raise ValueError(
                f"Could not connect to Chromium/Chrome: {e}. Start the browser with "
                "--remote-debugging-port=9222 (e.g. macOS: /Applications/Chromium.app/Contents/MacOS/Chromium "
                "--remote-debugging-port=9222 or Google Chrome with the same flag)."
            ) from e
        try:
            context = page.context
            downloads_dir = PATHS["downloads_dir"]
            if download_flag:
                downloads_dir.mkdir(parents=True, exist_ok=True)
            for url in urls:
                tab = context.new_page()
                try:
                    open_first_result_via_chromium(tab, url)
                    if download_flag:
                        clip_url = tab.url
                        video_url = get_video_url_from_page(tab)
                        if video_url:
                            dest = downloads_dir / build_download_filename(
                                None, clip_url
                            )
                            download_video(tab, video_url, dest)
                        else:
                            print("[download] Skipped (no video URL)")
                finally:
                    tab.close()
        finally:
            browser.close()
            playwright.stop()
    else:
        for url in urls:
            open_first_result(url)


def parse_args() -> argparse.Namespace:
    if len(sys.argv) >= 2 and sys.argv[1] == "urls":
        parser = argparse.ArgumentParser(description="Open Artgrid search URLs in browser (no audio)")
        parser.add_argument("urls", nargs="*", help="Artgrid search URLs (or use --file)")
        parser.add_argument("-f", "--file", nargs="?", const=PATHS["urls_file"], default=None, type=Path, metavar="PATH", help="Read URLs from file (one per line). Omit PATH to use input/urls.txt")
        parser.add_argument("--open", action="store_true", dest="open_in_browser", help="Open each URL in browser")
        parser.add_argument("--connect", action="store_true", dest="connect_flag", help="Connect to Chromium/Chrome with remote debugging; open first result per URL")
        parser.add_argument("--download", action="store_true", dest="download_flag", help="Download first result video per URL (requires --connect)")
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
    parser.add_argument("--connect", action="store_true", dest="connect_flag", help="Connect to Chromium/Chrome with remote debugging; open first result per segment")
    parser.add_argument("--download", action="store_true", dest="download_flag", help="Download first result video per segment (requires --connect)")
    parser.add_argument("--timelines", type=int, default=1, metavar="N", help="Number of timelines (1-3): download top N results per segment")
    parser.add_argument("-d", "--debug", action="store_true", help="Print concise debug summaries")
    args = parser.parse_args()
    if not (1 <= args.timelines <= 3):
        raise ValueError("--timelines must be 1, 2, or 3")
    return args


def main() -> None:
    args = parse_args()
    if hasattr(args, "urls"):
        run_urls_only(
            args.urls,
            args.open_in_browser,
            args.connect_flag,
            getattr(args, "download_flag", False),
        )
        return
    run_pipeline(
        args.audio,
        args.output,
        args.language,
        args.organize,
        args.open_in_browser,
        args.connect_flag,
        args.download_flag,
        args.timelines,
        args.debug,
    )


if __name__ == "__main__":
    main()
