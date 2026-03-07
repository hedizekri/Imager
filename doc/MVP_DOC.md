# B-Roll Generator — MVP (No Premiere Pro)

## Purpose

Standalone MVP that produces B-roll video clips from a narration audio file. No Adobe Premiere Pro: everything runs on the OS (macOS or Windows 11). Output is a folder of video files named by timestamp so they sort in sequence order.

## Input

- One audio file (e.g. narration, interview).

## Output

- A folder of video files, one per segment, named by segment start time so alphabetical order matches sequence order (e.g. `000000_000.mp4`, `000007_500.mp4`).

---

## High-Level Flow

```
Audio file
    ↓
Speech-to-Text (Whisper)
    ↓
Segments + keyword-as-description detection
    ↓
For each segment:
    Firefox → artgrid.io → enter keywords → first result → download via Download Helper
    ↓
Move files to output folder, rename with timestamps (ascending order)
```

---

## Technology Stack

- **Python** — Orchestration, STT, segment/keyword logic.
- **Whisper** — Speech-to-text.
- **LLM (e.g. OpenAI API)** — Keywords-as-description per segment (for stock search).
- **Firefox** — Browser for Artgrid (manual or automated).
- **Video DownloadHelper** — Firefox extension to download the selected video.
- **OS-only** — No Premiere; use `pathlib` and portable paths for macOS and Windows 11.

---

## Detailed Workflow

### Step 1 — Speech-to-Text

- **Input:** User-provided audio file.
- **Output:** Timestamped transcript (e.g. `transcript.json`).

Example segment:

```json
{
  "start": 0.0,
  "end": 7.5,
  "text": "Artificial intelligence is transforming finance."
}
```

### Step 2 — Sequence and Keywords-as-Description Detection

- From the transcript, define **sequences** (e.g. one per sentence or semantic chunk).
- For each sequence, produce **keywords-as-description** suitable for stock search (e.g. via LLM).
- **Output:** List of segments with `start`, `end`, and `keywords` (e.g. `segments.json`).

Example:

```json
[
  {
    "start": 0.0,
    "end": 7.5,
    "keywords": ["financial charts", "data center", "AI technology"]
  },
  {
    "start": 7.5,
    "end": 13.2,
    "keywords": ["bank office", "data analysis", "corporate meeting"]
  }
]
```

### Step 3 — Per-Segment: Firefox, Artgrid, Download

For **each** segment:

1. Open (or automate) **Firefox**.
2. Go to [artgrid.io](https://artgrid.io) (search page or homepage).
3. Enter the segment **keywords** in the search.
4. Select the **first video** result.
5. Start playback so **Video DownloadHelper** can see the stream.
6. Use Download Helper to **download** the video (default browser download folder or a configured folder).

**Prerequisites:**

- Firefox installed.
- Video DownloadHelper extension installed.
- Optional: Artgrid account logged in in that profile if required for download.

### Step 4 — Move and Rename by Timestamp

- **Source:** Browser download folder (or the folder Download Helper uses).
- **Target:** User-chosen output folder (e.g. `output/` or a path from config).
- **Rename rule:** Include segment start time so files sort in ascending sequence order.

Suggested naming (one convention):

- Format: `{start_seconds}_{start_milliseconds}.mp4`  
  Example: `000000_000.mp4`, `000007_500.mp4`, `000013_200.mp4`  
- Or: `HHMMSS_fff.mp4` if you prefer time-of-audio.

Mapping from segment index to file: assume downloads complete in segment order, or match by matching the last downloaded file to the current segment when automating. For a first version, “process one segment at a time and move/rename the most recent download” is enough.

Result: listing the output folder by name gives clips in sequence order.

---

## Project Folder Structure (MVP)

```
project_root/
    input/
        <audio file>
    data/
        transcript.json
        segments.json
    output/
        000000_000.mp4
        000007_500.mp4
        ...
    downloads/          # optional: Firefox/Download Helper target folder
    imager/             # or src/
        main.py
        transcription.py
        scene_extraction.py   # segments + keywords
        artgrid_firefox.py    # build search URL, optionally drive Firefox
        video_composition.py  # move + rename by timestamp
    config.py
```

---

## Cross-Platform: macOS and Windows 11

- **Target:** Both macOS and Windows 11.
- **Approach:** Use `pathlib.Path` for all paths; avoid shell-only or OS-specific commands in core logic. Same Python codebase for both; only launcher or env (e.g. Firefox path) may differ.
- **Practical rollout:** Implement and test on **macOS first**, then run the same code on **Windows 11** and fix path/env and Firefox automation quirks (e.g. Firefox profile path, default download directory). No separate “Mac-only” design; keep everything portable from the start.

---

## MVP Scope Summary

| Item | Scope |
|------|--------|
| Input | Single audio file |
| STT | Whisper |
| Segments | From transcript; keywords via LLM |
| Download | Firefox + Artgrid search + first result + Download Helper |
| Output | One folder; files renamed by timestamp for ascending order |
| Premiere | Not used |
| Platforms | macOS, Windows 11 (pathlib, portable code) |

---

## Out of Scope for This MVP

- Premiere Pro or any NLE integration.
- Rendered timeline or final edited video file.
- Automatic Firefox automation (can be added later); can be “script prints URLs and segment order, user downloads manually then script moves/renames” for true MVP.

---

## Optional: Automation Level for Firefox

- **Minimal:** Script outputs `segments.json` and a list of Artgrid search URLs; user opens each in Firefox, downloads first video with Download Helper; script watches output folder and moves/renames by timestamp.
- **Semi-auto:** Script drives Firefox (e.g. Playwright) to open each search URL; user (or script) triggers playback and Download Helper; script moves/renames after each download.
- **Full auto:** Script drives Firefox and triggers Download Helper via extension/API if available; then move/rename. (Depends on Download Helper’s automation support.)

MVP can start with minimal or semi-auto and evolve.
