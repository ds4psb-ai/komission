"""
Director Pack Compiler (L2: The Compiler)

Compiles VDG v4.0 analysis data into Director Pack for real-time coaching.

Blueprint Philosophy:
- VDG = Brain (SoR), Pack = Script (compressed rules)
- DNA Invariants = What to KEEP (불변 규칙)
- Mutation Slots = What can CHANGE (가변 영역)
- Policy = One-Command, Priority Queue

2-Pass Pipeline Integration:
- contract_candidates → dna_invariants
- capsule_brief.do_not → forbidden_mutations
- visual.analysis_results → metric-based rules
"""
from typing import List, Optional, Dict, Any
import logging
from app.schemas.vdg_v4 import VDGv4, Microbeat, ContractCandidates
from app.schemas.director_pack import (
    DirectorPack,
    DNAInvariant,
    MutationSlot,
    ForbiddenMutation,
    Checkpoint,
    Policy,
    PackMeta,
    RuntimeContract,
    TimeScope,
    RuleSpec,
    CoachLineTemplates,
    SourceRef,
    Scoring
)
import uuid

from app.utils.time import iso_now_z

logger = logging.getLogger(__name__)


class DirectorCompiler:
    """
    L2 Compiler: VDGv4 → DirectorPack
    
    Compresses VDG analysis data into executable coaching rules.
    
    Sources:
    1. Heuristic extraction from semantic/visual data
    2. contract_candidates from VDG Merger
    3. User persona preferences
    """
    
    # Coach line templates (Korean defaults)
    COACH_LINES = {
        "hook_timing": {
            "strict": "너무 늦어요! 시작하자마자 치고 나가세요.",
            "friendly": "조금 더 빨리 시작해볼까요~",
            "neutral": "훅 타이밍을 앞당겨주세요."
        },
        "center_composition": {
            "strict": "피사체를 중앙에 고정하세요!",
            "friendly": "중앙에 살짝 더 가까이~",
            "neutral": "구도를 중앙으로 조정하세요."
        },
        "scene_transition": {
            "strict": "장면 전환입니다. 준비하세요!",
            "friendly": "이제 다음 장면으로 넘어가요~",
            "neutral": "장면 전환 구간입니다."
        },
        "brightness": {
            "strict": "너무 어두워요! 조명을 확인하세요.",
            "friendly": "살짝 더 밝게 해볼까요?",
            "neutral": "조명을 조정해주세요."
        },
        "stability": {
            "strict": "흔들리지 마세요! 안정적으로!",
            "friendly": "조금 더 안정적으로 잡아볼까요?",
            "neutral": "카메라를 안정적으로 유지하세요."
        },
        "audio": {
            "strict": "소리가 안 들려요! 마이크 확인!",
            "friendly": "목소리가 작아요, 크게!",
            "neutral": "오디오 레벨을 확인하세요."
        }
    }
    
    # Domain to coach line mapping
    DOMAIN_COACH_MAPPING = {
        "timing": "hook_timing",
        "composition": "center_composition",
        "audio": "audio",
        "performance": "hook_timing",
        "safety": "stability"
    }
    
    @classmethod
    def _get_vdg_coach_message(cls, vdg: VDGv4, context: str = "hook") -> Optional[str]:
        """
        VDG capsule_brief에서 영상별 맞춤 코칭 메시지 추출
        
        Args:
            vdg: VDG v4 분석 결과
            context: "hook" | "shot" | "general"
        
        Returns:
            영상별 맞춤 메시지 또는 None (fallback 필요)
        """
        capsule = vdg.semantic.capsule_brief if vdg.semantic else None
        hook = vdg.semantic.hook_genome if vdg.semantic else None
        
        if context == "hook":
            # 1순위: hook_script (구체적 훅 가이드)
            if capsule and capsule.hook_script:
                msg = capsule.hook_script
                # 50자 제한 (실시간 코칭용)
                if len(msg) > 50:
                    msg = msg[:47] + "..."
                return msg
            
            # 2순위: hook_genome.hook_summary
            if hook and hook.hook_summary:
                msg = hook.hook_summary
                if len(msg) > 50:
                    msg = msg[:47] + "..."
                return msg
        
        elif context == "shot":
            # shotlist에서 첫 번째 샷 가이드 사용
            if capsule and capsule.shotlist:
                first_shot = capsule.shotlist[0] if capsule.shotlist else None
                if first_shot and isinstance(first_shot, dict):
                    return first_shot.get("guide", first_shot.get("description", ""))[:50]
        
        return None

    @classmethod
    def compile(
        cls,
        vdg: VDGv4,
        pattern_id: Optional[str] = None,
        pack_version: str = "1.0.2",
        persona_preset: Optional[str] = None
    ) -> DirectorPack:
        """
        Compile a VDGv4 analysis into a DirectorPack.
        
        Args:
            vdg: VDG v4.0 analysis result
            pattern_id: Override pattern ID (defaults to content_id)
            pack_version: Pack schema version
            persona_preset: Optional persona (활기찬/시니컬/진지한)
        
        Returns:
            DirectorPack ready for Gemini Live coaching
        """
        pack_id = str(uuid.uuid4())
        actual_pattern_id = pattern_id or vdg.content_id
        
        logger.info(f"🔧 Compiling DirectorPack for pattern: {actual_pattern_id}")
        
        try:
            # Phase 2: Track compiler warnings for operational debugging
            compiler_warnings: List[str] = []
            
            # H3 Hardening: contract_candidates is PRIMARY source
            # Heuristics are FALLBACK only when no candidates available
            
            # 1. Extract DNA Invariants - CONTRACT FIRST
            candidates = vdg.contract_candidates
            if candidates:
                invariants = cls._extract_from_contract_candidates(candidates)
                logger.info(f"   └─ Using contract_candidates as primary source")
            else:
                # Fallback to heuristic extraction if no candidates
                invariants = cls._extract_dna_invariants(vdg)
                logger.warning(f"   └─ No contract_candidates, using heuristic fallback")
                compiler_warnings.append("heuristic_fallback_used")
            
            # 2. Dedupe invariants by rule_id
            invariants = cls._dedupe_invariants(invariants)
            
            # H9: Minimum rules fallback (prevent silent director)
            if len(invariants) < 2:
                logger.warning(f"⚠️ Only {len(invariants)} invariant(s), adding fallback rules")
                invariants.extend(cls._get_fallback_invariants(vdg.duration_sec))
                invariants = cls._dedupe_invariants(invariants)
                compiler_warnings.append("fallback_invariants_used")
            
            logger.info(f"   └─ DNA Invariants: {len(invariants)}")
            
            # 3. Generate Mutation Slots - CONTRACT FIRST
            if candidates:
                slots = cls._extract_slots_from_contract_candidates(candidates)
            else:
                slots = cls._generate_mutation_slots(vdg, persona_preset)
            logger.info(f"   └─ Mutation Slots: {len(slots)}")
            
            # 4. Extract Forbidden Mutations - CONTRACT FIRST
            if candidates:
                forbidden = cls._extract_forbidden_from_contract_candidates(candidates)
            else:
                forbidden = cls._extract_forbidden_mutations(vdg)
            logger.info(f"   └─ Forbidden Mutations: {len(forbidden)}")
            
            # 5. Generate Checkpoints (always needs VDG duration info)
            checkpoints = cls._generate_checkpoints(vdg, invariants)
            logger.info(f"   └─ Checkpoints: {len(checkpoints)}")
            
            # 6. Calculate Scoring Weights
            scoring = cls._calculate_scoring(vdg, invariants)
            
            # 7. Build Pack
            pack = DirectorPack(
                pack_version=pack_version,
                pattern_id=actual_pattern_id,
                goal=f"VDG {actual_pattern_id} 기반 실시간 촬영 코칭",
                pack_meta=PackMeta(
                    pack_id=pack_id,
                    generated_at=iso_now_z(),
                    compiler_version=pack_version,
                    source_refs=[
                        SourceRef(
                            vdg_content_id=vdg.content_id,
                            vdg_version=vdg.vdg_version
                        )
                    ],
                    compiler_warnings=compiler_warnings  # Phase 2: Operational debugging
                ),
                runtime_contract=RuntimeContract(
                    input_modalities_expected=["video_1fps"],
                    verification_granularity="window",
                    max_instruction_words=10,
                    cooldown_sec_default=4.0
                ),
                scoring=scoring,
                dna_invariants=invariants,
                mutation_slots=slots,
                forbidden_mutations=forbidden,
                checkpoints=checkpoints,
                policy=Policy(
                    one_command_only=True,
                    cooldown_sec=4.0,
                    barge_in_handling="stop_and_ack",
                    uncertainty_policy="ask_user"
                )
            )
            
            logger.info(f"✅ DirectorPack compiled: {pack_id[:8]}...")
            return pack
            
        except Exception as e:
            logger.error(f"❌ DirectorCompiler failed: {e}")
            raise
    
    @classmethod
    def _extract_dna_invariants(cls, vdg: VDGv4) -> List[DNAInvariant]:
        """Extract DNA Invariants from VDG analysis (heuristic)."""
        invariants: List[DNAInvariant] = []
        hook = vdg.semantic.hook_genome
        
        # 1. Hook Timing Rule (Critical)
        if hook.microbeats:
            punch_beat = cls._find_microbeat(hook.microbeats, "punch")
            punch_time = punch_beat.t if punch_beat else hook.end_sec
            
            invariants.append(DNAInvariant(
                rule_id="hook_timing_2s",
                domain="timing",
                priority="critical",
                tolerance="tight",
                weight=1.0,
                time_scope=TimeScope(
                    t_window=[0.0, min(punch_time + 0.5, 3.0)],
                    relative_to="start"
                ),
                spec=RuleSpec(
                    metric_id="timing.hook_punch.v1",
                    op="<=",
                    target=2.0,
                    unit="sec",
                    required_inputs=["video_1fps"]
                ),
                check_hint="0~2초 내에 훅 펀치가 완성되어야 함",
                coach_line_templates=CoachLineTemplates(
                    strict=cls.COACH_LINES["hook_timing"]["strict"],
                    # VDG에서 영상별 맞춤 메시지 우선, 없으면 기본 메시지
                    friendly=cls._get_vdg_coach_message(vdg, "hook") or cls.COACH_LINES["hook_timing"]["friendly"],
                    neutral=cls.COACH_LINES["hook_timing"]["neutral"],
                    ko={
                        "strict": "너무 늦어요!",
                        "friendly": "더 빨리!",
                        "custom": cls._get_vdg_coach_message(vdg, "hook")  # 영상별 맞춤
                    }
                ),
                fallback="generic_tip"
            ))
        
        # 2. Hook Composition Rule (Critical)
        if hook.strength > 0.6:
            invariants.append(DNAInvariant(
                rule_id="hook_center_anchor",
                domain="composition",
                priority="critical",
                tolerance="normal",
                weight=0.9,
                time_scope=TimeScope(
                    t_window=[0.0, hook.end_sec],
                    relative_to="start"
                ),
                spec=RuleSpec(
                    metric_id="cmp.center_offset_xy.v1",
                    op="<=",
                    target=0.3,
                    aggregation="median",
                    required_inputs=["video_1fps"]
                ),
                check_hint=f"훅 구간({hook.end_sec}초) 피사체 중앙 유지",
                coach_line_templates=CoachLineTemplates(
                    strict=cls.COACH_LINES["center_composition"]["strict"],
                    friendly=cls.COACH_LINES["center_composition"]["friendly"],
                    neutral=cls.COACH_LINES["center_composition"]["neutral"]
                ),
                fallback="ask_user"
            ))
        
        # 3. Scene Transition Rules (High)
        for scene in vdg.semantic.scenes[1:]:  # Skip first scene
            if scene.time_start > hook.end_sec:
                invariants.append(DNAInvariant(
                    rule_id=f"scene_{scene.scene_id}_transition",
                    domain="composition",
                    priority="high",
                    tolerance="normal",
                    time_scope=TimeScope(
                        t_window=[scene.time_start - 0.5, scene.time_start + 1.0],
                        relative_to="start"
                    ),
                    spec=RuleSpec(
                        metric_id="cmp.stability_score.v1",
                        op=">=",
                        target=0.7,
                        required_inputs=["video_1fps"]
                    ),
                    check_hint=f"장면 전환 ({scene.time_start:.1f}초) 안정성 유지",
                    coach_line_templates=CoachLineTemplates(
                        strict=cls.COACH_LINES["scene_transition"]["strict"],
                        friendly=cls.COACH_LINES["scene_transition"]["friendly"],
                        neutral=cls.COACH_LINES["scene_transition"]["neutral"]
                    )
                ))
        
        # 4. Mise-en-Scene Signal Rules (Medium)
        for signal in vdg.mise_en_scene_signals:
            if signal.sentiment == "positive" and signal.likes > 300:
                safe_value = signal.value[:10].replace(" ", "_")
                invariants.append(DNAInvariant(
                    rule_id=f"mise_{signal.element}_{safe_value}",
                    domain="composition",
                    priority="medium",
                    time_scope=TimeScope(
                        t_window=[0.0, vdg.duration_sec or 60.0],
                        relative_to="start"
                    ),
                    spec=RuleSpec(
                        metric_id=f"mise.{signal.element}.v1",
                        op="exists",
                        required_inputs=["video_1fps"]
                    ),
                    check_hint=f"{signal.element}: {signal.value} 유지 (댓글 반응 좋음)",
                    coach_line_templates=CoachLineTemplates(
                        friendly=f"{signal.element}을(를) 유지해주세요~",
                        neutral=f"{signal.element} 요소 확인"
                    ),
                    evidence_refs=[f"comment_{signal.likes}"]
                ))
        
        # 5. Visual Pass Based Rules (from analysis_results)
        invariants.extend(cls._extract_from_visual_pass(vdg))
        
        return invariants
    
    @classmethod
    def _extract_from_visual_pass(cls, vdg: VDGv4) -> List[DNAInvariant]:
        """Extract rules from Visual Pass analysis results."""
        invariants: List[DNAInvariant] = []
        
        if not vdg.visual or not vdg.visual.analysis_results:
            return invariants
        
        for ap_id, result in vdg.visual.analysis_results.items():
            # Look for low stability scores
            if "cmp.stability_score.v1" in result.metrics:
                metric = result.metrics["cmp.stability_score.v1"]
                if metric.aggregated_value and metric.aggregated_value < 0.5:
                    # This point has stability issues - create a rule
                    invariants.append(DNAInvariant(
                        rule_id=f"stability_{ap_id}",
                        domain="composition",
                        priority="high",
                        time_scope=TimeScope(
                            t_window=[0.0, vdg.duration_sec or 60.0],
                            relative_to="start"
                        ),
                        spec=RuleSpec(
                            metric_id="cmp.stability_score.v1",
                            op=">=",
                            target=0.7,
                            required_inputs=["video_1fps"]
                        ),
                        check_hint=f"{ap_id} 구간 안정성 개선 필요",
                        coach_line_templates=CoachLineTemplates(
                            strict=cls.COACH_LINES["stability"]["strict"],
                            friendly=cls.COACH_LINES["stability"]["friendly"],
                            neutral=cls.COACH_LINES["stability"]["neutral"]
                        )
                    ))
        
        return invariants
    
    @classmethod
    def _extract_from_contract_candidates(
        cls,
        candidates: ContractCandidates
    ) -> List[DNAInvariant]:
        """Convert contract_candidates.dna_invariants_candidates to DNAInvariant."""
        invariants: List[DNAInvariant] = []
        
        if not candidates or not candidates.dna_invariants_candidates:
            return invariants
        
        for i, candidate in enumerate(candidates.dna_invariants_candidates):
            try:
                # Convert dict to DNAInvariant
                rule_id = candidate.get("rule_id", f"candidate_{i}")
                domain = candidate.get("domain", "composition")
                priority = candidate.get("priority", "medium")
                
                # Ensure valid domain
                if domain not in ["composition", "timing", "audio", "performance", "text", "safety"]:
                    domain = "composition"
                
                # Ensure valid priority
                if priority not in ["critical", "high", "medium", "low"]:
                    priority = "medium"
                
                # Build TimeScope
                t_window = candidate.get("t_window", [0.0, 60.0])
                time_scope = TimeScope(
                    t_window=t_window,
                    relative_to=candidate.get("relative_to", "start")
                )
                
                # Build RuleSpec with Phase 4 metric validation
                spec_data = candidate.get("spec", {})
                raw_metric_id = spec_data.get("metric_id", f"candidate.{rule_id}.v1")
                
                # Phase 4: Validate metric_id against registry
                from app.schemas.metric_registry import validate_metric_id
                validated_metric_id = validate_metric_id(raw_metric_id)
                
                spec = RuleSpec(
                    metric_id=validated_metric_id,  # Validated/normalized
                    op=spec_data.get("op", ">="),
                    target=spec_data.get("target"),
                    range=spec_data.get("range"),
                    required_inputs=spec_data.get("required_inputs", ["video_1fps"])
                )
                
                # Get coach lines
                coach_key = cls.DOMAIN_COACH_MAPPING.get(domain, "center_composition")
                coach_lines = cls.COACH_LINES.get(coach_key, cls.COACH_LINES["center_composition"])
                
                invariants.append(DNAInvariant(
                    rule_id=rule_id,
                    domain=domain,
                    priority=priority,
                    time_scope=time_scope,
                    spec=spec,
                    check_hint=candidate.get("check_hint", f"Contract candidate rule: {rule_id}"),
                    coach_line_templates=CoachLineTemplates(
                        strict=candidate.get("coach_strict", coach_lines["strict"]),
                        friendly=candidate.get("coach_friendly", coach_lines["friendly"]),
                        neutral=candidate.get("coach_neutral", coach_lines.get("neutral"))
                    ),
                    weight=candidates.weights_candidates.get(rule_id, 0.5),
                    tolerance=candidate.get("tolerance", "normal"),
                    evidence_refs=candidate.get("evidence_refs", [])
                ))
                
            except Exception as e:
                logger.warning(f"Failed to convert contract candidate {i}: {e}")
                continue
        
        return invariants
    
    @classmethod
    def _get_fallback_invariants(cls, duration_sec: float = 60.0) -> List[DNAInvariant]:
        """
        H9: Fallback rules when invariants < 2 (prevent silent director).
        
        Generic rules that apply to most short-form content:
        1. Hook timing (first 2 seconds)
        2. Center composition
        3. Brightness check
        """
        return [
            DNAInvariant(
                rule_id="fallback_hook_timing",
                domain="timing",
                priority="critical",
                tolerance="normal",
                time_scope=TimeScope(t_window=[0.0, 3.0], relative_to="start"),
                spec=RuleSpec(
                    metric_id="timing.hook_punch.v1",
                    op="<=",
                    target=2.0,
                    unit="sec"
                ),
                check_hint="처음 2초 안에 시선을 잡으세요",
                coach_line_templates=CoachLineTemplates(
                    strict="시작이 늦어요! 바로 치고 나가세요!",
                    friendly="조금 더 빨리 시작해볼까요~",
                    neutral="훅 타이밍을 앞당겨주세요."
                ),
                fallback="generic_tip"
            ),
            DNAInvariant(
                rule_id="fallback_center_composition",
                domain="composition",
                priority="high",
                tolerance="normal",
                time_scope=TimeScope(t_window=[0.0, min(duration_sec, 10.0)], relative_to="start"),
                spec=RuleSpec(
                    metric_id="cmp.center_offset_xy.v1",
                    op="<=",
                    target=0.3,
                    aggregation="median"
                ),
                check_hint="주 피사체를 중앙에 배치하세요",
                coach_line_templates=CoachLineTemplates(
                    strict="중앙에 고정하세요!",
                    friendly="조금 더 가운데로~",
                    neutral="구도를 중앙으로 조정하세요."
                ),
                fallback="ask_user"
            ),
            DNAInvariant(
                rule_id="fallback_brightness",
                domain="composition",
                priority="medium",
                tolerance="loose",
                time_scope=TimeScope(t_window=[0.0, duration_sec], relative_to="start"),
                spec=RuleSpec(
                    metric_id="lit.brightness_ratio.v1",
                    op=">=",
                    target=0.7
                ),
                check_hint="조명이 충분한지 확인하세요",
                coach_line_templates=CoachLineTemplates(
                    strict="너무 어두워요! 조명 확인!",
                    friendly="살짝 더 밝게 해볼까요?",
                    neutral="조명을 조정해주세요."
                ),
                fallback="generic_tip"
            )
        ]
    
    @classmethod
    def _extract_slots_from_contract_candidates(
        cls,
        candidates: ContractCandidates
    ) -> List[MutationSlot]:
        """Convert contract_candidates.mutation_slots_candidates to MutationSlot."""
        slots: List[MutationSlot] = []
        
        if not candidates or not candidates.mutation_slots_candidates:
            return slots
        
        for i, candidate in enumerate(candidates.mutation_slots_candidates):
            try:
                slot_type = candidate.get("slot_type", "other")
                if slot_type not in ["persona_tone", "setting", "props", "script_style",
                                     "reaction_intensity", "camera_distance", "wardrobe", "other"]:
                    slot_type = "other"
                
                slots.append(MutationSlot(
                    slot_id=candidate.get("slot_id", f"candidate_slot_{i}"),
                    slot_type=slot_type,
                    guide=candidate.get("guide", ""),
                    allowed_options=candidate.get("allowed_options", []),
                    coach_line_templates=candidate.get("coach_line_templates", {})
                ))
            except Exception as e:
                logger.warning(f"Failed to convert mutation slot candidate {i}: {e}")
                continue
        
        return slots
    
    @classmethod
    def _extract_forbidden_from_contract_candidates(
        cls,
        candidates: ContractCandidates
    ) -> List[ForbiddenMutation]:
        """Convert contract_candidates.forbidden_mutations_candidates to ForbiddenMutation."""
        forbidden: List[ForbiddenMutation] = []
        
        if not candidates or not candidates.forbidden_mutations_candidates:
            return forbidden
        
        for i, candidate in enumerate(candidates.forbidden_mutations_candidates):
            try:
                severity = candidate.get("severity", "medium")
                if severity not in ["critical", "high", "medium", "low"]:
                    severity = "medium"
                
                forbidden.append(ForbiddenMutation(
                    mutation_id=candidate.get("mutation_id", f"candidate_forbid_{i}"),
                    reason=candidate.get("reason", "From contract candidates"),
                    severity=severity,
                    evidence_refs=candidate.get("evidence_refs", [])
                ))
            except Exception as e:
                logger.warning(f"Failed to convert forbidden candidate {i}: {e}")
                continue
        
        return forbidden
    
    @classmethod
    def _dedupe_invariants(cls, invariants: List[DNAInvariant]) -> List[DNAInvariant]:
        """Dedupe invariants by rule_id, keeping highest priority."""
        seen: Dict[str, DNAInvariant] = {}
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        
        for inv in invariants:
            if inv.rule_id not in seen:
                seen[inv.rule_id] = inv
            else:
                # Keep higher priority
                existing = seen[inv.rule_id]
                if priority_order.get(inv.priority, 4) < priority_order.get(existing.priority, 4):
                    seen[inv.rule_id] = inv
        
        return list(seen.values())
    
    @classmethod
    def _generate_mutation_slots(
        cls,
        vdg: VDGv4,
        persona_preset: Optional[str]
    ) -> List[MutationSlot]:
        """Generate Mutation Slots for variable elements."""
        slots: List[MutationSlot] = []
        
        # 1. Persona Tone Slot
        slots.append(MutationSlot(
            slot_id="opening_tone",
            slot_type="persona_tone",
            guide="시작 톤을 자신의 스타일에 맞게 조절",
            allowed_options=["활기찬", "시니컬", "진지한 전문가", "친구 같은"],
            coach_line_templates={
                "활기찬": "에너지를 더 올려보세요!",
                "시니컬": "억지로 웃지 마세요. 평소처럼.",
                "진지한 전문가": "차분하게 전문성을 보여주세요.",
                "친구 같은": "편하게 말해주세요~"
            }
        ))
        
        # 2. Setting/Location Slot
        slots.append(MutationSlot(
            slot_id="shooting_location",
            slot_type="setting",
            guide="촬영 장소는 변경 가능",
            allowed_options=["집", "야외", "사무실", "스튜디오"],
            coach_line_templates={
                "집": "배경 정리 확인!",
                "야외": "조명과 소음 주의!",
                "사무실": "깔끔하게!",
                "스튜디오": "조명 완벽!"
            }
        ))
        
        # 3. Camera Distance Slot
        slots.append(MutationSlot(
            slot_id="camera_distance",
            slot_type="camera_distance",
            guide="카메라 거리는 조절 가능",
            allowed_options=["클로즈업", "미디엄", "와이드"],
            coach_line_templates={
                "클로즈업": "더 가까이!",
                "미디엄": "적당한 거리!",
                "와이드": "전체 보여주세요!"
            }
        ))
        
        # 4. Props Slot (from mise-en-scene)
        props_signals = [s for s in vdg.mise_en_scene_signals if s.element == "props"]
        if props_signals:
            slots.append(MutationSlot(
                slot_id="prop_usage",
                slot_type="props",
                guide="소품은 원본과 다르게 사용 가능",
                allowed_options=[s.value for s in props_signals[:5]],
                coach_line_templates={
                    "default": "소품을 더 잘 보이게 들어주세요!"
                }
            ))
        
        return slots
    
    @classmethod
    def _extract_forbidden_mutations(cls, vdg: VDGv4) -> List[ForbiddenMutation]:
        """Extract forbidden mutations from VDG."""
        forbidden: List[ForbiddenMutation] = []
        
        capsule = vdg.semantic.capsule_brief
        if capsule and capsule.do_not:
            for i, donot in enumerate(capsule.do_not):
                forbidden.append(ForbiddenMutation(
                    mutation_id=f"forbid_{i}",
                    reason=donot,
                    severity="high"
                ))
        
        # Auto-generate from negative mise-en-scene signals
        for signal in vdg.mise_en_scene_signals:
            if signal.sentiment == "negative" and signal.likes > 200:
                comment_preview = signal.source_comment[:50] if signal.source_comment else ""
                forbidden.append(ForbiddenMutation(
                    mutation_id=f"forbid_mise_{signal.element}",
                    reason=f"{signal.element}: {signal.value} 피해야 함 ({comment_preview})",
                    severity="medium",
                    evidence_refs=[f"comment_{signal.likes}"]
                ))
        
        return forbidden
    
    @classmethod
    def _generate_checkpoints(
        cls,
        vdg: VDGv4,
        invariants: List[DNAInvariant]
    ) -> List[Checkpoint]:
        """Generate time-based checkpoints for rule activation."""
        checkpoints: List[Checkpoint] = []
        hook = vdg.semantic.hook_genome
        duration = vdg.duration_sec or 60.0
        
        # 1. Hook Punch Checkpoint (Critical rules only)
        hook_rules = [r.rule_id for r in invariants if r.priority == "critical"]
        if hook_rules:
            checkpoints.append(Checkpoint(
                checkpoint_id="hook_punch",
                t_window=[0.0, hook.end_sec],
                active_rules=hook_rules,
                note="훅 펀치 구간 - Critical 규칙 활성화"
            ))
        
        # 2. Scene Transition Checkpoints
        for scene in vdg.semantic.scenes[1:]:
            scene_rules = [
                r.rule_id for r in invariants
                if f"scene_{scene.scene_id}" in r.rule_id
            ]
            if scene_rules:
                checkpoints.append(Checkpoint(
                    checkpoint_id=f"scene_{scene.scene_id}",
                    t_window=[scene.time_start - 0.5, scene.time_end],
                    active_rules=scene_rules,
                    note=f"씬 {scene.scene_id} ({scene.narrative_role or 'transition'})"
                ))
        
        # 3. Mid-video Checkpoint (High priority rules)
        high_rules = [r.rule_id for r in invariants if r.priority in ["critical", "high"]]
        if high_rules and duration > 5:
            checkpoints.append(Checkpoint(
                checkpoint_id="mid_video",
                t_window=[duration * 0.3, duration * 0.7],
                active_rules=high_rules,
                note="중반부 - Critical/High 규칙 활성화"
            ))
        
        # 4. Overall Checkpoint (all rules active)
        all_rule_ids = [r.rule_id for r in invariants]
        checkpoints.append(Checkpoint(
            checkpoint_id="overall",
            t_window=[0.0, duration],
            active_rules=all_rule_ids,
            note="전체 구간"
        ))
        
        return checkpoints
    
    @classmethod
    def _calculate_scoring(
        cls,
        vdg: VDGv4,
        invariants: List[DNAInvariant]
    ) -> Scoring:
        """Calculate scoring weights based on VDG analysis."""
        dna_weights: Dict[str, float] = {}
        
        # Base weights from invariants
        for inv in invariants:
            weight = inv.weight if inv.weight else 0.5
            if inv.priority == "critical":
                weight = max(weight, 0.9)
            elif inv.priority == "high":
                weight = max(weight, 0.7)
            dna_weights[inv.rule_id] = weight
        
        # Merge with contract_candidates weights
        if vdg.contract_candidates and vdg.contract_candidates.weights_candidates:
            for rule_id, weight in vdg.contract_candidates.weights_candidates.items():
                if rule_id in dna_weights:
                    # Average with existing
                    dna_weights[rule_id] = (dna_weights[rule_id] + weight) / 2
                else:
                    dna_weights[rule_id] = weight
        
        return Scoring(
            dna_weights=dna_weights,
            risk_penalty_rules=[
                {"trigger": "safety_violation", "penalty": -0.5},
                {"trigger": "audio_missing", "penalty": -0.3}
            ]
        )
    
    @staticmethod
    def _find_microbeat(beats: List[Microbeat], role: str) -> Optional[Microbeat]:
        """Find first microbeat with given role."""
        for beat in beats:
            if beat.role == role:
                return beat
        return None


# Convenience function for direct usage
def compile_director_pack(
    vdg: VDGv4,
    pattern_id: Optional[str] = None
) -> DirectorPack:
    """
    Compile VDG v4.0 → Director Pack
    
    Convenience wrapper for DirectorCompiler.compile()
    
    Args:
        vdg: VDG v4.0 analysis result
        pattern_id: Override pattern ID
    
    Returns:
        DirectorPack for real-time coaching
    """
    return DirectorCompiler.compile(vdg, pattern_id=pattern_id)
