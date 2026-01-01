"""
VDG Prompt Builder Utilities

영상 길이와 댓글 기반 동적 프롬프트 생성
"""
from typing import List, Dict, Any, Optional

from .constants import VDG_PROMPT


def get_analysis_depth_hints(duration_sec: float) -> str:
    """영상 길이에 따른 분석 깊이 지침 생성 (v3.6)"""
    
    if duration_sec <= 15:
        # 8-15초 초단편 (가장 세밀하게)
        return """
## 🎯 초단편 영상 분석 지침 (≤15초)
이 영상은 매우 짧으므로 **극도로 세밀한 분석**이 필요합니다.

### 필수 요구사항:
- **Microbeats**: 최소 5개 (0.3~0.5초 단위)
  - 모든 비트에 `t`, `role`, `cue`, `note` 상세 기술
  - role: start → build → build → punch → end 순서 권장
- **Keyframes**: 샷당 2-3개 (주요 동작/표정 변화 포인트)
  - 각 keyframe에 `role`, `desc`, `t_rel_shot` 필수
- **Focus Windows**: 4-5개 (2-3초 단위 구간)
  - 시청자 주의 집중 순간마다 hotspot 분석
- **Scenes**: 1-2개만 (너무 많이 나누지 말 것)
- **Shots per Scene**: 1-3개 (컷 전환점 기준)
"""
    elif duration_sec <= 30:
        # 15-30초 단편
        return """
## 🎯 단편 영상 분석 지침 (15-30초)

### 필수 요구사항:
- **Microbeats**: 최소 4개 (0.5~1초 단위)
- **Keyframes**: 샷당 1-2개
- **Focus Windows**: 4-6개 (3-5초 단위)
- **Scenes**: 2-3개
- **Shots per Scene**: 2-4개
"""
    elif duration_sec <= 60:
        # 30-60초 표준 숏폼
        return """
## 🎯 표준 숏폼 분석 지침 (30-60초)

### 필수 요구사항:
- **Microbeats**: 최소 3개
- **Keyframes**: 샷당 1-2개
- **Focus Windows**: 5-8개 (5-10초 단위)
- **Scenes**: 3-5개
- **Shots per Scene**: 2-5개
"""
    else:
        # 60초+ 롱폼
        return """
## ⚠️ 롱폼 영상 분석 지침 (>60초)
이 영상은 숏폼 분석에 최적화되지 않습니다.
주요 하이라이트 구간(훅, 클라이맥스, 엔딩)만 상세 분석하세요.
"""


def build_enhanced_prompt(
    duration_sec: float,
    audience_comments: Optional[List[Dict[str, Any]]] = None
) -> str:
    """영상 길이와 댓글 기반 동적 프롬프트 생성 (v3.6)"""
    
    # 1. Duration-based depth hints
    depth_hints = get_analysis_depth_hints(duration_sec)
    
    # 2. Comments context (if available)
    comments_section = ""
    if audience_comments:
        comments_text = "\n".join([
            f"- [{c.get('likes', 0)} likes] {c.get('text', '')[:200]}"
            for c in audience_comments[:10]
        ])
        comments_section = f"""
## 📝 시청자 반응 컨텍스트 (Top Comments)
실제 시청자들의 반응입니다. 이를 참고하여 viral_signal, audience_reaction을 분석하세요:

{comments_text}
"""
    
    # 3. Assemble final prompt
    return f"""
{depth_hints}
{comments_section}

---

{VDG_PROMPT}
"""


# Backward compatibility aliases
_get_analysis_depth_hints = get_analysis_depth_hints
_build_enhanced_prompt = build_enhanced_prompt
