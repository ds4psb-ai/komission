"""
VDG Extractor - Video Data Graph Analysis Extraction Utilities

Extracted from outliers.py for better maintainability.
Provides functions to extract various fields from VDG analysis results.

Usage:
    from app.services.vdg_extractor import (
        extract_hook_pattern, extract_shotlist, translate_vdg_to_korean
    )
"""
from typing import Dict, List, Optional, Any


# ==================
# KOREAN TRANSLATION LAYER
# ==================

VDG_KOREAN_MAP = {
    # Camera shots
    "LS": "롱샷 (LS)", "MS": "미디엄샷 (MS)", "CU": "클로즈업 (CU)", 
    "ECU": "익스트림 CU", "WS": "와이드샷 (WS)", "MCU": "미디엄 CU",
    "OTS": "오버더숄더", "POV": "1인칭 시점", "FS": "풀샷 (FS)",
    "2-Shot": "투샷", "3-Shot": "쓰리샷", "Group Shot": "그룹샷",
    # Camera moves  
    "zoom_in": "줌인", "zoom_out": "줌아웃", "pan": "패닝", "tilt": "틸트",
    "dolly": "돌리", "track": "트래킹", "static": "고정샷", "handheld": "핸드헬드",
    "track_back": "트래킹백", "shake_effect": "흔들림 효과", "follow": "팔로우샷",
    # Camera angles
    "eye": "아이레벨", "low": "로우앵글", "high": "하이앵글", "dutch": "더치앵글",
    # Narrative roles
    "Action": "액션", "Reaction": "리액션", "Hook": "훅", "Setup": "셋업",
    "Payoff": "페이오프", "Conflict": "갈등", "Resolution": "해결",
    "Main Event": "메인 이벤트", "Full Sketch": "풀 스케치", "Hook & Setup": "훅 & 셋업",
    "Climax": "클라이맥스", "Outro": "아웃트로", "Transition": "전환",
    # Hook patterns
    "pattern_break": "패턴 브레이크", "question": "질문", "reveal": "공개/리빌",
    "transformation": "변신", "unboxing": "언박싱", "challenge": "챌린지",
    # Edit pace
    "real_time": "실시간", "fast": "빠른 편집", "slow": "슬로우", "jump_cut": "점프컷",
    "medium": "보통 속도",
    # Audio events
    "impact_sound": "충격음", "crowd_laughter": "관객 웃음", "speech": "대사",
    "music": "음악", "ambient": "환경음", "sfx": "효과음", "silence": "무음",
    "Laughter": "웃음", "Dialogue": "대화", "Buzzer": "버저음", "Applause": "박수",
    "Voiceover": "내레이션", "Sound Effect": "효과음", "Background Music": "배경 음악",
    # Visual style / Lighting
    "Stage Lighting": "무대 조명", "Natural": "자연광", "Dramatic": "드라마틱 조명",
    "Soft": "소프트 조명", "High Key": "하이키 조명", "Low Key": "로우키 조명",
    "High Key Studio": "스튜디오 조명", "Warm/Indoor": "따뜻한 실내광",
    "Outdoor": "야외광", "Neon": "네온 조명", "Cinematic": "시네마틱",
}


def translate_term(term: str) -> str:
    """Translate a single English term to Korean"""
    if not term:
        return term
    return VDG_KOREAN_MAP.get(term, term)


# ==================
# HOOK EXTRACTION
# ==================

def extract_hook_pattern(analysis: dict) -> Optional[str]:
    """Extract hook pattern from gemini_analysis (VDG v3/v4/v5 schema)"""
    pattern = None
    hook_genome = None
    
    # 1. VDG v5: semantic.hook_genome
    semantic = analysis.get("semantic", {})
    if isinstance(semantic, dict):
        hook_genome = semantic.get("hook_genome")
        if isinstance(hook_genome, dict):
            pattern = hook_genome.get("pattern")
    
    # 2. Direct hook_genome field (VDG v3/v4)
    if not hook_genome:
        hook_genome = analysis.get("hook_genome")
        if isinstance(hook_genome, dict):
            pattern = hook_genome.get("pattern")
    
    # If pattern is "other" or None, try better alternatives
    if pattern in ("other", None) and isinstance(hook_genome, dict):
        # Try hook_summary first (best description)
        hook_summary = hook_genome.get("hook_summary")
        if hook_summary and len(hook_summary) > 5:
            return hook_summary[:50]
        
        # Try first microbeat note
        microbeats = hook_genome.get("microbeats", [])
        if microbeats and isinstance(microbeats[0], dict):
            note = microbeats[0].get("note") or microbeats[0].get("description", "")
            if note and len(note) > 5:
                return note[:50]
        
        # Try delivery as pattern
        delivery = hook_genome.get("delivery")
        if delivery and delivery != "visual_gag":
            return delivery
    
    # Return pattern if it's a good value
    if pattern and pattern != "other":
        return pattern
    
    # 3. VDG v3: scenes[0].narrative_unit.role
    if "scenes" in analysis and len(analysis["scenes"]) > 0:
        first_scene = analysis["scenes"][0]
        narrative = first_scene.get("narrative_unit", {})
        if narrative.get("role"):
            return narrative["role"].lower().replace(" ", "_")
        # VDG v5: scene-level summary
        summary = first_scene.get("summary")
        if summary and len(summary) > 10:
            return summary[:50]
    
    # 4. Legacy pattern field
    return analysis.get("pattern") or pattern


def extract_hook_score(analysis: dict) -> Optional[float]:
    """Extract hook strength score (VDG v3/v4/v5)"""
    # 1. VDG v5: semantic.hook_genome.strength
    semantic = analysis.get("semantic", {})
    if isinstance(semantic, dict):
        hook_genome = semantic.get("hook_genome")
        if isinstance(hook_genome, dict):
            strength = hook_genome.get("strength")
            if strength is not None:
                return float(strength)
    
    # 2. Direct hook_genome.strength (VDG v3/v4)
    hook_genome = analysis.get("hook_genome", {})
    if isinstance(hook_genome, dict):
        strength = hook_genome.get("strength")
        if strength is not None:
            return float(strength)
    
    # 3. Legacy metrics.hook_strength
    metrics = analysis.get("metrics", {})
    virality = metrics.get("virality", {})
    if virality.get("hook_strength") is not None:
        return float(virality["hook_strength"])
    
    return None


def extract_hook_duration(analysis: dict) -> Optional[float]:
    """Extract hook duration (VDG v3/v4/v5)"""
    # 1. VDG v5: semantic.hook_genome.end_sec
    semantic = analysis.get("semantic", {})
    if isinstance(semantic, dict):
        hook_genome = semantic.get("hook_genome")
        if isinstance(hook_genome, dict):
            end_sec = hook_genome.get("end_sec")
            if end_sec is not None:
                return float(end_sec)
            # Fallback to hook_end_ms
            end_ms = hook_genome.get("hook_end_ms")
            if end_ms is not None:
                return float(end_ms) / 1000.0
    
    # 2. Direct hook_genome (VDG v3/v4)
    hook_genome = analysis.get("hook_genome", {})
    if isinstance(hook_genome, dict):
        end_sec = hook_genome.get("end_sec")
        if end_sec is not None:
            return float(end_sec)
        duration = hook_genome.get("duration_sec")
        if duration is not None:
            return float(duration)
        # Fallback to hook_end_ms
        end_ms = hook_genome.get("hook_end_ms")
        if end_ms is not None:
            return float(end_ms) / 1000.0
    
    return None


# ==================
# SHOTLIST / TIMING / DO_NOT
# ==================

def extract_shotlist(analysis: dict) -> Optional[List[str]]:
    """Extract shotlist from VDG - supports v3, v4, v5 schemas"""
    shotlist = []
    
    # 1. VDG v5: semantic.capsule_brief.shotlist
    capsule = analysis.get("semantic", {}).get("capsule_brief", {})
    if capsule.get("shotlist"):
        return capsule["shotlist"]
    
    # 2. VDG v5: Use viral_kicks as shotlist
    provenance = analysis.get("provenance", {})
    kicks = provenance.get("viral_kicks", [])
    if kicks:
        for kick in kicks:
            title = kick.get("title", "")
            instr = kick.get("creator_instruction", "")
            t_start = kick.get("t_start_ms", 0) / 1000
            t_end = kick.get("t_end_ms", 0) / 1000
            shotlist.append(f"[{t_start:.0f}-{t_end:.0f}s] {title}: {instr[:50]}...")
        if shotlist:
            return shotlist
    
    # 3. VDG v3: scenes[].narrative_unit.summary
    if "scenes" in analysis and analysis["scenes"]:
        for i, scene in enumerate(analysis["scenes"]):
            narrative = scene.get("narrative_unit", {})
            summary = narrative.get("summary")
            if summary:
                duration = scene.get("duration_sec")
                if duration:
                    shotlist.append(f"{summary} ({duration}s)")
                else:
                    shotlist.append(summary)
        if shotlist:
            return shotlist
    
    # 4. Legacy shotlist field
    if "shotlist" in analysis:
        return analysis["shotlist"]
    
    return None


def extract_timing(analysis: dict) -> Optional[List[str]]:
    """Extract timing info from VDG - supports v3, v4, v5 schemas"""
    timings = []
    
    def _safe_float(value, fallback: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return fallback
    
    # 1. VDG v5: analysis_plan.points
    analysis_plan = analysis.get("analysis_plan", {})
    points = analysis_plan.get("points", [])
    if points:
        for point in points[:6]:
            t_center = _safe_float(point.get("t_center"))
            t_window = point.get("t_window", [])
            if t_window and len(t_window) == 2:
                start = _safe_float(t_window[0])
                end = _safe_float(t_window[1])
                timings.append(f"{start:.1f}-{end:.1f}s: {point.get('reason', 'analysis')}")
            elif t_center:
                timings.append(f"{t_center:.1f}s: {point.get('reason', 'analysis')}")
        if timings:
            return timings
    
    # 2. VDG v5: Use viral_kicks for timing
    provenance = analysis.get("provenance", {})
    kicks = provenance.get("viral_kicks", [])
    if kicks:
        for kick in kicks:
            window = kick.get("window", {})
            t_start = (
                window.get("start_ms", 0) / 1000 if window.get("start_ms") is not None
                else kick.get("t_start_ms", 0) / 1000
            )
            t_end = (
                window.get("end_ms", 0) / 1000 if window.get("end_ms") is not None
                else kick.get("t_end_ms", 0) / 1000
            )
            timings.append(f"{t_start:.0f}-{t_end:.0f}s: {kick.get('title', 'kick')}")
        if timings:
            return timings
    
    # 3. VDG v3: scenes
    if "scenes" in analysis and analysis["scenes"]:
        for scene in analysis["scenes"]:
            if "duration_sec" in scene:
                timings.append(f"{scene['duration_sec']}s")
            elif "time_start" in scene and "time_end" in scene:
                start = _safe_float(scene.get("time_start"))
                end = _safe_float(scene.get("time_end"), start)
                timings.append(f"{end - start:.1f}s")
        if timings:
            return timings
    
    return None


def extract_do_not(analysis: dict) -> Optional[List[str]]:
    """Extract things to avoid - supports v3, v4, v5 schemas"""
    do_not = []
    
    # 1. VDG v5: semantic.capsule_brief.do_not
    capsule = analysis.get("semantic", {}).get("capsule_brief", {})
    if capsule.get("do_not"):
        return capsule["do_not"]
    
    # 2. VDG v4: remix_suggestions[0].do_not or variable_elements
    remix = analysis.get("remix_suggestions", [])
    if remix:
        first_remix = remix[0]
        if first_remix.get("do_not"):
            return first_remix["do_not"]
    
    # 3. Legacy do_not field
    if "do_not" in analysis:
        return analysis["do_not"]
    
    return None


# ==================
# INVARIANT / VARIABLE (Temporal Variation Theory)
# ==================

def extract_invariant(analysis: dict) -> Optional[List[str]]:
    """
    Extract must-keep elements (불변 요소) from VDG analysis
    Priority: replication_recipe > hook_genome > viral_kicks
    """
    invariant = []
    
    delivery_map = {
        "visual_gag": "시각적 개그",
        "storytelling": "스토리텔링",
        "reaction": "리액션",
        "tutorial": "튜토리얼",
        "reveal": "반전/공개",
        "montage": "몽타주",
        "talking_head": "토킹 헤드",
    }
    
    prov = analysis.get("provenance", {})
    
    # 1. PRIMARY: Use replication_recipe from causal_reasoning
    causal = prov.get("causal_reasoning", {})
    recipe = causal.get("replication_recipe", [])
    if recipe:
        for step in recipe[:3]:
            if step and isinstance(step, str):
                invariant.append(f"📋 {step}")
    
    # 2. SECONDARY: Hook genome details
    if len(invariant) < 3:
        semantic = analysis.get("semantic", {})
        if isinstance(semantic, dict):
            hg = semantic.get("hook_genome", {})
            if isinstance(hg, dict):
                pattern = hg.get("pattern")
                if pattern and pattern != "other":
                    invariant.append(f"🎣 훅 패턴: {pattern}")
                elif pattern == "other":
                    microbeats = hg.get("microbeats", [])
                    if microbeats and microbeats[0].get("note"):
                        note = microbeats[0]["note"][:40]
                        invariant.append(f"🎣 훅 시작: {note}")
                
                delivery = hg.get("delivery")
                if delivery:
                    delivery_kr = delivery_map.get(delivery, delivery)
                    invariant.append(f"🎯 전달 방식: {delivery_kr}")
                
                end_sec = hg.get("end_sec")
                if end_sec:
                    invariant.append(f"⏱️ 훅 완성: {end_sec}초 안에")
    
    return invariant if invariant else None


def extract_variable(analysis: dict) -> Optional[List[str]]:
    """
    Extract creative variation elements (가변 요소)
    Priority: viral_kicks.creator_instruction > format-based suggestions
    """
    variable = []
    
    prov = analysis.get("provenance", {})
    
    # 1. PRIMARY: Use viral_kicks.creator_instruction
    kicks = prov.get("viral_kicks", [])
    if kicks:
        for kick in kicks:
            instruction = kick.get("creator_instruction")
            if instruction and isinstance(instruction, str):
                text = instruction[:80] + "..." if len(instruction) > 80 else instruction
                variable.append(f"🎬 {text}")
    
    # 2. SECONDARY: Additional recipe steps
    if len(variable) < 3:
        causal = prov.get("causal_reasoning", {})
        recipe = causal.get("replication_recipe", [])
        for step in recipe[3:5]:
            if step and isinstance(step, str):
                text = step[:60] + "..." if len(step) > 60 else step
                variable.append(f"✨ {text}")
    
    # 3. FALLBACK: Format-based suggestions
    if not variable:
        semantic = analysis.get("semantic", {})
        hook_genome = semantic.get("hook_genome", {}) if isinstance(semantic, dict) else {}
        delivery = hook_genome.get("delivery", "")
        
        variable = [
            "🎨 소재: 동일 포맷의 다른 주제 적용 가능",
            "👤 인물: 다른 크리에이터 스타일로 재해석",
            "📍 배경: 장소/환경 자유롭게 변경",
        ]
        
        if delivery == "visual_gag":
            variable.append("😂 개그 소재: 다른 밈/유머로 대체 가능")
        elif delivery == "storytelling":
            variable.append("📖 스토리: 다른 내러티브로 재구성 가능")
    
    return variable if variable else None


# ==================
# VISUAL / AUDIO PATTERNS
# ==================

def extract_visual_patterns(analysis: dict) -> Optional[List[str]]:
    """Extract visual patterns from VDG - supports v3, v4, v5 schemas"""
    patterns = []
    
    # 1. VDG v5: semantic.mise_en_scene_signals
    semantic = analysis.get("semantic", {})
    mise_signals = semantic.get("mise_en_scene_signals", []) if isinstance(semantic, dict) else []
    if mise_signals:
        for signal in mise_signals[:6]:
            if isinstance(signal, dict):
                element = signal.get("element", "")
                value = signal.get("value", "")
                if element and value:
                    patterns.append(f"{translate_term(element)}: {value}")
        if patterns:
            return patterns
    
    # 2. VDG v4: visual_analysis.results
    visual = analysis.get("visual_analysis", {})
    if visual.get("analysis_results"):
        for result in visual["analysis_results"][:3]:
            metrics = result.get("metrics", {})
            for metric_id in metrics.keys():
                if "color" in metric_id:
                    patterns.append("시각적 색상")
                if "motion" in metric_id:
                    patterns.append("모션/움직임")
    
    # 3. Legacy: scenes[].shots[].camera
    if "scenes" in analysis and analysis["scenes"]:
        for scene in analysis["scenes"][:3]:
            shots = scene.get("shots", [])
            for shot in shots[:2]:
                camera = shot.get("camera", {})
                if camera.get("shot"):
                    patterns.append(translate_term(camera["shot"]))
                if camera.get("move"):
                    patterns.append(translate_term(camera["move"]))
    
    return list(dict.fromkeys(patterns))[:6] if patterns else None


def extract_audio_pattern(analysis: dict) -> Optional[str]:
    """Extract audio pattern from VDG with Korean translation"""
    # Direct audio field
    audio = analysis.get("audio")
    if isinstance(audio, dict):
        pattern = audio.get("type") or audio.get("style")
        return translate_term(pattern) if pattern else None
    if isinstance(audio, str):
        return translate_term(audio) if audio else None
    
    # VDG v3: scenes[].setting.audio_style
    if "scenes" in analysis:
        for scene in analysis["scenes"]:
            setting = scene.get("setting", {})
            audio_style = setting.get("audio_style", {})
            if audio_style.get("music"):
                return translate_term(audio_style["music"])
            if audio_style.get("tone"):
                return translate_term(audio_style["tone"])
    
    return None


# ==================
# VDG TRANSLATION (for Storyboard UI)
# ==================

def translate_vdg_to_korean(analysis: dict) -> dict:
    """
    Translate VDG analysis to Korean for Storyboard UI.
    Returns structured scene data with Korean labels.
    """
    result = {
        "title": analysis.get("title", ""),
        "title_ko": analysis.get("title", ""),
        "total_duration": 0,
        "scene_count": 0,
        "scenes": [],
    }
    
    # VDG v5: semantic.scenes OR top-level scenes
    scenes = analysis.get("semantic", {}).get("scenes") or analysis.get("scenes") or []
    if not isinstance(scenes, list):
        scenes = []
    scenes = [scene for scene in scenes if isinstance(scene, dict)]
    result["scene_count"] = len(scenes)
    
    # Fill title and duration from analysis
    result["title"] = analysis.get("title") or analysis.get("semantic", {}).get("summary", "")[:50] or "영상 분석"
    result["title_ko"] = result["title"]
    pre_set_duration = analysis.get("duration_sec", 0)
    result["total_duration"] = pre_set_duration
    
    for i, scene in enumerate(scenes):
        narrative = scene.get("narrative_unit") or {}
        setting = scene.get("setting") or {}
        visual_style = setting.get("visual_style") or {}
        audio_style = setting.get("audio_style") or {}
        shots = scene.get("shots") or []
        
        # Calculate timing
        window = scene.get("window", {})
        time_start = (
            window.get("start_ms", 0) / 1000.0
            if window.get("start_ms") is not None
            else scene.get("time_start")
        )
        time_end = (
            window.get("end_ms", 0) / 1000.0
            if window.get("end_ms") is not None
            else scene.get("time_end")
        )
        try:
            time_start = float(time_start) if time_start is not None else 0.0
        except (TypeError, ValueError):
            time_start = 0.0
        try:
            time_end = float(time_end) if time_end is not None else 0.0
        except (TypeError, ValueError):
            time_end = 0.0

        raw_duration = scene.get("duration_sec")
        try:
            duration = float(raw_duration) if raw_duration is not None else (time_end - time_start)
        except (TypeError, ValueError):
            duration = time_end - time_start
        
        if not pre_set_duration:
            result["total_duration"] += duration
        
        # Extract camera info from first shot
        camera_info = {}
        if shots:
            cam = shots[0].get("camera", {})
            camera_info = {
                "shot": translate_term(cam.get("shot", "")),
                "shot_en": cam.get("shot", ""),
                "move": translate_term(cam.get("move", "")),
                "move_en": cam.get("move", ""),
                "angle": translate_term(cam.get("angle", "")),
                "angle_en": cam.get("angle", ""),
            }
        
        # Extract audio events
        audio_events = audio_style.get("audio_events") or []
        audio_descriptions = [
            {
                "label": translate_term(e.get("description", "")),
                "label_en": e.get("description", ""),
                "intensity": e.get("intensity", "medium"),
            }
            for e in audio_events
            if isinstance(e, dict) and e.get("description")
        ]
        
        scene_data = {
            "scene_id": scene.get("scene_id", f"S{i+1:02d}"),
            "scene_number": i + 1,
            "time_start": time_start,
            "time_end": time_end,
            "duration_sec": duration,
            "time_label": f"{int(time_start//60)}:{int(time_start%60):02d} - {int(time_end//60)}:{int(time_end%60):02d}",
            # Narrative - VDG v5: scene-level fields; legacy: narrative_unit
            "role": translate_term(scene.get("narrative_role") or narrative.get("role", "")),
            "role_en": scene.get("narrative_role") or narrative.get("role", ""),
            "summary": scene.get("summary") or narrative.get("summary", ""),
            "summary_ko": scene.get("summary") or narrative.get("summary", ""),
            "dialogue": narrative.get("dialogue", ""),
            "comedic_device": narrative.get("comedic_device", []),
            # Camera
            "camera": camera_info,
            # Setting
            "location": setting.get("location", ""),
            "lighting": translate_term(visual_style.get("lighting", "")),
            "lighting_en": visual_style.get("lighting", ""),
            "edit_pace": translate_term(visual_style.get("edit_pace", "")),
            "edit_pace_en": visual_style.get("edit_pace", ""),
            # Audio
            "audio_events": audio_descriptions,
            "music": audio_style.get("music", ""),
            "ambient": audio_style.get("ambient_sound", ""),
        }
        result["scenes"].append(scene_data)
    
    return result


# ==================
# PLATFORM TIPS
# ==================

def get_platform_specific_tips(platform: str) -> List[str]:
    """Get platform-specific shooting tips"""
    tips = {
        "youtube": [
            "🎬 쇼츠: 첫 1초가 생명, Thumbnail = 첫 프레임",
            "📱 세로 9:16 필수, 60초 이내",
        ],
        "tiktok": [
            "🎵 틱톡: 트렌딩 사운드 활용이 핵심",
            "🔄 듀엣/스티치 가능한 포맷 고려",
            "📱 세로 9:16, 15/30/60초 권장",
        ],
        "instagram": [
            "📸 릴스: 첫 3초 안에 주제 명확히",
            "🏷️ 해시태그 활용 중요",
        ],
    }
    return tips.get(platform.lower(), [])
