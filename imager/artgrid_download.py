import re
from pathlib import Path

from imager.config import (
    ARTGRID_SEARCH_BASE,
    ARTGRID_VIDEO_SELECTOR,
    BROWSER_VIDEO_WAIT_MS,
)
from imager.types import Scene

MAX_FILENAME_LEN = 200


def _sanitize(s: str) -> str:
    s = re.sub(r"[^\w\-]", "_", s, flags=re.ASCII)
    return re.sub(r"_+", "_", s).strip("_")[:MAX_FILENAME_LEN]


def build_download_filename(
    scene: Scene | None,
    clip_url: str | None,
) -> str:
    if scene is not None:
        start_m = int(scene.start_time) // 60
        start_s = int(scene.start_time) % 60
        end_m = int(scene.end_time) // 60
        end_s = int(scene.end_time) % 60
        time_part = f"{start_m:02d}:{start_s:02d}-{end_m:02d}:{end_s:02d}"
        kw_part = "_".join(scene.keywords) if scene.keywords else "clip"
        name = f"{time_part}-{_sanitize(kw_part)}.mp4"
    elif clip_url is not None:
        match = re.search(r"/clip/\d+/([^/?]+)", clip_url)
        slug = match.group(1) if match else "clip"
        name = f"00:00-00:01-{_sanitize(slug)}.mp4"
    else:
        raise ValueError("Either scene or clip_url must be provided")
    if len(name) > MAX_FILENAME_LEN:
        name = name[: MAX_FILENAME_LEN - 4] + ".mp4"
    return name


def get_video_url_from_page(page) -> str | None:
    try:
        page.locator(ARTGRID_VIDEO_SELECTOR).first.wait_for(
            state="attached", timeout=BROWSER_VIDEO_WAIT_MS
        )
    except Exception as e:
        print(f"[download] No video element: {e}")
        return None
    js = """
        () => {
            const s = document.querySelector('video source');
            const v = document.querySelector('video');
            return (s && s.src) || (v && (v.src || v.currentSrc)) || null;
        }
    """
    href = page.evaluate(js)
    if not href or not isinstance(href, str):
        print("[download] Video element had no src")
        return None
    print(f"[download] Raw video src: {href[:120]}{'...' if len(href) > 120 else ''}")
    if href.startswith("blob:"):
        print("[download] WARNING: blob URL cannot be fetched by request.get (browser-only)")
    elif ".m3u8" in href or "m3u8" in href.lower():
        print("[download] WARNING: HLS manifest URL; response will be playlist text, not full video")
    if not href.startswith("http"):
        base = ARTGRID_SEARCH_BASE.rstrip("/")
        href = base + ("/" + href.lstrip("/"))
    return href


def download_video(page, video_url: str, dest_path: Path) -> None:
    if not video_url.startswith("http"):
        raise ValueError(f"Invalid video URL: {video_url}")
    print(f"[download] Fetching: {video_url[:100]}{'...' if len(video_url) > 100 else ''}")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    response = page.request.get(video_url)
    status = response.status
    headers = response.headers
    content_type = headers.get("content-type", "")
    body = response.body()
    size = len(body)
    print(f"[download] Response: status={status} content-type={content_type} size={size} bytes")
    if size > 0 and size < 5000:
        sample = body[:200].decode("utf-8", errors="replace")
        print(f"[download] Body sample (first 200 chars): {repr(sample)}")
    if not response.ok:
        raise ValueError(
            f"Video request failed: {status} {video_url}"
        )
    if not body:
        raise ValueError(f"Empty response body: {video_url}")
    dest_path.write_bytes(body)
    print(f"[download] Saved {dest_path} ({size} bytes)")
