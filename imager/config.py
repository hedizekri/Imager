from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

PATHS = {
    "input_dir": BASE_DIR / "input",
    "data_dir": BASE_DIR / "data",
    "output_dir": BASE_DIR / "output",
    "downloads_dir": BASE_DIR / "downloads",
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
