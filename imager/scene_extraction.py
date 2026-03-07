import json

import ollama

from imager.config import SCENE_EXTRACTION
from imager.types import Scene, Transcript


class SceneExtractionError(Exception):
    pass


MAX_RETRIES = 3

SCENE_PROMPT = """Create one JSON scene per segment. Use segment INDEX numbers [0], [1], [2], etc.

{segments}

For each segment, output:
- description: what a camera would show
- keywords: 5 SINGLE ENGLISH words for video search (dog, coffee, library, doctor, cinema)
- segment_start: the [X] number
- segment_end: same as segment_start for single segments

CRITICAL: segment_start and segment_end must be INDEX numbers like 0, 1, 2, 3, 4 - NOT timestamps!

Output ONLY this JSON format, nothing else:
[{{"description": "person drinking coffee", "keywords": ["coffee", "cafe", "drink", "cup", "morning"], "segment_start": 0, "segment_end": 0}}, {{"description": "person walking dog", "keywords": ["dog", "walk", "pet", "outdoor", "leash"], "segment_start": 1, "segment_end": 1}}]

JSON:"""


def extract_scenes(transcript: Transcript) -> list[Scene]:
    if not transcript.full_text.strip():
        raise SceneExtractionError("Transcript is empty")

    segments_text = _format_segments_with_timestamps(transcript.segments)
    prompt = SCENE_PROMPT.format(segments=segments_text)

    for attempt in range(MAX_RETRIES):
        response = _call_ollama(prompt)
        try:
            return _parse_scenes(response, transcript)
        except SceneExtractionError as e:
            if attempt == MAX_RETRIES - 1:
                raise e
            print(f"  Retry {attempt + 1}/{MAX_RETRIES}: LLM output invalid")

    raise SceneExtractionError("Failed to extract scenes after retries")


def _format_segments_with_timestamps(segments: list) -> str:
    lines = []
    for i, seg in enumerate(segments):
        lines.append(f"[{i}] ({seg.start_time:.1f}s - {seg.end_time:.1f}s): {seg.text}")
    return "\n".join(lines)


def _call_ollama(prompt: str) -> str:
    try:
        response = ollama.chat(
            model=SCENE_EXTRACTION["model"],
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.1}
        )
        return response["message"]["content"]
    except Exception as e:
        raise SceneExtractionError(f"Ollama request failed: {e}")


def _parse_scenes(response: str, transcript: Transcript) -> list[Scene]:
    cleaned = _extract_json_array(response)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise SceneExtractionError(f"Invalid JSON: {e}\nExtracted: {cleaned[:500]}")

    if not isinstance(data, list):
        raise SceneExtractionError(f"Expected list, got {type(data)}")

    scenes = [_dict_to_scene(item, transcript) for item in data]
    scenes = [s for s in scenes if s is not None]
    return _fill_timing_gaps(scenes)


def _fill_timing_gaps(scenes: list[Scene]) -> list[Scene]:
    if not scenes:
        return scenes

    sorted_scenes = sorted(scenes, key=lambda s: s.start_time)
    adjusted = []

    for i, scene in enumerate(sorted_scenes):
        new_start = 0.0 if i == 0 else adjusted[i - 1].end_time
        new_end = sorted_scenes[i + 1].start_time if i < len(sorted_scenes) - 1 \
            else scene.end_time

        adjusted.append(Scene(
            description=scene.description,
            keywords=scene.keywords,
            start_time=new_start,
            end_time=new_end
        ))

    return adjusted


def _extract_json_array(text: str) -> str:
    arrays = []
    pos = 0

    while pos < len(text):
        start = text.find("[", pos)
        if start == -1:
            break

        bracket_count = 0
        end = start
        for i, char in enumerate(text[start:], start):
            if char == "[":
                bracket_count += 1
            elif char == "]":
                bracket_count -= 1
                if bracket_count == 0:
                    end = i + 1
                    break

        if bracket_count != 0:
            break

        array_str = text[start:end]
        try:
            parsed = json.loads(array_str)
            if isinstance(parsed, list):
                arrays.extend(parsed)
        except json.JSONDecodeError:
            pass

        pos = end

    if not arrays:
        raise SceneExtractionError(f"No JSON array found in: {text[:200]}")

    return json.dumps(arrays)


def _find_segment_by_time(segments: list, time_value: float) -> int:
    for i, seg in enumerate(segments):
        if seg.start_time <= time_value < seg.end_time:
            return i
        if abs(seg.start_time - time_value) < 1.0:
            return i
    return 0


def _dict_to_scene(data: dict, transcript: Transcript) -> Scene | None:
    segments = transcript.segments
    if not segments:
        return None

    seg_start = int(data.get("segment_start", 0))
    seg_end_raw = data.get("segment_end", data.get("segments_end", None))
    seg_end = int(seg_end_raw) if seg_end_raw is not None else seg_start

    if seg_start >= len(segments):
        seg_start = _find_segment_by_time(segments, seg_start)
    if seg_end >= len(segments):
        seg_end = _find_segment_by_time(segments, seg_end)

    seg_start = max(0, min(seg_start, len(segments) - 1))
    seg_end = max(0, min(seg_end, len(segments) - 1))

    if seg_end < seg_start:
        seg_end = seg_start

    start_time = segments[seg_start].start_time
    end_time = segments[seg_end].end_time

    return Scene(
        description=data.get("description", ""),
        keywords=data.get("keywords", []),
        start_time=start_time,
        end_time=end_time
    )


