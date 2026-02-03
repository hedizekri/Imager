import json
import time
from pathlib import Path

from imager.config import PATHS
from imager.types import MatchedScene, Scene, VideoMetadata

# #region agent log
DEBUG_LOG_PATH = "/Users/hedizekri/Perso/Imager/.cursor/debug.log"
def _debug_log(loc, msg, data, hyp):
    with open(DEBUG_LOG_PATH, "a") as f:
        f.write(json.dumps({"location": loc, "message": msg, "data": data, "hypothesisId": hyp, "timestamp": int(time.time()*1000), "sessionId": "debug-session"}) + "\n")
# #endregion


class VideoMatchingError(Exception):
    pass


def load_video_index() -> dict[str, VideoMetadata]:
    manifest_path = PATHS["manifest"]
    if not manifest_path.exists():
        raise VideoMatchingError(f"Manifest not found: {manifest_path}")

    with open(manifest_path) as f:
        data = json.load(f)

    return {
        filename: VideoMetadata(
            filename=filename,
            tags=meta["tags"],
            description=meta.get("description", "")
        )
        for filename, meta in data.items()
    }


def match_scenes_to_videos(
    scenes: list[Scene],
    index: dict[str, VideoMetadata]
) -> list[MatchedScene]:
    matches = [_match_single_scene(scene, index) for scene in scenes]
    # #region agent log
    _debug_log("video_matching.py:match_scenes_to_videos", "all_matches", {"count": len(matches), "matches": [{"video": str(m.video_path.name), "is_placeholder": m.is_placeholder, "scene_start": m.scene.start_time, "scene_end": m.scene.end_time} for m in matches]}, "H2")
    # #endregion
    return matches


def _match_single_scene(
    scene: Scene,
    index: dict[str, VideoMetadata]
) -> MatchedScene:
    best_match = None
    best_score = 0

    scene_keywords = set(kw.lower() for kw in scene.keywords)
    scores = {}

    for filename, metadata in index.items():
        video_tags = set(tag.lower() for tag in metadata.tags)
        matching_tags = scene_keywords & video_tags
        score = len(matching_tags)
        scores[filename] = {"score": score, "matching": list(matching_tags)}

        if score > best_score:
            best_score = score
            best_match = filename

    # #region agent log
    _debug_log("video_matching.py:_match_single_scene", "matching_details", {"scene_keywords": list(scene_keywords), "scores": scores, "best_match": best_match, "best_score": best_score}, "H2")
    # #endregion

    if best_match:
        return MatchedScene(
            scene=scene,
            video_path=PATHS["video_stock"] / best_match,
            is_placeholder=False
        )

    return MatchedScene(
        scene=scene,
        video_path=PATHS["placeholder"],
        is_placeholder=True
    )
