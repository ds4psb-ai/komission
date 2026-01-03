"use client";
import { useTranslations } from 'next-intl';

import { memo } from "react";
import {
    Zap, Eye, Music, Brain, Heart, Laugh, MessageCircle,
    AlertTriangle, ArrowRight, Wrench, MapPin, Users, Sparkles
} from "lucide-react";
import { cn } from "@/lib/utils";

// ==================== TYPES ====================
interface DopamineRadar {
    visual_spectacle?: number;
    audio_stimulation?: number;
    narrative_intrigue?: number;
    emotional_resonance?: number;
    comedy_shock?: number;
}

interface IronyAnalysis {
    setup?: string;
    twist?: string;
    gap_type?: string;
}

interface ProductionConstraints {
    min_actors?: number;
    locations?: string[];
    props?: string[];
    difficulty?: string;
    primary_challenge?: string;
}

interface HookGenome {
    pattern?: string;
    delivery?: string;
    strength?: number;
    hook_summary?: string;
}

interface IntentLayer {
    hook_trigger?: string;
    irony_analysis?: IronyAnalysis;
    dopamine_radar?: DopamineRadar;
}

interface CapsuleBrief {
    constraints?: ProductionConstraints;
}

interface BestComment {
    text: string;
    likes: number;
    author?: string;
    lang?: string;
}

export interface VDGData {
    title?: string;
    summary?: string;
    hook_genome?: HookGenome;
    intent_layer?: IntentLayer;
    capsule_brief?: CapsuleBrief;
    best_comments?: BestComment[];
}

// ==================== KOREAN TRANSLATIONS ====================

const HOOK_PATTERN_KO: Record<string, { name: string; desc: string; emoji: string }> = {
    pattern_break: { name: "패턴 브레이크", desc: "예상을 깨는 반전으로 시선 고정", emoji: "⚡" },
    visual_reaction: { name: "시각적 리액션", desc: "표정/행동 변화로 감정 전달", emoji: "😲" },
    transformation: { name: "변신/트랜스폼", desc: "Before→After로 호기심 유발", emoji: "✨" },
    reveal: { name: "공개/리빌", desc: "숨겨진 것을 드러내며 긴장감 조성", emoji: "🎁" },
    unboxing: { name: "언박싱", desc: "개봉 과정의 설렘과 기대감 활용", emoji: "📦" },
    challenge: { name: "챌린지", desc: "참여 욕구와 경쟁심 자극", emoji: "🏆" },
    question: { name: "질문 유도", desc: "궁금증을 유발하여 끝까지 시청", emoji: "❓" },
    comparison: { name: "비교", desc: "대조를 통한 차이점 강조", emoji: "⚖️" },
    countdown: { name: "카운트다운", desc: "긴장감과 기대감 동시 유발", emoji: "⏱️" },
    action: { name: "액션", desc: "역동적인 움직임으로 몰입 유도", emoji: "🎬" },
    setup: { name: "셋업", desc: "상황 설정으로 맥락 전달", emoji: "🎭" },
    shock: { name: "충격", desc: "예상치 못한 장면으로 집중력 극대화", emoji: "💥" },
};

const IRONY_GAP_KO: Record<string, string> = {
    expectation_reality: "기대 vs 현실",
    visual_audio: "시각 vs 청각",
    setup_punchline: "설정 vs 반전",
    effort_result: "노력 vs 결과",
    appearance_reality: "겉모습 vs 실제",
};

const DIFFICULTY_KO: Record<string, string> = {
    Easy: "쉬움",
    Medium: "보통",
    Hard: "어려움",
};

// ==================== SUB-COMPONENTS ====================

const DopamineBar = memo(({
    icon: Icon,
    label,
    value,
    color
}: {
    icon: React.ElementType;
    label: string;
    value: number;
    color: string;
}) => (
    <div className="flex items-center gap-2 text-xs">
        <Icon className={cn("w-3.5 h-3.5", color)} />
        <span className="w-14 text-white/50">{label}</span>
        <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
            <div
                className={cn("h-full rounded-full transition-all", color.replace("text-", "bg-"))}
                style={{ width: `${value * 10}%` }}
            />
        </div>
        <span className="w-4 text-right text-white/60">{value}</span>
    </div>
));
DopamineBar.displayName = "DopamineBar";

const HookPatternSection = memo(({ hook }: { hook: HookGenome }) => {
    const patternKey = hook.pattern?.toLowerCase().replace(/\s+/g, "_") || "";
    const patternInfo = HOOK_PATTERN_KO[patternKey] || {
        name: hook.pattern || "알 수 없음",
        desc: "훅 패턴 분석 중...",
        emoji: "🎣"
    };
    const strengthPercent = (hook.strength || 0) * 100;

    return (
        <div className="space-y-3 p-4 bg-gradient-to-br from-violet-900/30 to-purple-900/20 rounded-xl border border-violet-500/30">
            <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                    <span className="text-2xl">{patternInfo.emoji}</span>
                    <div>
                        <div className="font-bold text-white text-sm">{patternInfo.name}</div>
                        <div className="text-[10px] text-white/40 uppercase">{hook.pattern}</div>
                    </div>
                </div>
                <div className="text-right">
                    <div className="text-lg font-black text-violet-300">{strengthPercent.toFixed(0)}%</div>
                    <div className="text-[10px] text-white/40">훅 강도</div>
                </div>
            </div>

            <div className="text-xs text-white/70 leading-relaxed">
                💡 <span className="text-violet-200">{patternInfo.desc}</span>
            </div>

            {hook.hook_summary && (
                <div className="p-3 bg-black/20 rounded-lg border border-white/5">
                    <div className="text-[10px] text-white/40 mb-1">이 영상의 훅</div>
                    <p className="text-xs text-white/80 leading-relaxed">{hook.hook_summary}</p>
                </div>
            )}

            {/* Strength Bar */}
            <div className="space-y-1">
                <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-gradient-to-r from-violet-500 to-purple-400 rounded-full transition-all"
                        style={{ width: `${strengthPercent}%` }}
                    />
                </div>
                <div className="flex justify-between text-[10px] text-white/30">
                    <span>약함</span>
                    <span>강함</span>
                </div>
            </div>
        </div>
    );
});
HookPatternSection.displayName = "HookPatternSection";

const IronyGapSection = memo(({ irony }: { irony: IronyAnalysis }) => {
    const gapType = irony.gap_type?.toLowerCase().replace(/\s+/g, "_") || "";
    const gapLabel = IRONY_GAP_KO[gapType] || irony.gap_type || "아이러니";

    return (
        <div className="space-y-2 p-3 bg-amber-500/10 rounded-lg border border-amber-500/20">
            <div className="flex items-center gap-2 text-xs text-amber-400 font-medium">
                <AlertTriangle className="w-3.5 h-3.5" />
                아이러니 갭: {gapLabel}
            </div>
            <div className="flex items-center gap-2 text-xs">
                <div className="flex-1 p-2 bg-white/5 rounded text-white/70 text-[11px] line-clamp-2">
                    <span className="text-white/40">설정:</span> {irony.setup || "N/A"}
                </div>
                <ArrowRight className="w-4 h-4 text-amber-400 flex-shrink-0" />
                <div className="flex-1 p-2 bg-amber-500/10 rounded text-amber-200 text-[11px] line-clamp-2">
                    <span className="text-amber-400/60">반전:</span> {irony.twist || "N/A"}
                </div>
            </div>
        </div>
    );
});
IronyGapSection.displayName = "IronyGapSection";

const BestCommentsSection = memo(({ comments }: { comments: BestComment[] }) => {
    if (!comments || comments.length === 0) return null;

    const topComments = comments.slice(0, 3);

    return (
        <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs text-cyan-400 font-medium">
                <MessageCircle className="w-3.5 h-3.5" />
                <span>시청자 반응 (바이럴 인사이트)</span>
                <span className="text-[10px] text-white/30">TOP {topComments.length}</span>
            </div>
            <div className="space-y-2">
                {topComments.map((comment, idx) => (
                    <div
                        key={idx}
                        className="p-3 bg-white/5 rounded-lg border border-white/10 hover:border-cyan-500/30 transition-colors"
                    >
                        <p className="text-xs text-white/80 leading-relaxed line-clamp-2">
                            &ldquo;{comment.text}&rdquo;
                        </p>
                        <div className="flex items-center gap-2 mt-2 text-[10px] text-white/40">
                            <span>❤️ {comment.likes >= 1000 ? `${(comment.likes / 1000).toFixed(1)}K` : comment.likes}</span>
                            {comment.author && <span>@{comment.author}</span>}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
});
BestCommentsSection.displayName = "BestCommentsSection";

const ConstraintsSection = memo(({ constraints }: { constraints: ProductionConstraints }) => (
    <div className="grid grid-cols-2 gap-2 text-[11px]">
        <div className="flex items-center gap-2 text-white/60">
            <Users className="w-3.5 h-3.5 text-cyan-400" />
            <span>{constraints.min_actors}명 이상</span>
        </div>
        <div className="flex items-center gap-2 text-white/60">
            <Zap className="w-3.5 h-3.5 text-yellow-400" />
            <span className={cn(
                constraints.difficulty === "Easy" && "text-green-400",
                constraints.difficulty === "Medium" && "text-yellow-400",
                constraints.difficulty === "Hard" && "text-red-400"
            )}>
                {DIFFICULTY_KO[constraints.difficulty || ""] || constraints.difficulty}
            </span>
        </div>
        {constraints.locations && constraints.locations.length > 0 && (
            <div className="flex items-center gap-2 text-white/60 col-span-2">
                <MapPin className="w-3.5 h-3.5 text-purple-400" />
                <span>{constraints.locations.join(", ")}</span>
            </div>
        )}
        {constraints.props && constraints.props.length > 0 && (
            <div className="flex items-center gap-2 text-white/60 col-span-2">
                <Wrench className="w-3.5 h-3.5 text-orange-400" />
                <span>{constraints.props.join(", ")}</span>
            </div>
        )}
    </div>
));
ConstraintsSection.displayName = "ConstraintsSection";

// ==================== MAIN COMPONENT ====================

export const VDGCard = memo(({ vdg, className }: { vdg: VDGData; className?: string }) => {
    const hook = vdg.hook_genome;
    const intent = vdg.intent_layer;
    const dopamine = intent?.dopamine_radar;
    const irony = intent?.irony_analysis;
    const constraints = vdg.capsule_brief?.constraints;
    const bestComments = vdg.best_comments;

    if (!vdg) return null;

    return (
        <div className={cn(
            "glass-panel rounded-xl border border-cyan-500/30 overflow-hidden",
            "bg-gradient-to-br from-slate-900/95 to-slate-950/95 backdrop-blur-xl",
            "shadow-[0_0_40px_rgba(6,182,212,0.1)]",
            className
        )}>
            {/* Header */}
            <div className="px-4 py-3 border-b border-cyan-500/20 bg-gradient-to-r from-cyan-900/30 to-transparent">
                <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-cyan-400" />
                    <span className="text-xs font-bold tracking-wider text-white/80">
                        🧬 바이럴 DNA 분석
                    </span>
                </div>
            </div>

            {/* Content */}
            <div className="p-4 space-y-4">
                {/* Hook Pattern - Primary Focus */}
                {hook && hook.pattern && (
                    <HookPatternSection hook={hook} />
                )}

                {/* Best Comments - Viral Insights */}
                {bestComments && bestComments.length > 0 && (
                    <BestCommentsSection comments={bestComments} />
                )}

                {/* Dopamine Radar */}
                {dopamine && (
                    <div className="space-y-2">
                        <div className="text-[10px] text-white/40 uppercase tracking-wider flex items-center gap-1.5">
                            <Brain className="w-3 h-3" />
                            도파민 레이더
                        </div>
                        <div className="space-y-1.5">
                            <DopamineBar icon={Eye} label="시각 자극" value={dopamine.visual_spectacle ?? 0} color="text-purple-400" />
                            <DopamineBar icon={Music} label="청각 자극" value={dopamine.audio_stimulation ?? 0} color="text-blue-400" />
                            <DopamineBar icon={Brain} label="스토리" value={dopamine.narrative_intrigue ?? 0} color="text-green-400" />
                            <DopamineBar icon={Heart} label="감정" value={dopamine.emotional_resonance ?? 0} color="text-pink-400" />
                            <DopamineBar icon={Laugh} label="유머" value={dopamine.comedy_shock ?? 0} color="text-yellow-400" />
                        </div>
                    </div>
                )}

                {/* Irony Gap */}
                {irony && irony.gap_type !== "none" && (
                    <IronyGapSection irony={irony} />
                )}

                {/* Production Constraints */}
                {constraints && (
                    <div className="space-y-2">
                        <div className="text-[10px] text-white/40 uppercase tracking-wider flex items-center gap-1.5">
                            <Wrench className="w-3 h-3" />
                            복제 가이드
                        </div>
                        <ConstraintsSection constraints={constraints} />
                        {constraints.primary_challenge && (
                            <div className="text-[10px] text-orange-300/80 mt-2">
                                ⚠️ {constraints.primary_challenge}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
});

VDGCard.displayName = "VDGCard";

export default VDGCard;
