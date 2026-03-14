import json

import ollama

from imager.config import SCENE_EXTRACTION
from imager.types import Scene, Transcript


MAX_RETRIES = 2

SCENE_PROMPT = """Goal: from each transcript segment, derive search terms that will find B-roll footage matching what is being said in that segment. Your keywords are used for separate stock-video searches; give each segment a distinct visual focus so each search returns different clips, and do not repeat the same topic or theme words in every segment.

{segments}

For each segment, output one JSON object with:
- description (optional): what a camera would show
- keywords: exactly 3 SINGLE ENGLISH words for stock video search. Derive keywords from the content of that segment (topic, actions, objects mentioned). Segment text may be in any language; translate its meaning into English search terms. Do not use generic or unrelated terms. The 3 keywords must be distinct concepts: no synonyms or repetition of the same idea (e.g. avoid "exercise", "workout", "training" together). Each keyword should suggest a different type of visual: e.g. one for place or setting, one for object or detail, one for action or mood, so the search can return varied footage.

If two consecutive or thematically similar segments would get the same or very similar keywords, vary the second: use different visuals, synonyms, or a different aspect of the topic so search results are not duplicated. No two segments may have the same set of 3 keywords; every segment must have a unique keyword set so each search returns a different clip.

Output exactly {count} objects in the same order as the segments above. Do not include indices or timestamps.

Output ONLY this JSON format, nothing else:
[{{"description": "person exercising in gym", "keywords": ["workout", "gym", "fitness"]}}, {{"description": "team meeting in office", "keywords": ["meeting", "office", "discussion"]}}]

JSON:"""


def extract_scenes(transcript: Transcript, debug: bool = False) -> list[Scene]:
    if not transcript.full_text.strip():
        raise ValueError("Transcript is empty")

    segments_text = _format_segments_with_timestamps(transcript.segments)
    prompt = SCENE_PROMPT.format(segments=segments_text, count=len(transcript.segments))
    if debug:
        print("[debug] scene prompt content:")
        print(prompt)

    for attempt in range(MAX_RETRIES):
        response = _call_ollama(prompt)
        try:
            return _parse_scenes(response, transcript)
        except ValueError as e:
            if attempt == MAX_RETRIES - 1:
                raise e
            print(f"  Retry {attempt + 1}/{MAX_RETRIES}: LLM output invalid: {e}")
            if debug:
                print(f"[debug] raw LLM response (first 1000 chars):\n{response[:1000]}")

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

    n = len(transcript.segments)
    if len(data) != n:
        raise ValueError(f"Expected {n} items, got {len(data)}")

    scenes = []
    for i in range(n):
        seg = transcript.segments[i]
        item = data[i]
        keywords = item.get("keywords", []) if isinstance(item, dict) else []
        scenes.append(
            Scene(
                keywords=keywords,
                start_time=seg.start_time,
                end_time=seg.end_time,
            )
        )
    _raise_if_duplicate_keyword_sets(scenes)
    return scenes


def _raise_if_duplicate_keyword_sets(scenes: list[Scene]) -> None:
    seen: dict[tuple[str, ...], list[int]] = {}
    for i, scene in enumerate(scenes):
        if not scene.keywords:
            continue
        sig = tuple(sorted(k.lower() for k in scene.keywords))
        if sig not in seen:
            seen[sig] = []
        seen[sig].append(i)
    duplicates = {sig: indices for sig, indices in seen.items() if len(indices) > 1}
    if duplicates:
        parts = [f"segments {indices}: {list(sig)}" for sig, indices in duplicates.items()]
        raise ValueError(f"Duplicate keyword sets: {'; '.join(parts)}")


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

