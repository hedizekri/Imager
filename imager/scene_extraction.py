import json

import ollama

from imager.config import SCENE_EXTRACTION
from imager.types import Scene, Transcript


class SceneExtractionError(Exception):
    pass


MAX_RETRIES = 3

SCENE_PROMPT = """You are a JSON generator. Extract visual scenes from this transcript.

Transcript:
{transcript}

Output ONLY a valid JSON array. No explanations, no other text.
Each object needs: description, keywords (3-5 words), start_time, end_time.

Example format:
[{{"description": "person in bus", "keywords": ["bus", "passenger"], "start_time": 0.0, "end_time": 5.0}}]

JSON array:"""


def extract_scenes(transcript: Transcript) -> list[Scene]:
    if not transcript.full_text.strip():
        raise SceneExtractionError("Transcript is empty")

    prompt = SCENE_PROMPT.format(transcript=transcript.full_text)

    for attempt in range(MAX_RETRIES):
        response = _call_ollama(prompt)
        try:
            return _parse_scenes(response, transcript)
        except SceneExtractionError as e:
            if attempt == MAX_RETRIES - 1:
                raise e
            print(f"  Retry {attempt + 1}/{MAX_RETRIES}: LLM output invalid")

    raise SceneExtractionError("Failed to extract scenes after retries")


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

    return [_dict_to_scene(item, transcript) for item in data]


def _extract_json_array(text: str) -> str:
    start = text.find("[")
    if start == -1:
        raise SceneExtractionError(f"No JSON array found in: {text[:200]}")

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
        raise SceneExtractionError("Unbalanced brackets in JSON")

    return text[start:end]


def _dict_to_scene(data: dict, transcript: Transcript) -> Scene:
    max_time = transcript.segments[-1].end_time if transcript.segments else 0

    return Scene(
        description=data.get("description", ""),
        keywords=data.get("keywords", []),
        start_time=min(float(data.get("start_time", 0)), max_time),
        end_time=min(float(data.get("end_time", 0)), max_time)
    )
