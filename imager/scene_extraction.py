import json

import ollama

from imager.config import SCENE_EXTRACTION
from imager.types import Scene, Transcript


MAX_RETRIES = 2

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
        raise ValueError("Transcript is empty")

    segments_text = _format_segments_with_timestamps(transcript.segments)
    prompt = SCENE_PROMPT.format(segments=segments_text)

    for attempt in range(MAX_RETRIES):
        response = _call_ollama(prompt)
        try:
            return _parse_scenes(response, transcript)
        except ValueError as e:
            if attempt == MAX_RETRIES - 1:
                raise e
            print(f"  Retry {attempt + 1}/{MAX_RETRIES}: LLM output invalid")

    raise ValueError("Failed to extract scenes after retries")


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
        raise ValueError(f"Ollama request failed: {e}")


def _parse_scenes(response: str, transcript: Transcript) -> list[Scene]:
    cleaned = _extract_json_array(response)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}\nExtracted: {cleaned[:500]}")

    if not isinstance(data, list):
        raise ValueError(f"Expected list, got {type(data)}")

    scenes = [_dict_to_scene(item, transcript) for item in data]
    return [s for s in scenes if s is not None]


def _extract_json_array(text: str) -> str:
    start = text.find("[")
    if start == -1:
        raise ValueError(f"No JSON array found in: {text[:200]}")
    bracket_count = 0
    for i, char in enumerate(text[start:], start):
        if char == "[":
            bracket_count += 1
        elif char == "]":
            bracket_count -= 1
            if bracket_count == 0:
                return text[start:i + 1]
    raise ValueError(f"No JSON array found in: {text[:200]}")


def _dict_to_scene(data: dict, transcript: Transcript) -> Scene | None:
    segments = transcript.segments
    if not segments:
        return None

    seg_start = max(0, min(int(data.get("segment_start", 0)), len(segments) - 1))
    seg_end_raw = data.get("segment_end", data.get("segments_end", seg_start))
    seg_end = max(0, min(int(seg_end_raw) if seg_end_raw is not None else seg_start, len(segments) - 1))
    if seg_end < seg_start:
        seg_end = seg_start

    start_time = segments[seg_start].start_time
    end_time = segments[seg_end].end_time
    return Scene(
        keywords=data.get("keywords", []),
        start_time=start_time,
        end_time=end_time
    )
