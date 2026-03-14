# Imager B-roll to Sequence (Premiere Pro)

Run this script from Premiere Pro to build a sequence from an Imager output folder: one audio track and one video track with B-roll clips placed by timestamp.

## How to run

1. In Premiere Pro: **File > Scripts > Run Script**.
2. Select `ImagerBrollToSequence.jsx` (this folder or your copy).
3. In the dialog:
   - **Folder:** Path to the Imager output folder (e.g. `output/test_sport`). Use **Browse** to pick any file inside that folder; the script uses its parent as the folder.
   - **Preset:** **Vertical (TikTok 9:16)** or **Horizontal (YouTube 16:9)**.
4. Click **Run**.

The script creates a new sequence named after the folder, imports the folder’s media into a bin “Imager Import”, places the audio at 00:00, and places each video at the start time from its filename. Clips longer than their interval are trimmed to the interval; clips shorter than their interval are placed at full length (Premiere’s ExtendScript API does not support changing clip speed).

## Folder requirements

- **Exactly one audio file** (e.g. `.mp3`, `.wav`, `.m4a`, `.aiff`).
- **At least one video file** (e.g. `.mp4`, `.mov`).
- **Video filenames** must start with the timestamp pattern `MM-SS-MM-SS` (e.g. `00-00-00-06-home_workout_dumbbell_motivation.mp4`). That is the same format Imager uses when downloading B-roll. Videos that don’t match are skipped.

## Presets

| Preset | Resolution | Aspect ratio | Frame rate |
|--------|------------|--------------|------------|
| Vertical (TikTok 9:16) | 1080 × 1920 | 9:16 | 30 fps |
| Horizontal (YouTube 16:9) | 1920 × 1080 | 16:9 | 30 fps |

Sequence frame size is set from the chosen preset. Frame rate depends on the project/default if the API does not allow changing it.
