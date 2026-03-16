import json

import ollama

from imager.config import SCENE_EXTRACTION
from imager.types import Scene, Transcript


MAX_RETRIES = 3
CHUNK_SIZE = 5

SCENE_PROMPT = """Goal: from each transcript segment, derive search terms that will find B-roll footage matching what is being said in that segment. Your keywords are used for separate stock-video searches; give each segment a distinct visual focus so each search returns different clips, and do not repeat the same topic or theme words in every segment.

{segments}

Segment text may be in any language (e.g. French); always output keywords in English. Derive meaning from the segment, do not translate literally.

For each segment, output one JSON object with only keywords: exactly 3 single English words for stock video search. Derive keywords from the content (topic, actions, objects). Do not use generic or unrelated terms. The 3 keywords must be distinct concepts: no synonyms or repetition (e.g. avoid "exercise", "workout", "training" together). Each keyword should suggest a different type of visual: place or setting, object or detail, action or mood.

If two consecutive or thematically similar segments would get the same or very similar keywords, vary the second. No two segments may have the same set of 3 keywords; every segment must have a unique keyword set.

Output a single JSON array of exactly {count} objects, one object per segment, in the same order as the segments above. Do not output one object; output an array. Do not wrap in markdown code blocks (no ```). Do not include indices or timestamps.

Output ONLY the raw JSON array, nothing else:
[{{"keywords": ["workout", "gym", "fitness"]}}, {{"keywords": ["meeting", "office", "discussion"]}}]"""


def extract_scenes(transcript: Transcript, debug: bool = False) -> list[Scene]:
    if not transcript.full_text.strip():
        raise ValueError("Transcript is empty")

    segments = transcript.segments
    scenes: list[Scene] = []
    for start in range(0, len(segments), CHUNK_SIZE):
        chunk = segments[start : start + CHUNK_SIZE]
        chunk_transcript = Transcript(full_text="", segments=chunk)
        segments_text = _format_segments_with_timestamps(chunk)
        prompt = SCENE_PROMPT.format(segments=segments_text, count=len(chunk))
        if debug:
            end = start + len(chunk)
            print(f"[debug] chunk {start // CHUNK_SIZE + 1}, segments {start}-{end}")
        for attempt in range(MAX_RETRIES):
            response = _call_ollama(prompt)
            try:
                chunk_scenes = _parse_scenes(response, chunk_transcript)
                scenes.extend(chunk_scenes)
                break
            except ValueError as e:
                if attempt == MAX_RETRIES - 1:
                    raise e
                print(f"  Retry {attempt + 1}/{MAX_RETRIES}: LLM output invalid: {e}")
                if debug:
                    print(f"[debug] raw LLM response (first 1000 chars):\n{response[:1000]}")
    return scenes


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
    response = _strip_markdown_fences(response)
    cleaned = _extract_json_array(response)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}\nExtracted: {cleaned[:500]}")

    if not isinstance(data, list):
        raise ValueError(f"Expected list, got {type(data)}")

    n = len(transcript.segments)
    if len(data) > n:
        data = data[:n]

    scenes = []
    for i in range(n):
        seg = transcript.segments[i]
        if i < len(data):
            item = data[i]
            keywords = item.get("keywords", []) if isinstance(item, dict) else []
        else:
            keywords = ["b-roll", "footage", f"t{seg.start_time:.0f}"]
        scenes.append(
            Scene(
                keywords=keywords,
                start_time=seg.start_time,
                end_time=seg.end_time,
            )
        )
    return scenes


def _strip_markdown_fences(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        lines = s.split("\n")
        if lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        s = "\n".join(lines)
    return s


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

