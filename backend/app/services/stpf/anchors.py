"""
STPF v3.1 VDG Scale Anchors

1-10 점수에 대한 도메인별 기준 정의.
주관적 점수를 객관화하기 위한 앵커 포인트.

사용법:
- 점수 입력 시 참조 가이드
- 점수 출력 시 해석 가이드
- VDG Mapper의 변환 기준
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class AnchorPoint(BaseModel):
    """개별 앵커 포인트"""
    score: int = Field(ge=1, le=10)
    description: str
    examples: list = Field(default_factory=list)


class VariableAnchor(BaseModel):
    """변수별 앵커 정의"""
    variable_name: str
    domain: str
    description: str
    anchors: Dict[int, str] = Field(default_factory=dict)
    examples: Dict[int, list] = Field(default_factory=dict)


# ================================
# VDG SCALE ANCHORS (핵심 정의)
# ================================

VDG_SCALE_ANCHORS: Dict[str, Dict[str, Any]] = {
    # ============ NUMERATOR (가치 변수) ============
    
    "essence": {
        "domain": "바이럴 영상",
        "description": "시청자의 스크롤을 멈추는 핵심 힘",
        "korean_name": "본질/핵심 가치",
        "anchors": {
            1: "훅 없음, 즉시 스킵 (0.5초 이내 이탈)",
            2: "매우 약한 훅, 2초 미만 시청",
            3: "약한 호기심, 3초 시청 후 이탈",
            4: "평균 이하, 50% 3초 통과",
            5: "평균 훅, 끝까지 시청 50%",
            6: "평균 이상, 댓글 유도 시작",
            7: "강한 훅, 댓글 다수 유도",
            8: "매우 강한 훅, 저장 유도",
            9: "압도적 훅, 저장+공유",
            10: "전설적 훅, 저장+공유+무한 루프 시청",
        },
        "examples": {
            1: ["무음 영상", "정적 이미지만"],
            5: ["일반적인 일상 브이로그"],
            10: ["Khaby Lame 무반응 리액션", "Bella Poarch head nod"],
        }
    },
    
    "capability": {
        "domain": "제작 역량",
        "description": "기술적/창의적 실행 능력",
        "korean_name": "실행 역량",
        "anchors": {
            1: "아마추어 촬영, 기본 편집 불가",
            3: "스마트폰 촬영, 기본 컷 편집",
            5: "표준 프로덕션, 트랜지션 활용",
            7: "프로급, 색보정/사운드 디자인",
            10: "스튜디오급, 영화 수준 퀄리티",
        },
    },
    
    "novelty": {
        "domain": "차별성",
        "description": "기존 콘텐츠 대비 신선도",
        "korean_name": "차별성/의외성",
        "anchors": {
            1: "완전 모방, 원본과 동일",
            3: "약간의 변형, 인식 가능",
            5: "적당한 차별화, 신선함 있음",
            7: "독특한 접근, 새로운 관점",
            10: "장르 창조, 트렌드 선도",
        },
    },
    
    "connection": {
        "domain": "전달력",
        "description": "시청자와의 정서적 연결",
        "korean_name": "전달력/공감",
        "anchors": {
            1: "공감 불가, 이해 어려움",
            3: "약간 공감, 관심은 있음",
            5: "보통 공감, 호감 유발",
            7: "강한 공감, 감정 이입",
            10: "완벽한 공감, 팬 형성",
        },
    },
    
    "proof": {
        "domain": "증거",
        "description": "패턴 성공의 비용 지불 증거",
        "korean_name": "증거/핸디캡",
        "anchors": {
            1: "증거 없음, 추측만",
            2: "자기 주장만, 검증 불가",
            3: "1회 성공, 우연 가능",
            4: "2회 성공, 패턴 조짐",
            5: "3회 이상 반복, 일관성 있음",
            6: "5회 이상, 패턴 확립",
            7: "다수 크리에이터 재현, 외부 검증",
            8: "업계 인정, 케이스 스터디",
            9: "학술적 분석, 논문 인용",
            10: "플랫폼 공식 사례, 장기 누적 증거",
        },
    },
    
    # ============ DENOMINATOR (마찰 변수) ============
    
    "cost": {
        "domain": "비용",
        "description": "제작/실행 비용 (낮을수록 좋음)",
        "korean_name": "비용/복잡도",
        "anchors": {
            1: "거의 무비용, 즉흥 촬영",
            3: "저비용, 기본 장비",
            5: "중간 비용, 표준 프로덕션",
            7: "고비용, 전문 팀 필요",
            10: "최고 비용, 대규모 프로덕션",
        },
    },
    
    "risk": {
        "domain": "리스크",
        "description": "실패 확률 (낮을수록 좋음)",
        "korean_name": "실패 확률",
        "anchors": {
            1: "거의 안전, 검증된 패턴",
            3: "낮은 리스크, 예측 가능",
            5: "보통 리스크, 결과 불확실",
            7: "높은 리스크, 실패 가능성 높음",
            10: "극도로 위험, 성공 사례 희박",
        },
    },
    
    "threat": {
        "domain": "경쟁",
        "description": "동일 패턴 경쟁 강도 (낮을수록 좋음)",
        "korean_name": "경쟁 강도",
        "anchors": {
            1: "블루오션, 경쟁자 없음",
            3: "틈새 시장, 경쟁 약함",
            5: "일반 경쟁, 차별화 필요",
            7: "레드오션, 대형 크리에이터 다수",
            10: "포화 상태, 진입 무의미",
        },
    },
    
    "pressure": {
        "domain": "압박",
        "description": "외부 압박/피로도 (낮을수록 좋음)",
        "korean_name": "압박/피로도",
        "anchors": {
            1: "여유, 시간 충분",
            5: "보통 압박, 일정 준수",
            10: "극심한 압박, 번아웃 위험",
        },
    },
    
    "time_lag": {
        "domain": "지연",
        "description": "성과 나타나는 데 걸리는 시간 (낮을수록 좋음)",
        "korean_name": "성과 지연",
        "anchors": {
            1: "즉시 결과, 24시간 내",
            3: "단기 결과, 1주일 내",
            5: "중기 결과, 1개월 내",
            7: "장기 결과, 분기 이상",
            10: "초장기, 1년 이상",
        },
    },
    
    "uncertainty": {
        "domain": "불확실성",
        "description": "결과 예측 어려움 (낮을수록 좋음)",
        "korean_name": "예측 불가성",
        "anchors": {
            1: "확실, 결과 예측 가능",
            5: "보통, 50% 예측",
            10: "완전 불확실, 예측 불가",
        },
    },
    
    # ============ MULTIPLIERS (승수 변수) ============
    
    "scarcity": {
        "domain": "희소성",
        "description": "유일한 가치",
        "korean_name": "희소성",
        "anchors": {
            1: "흔함, 어디서나 볼 수 있음",
            5: "중간, 차별화된 요소 있음",
            10: "유일무이, 대체 불가",
        },
    },
    
    "network": {
        "domain": "네트워크",
        "description": "사람이 사람을 데려오는 구조",
        "korean_name": "네트워크 효과",
        "anchors": {
            1: "개인 의존, 확산 없음",
            3: "일부 공유, 선형 성장",
            5: "추천 루프 존재, 중간 바이럴",
            7: "커뮤니티 자생, 지수 성장 시작",
            9: "밈화, 리믹스 다수",
            10: "리믹스 폭발, 플랫폼 트렌드 선도",
        },
        "examples": {
            7: ["TikTok 듀엣 체인"],
            10: ["Ice Bucket Challenge", "Harlem Shake"],
        }
    },
    
    "leverage": {
        "domain": "레버리지",
        "description": "재활용 가능성",
        "korean_name": "레버리지",
        "anchors": {
            1: "1회성, 재사용 불가",
            5: "템플릿화 가능, 변형 용이",
            10: "무한 재활용, 시스템화",
        },
    },
    
    # ============ GATES (임계값 변수) ============
    
    "trust_gate": {
        "domain": "신뢰",
        "description": "크리에이터/콘텐츠 신뢰도",
        "korean_name": "신뢰도 게이트",
        "anchors": {
            1: "사기 의심, 허위 정보",
            4: "임계점 (4 미만 = FAIL)",
            5: "신뢰 불분명",
            7: "신뢰할 만함",
            10: "완전 신뢰, 검증된 크리에이터",
        },
    },
    
    "legality_gate": {
        "domain": "합법성",
        "description": "법/규정 준수",
        "korean_name": "합법성 게이트",
        "anchors": {
            1: "명백한 위반",
            4: "임계점 (4 미만 = FAIL)",
            7: "규정 준수",
            10: "완벽한 준수",
        },
    },
    
    "hygiene_gate": {
        "domain": "위생",
        "description": "기본 품질 요건",
        "korean_name": "기본 품질 게이트",
        "anchors": {
            1: "품질 미달, 시청 불가",
            4: "임계점 (4 미만 = FAIL)",
            7: "표준 품질",
            10: "최고 품질",
        },
    },
}


class VDGAnchorLookup:
    """VDG 앵커 조회 유틸리티"""
    
    @staticmethod
    def get_anchor(variable: str, score: int) -> Optional[str]:
        """특정 변수의 점수에 해당하는 앵커 설명"""
        if variable not in VDG_SCALE_ANCHORS:
            return None
        
        anchors = VDG_SCALE_ANCHORS[variable].get("anchors", {})
        
        # 정확한 점수가 있으면 반환
        if score in anchors:
            return anchors[score]
        
        # 가장 가까운 하위 앵커 반환
        lower_scores = [s for s in anchors.keys() if s <= score]
        if lower_scores:
            closest = max(lower_scores)
            return anchors[closest]
        
        return None
    
    @staticmethod
    def get_all_anchors(variable: str) -> Dict[int, str]:
        """변수의 모든 앵커 반환"""
        if variable not in VDG_SCALE_ANCHORS:
            return {}
        return VDG_SCALE_ANCHORS[variable].get("anchors", {})
    
    @staticmethod
    def interpret_score(variable: str, score: float) -> Dict[str, Any]:
        """점수 해석 결과 반환"""
        if variable not in VDG_SCALE_ANCHORS:
            return {"error": f"Unknown variable: {variable}"}
        
        config = VDG_SCALE_ANCHORS[variable]
        anchor = VDGAnchorLookup.get_anchor(variable, int(score))
        
        return {
            "variable": variable,
            "korean_name": config.get("korean_name", variable),
            "score": score,
            "interpretation": anchor,
            "domain": config.get("domain"),
            "description": config.get("description"),
        }
    
    @staticmethod
    def get_variable_info(variable: str) -> Optional[Dict[str, Any]]:
        """변수 정보 반환"""
        if variable not in VDG_SCALE_ANCHORS:
            return None
        return VDG_SCALE_ANCHORS[variable]
    
    @staticmethod
    def list_all_variables() -> list:
        """모든 변수 목록"""
        return list(VDG_SCALE_ANCHORS.keys())


# Singleton instance
anchor_lookup = VDGAnchorLookup()
