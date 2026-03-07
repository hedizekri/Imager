# AI B-Roll Generator for Adobe Premiere Pro

## Project Overview

This project builds an **AI-powered plugin for Adobe Premiere Pro** that automatically generates B-roll sequences from a narration audio track.

The system analyzes a voice-over audio file, identifies semantic segments, searches relevant stock footage on Artgrid, downloads the videos automatically using Firefox + DownloadHelper, and inserts the clips into the Premiere Pro timeline at the correct timestamps.

The goal is to **automate the B-roll editing workflow** for video editors while keeping them entirely inside the Premiere Pro interface.

## Core Objective

### Input

- A narration audio file (from 15 seconds up to 15 minutes)
- An existing Premiere Pro project
- User launches the plugin from inside Premiere Pro

### Output

- A fully populated Premiere Pro timeline containing B-roll clips synchronized with the narration.

**Important:** The output is **NOT** a rendered video file. The output is a constructed sequence inside Adobe Premiere Pro.

---

## High-Level Architecture

The system contains three main components:

1. **Premiere Pro Extension** — User interface
2. **Python Backend** — AI and orchestration
3. **Firefox automation** — Downloading stock videos

Architecture flow:

```
Premiere Pro Panel
        ↓
Python Backend
        ↓
Speech-to-Text (Whisper)
        ↓
LLM Keyword Generation
        ↓
Artgrid Search
        ↓
Firefox Automation
        ↓
DownloadHelper Extension
        ↓
Local Video Files
        ↓
Premiere ExtendScript
        ↓
Timeline Assembly
```

---

## Technology Stack

### AI Processing (Python)

- **Whisper** — Speech-to-Text
- **OpenAI API** — Keyword generation

### Browser Automation

- **Browser:** Firefox
- **Automation:** Playwright or Selenium
- **Extension:** Video DownloadHelper

### Video Editing Integration

- **Premiere scripting:** ExtendScript
- **Extension UI:** HTML, CSS, JavaScript, Adobe CEP framework

---

## Detailed System Workflow

### Step 1 — User Interaction in Premiere

**Path:** Window → Extensions → AI B-Roll Generator

The extension panel contains:

- Audio selection
- Generate B-roll button
- Progress display

When the user clicks **Generate**, the extension sends a request to the backend.

**API call:**

- **Method:** `POST http://localhost:8000/generate_broll`
- **Payload:**

```json
{
  "audio_path": "input/audio.mp3",
  "project_path": "/Users/editor/project"
}
```

### Step 2 — Speech to Text

The backend performs speech-to-text on the narration audio using **Whisper**.

- **Input:** `audio.mp3`
- **Output:** `transcript.json`

Example:

```json
[
  {
    "start": 0.0,
    "end": 7.5,
    "text": "Artificial intelligence is transforming finance."
  },
  {
    "start": 7.5,
    "end": 13.2,
    "text": "Banks increasingly rely on data-driven decisions."
  }
]
```

### Step 3 — Semantic Keyword Generation

Each transcript segment is analyzed using an LLM to generate visual keywords suitable for stock footage search.

- **Output file:** `segments.json`

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

### Step 4 — Artgrid Stock Video Search

The backend searches stock videos on [Artgrid](https://artgrid.io). Search URLs are generated from keywords.

Example: `https://artgrid.io/search?q=data%20center`

### Step 5 — Video Download via Firefox

Videos are downloaded using Firefox with the **Video DownloadHelper** extension.

Firefox automation:

1. Open Artgrid search page
2. Select relevant video
3. Start video playback
4. DownloadHelper detects video stream
5. Trigger download
6. Save file locally

**Firefox requirements:**

- Installed extension: Video DownloadHelper
- Download directory: `project/videos/`
- Persistent browser profile (Artgrid login, extension configuration)

### Step 6 — Local Video Storage

Downloaded videos are stored locally, e.g.:

- `videos/segment_01.mp4`
- `videos/segment_02.mp4`
- `videos/segment_03.mp4`

### Step 7 — Timeline Instruction File

The backend generates `timeline.json` for Premiere.

Example:

```json
[
  {
    "video_path": "videos/segment_01.mp4",
    "timeline_start": 0.0,
    "duration": 7.5
  },
  {
    "video_path": "videos/segment_02.mp4",
    "timeline_start": 7.5,
    "duration": 5.7
  }
]
```

### Step 8 — Premiere Timeline Assembly

ExtendScript runs inside Premiere Pro and:

- Imports audio narration
- Imports downloaded videos
- Creates or selects a sequence
- Inserts clips at timestamps
- Trims clips to match duration

**ExtendScript required inputs** (from `timeline.json`):

| Field          | Description                |
|----------------|----------------------------|
| `video_path`   | Local path to video        |
| `timeline_start` | Position in seconds      |
| `duration`     | Duration of the segment    |

---

## Project Folder Structure

```
project_root/
    backend/
        main.py
        stt.py
        keyword_generation.py
        artgrid_search.py
        video_download.py
    data/
        transcript.json
        segments.json
        timeline.json
    videos/
        segment_01.mp4
        segment_02.mp4
    input/
        audio.mp3
    premiere_extension/
        index.html
        panel.js
        premiere_script.jsx
        manifest.xml
```

---

## Component Responsibilities

### Backend

- Receive request from Premiere panel
- Run speech-to-text
- Generate semantic keywords
- Search Artgrid
- Automate Firefox downloads
- Generate timeline instructions
- **API:** `POST /generate_broll`

### Premiere Extension

- User interface: select audio file, trigger B-roll generation, show progress
- Trigger ExtendScript execution

### ExtendScript

- Import audio and videos
- Create sequence
- Insert and trim clips
- Align clips with timestamps

---

## Requirements

### Cross-Platform

- **macOS** and **Windows**
- Use Python `pathlib` for paths
- Avoid OS-specific commands

### Performance Targets

- Target audio length: 15 minutes
- Estimated segments: 80–120
- Estimated downloads: 50–100 videos
- Optimization: download only top search results, cache downloaded videos

### MVP Scope

- Single narration track
- Automatic segmentation
- One B-roll per segment
- Automatic timeline assembly
- No transitions required

---

## Future Improvements

- Semantic video similarity search
- Clip duplication detection
- Automatic transitions
- Clip quality ranking
- AI visual matching
