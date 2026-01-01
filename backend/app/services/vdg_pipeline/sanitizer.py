"""
VDG Payload Sanitization & Legacy Field Population

LLM 출력의 스키마 엣지 케이스 정규화 및 레거시 호환성 필드 채우기
"""
import logging
from typing import Dict, Any

from app.schemas.vdg import VDG

logger = logging.getLogger(__name__)


def sanitize_vdg_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Coerce known schema edge-cases from LLM output before Pydantic validation."""
    scenes = payload.get("scenes") or []
    if not isinstance(scenes, list):
        scenes = []
    scenes = [scene for scene in scenes if isinstance(scene, dict)]
    payload["scenes"] = scenes
    
    for scene in scenes:
        setting = scene.get("setting") or {}
        audio_style = setting.get("audio_style") or {}
        audio_events = audio_style.get("audio_events")
        if isinstance(audio_events, list):
            normalized = []
            for idx, event in enumerate(audio_events):
                if isinstance(event, dict):
                    normalized.append(event)
                elif isinstance(event, str):
                    normalized.append(
                        {
                            "timestamp": 0.0,
                            "event": "note",
                            "description": event,
                            "intensity": "medium",
                        }
                    )
            audio_style["audio_events"] = normalized
            setting["audio_style"] = audio_style
            scene["setting"] = setting

    commerce = payload.get("commerce")
    if not isinstance(commerce, dict):
        commerce = {}
        payload["commerce"] = commerce
    service_mentions = commerce.get("service_mentions")
    if isinstance(service_mentions, list):
        normalized_services = []
        for item in service_mentions:
            if isinstance(item, str):
                normalized_services.append(item)
            elif isinstance(item, dict):
                name = item.get("name") or item.get("brand") or item.get("category")
                normalized_services.append(name or str(item))
            else:
                normalized_services.append(str(item))
        commerce["service_mentions"] = normalized_services
        payload["commerce"] = commerce

    # === Localization Check: Detect English-only fields ===
    for scene in scenes:
        nu = scene.get("narrative_unit", {})
        summary = nu.get("summary", "")
        if summary:
            # Check if summary contains Korean characters
            has_korean = any('\uac00' <= c <= '\ud7a3' for c in summary)
            if not has_korean:
                # English-only summary detected - mark for frontend
                nu["summary_ko"] = None
                logger.warning(
                    f"Scene {scene.get('scene_id', '?')} has English-only summary: "
                    f"{summary[:50]}... (will show [EN] in UI)"
                )
            else:
                # Korean summary - copy to summary_ko for explicit handling
                nu["summary_ko"] = summary
            scene["narrative_unit"] = nu

    return payload


def populate_legacy_fields(vdg: VDG) -> None:
    """Populate legacy compatibility fields for frontend"""
    # global_context
    hook = vdg.hook_genome
    intent = vdg.intent_layer
    
    vdg.global_context = {
        "title": vdg.title[:100] if vdg.title else "Analyzed Video",
        "mood": "dynamic",  # simplified
        "keywords": ["viral", vdg.platform, intent.hook_trigger],
        "hashtags": [],
        "video_id": vdg.content_id,
        "hook_pattern": hook.pattern,
        "hook_delivery": hook.delivery,
        "hook_strength_score": hook.strength,
        "viral_hook_summary": hook.hook_summary,
        "key_action_description": intent.hook_trigger_reason
    }
    
    # scene_frames (simplified from scenes)
    frames = []
    for scene in vdg.scenes:
        for shot in scene.shots:
            frame = {
                "timestamp": shot.start,
                "duration": shot.end - shot.start,
                "description": shot.keyframes[0].desc if shot.keyframes else scene.narrative_unit.summary,
                "camera": {
                    "type": shot.camera.move,
                    "shot_size": shot.camera.shot,
                    "angle": shot.camera.angle
                }
            }
            frames.append(frame)
    vdg.scene_frames = frames


# Backward compatibility aliases
_sanitize_vdg_payload = sanitize_vdg_payload
_populate_legacy_fields = populate_legacy_fields
