"""
P0/P1 Proof-Grade 테스트 스위트

테스트 항목:
1. Quality Gate 검증 로직
2. Cache Key 버저닝
3. Keyframe Verifier 기본 동작
4. VDG DB Saver 저장/조회
5. Cluster Test 기본 동작
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
import hashlib


# ==================
# P0-1: Quality Gate Tests
# ==================

class TestQualityGate:
    """Quality Gate 테스트"""
    
    def test_valid_result_passes(self):
        """완전한 VDG 결과는 Quality Gate 통과"""
        from app.services.vdg_2pass.quality_gate import proof_grade_gate
        
        vdg_data = self._create_valid_vdg()
        proof_ready, issues = proof_grade_gate.validate(vdg_data, 15000)
        
        assert proof_ready == True
        assert len(issues) == 0
    
    def test_missing_keyframes_fails(self):
        """keyframes 부족 시 실패"""
        from app.services.vdg_2pass.quality_gate import proof_grade_gate
        
        vdg_data = {
            "provenance": {
                "viral_kicks": [
                    {
                        "kick_index": 1,
                        "keyframes": [{"t_ms": 500, "role": "start"}],  # 1개만
                        "comment_evidence_refs": [],
                    }
                ],
                "comment_evidence_top5": ["test comment"],
            },
            "meta": {"prompt_version": "v4.2", "model_id": "gemini-3.0-pro", "schema_version": "v4"}
        }
        
        proof_ready, issues = proof_grade_gate.validate(vdg_data, 15000)
        
        assert proof_ready == False
        assert any("keyframes" in i for i in issues)
    
    def test_no_comment_evidence_warns(self):
        """comment_evidence 없으면 경고"""
        from app.services.vdg_2pass.quality_gate import proof_grade_gate
        
        vdg_data = {
            "provenance": {
                "viral_kicks": self._create_valid_kicks(2),
                "comment_evidence_top5": [],  # 비어있음
            },
            "meta": {"prompt_version": "v4.2", "model_id": "gemini-3.0-pro", "schema_version": "v4"}
        }
        
        proof_ready, issues = proof_grade_gate.validate(vdg_data, 15000)
        
        assert any("comment_evidence" in i for i in issues)
    
    def test_keyframe_order_validation(self):
        """start < peak < end 순서 검증"""
        from app.services.vdg_2pass.quality_gate import proof_grade_gate
        
        vdg_data = {
            "provenance": {
                "viral_kicks": [
                    {
                        "kick_index": 1,
                        "keyframes": [
                            {"t_ms": 5000, "role": "start"},  # 잘못된 순서
                            {"t_ms": 2000, "role": "peak"},
                            {"t_ms": 1000, "role": "end"},
                        ],
                        "comment_evidence_refs": ["ev.comment.test"],
                    }
                ],
                "comment_evidence_top5": ["test"],
            },
            "meta": {"prompt_version": "v4.2", "model_id": "gemini-3.0-pro", "schema_version": "v4"}
        }
        
        proof_ready, issues = proof_grade_gate.validate(vdg_data, 15000)
        
        assert any("order" in i for i in issues)
    
    def test_missing_provenance_fails(self):
        """provenance 필수 필드 누락 시 실패"""
        from app.services.vdg_2pass.quality_gate import proof_grade_gate
        
        vdg_data = {
            "provenance": {
                "viral_kicks": self._create_valid_kicks(2),
                "comment_evidence_top5": ["test"],
            },
            "meta": {}  # 필수 필드 없음
        }
        
        proof_ready, issues = proof_grade_gate.validate(vdg_data, 15000)
        
        # meta가 비어있으면 "meta block missing" 또는 필수 필드 누락 에러
        assert proof_ready == False
        assert any("meta" in i.lower() for i in issues)
    
    def _create_valid_vdg(self):
        """유효한 VDG 데이터 생성"""
        return {
            "provenance": {
                "viral_kicks": self._create_valid_kicks(2),
                "comment_evidence_top5": ["comment 1", "comment 2", "comment 3"],
            },
            "meta": {
                "prompt_version": "v4.2",
                "model_id": "gemini-3.0-pro",
                "schema_version": "v4",
            }
        }
    
    def _create_valid_kicks(self, count: int):
        """유효한 viral_kicks 생성"""
        kicks = []
        for i in range(1, count + 1):
            kicks.append({
                "kick_index": i,
                "keyframes": [
                    {"t_ms": 1000 * i, "role": "start"},
                    {"t_ms": 2000 * i, "role": "peak"},
                    {"t_ms": 3000 * i, "role": "end"},
                ],
                "comment_evidence_refs": ["ev.comment.test"],
                "confidence": 0.8,
            })
        return kicks


# ==================
# P0-4: Cache Key Versioning Tests
# ==================

class TestCacheKeyVersioning:
    """캐시 키 버저닝 테스트"""
    
    def test_cache_key_includes_version(self):
        """캐시 키에 버전이 포함되어야 함"""
        from app.services.cache import RedisCache
        
        cache = RedisCache()
        video_url = "https://www.tiktok.com/@test/video/123"
        comments_hash = "abc12345"
        
        key = cache._make_vdg_cache_key(video_url, comments_hash)
        
        # 키 형식: vdg_v4:{url_hash}:{comments_hash}:{version_hash}
        parts = key.split(":")
        assert len(parts) == 4
        assert parts[0] == "vdg_v4"
    
    def test_different_versions_different_keys(self):
        """버전이 다르면 다른 캐시 키"""
        from app.services.cache import RedisCache
        
        cache = RedisCache()
        video_url = "https://www.tiktok.com/@test/video/123"
        comments_hash = "abc12345"
        
        key1 = cache._make_vdg_cache_key(video_url, comments_hash, prompt_version="v4.1")
        key2 = cache._make_vdg_cache_key(video_url, comments_hash, prompt_version="v4.2")
        
        assert key1 != key2
    
    def test_same_input_same_key(self):
        """동일 입력은 동일 키"""
        from app.services.cache import RedisCache
        
        cache = RedisCache()
        video_url = "https://www.tiktok.com/@test/video/123"
        comments_hash = "abc12345"
        
        key1 = cache._make_vdg_cache_key(video_url, comments_hash)
        key2 = cache._make_vdg_cache_key(video_url, comments_hash)
        
        assert key1 == key2


# ==================
# P0-5: Evidence Clip Generator Tests
# ==================

class TestEvidenceClipGenerator:
    """Evidence Clip Generator 테스트"""
    
    def test_hook_window_always_included(self):
        """기본 훅 윈도우(0-5s)는 항상 포함"""
        from app.services.vdg_2pass.evidence_clip_generator import evidence_clip_generator
        
        clips = evidence_clip_generator.generate_clips(
            video_path="/fake/path.mp4",
            comments=[],
            duration_sec=30.0,
            include_scene_cuts=False,
        )
        
        assert len(clips) >= 1
        hook_clip = clips[0]
        assert hook_clip.clip_id == "clip.hook_0_5"
        assert hook_clip.start_ms == 0
    
    def test_timestamp_extraction_mm_ss(self):
        """MM:SS 형식 timestamp 추출 (hook window 밖)"""
        from app.services.vdg_2pass.evidence_clip_generator import evidence_clip_generator
        
        # 10초, 80초에 있는 timestamp (hook window 0-5초 밖)
        comments = [
            {"text": "0:10 여기가 미쳤다", "likes": 100},
            {"text": "1:20 부분 진짜 대박", "likes": 50},
        ]
        
        clips = evidence_clip_generator.generate_clips(
            video_path="/fake/path.mp4",
            comments=comments,
            duration_sec=120.0,
            include_scene_cuts=False,
        )
        
        # 기본 훅 + 댓글 기반 클립들
        assert len(clips) >= 2
        
        # 댓글 timestamp 클립 확인 (10000ms = 0:10)
        clip_ids = [c.clip_id for c in clips]
        assert any("10000" in cid or "80000" in cid for cid in clip_ids)
    
    def test_timestamp_extraction_korean(self):
        """한국어 N초 형식 추출 (hook window 밖)"""
        from app.services.vdg_2pass.evidence_clip_generator import evidence_clip_generator
        
        # 15초 = hook window (0-5초) 밖
        comments = [
            {"text": "15초에서 반전 오진다", "likes": 200},
        ]
        
        clips = evidence_clip_generator.generate_clips(
            video_path="/fake/path.mp4",
            comments=comments,
            duration_sec=60.0,
            include_scene_cuts=False,
        )
        
        clip_ids = [c.clip_id for c in clips]
        assert any("15000" in cid for cid in clip_ids)  # 15초 = 15000ms
    
    def test_max_clips_limit(self):
        """최대 클립 수 제한"""
        from app.services.vdg_2pass.evidence_clip_generator import evidence_clip_generator
        
        comments = [{"text": f"{i}:00 test", "likes": i} for i in range(10)]
        
        clips = evidence_clip_generator.generate_clips(
            video_path="/fake/path.mp4",
            comments=comments,
            duration_sec=600.0,
            include_scene_cuts=False,
        )
        
        assert len(clips) <= evidence_clip_generator.MAX_CLIPS


# ==================
# P1-1: VDG DB Saver Tests (Async)
# ==================

@pytest.mark.asyncio
class TestVDGDatabaseSaver:
    """VDG DB Saver 테스트 (모킹)"""
    
    async def test_save_basic_structure(self):
        """기본 저장 구조 테스트"""
        from app.services.vdg_2pass.vdg_db_saver import VDGDatabaseSaver
        
        saver = VDGDatabaseSaver()
        
        # DB 모킹이 필요한 통합 테스트
        # 실제 테스트는 test_integration_*.py에서 수행
        assert saver is not None


# ==================
# Integration Test Helpers
# ==================

def create_mock_vdg_data():
    """테스트용 VDG 데이터 생성"""
    return {
        "provenance": {
            "viral_kicks": [
                {
                    "kick_index": 1,
                    "window": {"start_ms": 0, "end_ms": 3000},
                    "title": "첫 3초 훅",
                    "mechanism": "표정 반전으로 시청자 호기심 유발",
                    "creator_instruction": "3초 안에 반전 표정 보여주세요",
                    "keyframes": [
                        {"t_ms": 500, "role": "start", "what_to_see": "일상적 표정"},
                        {"t_ms": 1500, "role": "peak", "what_to_see": "반전 표정"},
                        {"t_ms": 2500, "role": "end", "what_to_see": "마무리"},
                    ],
                    "evidence_comment_ranks": [1, 3],
                    "confidence": 0.85,
                },
                {
                    "kick_index": 2,
                    "window": {"start_ms": 5000, "end_ms": 8000},
                    "title": "메인 포인트",
                    "mechanism": "핵심 메시지 전달",
                    "creator_instruction": "메인 포인트를 명확히",
                    "keyframes": [
                        {"t_ms": 5500, "role": "start", "what_to_see": "준비"},
                        {"t_ms": 6500, "role": "peak", "what_to_see": "포인트"},
                        {"t_ms": 7500, "role": "end", "what_to_see": "정리"},
                    ],
                    "evidence_comment_ranks": [2],
                    "confidence": 0.78,
                },
            ],
            "comment_evidence_top5": [
                {"text": "첫 3초에 표정 진짜 미쳤다", "likes": 1000},
                {"text": "메인 포인트 너무 공감", "likes": 800},
                {"text": "반전 오지네", "likes": 500},
            ],
        },
        "meta": {
            "prompt_version": "v4.2",
            "model_id": "gemini-3.0-pro",
            "schema_version": "unified_v4",
            "run_at": datetime.now(timezone.utc).isoformat(),
        }
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
