"""
VDG → DB 저장 서비스 (P1-1 완전 통합)

VDG 분석 결과를 정규화된 테이블에 저장:
1. viral_kicks 테이블에 개별 kick 저장
2. keyframe_evidences 테이블에 CV 검증된 keyframes 저장
3. comment_evidences 테이블에 댓글 증거 저장

사용:
    from app.services.vdg_2pass.vdg_db_saver import vdg_db_saver
    await vdg_db_saver.save_vdg_to_db(db, node_id, vdg_data, video_path)
"""
import hashlib
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)


class VDGDatabaseSaver:
    """
    VDG 분석 결과 → 정규화된 DB 저장
    
    viral_kicks, keyframe_evidences, comment_evidences 테이블에
    조인 가능한 형태로 저장
    """
    
    async def save_vdg_to_db(
        self,
        db: AsyncSession,
        node_id: str,
        vdg_data: Dict[str, Any],
        video_path: Optional[str] = None,
        outlier_item_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        VDG 분석 결과를 DB에 저장
        
        Args:
            db: Database session
            node_id: RemixNode ID (UUID string)
            vdg_data: VDG 분석 결과 (dict)
            video_path: 비디오 파일 경로 (keyframe 검증용)
            outlier_item_id: OutlierItem ID (optional)
            
        Returns:
            {
                "kicks_saved": int,
                "keyframes_saved": int,
                "comments_saved": int,
                "proof_ready": bool,
            }
        """
        from app.models import ViralKick, KeyframeEvidence, CommentEvidence, ViralKickStatus, RemixNode
        from app.services.vdg_2pass.quality_gate import proof_grade_gate
        from app.services.vdg_2pass.keyframe_verifier import keyframe_verifier, CV2_AVAILABLE
        
        logger.info(f"💾 Saving VDG to DB for node {node_id}")
        
        # 1. Node UUID 확인
        try:
            node_uuid = uuid.UUID(node_id)
        except ValueError:
            # node_id가 UUID가 아니면 DB에서 찾기
            result = await db.execute(
                select(RemixNode).where(RemixNode.node_id == node_id)
            )
            node = result.scalar_one_or_none()
            if not node:
                logger.error(f"Node not found: {node_id}")
                return {"error": f"Node not found: {node_id}"}
            node_uuid = node.id
        
        # 2. OutlierItem UUID
        outlier_uuid = None
        if outlier_item_id:
            try:
                outlier_uuid = uuid.UUID(outlier_item_id)
            except ValueError:
                pass
        
        # 3. VDG 데이터 추출 (여러 경로에서 fallback)
        provenance = vdg_data.get('provenance', {})
        
        # viral_kicks: provenance에 없으면 직접 필드 체크
        viral_kicks = provenance.get('viral_kicks', [])
        if not viral_kicks:
            viral_kicks = vdg_data.get('viral_kicks', [])
        
        # comment_evidence: provenance에 없으면 직접 필드 체크
        comment_evidence_top5 = provenance.get('comment_evidence_top5', [])
        if not comment_evidence_top5:
            comment_evidence_top5 = vdg_data.get('comment_evidence_top5', [])
        
        # 빈 데이터 early return (에러 아님, 정상 케이스)
        if not viral_kicks:
            logger.warning(f"No viral_kicks found in VDG data for node {node_id}")
            return {
                "kicks_saved": 0,
                "keyframes_saved": 0, 
                "comments_saved": 0,
                "proof_ready": False,
                "warning": "no_viral_kicks_in_vdg_data"
            }
        
        # 4. Quality Gate 체크 (이미 되어있으면 재사용)
        meta = vdg_data.get('meta', {})
        proof_ready = meta.get('proof_ready', False)
        
        if 'proof_ready' not in meta:
            # Duration 추정
            duration_ms = 60000  # Default 1분
            if video_path:
                from app.services.vdg_2pass.unified_pass import get_video_duration_ms
                try:
                    duration_ms = get_video_duration_ms(video_path)
                except:
                    pass
            
            proof_ready, _ = proof_grade_gate.validate(vdg_data, duration_ms)
        
        kicks_saved = 0
        keyframes_saved = 0
        comments_saved = 0
        
        # 5. Comment Evidence 먼저 저장 (kick에서 참조하기 위해)
        comment_map = {}  # rank → evidence_id
        for i, comment in enumerate(comment_evidence_top5[:5]):
            if isinstance(comment, str):
                text = comment
                likes = 0
            else:
                text = comment.get('text', '') or str(comment)
                likes = comment.get('likes', 0) or 0
            
            text_hash = hashlib.md5(text[:100].encode()).hexdigest()[:8]
            evidence_id = f"ev.comment.{text_hash}"
            
            # 중복 체크
            existing = await db.execute(
                select(CommentEvidence).where(CommentEvidence.evidence_id == evidence_id)
            )
            if existing.scalar_one_or_none():
                comment_map[i + 1] = evidence_id
                continue
            
            comment_evidence = CommentEvidence(
                evidence_id=evidence_id,
                node_id=node_uuid,
                text_snippet=text[:500],
                like_count=likes,
                rank=i + 1,
                matched_kick_ids=[],
            )
            db.add(comment_evidence)
            comments_saved += 1
            comment_map[i + 1] = evidence_id
        
        # 6. Viral Kicks 저장
        for kick_data in viral_kicks:
            if isinstance(kick_data, dict):
                kick_index = kick_data.get('kick_index', 1)
                title = kick_data.get('title', f'Kick {kick_index}')
                mechanism = kick_data.get('mechanism', '')
                creator_instruction = kick_data.get('creator_instruction', '')
                
                # Handle both formats: window dict OR direct t_start_ms/t_end_ms
                window = kick_data.get('window', {})
                if isinstance(window, dict) and window:
                    start_ms = window.get('start_ms', 0)
                    end_ms = window.get('end_ms', 5000)
                else:
                    # VDG pipeline stores t_start_ms/t_end_ms directly
                    start_ms = kick_data.get('t_start_ms', 0)
                    end_ms = kick_data.get('t_end_ms', 5000)
                
                keyframes_data = kick_data.get('keyframes', [])
                evidence_ranks = kick_data.get('evidence_comment_ranks', [])
                confidence = kick_data.get('confidence', 0.7)
                missing_reason = kick_data.get('missing_reason')
            else:
                # Pydantic model
                kick_index = getattr(kick_data, 'kick_index', 1)
                title = getattr(kick_data, 'title', f'Kick {kick_index}')
                mechanism = getattr(kick_data, 'mechanism', '')
                creator_instruction = getattr(kick_data, 'creator_instruction', '')
                
                window = getattr(kick_data, 'window', None)
                start_ms = window.start_ms if window else 0
                end_ms = window.end_ms if window else 5000
                
                keyframes_data = getattr(kick_data, 'keyframes', []) or []
                evidence_ranks = getattr(kick_data, 'evidence_comment_ranks', []) or []
                confidence = getattr(kick_data, 'confidence', 0.7)
                missing_reason = getattr(kick_data, 'missing_reason', None)
            
            # Kick ID 생성
            kick_id = f"vk_{node_id[:8]}_{kick_index}"
            
            # 중복 체크
            existing_kick = await db.execute(
                select(ViralKick).where(ViralKick.kick_id == kick_id)
            )
            if existing_kick.scalar_one_or_none():
                logger.warning(f"Kick already exists: {kick_id}")
                continue
            
            # Comment evidence refs
            comment_refs = [comment_map.get(r) for r in evidence_ranks if r in comment_map]
            
            # Peak MS (keyframes에서)
            peak_ms = None
            for kf in keyframes_data:
                if isinstance(kf, dict):
                    if kf.get('role') == 'peak':
                        peak_ms = kf.get('t_ms')
                else:
                    if getattr(kf, 'role', '') == 'peak':
                        peak_ms = getattr(kf, 't_ms', None)
            
            # ViralKick 생성
            viral_kick = ViralKick(
                kick_id=kick_id,
                node_id=node_uuid,
                outlier_item_id=outlier_uuid,
                kick_index=kick_index,
                title=title[:200],
                mechanism=mechanism[:500],  # DB 컬럼 500자에 맞춤
                creator_instruction=creator_instruction[:500] if creator_instruction else None,  # DB 컬럼 500자에 맞춤
                start_ms=start_ms,
                end_ms=end_ms,
                peak_ms=peak_ms,
                confidence=confidence,
                missing_reason=missing_reason,
                proof_ready=proof_ready and confidence >= 0.6 and len(keyframes_data) >= 3,
                comment_evidence_ids=comment_refs,
                frame_evidence_ids=[],  # CV 검증 후 채움
                evidence_comment_ranks=evidence_ranks,
                status=ViralKickStatus.PENDING,
            )
            db.add(viral_kick)
            await db.flush()  # ID 할당
            kicks_saved += 1
            
            # 7. Keyframe Evidences 저장 (CV 검증)
            frame_evidence_ids = []
            
            for kf in keyframes_data:
                if isinstance(kf, dict):
                    t_ms = kf.get('t_ms', 0)
                    role = kf.get('role', 'unknown')
                    what_to_see = kf.get('what_to_see', '')
                else:
                    t_ms = getattr(kf, 't_ms', 0)
                    role = getattr(kf, 'role', 'unknown')
                    what_to_see = getattr(kf, 'what_to_see', '')
                
                # Evidence ID
                frame_hash = hashlib.md5(f"{node_id}_{kick_index}_{role}_{t_ms}".encode()).hexdigest()[:8]
                evidence_id = f"ev.frame.k{kick_index}.{role}.{frame_hash}"
                
                # 중복 체크
                existing_kf = await db.execute(
                    select(KeyframeEvidence).where(KeyframeEvidence.evidence_id == evidence_id)
                )
                if existing_kf.scalar_one_or_none():
                    frame_evidence_ids.append(evidence_id)
                    continue
                
                # CV 검증 (video_path 있을 때만)
                blur_score = None
                brightness = None
                motion_proxy = None
                verified = False
                verification_reason = "no_video_path"
                
                if video_path and CV2_AVAILABLE:
                    try:
                        import cv2
                        cap = cv2.VideoCapture(video_path)
                        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
                        frame_num = int((t_ms / 1000) * fps)
                        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                        ret, frame = cap.read()
                        cap.release()
                        
                        if ret and frame is not None:
                            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                            blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
                            brightness = float(gray.mean())
                            verified = True
                            verification_reason = None
                        else:
                            verification_reason = "frame_extraction_failed"
                    except Exception as e:
                        verification_reason = f"cv_error: {str(e)[:50]}"
                
                keyframe_evidence = KeyframeEvidence(
                    evidence_id=evidence_id,
                    kick_id=viral_kick.id,
                    node_id=node_uuid,
                    role=role,
                    t_ms=t_ms,
                    what_to_see=what_to_see[:200] if what_to_see else None,
                    blur_score=round(blur_score, 2) if blur_score else None,
                    brightness=round(brightness, 2) if brightness else None,
                    motion_proxy=motion_proxy,
                    frame_hash=frame_hash,
                    verified=verified,
                    verification_reason=verification_reason,
                )
                db.add(keyframe_evidence)
                keyframes_saved += 1
                frame_evidence_ids.append(evidence_id)
            
            # Frame evidence IDs 업데이트
            viral_kick.frame_evidence_ids = frame_evidence_ids
        
        # 8. Commit
        await db.commit()
        
        logger.info(
            f"✅ VDG saved to DB: {kicks_saved} kicks, "
            f"{keyframes_saved} keyframes, {comments_saved} comments"
        )
        
        return {
            "kicks_saved": kicks_saved,
            "keyframes_saved": keyframes_saved,
            "comments_saved": comments_saved,
            "proof_ready": proof_ready,
        }
    
    async def get_kicks_for_node(
        self,
        db: AsyncSession,
        node_id: str,
    ) -> List[Dict[str, Any]]:
        """노드의 저장된 kicks 조회"""
        from app.models import ViralKick, RemixNode
        
        # Node UUID 찾기
        try:
            node_uuid = uuid.UUID(node_id)
        except ValueError:
            result = await db.execute(
                select(RemixNode).where(RemixNode.node_id == node_id)
            )
            node = result.scalar_one_or_none()
            if not node:
                return []
            node_uuid = node.id
        
        result = await db.execute(
            select(ViralKick).where(ViralKick.node_id == node_uuid)
        )
        kicks = result.scalars().all()
        
        return [
            {
                "kick_id": k.kick_id,
                "title": k.title,
                "mechanism": k.mechanism,
                "confidence": k.confidence,
                "proof_ready": k.proof_ready,
                "status": k.status.value if hasattr(k.status, 'value') else k.status,
            }
            for k in kicks
        ]


# Singleton
vdg_db_saver = VDGDatabaseSaver()
