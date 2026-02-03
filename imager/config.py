from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

PATHS = {
    "video_stock": BASE_DIR / "video_stock",
    "manifest": BASE_DIR / "video_stock" / "manifest.json",
    "placeholder": BASE_DIR / "video_stock" / "placeholder.mp4",
    "output_dir": BASE_DIR / "output",
}

TRANSCRIPTION = {
    "model_size": "base",
    "default_language": "fr",
    "device": "cpu",
}

SCENE_EXTRACTION = {
    "model": "phi3",
    "ollama_host": "http://localhost:11434",
}

COMPOSITION = {
    "output_format": "mp4",
    "fps": 24,
    "resolution": (1920, 1080),
}
