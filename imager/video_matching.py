import json
from pathlib import Path

from imager.config import PATHS
from imager.types import MatchedScene, Scene, VideoMetadata


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
    return [_match_single_scene(scene, index) for scene in scenes]


def _match_single_scene(
    scene: Scene,
    index: dict[str, VideoMetadata]
) -> MatchedScene:
    best_match = None
    best_score = 0

    scene_keywords = set(kw.lower() for kw in scene.keywords)

    for filename, metadata in index.items():
        video_tags = set(tag.lower() for tag in metadata.tags)
        score = len(scene_keywords & video_tags)

        if score > best_score:
            best_score = score
            best_match = filename

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
