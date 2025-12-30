"""
Template Seeds API Router
Based on 15_FINAL_ARCHITECTURE.md - Opal 템플릿 시드 생성기

Opal의 역할:
- 초기 템플릿/노드 스펙을 생성 (캡슐/템플릿 시드)
- 결과를 DB에 저장
- 사용자에게는 블랙박스 노드로 노출
"""
import logging
from typing import Optional
from datetime import datetime
import uuid as uuid_lib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.time import utcnow
from app.services.genai_client import get_genai_client, DEFAULT_MODEL_FLASH

from app.database import get_db
from app.config import settings
from app.models import TemplateSeed, RemixNode, NotebookLibraryEntry
from app.schemas.template_seeds import (
    GenerateSeedRequest,
    GenerateSeedResponse,
    TemplateSeedResponse,
    SeedParams,
    TemplateType,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/template-seeds", tags=["template-seeds"])

OPAL_PROMPT_VERSION = "v1.0"


def _build_opal_prompt(
    template_type: TemplateType,
    parent_data: Optional[dict] = None,
    cluster_id: Optional[str] = None,
    context: Optional[dict] = None,
) -> str:
    """Opal 템플릿 시드 생성 프롬프트"""
    
    context_str = ""
    if parent_data:
        context_str += f"\n\nParent Node Data:\n{parent_data}"
    if cluster_id:
        context_str += f"\n\nCluster ID: {cluster_id}"
    if context:
        context_str += f"\n\nAdditional Context:\n{context}"
    
    return f"""You are Opal, a template seed generator for short-form video content.

Your role is to generate an initial template seed for {template_type.value} content.
{context_str}

Generate a JSON template seed with these fields:
- hook: 0-2초 훅 문장/장면
- shotlist: 3-6개 샷 시퀀스 (list of strings)
- audio: 추천 사운드/리듬
- scene: 장소/소품/분위기
- timing: 컷 길이/템포 (list like ["1.2s", "0.8s", "1.5s"])
- do_not: 금지 요소 (브랜드/법적/리스크)

Return ONLY valid JSON matching this schema:
{{
  "hook": "string",
  "shotlist": ["string", "string", ...],
  "audio": "string",
  "scene": "string",
  "timing": ["string", "string", ...],
  "do_not": ["string", ...]
}}
"""


@router.post("/generate", response_model=GenerateSeedResponse)
async def generate_template_seed(
    request: GenerateSeedRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Opal을 사용하여 템플릿 시드 생성
    
    - parent_id: Parent 노드 ID (필수)
    - cluster_id: 참고할 클러스터 ID (선택)
    - template_type: capsule | guide | edit
    """
    try:
        # Parent 노드 조회
        parent_data = None
        if request.parent_id:
            result = await db.execute(
                select(RemixNode).where(RemixNode.node_id == request.parent_id)
            )
            parent_node = result.scalar_one_or_none()
            if parent_node:
                parent_data = {
                    "title": parent_node.title,
                    "platform": parent_node.platform,
                    "gemini_analysis": parent_node.gemini_analysis,
                }
        
        # 시드 파라미터 생성 (Gemini 호출 또는 목업)
        seed_params = await _generate_seed_params(
            request.template_type,
            parent_data,
            request.cluster_id,
            request.context,
        )
        
        # DB에 저장
        seed_id = f"seed_{utcnow().strftime('%Y%m%d%H%M%S')}_{uuid_lib.uuid4().hex[:6]}"
        
        new_seed = TemplateSeed(
            seed_id=seed_id,
            parent_id=uuid_lib.UUID(request.parent_id) if request.parent_id and _is_uuid(request.parent_id) else None,
            cluster_id=request.cluster_id,
            template_type=request.template_type.value,
            prompt_version=OPAL_PROMPT_VERSION,
            seed_json=seed_params.model_dump(),
        )
        
        db.add(new_seed)
        await db.commit()
        await db.refresh(new_seed)
        
        return GenerateSeedResponse(
            success=True,
            seed=TemplateSeedResponse(
                seed_id=seed_id,
                parent_id=request.parent_id,
                cluster_id=request.cluster_id,
                template_type=request.template_type,
                prompt_version=OPAL_PROMPT_VERSION,
                seed_params=seed_params,
                created_at=new_seed.created_at,
            ),
        )
        
    except Exception as e:
        logger.error(f"Failed to generate template seed: {e}")
        return GenerateSeedResponse(
            success=False,
            error=str(e),
        )


@router.get("/{seed_id}", response_model=TemplateSeedResponse)
async def get_template_seed(
    seed_id: str,
    db: AsyncSession = Depends(get_db),
):
    """템플릿 시드 조회"""
    result = await db.execute(
        select(TemplateSeed).where(TemplateSeed.seed_id == seed_id)
    )
    seed = result.scalar_one_or_none()
    
    if not seed:
        raise HTTPException(status_code=404, detail="Template seed not found")
    
    return TemplateSeedResponse(
        seed_id=seed.seed_id,
        parent_id=str(seed.parent_id) if seed.parent_id else None,
        cluster_id=seed.cluster_id,
        template_type=TemplateType(seed.template_type),
        prompt_version=seed.prompt_version,
        seed_params=SeedParams(**seed.seed_json),
        created_at=seed.created_at,
    )


async def _generate_seed_params(
    template_type: TemplateType,
    parent_data: Optional[dict],
    cluster_id: Optional[str],
    context: Optional[dict],
) -> SeedParams:
    """Gemini를 사용하여 시드 파라미터 생성 (new SDK)"""
    
    try:
        client = get_genai_client()
        prompt = _build_opal_prompt(template_type, parent_data, cluster_id, context)
        
        response = client.models.generate_content(
            model=DEFAULT_MODEL_FLASH,
            contents=[prompt],
            config={
                "temperature": 0.3,
                "response_mime_type": "application/json",
            },
        )
        
        import json
        params = json.loads(response.text)
        return SeedParams(**params)
        
    except Exception as e:
        logger.warning(f"Gemini call failed, using mock: {e}")
    
    # Mock fallback
    return SeedParams(
        hook="이거 진짜 대박인데... 3초 안에 관심 끌기",
        shotlist=[
            "클로즈업 - 제품/얼굴 (1.5s)",
            "슬로모션 - 사용 장면 (2s)",
            "빠른 컷 - 결과 비교 (1s)",
            "리액션 - 감탄 표현 (1.5s)",
        ],
        audio="트렌딩 K-pop 비트 + 보이스오버",
        scene="밝은 조명의 실내, 미니멀 배경",
        timing=["1.5s", "2s", "1s", "1.5s", "3s"],
        do_not=["경쟁사 제품 노출", "과장 광고 표현", "저작권 음원"],
    )


def _is_uuid(value: str) -> bool:
    """UUID 형식 체크"""
    try:
        uuid_lib.UUID(value)
        return True
    except ValueError:
        return False
