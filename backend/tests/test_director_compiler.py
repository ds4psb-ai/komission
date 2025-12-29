"""
Unit tests for DirectorCompiler (L2: The Compiler)

Tests VDG v4.0 → Director Pack compilation logic.
"""
import pytest
from app.services.vdg_2pass.director_compiler import DirectorCompiler
from app.schemas.vdg_v4 import (
    VDGv4,
    SemanticPassResult,
    HookGenome,
    Microbeat,
    Scene,
    CapsuleBrief,
    MiseEnSceneSignal
)


@pytest.fixture
def sample_vdg() -> VDGv4:
    """Create a sample VDG for testing."""
    return VDGv4(
        content_id="test_video_001",
        platform="tiktok",
        duration_sec=15.0,
        semantic=SemanticPassResult(
            hook_genome=HookGenome(
                start_sec=0.0,
                end_sec=3.0,
                pattern="subversion",
                delivery="dialogue",
                strength=0.85,
                hook_summary="손님이 정중하게 질문하자 사장이 비꼬는 답변",
                microbeats=[
                    Microbeat(t=0.5, role="start", cue="audio", note="손님이 정중하게 질문"),
                    Microbeat(t=1.8, role="build", cue="audio", note="사장이 비꼬는 답변"),
                    Microbeat(t=2.5, role="punch", cue="audio", note="직접적인 욕설 투척")
                ]
            ),
            scenes=[
                Scene(
                    scene_id="S01",
                    time_start=0.0,
                    time_end=5.0,
                    duration_sec=5.0,
                    narrative_role="Hook",
                    summary="충격적인 시작"
                ),
                Scene(
                    scene_id="S02",
                    time_start=5.0,
                    time_end=10.0,
                    duration_sec=5.0,
                    narrative_role="Development",
                    summary="상황 전개"
                ),
                Scene(
                    scene_id="S03",
                    time_start=10.0,
                    time_end=15.0,
                    duration_sec=5.0,
                    narrative_role="Punchline",
                    summary="펀치라인"
                )
            ],
            capsule_brief=CapsuleBrief(
                hook_script="시작하자마자 충격적인 대사",
                do_not=["긴 인트로", "흐릿한 화면", "BGM 너무 크게"]
            )
        ),
        mise_en_scene_signals=[
            MiseEnSceneSignal(
                element="outfit_color",
                value="yellow",
                sentiment="positive",
                source_comment="노란 옷 미쳤다 ㅋㅋ",
                likes=1200
            ),
            MiseEnSceneSignal(
                element="background",
                value="cluttered",
                sentiment="negative",
                source_comment="배경 너무 지저분해",
                likes=300
            )
        ]
    )


class TestDirectorCompiler:
    """DirectorCompiler 테스트"""
    
    def test_compile_returns_director_pack(self, sample_vdg):
        """compile()이 DirectorPack을 반환하는지 확인"""
        pack = DirectorCompiler.compile(sample_vdg)
        
        assert pack is not None
        assert pack.pack_version == "1.0.2"
        assert pack.pattern_id == "test_video_001"
    
    def test_compile_generates_hook_timing_rule(self, sample_vdg):
        """훅 타이밍 규칙(hook_timing_2s)이 생성되는지 확인"""
        pack = DirectorCompiler.compile(sample_vdg)
        
        hook_timing_rules = [
            r for r in pack.dna_invariants
            if r.rule_id == "hook_timing_2s"
        ]
        
        assert len(hook_timing_rules) == 1
        rule = hook_timing_rules[0]
        assert rule.domain == "timing"
        assert rule.priority == "critical"
        assert rule.time_scope.t_window[0] == 0.0
        assert rule.coach_line_templates.strict is not None
    
    def test_compile_generates_hook_center_anchor_rule(self, sample_vdg):
        """훅 중앙 구도 규칙이 생성되는지 확인 (hook_strength > 0.6)"""
        pack = DirectorCompiler.compile(sample_vdg)
        
        center_rules = [
            r for r in pack.dna_invariants
            if r.rule_id == "hook_center_anchor"
        ]
        
        assert len(center_rules) == 1
        rule = center_rules[0]
        assert rule.domain == "composition"
        assert rule.priority == "critical"
    
    def test_compile_generates_scene_transition_rules(self, sample_vdg):
        """씬 전환 규칙이 생성되는지 확인"""
        pack = DirectorCompiler.compile(sample_vdg)
        
        scene_rules = [
            r for r in pack.dna_invariants
            if "scene_" in r.rule_id and "transition" in r.rule_id
        ]
        
        # S02, S03 전환 규칙 (S01은 제외)
        assert len(scene_rules) >= 1
    
    def test_compile_generates_mise_en_scene_rules(self, sample_vdg):
        """미장센 신호 기반 규칙이 생성되는지 확인"""
        pack = DirectorCompiler.compile(sample_vdg)
        
        mise_rules = [
            r for r in pack.dna_invariants
            if r.rule_id.startswith("mise_")
        ]
        
        # positive sentiment + likes > 300 인 것만
        assert len(mise_rules) >= 1
        assert any("outfit_color" in r.rule_id for r in mise_rules)
    
    def test_compile_generates_checkpoints(self, sample_vdg):
        """Checkpoint가 생성되는지 확인"""
        pack = DirectorCompiler.compile(sample_vdg)
        
        assert len(pack.checkpoints) >= 2
        
        # hook_punch checkpoint 확인
        hook_cps = [cp for cp in pack.checkpoints if cp.checkpoint_id == "hook_punch"]
        assert len(hook_cps) == 1
        assert len(hook_cps[0].active_rules) >= 1
    
    def test_compile_generates_mutation_slots(self, sample_vdg):
        """Mutation Slots가 생성되는지 확인"""
        pack = DirectorCompiler.compile(sample_vdg)
        
        assert len(pack.mutation_slots) >= 2
        
        # opening_tone slot 확인
        tone_slots = [s for s in pack.mutation_slots if s.slot_id == "opening_tone"]
        assert len(tone_slots) == 1
        assert "활기찬" in tone_slots[0].allowed_options
    
    def test_compile_generates_forbidden_mutations(self, sample_vdg):
        """Forbidden Mutations가 생성되는지 확인"""
        pack = DirectorCompiler.compile(sample_vdg)
        
        assert len(pack.forbidden_mutations) >= 3  # do_not에서 3개
        
        # do_not에서 생성된 것 확인
        forbid_reasons = [f.reason for f in pack.forbidden_mutations]
        assert "긴 인트로" in forbid_reasons
    
    def test_compile_policy_one_command_only(self, sample_vdg):
        """One-Command-Only 정책이 설정되는지 확인"""
        pack = DirectorCompiler.compile(sample_vdg)
        
        assert pack.policy.one_command_only is True
        assert pack.policy.cooldown_sec == 4.0
    
    def test_compile_with_weak_hook(self):
        """hook_strength가 낮을 때 hook_center_anchor가 생성되지 않음"""
        vdg = VDGv4(
            content_id="weak_hook",
            duration_sec=10.0,
            semantic=SemanticPassResult(
                hook_genome=HookGenome(
                    strength=0.4,  # Below 0.6 threshold
                    microbeats=[Microbeat(t=1.0, role="punch")]
                )
            )
        )
        
        pack = DirectorCompiler.compile(vdg)
        
        center_rules = [r for r in pack.dna_invariants if r.rule_id == "hook_center_anchor"]
        assert len(center_rules) == 0
    
    def test_compile_without_microbeats(self):
        """microbeats가 없을 때도 동작하는지 확인"""
        vdg = VDGv4(
            content_id="no_microbeats",
            duration_sec=10.0,
            semantic=SemanticPassResult(
                hook_genome=HookGenome(
                    strength=0.8,
                    microbeats=[]  # Empty
                )
            )
        )
        
        pack = DirectorCompiler.compile(vdg)
        
        # hook_timing_2s는 생성되지 않아야 함
        timing_rules = [r for r in pack.dna_invariants if r.rule_id == "hook_timing_2s"]
        assert len(timing_rules) == 0
        
        # hook_center_anchor는 생성되어야 함 (strength > 0.6)
        center_rules = [r for r in pack.dna_invariants if r.rule_id == "hook_center_anchor"]
        assert len(center_rules) == 1


class TestDirectorCompilerEdgeCases:
    """엣지 케이스 테스트"""
    
    def test_empty_vdg(self):
        """빈 VDG로도 Pack이 생성되는지 확인"""
        vdg = VDGv4(content_id="empty", duration_sec=0.0)
        pack = DirectorCompiler.compile(vdg)
        
        assert pack is not None
        assert pack.pattern_id == "empty"
        assert len(pack.mutation_slots) >= 2  # 기본 slots
    
    def test_no_do_not_list(self):
        """do_not이 없어도 동작하는지 확인"""
        vdg = VDGv4(
            content_id="no_donot",
            duration_sec=10.0,
            semantic=SemanticPassResult(
                capsule_brief=CapsuleBrief(do_not=[])
            )
        )
        
        pack = DirectorCompiler.compile(vdg)
        
        # forbidden_mutations는 빈 배열이거나 mise-en-scene에서만 생성
        assert pack.forbidden_mutations is not None


class TestContractCandidatesIntegration:
    """contract_candidates 통합 테스트"""
    
    def test_compile_with_contract_candidates(self):
        """contract_candidates가 있을 때 규칙이 추가되는지 확인"""
        from app.schemas.vdg_v4 import ContractCandidates
        
        vdg = VDGv4(
            content_id="with_candidates",
            duration_sec=15.0,
            contract_candidates=ContractCandidates(
                dna_invariants_candidates=[
                    {
                        "rule_id": "custom_rule_1",
                        "domain": "composition",
                        "priority": "high",
                        "t_window": [0.0, 5.0],
                        "spec": {
                            "metric_id": "custom.metric.v1",
                            "op": ">=",
                            "target": 0.8
                        },
                        "check_hint": "커스텀 규칙 테스트"
                    }
                ],
                mutation_slots_candidates=[
                    {
                        "slot_id": "custom_slot",
                        "slot_type": "props",
                        "guide": "커스텀 슬롯"
                    }
                ],
                forbidden_mutations_candidates=[
                    {
                        "mutation_id": "custom_forbid",
                        "reason": "커스텀 금지 항목"
                    }
                ],
                weights_candidates={
                    "custom_rule_1": 0.9
                }
            )
        )
        
        pack = DirectorCompiler.compile(vdg)
        
        # contract_candidates에서 추가된 규칙 확인
        custom_rules = [r for r in pack.dna_invariants if r.rule_id == "custom_rule_1"]
        assert len(custom_rules) == 1
        
        # mutation_slots에서 추가된 슬롯 확인
        custom_slots = [s for s in pack.mutation_slots if s.slot_id == "custom_slot"]
        assert len(custom_slots) == 1
        
        # forbidden_mutations에서 추가된 금지 확인
        custom_forbids = [f for f in pack.forbidden_mutations if f.mutation_id == "custom_forbid"]
        assert len(custom_forbids) == 1
        
        # scoring weights 확인
        assert pack.scoring.dna_weights.get("custom_rule_1") is not None
    
    def test_compile_dedupes_invariants(self):
        """중복 rule_id가 dedupe되는지 확인"""
        from app.schemas.vdg_v4 import ContractCandidates
        
        vdg = VDGv4(
            content_id="dedupe_test",
            duration_sec=15.0,
            semantic=SemanticPassResult(
                hook_genome=HookGenome(
                    strength=0.9,
                    microbeats=[Microbeat(t=1.5, role="punch")]
                )
            ),
            contract_candidates=ContractCandidates(
                dna_invariants_candidates=[
                    {
                        "rule_id": "hook_timing_2s",  # 중복!
                        "domain": "timing",
                        "priority": "medium",  # 낮은 우선순위
                        "spec": {"metric_id": "test.v1", "op": ">="}
                    }
                ]
            )
        )
        
        pack = DirectorCompiler.compile(vdg)
        
        # hook_timing_2s가 하나만 있어야 함
        hook_rules = [r for r in pack.dna_invariants if r.rule_id == "hook_timing_2s"]
        assert len(hook_rules) == 1
        
        # 높은 priority가 유지되어야 함 (critical)
        assert hook_rules[0].priority == "critical"


class TestCompileDirectorPackFunction:
    """compile_director_pack 함수 테스트"""
    
    def test_convenience_function_works(self):
        """compile_director_pack() 함수 동작 확인"""
        from app.services.vdg_2pass.director_compiler import compile_director_pack
        
        vdg = VDGv4(content_id="func_test", duration_sec=10.0)
        pack = compile_director_pack(vdg)
        
        assert pack is not None
        assert pack.pattern_id == "func_test"
    
    def test_convenience_function_with_pattern_id(self):
        """pattern_id 오버라이드 확인"""
        from app.services.vdg_2pass.director_compiler import compile_director_pack
        
        vdg = VDGv4(content_id="original_id", duration_sec=10.0)
        pack = compile_director_pack(vdg, pattern_id="custom_pattern")
        
        assert pack.pattern_id == "custom_pattern"
