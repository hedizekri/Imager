# Imager: install and usage

## Prerequisites

- **Python 3.12+** (3.13 recommended; avoid 3.14 if you hit dependency issues)
- **Ollama** (for scene/keyword extraction): [ollama.com](https://ollama.com). Install, then run `ollama pull phi3` (or the model set in `imager/config.py`)
- **ffmpeg** (only if you use `--download`): `brew install ffmpeg`
- **Chromium or Google Chrome** (only if you use `--connect` / `--download`): use your normal install; the script connects to an existing window via remote debugging

## Install

From the project root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

No `playwright install` is required: the script connects to your existing browser, it does not launch its own.

## Folder layout

- `input/` – put your audio file(s) here (e.g. `input/audio.mp3`)
- `input/urls.txt` – optional; one Artgrid search URL per line for URL-only mode
- `data/` – transcript and segments JSON (created automatically)
- `downloads/{project_name}/` – videos and a copy of the audio per run (project name = audio stem, lowercase, spaces → underscores)
- `output/{project_name}/` – destination when using `--organize`; one folder per project with clips and audio (Premiere-ready)

## Usage

### 1. Pipeline from audio (transcribe → scenes → Artgrid URLs)

**Full process in one command** (transcribe, extract, download first result per segment, organize into project folder). Start Chromium or Chrome with `--remote-debugging-port=9222` first (see step 1 below):

```bash
python -m imager.main input/test_sport.mp3 --connect --download --organize
```

Result: `downloads/test_sport/` and `output/test_sport/` with the audio file and clips; point Premiere at `output/test_sport/`.

Basic run (no browser; only prints segment URLs):

```bash
python -m imager.main input/audio.mp3
```

Open each search URL in your default browser (you click the first result and download manually if needed):

```bash
python -m imager.main input/audio.mp3 --open
```

Automate with Chromium/Chrome (first result opened per segment; optional download):

1. Start the browser with remote debugging (leave this terminal open):

   **Chromium (macOS):**
   ```bash
   /Applications/Chromium.app/Contents/MacOS/Chromium --remote-debugging-port=9222
   ```

2. In another terminal, from the project root with the venv activated:

   ```bash
   python -m imager.main input/audio.mp3 --open --connect
   ```
   To also download each first-result video into `downloads/{project_name}/` (requires ffmpeg):

   ```bash
   python -m imager.main input/audio.mp3 --connect --download
   ```

Move downloaded files into `output/{project_name}/` (and copy the audio there):

```bash
python -m imager.main input/audio.mp3 --organize
```

Use `-o /path` to set a different output root; the project folder is always `{output_root}/{project_name}/`.

Other options:

- `-l en` – language code for transcription (default from `imager/config.py`, e.g. `fr`)
- `-o output` – output directory for `--organize`
- `-d` / `--debug` – print debug summaries (transcript preview, scene prompt, etc.)

### 2. URL-only mode (no audio)

Use when you already have a list of Artgrid search URLs (e.g. in `input/urls.txt`):

```bash
python -m imager.main urls --file --open --connect
```

With download:

```bash
python -m imager.main urls --file --connect --download
```

`--file` without a path uses `input/urls.txt`. To use another file:

```bash
python -m imager.main urls --file /path/to/urls.txt --connect --download
```

### Summary of flags

| Flag | Meaning |
|------|--------|
| `--open` | Open URLs in default browser (pipeline or URL mode) |
| `--connect` | Use existing Chromium/Chrome via port 9222; open first result per URL |
| `--download` | Download first-result video per URL into `downloads/` (requires `--connect` and ffmpeg) |
| `--organize` | Move files from `downloads/{project_name}/` to `output/{project_name}/` and copy audio (Premiere-ready folder) |
| `-l`, `-o`, `-d` | Language, output dir, debug |

## One MacBook to another

1. Clone or copy the repo.
2. Create venv and install deps (see Install above).
3. Install Ollama and pull the scene model (`ollama pull phi3`).
4. If you use `--download`: install ffmpeg (`brew install ffmpeg`).
5. Put your audio in `input/` and run the commands above; for automated open/download, start Chromium or Chrome with `--remote-debugging-port=9222` first.
