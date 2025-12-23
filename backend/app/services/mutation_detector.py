"""
Mutation Detector - Compares Parent and Child video analysis results
"핵심: 두 영상의 차이점(Mutation)을 추출하여 Genealogy Graph에 저장"
"""
from typing import Optional
from app.schemas.analysis_v3 import (
    ReconstructibleAnalysisResult,
    MutationProfile,
    MutationDelta
)
from app.schemas.viral_codebook import VisualPatternCode, AudioPatternCode, SemanticIntent


class MutationDetector:
    """
    두 영상 분석 결과를 비교하여 Mutation Profile 생성
    
    사용 시나리오:
    1. 사용자가 Parent 노드를 Fork
    2. 자신만의 영상을 촬영/업로드
    3. 두 영상의 Gemini 분석 결과 비교
    4. Mutation Profile 생성 → Neo4j EVOLVED_TO 엣지에 저장
    """
    
    def detect_mutations(
        self,
        parent_result: ReconstructibleAnalysisResult,
        child_result: ReconstructibleAnalysisResult
    ) -> MutationProfile:
        """
        두 분석 결과를 비교하여 MutationProfile 생성
        
        Returns:
            MutationProfile: 부모→자식 간 모든 뮤테이션 요약
        """
        profile = MutationProfile(
            parent_node_id=parent_result.video_id,
            child_node_id=child_result.video_id
        )
        
        # 1. Audio Mutation 감지
        audio_mutation = self._detect_audio_mutation(parent_result, child_result)
        if audio_mutation:
            profile.audio_mutation = audio_mutation
            profile.mutation_count += 1
        
        # 2. Visual Mutation 감지
        visual_mutation = self._detect_visual_mutation(parent_result, child_result)
        if visual_mutation:
            profile.visual_mutation = visual_mutation
            profile.mutation_count += 1
        
        # 3. Hook Pattern Mutation 감지
        hook_mutation = self._detect_hook_mutation(parent_result, child_result)
        if hook_mutation:
            profile.hook_pattern_mutation = hook_mutation
            profile.mutation_count += 1
        
        # 4. Setting/Mood Mutation 감지
        setting_mutation = self._detect_setting_mutation(parent_result, child_result)
        if setting_mutation:
            profile.setting_mutation = setting_mutation
            profile.mutation_count += 1
        
        # Primary Mutation 결정
        profile.primary_mutation_type = self._determine_primary_mutation(profile)
        profile.mutation_summary = self._generate_mutation_summary(profile)
        
        return profile
    
    def _detect_audio_mutation(
        self,
        parent: ReconstructibleAnalysisResult,
        child: ReconstructibleAnalysisResult
    ) -> Optional[MutationDelta]:
        """Viral Mosaic의 첫 번째 타일 기준 Audio 비교"""
        if not parent.viral_mosaic or not child.viral_mosaic:
            return None
        
        parent_audio = parent.viral_mosaic[0].audio_pattern_id
        child_audio = child.viral_mosaic[0].audio_pattern_id
        
        if parent_audio != child_audio:
            return MutationDelta(
                before=parent_audio.value if isinstance(parent_audio, AudioPatternCode) else str(parent_audio),
                after=child_audio.value if isinstance(child_audio, AudioPatternCode) else str(child_audio),
                delta_type="replaced",
                confidence=0.9
            )
        return None
    
    def _detect_visual_mutation(
        self,
        parent: ReconstructibleAnalysisResult,
        child: ReconstructibleAnalysisResult
    ) -> Optional[MutationDelta]:
        """Viral Mosaic의 첫 번째 타일 기준 Visual 비교"""
        if not parent.viral_mosaic or not child.viral_mosaic:
            return None
        
        parent_visual = parent.viral_mosaic[0].visual_pattern_id
        child_visual = child.viral_mosaic[0].visual_pattern_id
        
        if parent_visual != child_visual:
            return MutationDelta(
                before=parent_visual.value if isinstance(parent_visual, VisualPatternCode) else str(parent_visual),
                after=child_visual.value if isinstance(child_visual, VisualPatternCode) else str(child_visual),
                delta_type="replaced",
                confidence=0.9
            )
        return None
    
    def _detect_hook_mutation(
        self,
        parent: ReconstructibleAnalysisResult,
        child: ReconstructibleAnalysisResult
    ) -> Optional[MutationDelta]:
        """Global Context의 Hook Pattern 비교"""
        parent_hook = parent.global_context.hook_pattern
        child_hook = child.global_context.hook_pattern
        
        if parent_hook != child_hook:
            return MutationDelta(
                before=parent_hook,
                after=child_hook,
                delta_type="replaced",
                confidence=0.85
            )
        return None
    
    def _detect_setting_mutation(
        self,
        parent: ReconstructibleAnalysisResult,
        child: ReconstructibleAnalysisResult
    ) -> Optional[MutationDelta]:
        """Global Context의 Mood/Setting 비교"""
        parent_mood = parent.global_context.mood
        child_mood = child.global_context.mood
        
        if parent_mood != child_mood:
            return MutationDelta(
                before=parent_mood,
                after=child_mood,
                delta_type="modified",
                confidence=0.8
            )
        return None
    
    def _determine_primary_mutation(self, profile: MutationProfile) -> str:
        """가장 중요한 뮤테이션 타입 결정"""
        # 우선순위: audio > visual > hook > setting
        if profile.audio_mutation:
            return "audio"
        if profile.visual_mutation:
            return "visual"
        if profile.hook_pattern_mutation:
            return "hook_pattern"
        if profile.setting_mutation:
            return "setting"
        return "none"
    
    def _generate_mutation_summary(self, profile: MutationProfile) -> str:
        """Human-readable 뮤테이션 요약 생성"""
        if profile.mutation_count == 0:
            return "No significant mutations detected"
        
        parts = []
        if profile.audio_mutation:
            parts.append(f"Audio: {profile.audio_mutation.before} → {profile.audio_mutation.after}")
        if profile.visual_mutation:
            parts.append(f"Visual: {profile.visual_mutation.before} → {profile.visual_mutation.after}")
        if profile.hook_pattern_mutation:
            parts.append(f"Hook: {profile.hook_pattern_mutation.before} → {profile.hook_pattern_mutation.after}")
        if profile.setting_mutation:
            parts.append(f"Mood: {profile.setting_mutation.before} → {profile.setting_mutation.after}")
        
        return " | ".join(parts)


# Singleton instance
mutation_detector = MutationDetector()
