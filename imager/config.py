from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

PATHS = {
    "input_dir": BASE_DIR / "input",
    "data_dir": BASE_DIR / "data",
    "output_dir": BASE_DIR / "output",
    "downloads_dir": BASE_DIR / "downloads",
    "urls_file": BASE_DIR / "input" / "urls.txt",
}

TRANSCRIPTION = {
    "model_size": "base",
    "default_language": "fr",
    "device": "cpu",
    "compute_type": "float32",
}

SCENE_EXTRACTION = {
    "model": "phi3",
}

ARTGRID_SEARCH_BASE = "https://artgrid.io/"
ARTGRID_FIRST_RESULT_SELECTOR = "a[href*='/clip/']"
ARTGRID_VIDEO_SELECTOR = "video source, video"
BROWSER_VIDEO_WAIT_MS = 5000

BROWSER_OPEN_DELAY_MIN = 1.0
BROWSER_OPEN_DELAY_MAX = 2.0
BROWSER_SELECTOR_TIMEOUT_MS = 8000
BROWSER_NAVIGATION_TIMEOUT_MS = 12000

CHROMIUM_CDP_URL = "http://localhost:9222"
