from pathlib import Path
import sys

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

BROWSER_OPEN_DELAY_MIN = 3.0
BROWSER_OPEN_DELAY_MAX = 5.0

FIREFOX_MARIONETTE_PORT = 2828

if sys.platform == "darwin":
    FIREFOX_BINARY = "/Applications/Firefox.app/Contents/MacOS/firefox"
elif sys.platform == "win32":
    FIREFOX_BINARY = "C:\\Program Files\\Mozilla Firefox\\firefox.exe"
else:
    FIREFOX_BINARY = "firefox"
