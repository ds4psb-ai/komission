from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from typing import List

from app.database import get_db
from app.models import CreatorCalibrationChoice, CalibrationChoice as DBModelChoice
from app.schemas.calibration import (
    CalibrationPairResponse, 
    CalibrationPair, 
    CalibrationSubmitRequest, 
    CalibrationSubmitResponse,
    CalibrationChoice
)

router = APIRouter(prefix="/calibration", tags=["calibration"])

# Mock Pairs Data
MOCK_PAIRS = [
    CalibrationPair(
        pair_id="pair_001_pacing",
        question="어떤 편집 스타일이 더 편안하게 느껴지나요?",
        option_a={"id": "fast", "label": "⚡️ Fast & Punchy", "description": "0.5초 컷편집, 자막 가득, 빠른 호흡", "icon": "⚡️"},
        option_b={"id": "calm", "label": "🌿 Calm & Flow", "description": "긴 호흡, 잔잔한 배경음항, 여백", "icon": "🌿"}
    ),
    CalibrationPair(
        pair_id="pair_002_hook",
        question="영상을 시작할 때 선호하는 방식은?",
        option_a={"id": "visual", "label": "👀 시각적 충격", "description": "이상한 행동/의상으로 시선 끌기", "icon": "👀"},
        option_b={"id": "text", "label": "🗣 대화/질문", "description": "질문이나 상황 설명으로 시작", "icon": "🗣"}
    ),
    CalibrationPair(
        pair_id="pair_003_tone",
        question="나의 평소 말하기 톤은?",
        option_a={"id": "high", "label": "🔥 하이텐션", "description": "높은 톤, 과장된 리액션, 에너지", "icon": "🔥"},
        option_b={"id": "grounded", "label": "☕️ 차분/지적", "description": "신뢰감 있는 목소리, 설명조", "icon": "☕️"}
    ),
    CalibrationPair(
        pair_id="pair_004_music",
        question="배경 음악 취향은?",
        option_a={"id": "trend", "label": "🎵 틱톡/릴스 트렌드", "description": "유행하는 비트 빠른 음악", "icon": "🎵"},
        option_b={"id": "lofi", "label": "🎧 Lo-fi / Jazz", "description": "가사 없는 분위기 있는 배경음", "icon": "🎧"}
    ),
    CalibrationPair(
        pair_id="pair_005_face",
        question="얼굴 노출 선호도는?",
        option_a={"id": "full", "label": "😎 당당하게 클로즈업", "description": "자신감 있는 표정 연기", "icon": "😎"},
        option_b={"id": "scene", "label": "✋ 손/제품 중심", "description": "얼굴보단 행동이나 제품 위주", "icon": "✋"}
    ),
]

@router.get("/pairs", response_model=CalibrationPairResponse)
async def get_calibration_pairs():
    """
    Get a set of pairwise choices for Taste Calibration.
    Currently returns distinct MOCK pairs logic.
    """
    return CalibrationPairResponse(
        session_id=str(uuid.uuid4()),
        pairs=MOCK_PAIRS
    )

@router.post("/choice", response_model=CalibrationSubmitResponse)
async def submit_calibration_choice(
    payload: CalibrationSubmitRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a single choice for calibration.
    """
    try:
        # DB에 저장
        db_choice = CreatorCalibrationChoice(
            creator_id=payload.creator_id,
            pair_id=payload.pair_id,
            option_a_id=payload.pair_id + "_a", # Simple mapping for mock
            option_b_id=payload.pair_id + "_b",
            selected=DBModelChoice(payload.selection.value)
        )
        
        db.add(db_choice)
        await db.commit()
        await db.refresh(db_choice)
        
        return CalibrationSubmitResponse(
            status="success",
            saved_choice_id=db_choice.id
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
