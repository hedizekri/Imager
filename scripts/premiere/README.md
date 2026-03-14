# Imager B-roll to Sequence (Premiere Pro)

Run this script from Premiere Pro to fill the **active sequence** with media from an Imager output folder: one audio track and one video track with B-roll clips placed by timestamp.

## How to run

1. In Premiere Pro: create a **new sequence** and set its format (vertical/horizontal, resolution, frame rate) in the Premiere interface. Select that sequence so it is active.
2. Run the script (e.g. from VS Code with ExtendScript, Run without Debugging).
3. In the file dialog: pick **any file inside** the Imager output folder (e.g. `output/test_sport`). The script uses that file’s folder.
4. The script imports the folder’s media into a bin “Imager Import”, places the audio at 00:00, and places each video at the start time from its filename.

Clips longer than their interval are trimmed; clips shorter are placed at full length (no speed change in script).

## Folder requirements

- **Exactly one audio file** (e.g. `.mp3`, `.wav`, `.m4a`, `.aiff`).
- **At least one video file** (e.g. `.mp4`, `.mov`).
- **Video filenames** must start with the timestamp pattern `MM-SS-MM-SS` (e.g. `00-00-00-06-home_workout_dumbbell_motivation.mp4`). That is the same format Imager uses when downloading B-roll. Videos that don’t match are skipped.
