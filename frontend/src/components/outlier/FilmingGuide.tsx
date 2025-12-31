'use client';

/**
 * FilmingGuide - VDG-based filming guide component
 * 
 * Shows 3-step filming guide based on VDG hook_genome.pattern
 * - If VDG analysis complete: Shows pattern-specific steps
 * - If pending: Shows empty/waiting state
 */

import { Lightbulb, Zap } from 'lucide-react';

// VDG Data types (subset of VDGCard types)
interface HookGenome {
    pattern?: string;
    delivery?: string;
    strength?: number;
    hook_summary?: string;
}

interface VDGData {
    hook_genome?: HookGenome;
    summary?: string;
    [key: string]: unknown;
}

interface FilmingGuideProps {
    vdgAnalysis?: VDGData | null;
    analysisStatus?: 'pending' | 'promoted' | 'approved' | 'analyzing' | 'completed' | 'skipped' | 'comments_pending_review' | 'comments_failed' | 'comments_ready';
    compact?: boolean;
    className?: string;
}

// Hook pattern guide configurations (from QuickGuide.tsx)
const HOOK_PATTERN_GUIDE: Record<string, { steps: { title: string; desc: string; color: string }[] }> = {
    pattern_break: {
        steps: [
            { title: "예상 설정", desc: "시청자가 예상하는 상황 연출", color: "violet" },
            { title: "반전 순간", desc: "예상을 깨는 충격적 전환", color: "pink" },
            { title: "리액션", desc: "반전 후 감정 표현으로 마무리", color: "orange" },
        ],
    },
    visual_reaction: {
        steps: [
            { title: "자극 제시", desc: "반응할 대상/상황을 보여주기", color: "violet" },
            { title: "표정 연기", desc: "과장된 리액션으로 감정 전달", color: "pink" },
            { title: "공감 유도", desc: "시청자도 같은 감정 느끼게", color: "orange" },
        ],
    },
    transformation: {
        steps: [
            { title: "Before", desc: "변화 전 상태 강조", color: "violet" },
            { title: "과정/전환", desc: "변화 과정 드라마틱하게", color: "pink" },
            { title: "After", desc: "극적인 결과 공개", color: "orange" },
        ],
    },
    reveal: {
        steps: [
            { title: "티저", desc: "숨겨진 것에 대한 궁금증 유발", color: "violet" },
            { title: "빌드업", desc: "기대감 고조시키기", color: "pink" },
            { title: "공개", desc: "드라마틱하게 드러내기", color: "orange" },
        ],
    },
    challenge: {
        steps: [
            { title: "규칙 설명", desc: "챌린지 룰을 명확히", color: "violet" },
            { title: "도전", desc: "직접 시도하는 모습", color: "pink" },
            { title: "결과", desc: "성공/실패 결과와 리액션", color: "orange" },
        ],
    },
    default: {
        steps: [
            { title: "훅 시작", desc: "첫 3초 안에 시선을 사로잡으세요", color: "violet" },
            { title: "핵심 전달", desc: "원본의 핵심 패턴을 따라하세요", color: "pink" },
            { title: "CTA 마무리", desc: "팔로우, 좋아요, 댓글 유도", color: "orange" },
        ],
    },
};

const getColorClass = (color: string, type: 'bg' | 'shadow') => {
    const colors: Record<string, Record<string, string>> = {
        violet: { bg: "bg-violet-500", shadow: "shadow-[0_0_15px_rgba(139,92,246,0.4)]" },
        pink: { bg: "bg-pink-500", shadow: "shadow-[0_0_15px_rgba(236,72,153,0.4)]" },
        orange: { bg: "bg-orange-500", shadow: "shadow-[0_0_15px_rgba(249,115,22,0.4)]" },
    };
    return colors[color]?.[type] || colors.violet[type];
};

export function FilmingGuide({
    vdgAnalysis,
    analysisStatus = 'pending',
    compact = false,
    className = '',
}: FilmingGuideProps) {
    // Extract hook pattern from VDG analysis
    const hookPattern = vdgAnalysis?.hook_genome?.pattern?.toLowerCase().replace(/\s+/g, "_");
    const hookSummary = vdgAnalysis?.hook_genome?.hook_summary;
    const isVDGConnected = !!hookPattern && hookPattern !== "default";

    // Get guide steps based on hook pattern
    const guideConfig = HOOK_PATTERN_GUIDE[hookPattern || ""] || HOOK_PATTERN_GUIDE.default;

    // Pending/Analyzing state
    if (analysisStatus !== 'completed' || !vdgAnalysis) {
        return (
            <div className={`p-4 bg-white/5 rounded-xl border border-dashed border-white/10 ${className}`}>
                <div className="flex items-center gap-2 text-white/40 mb-3">
                    <Zap className="w-4 h-4" />
                    <span className="text-sm font-bold">🎬 촬영 가이드</span>
                </div>
                <div className="text-center py-6">
                    {analysisStatus === 'analyzing' || analysisStatus === 'approved' ? (
                        <>
                            <div className="w-6 h-6 mx-auto border-2 border-purple-500 border-t-transparent rounded-full animate-spin mb-2" />
                            <p className="text-xs text-purple-400">VDG 분석 중...</p>
                        </>
                    ) : (
                        <>
                            <span className="text-3xl mb-2 block opacity-30">📋</span>
                            <p className="text-xs text-white/30">승격 후 VDG 분석 완료 시 활성화됩니다</p>
                        </>
                    )}
                </div>
            </div>
        );
    }

    // Compact mode for cards
    if (compact) {
        return (
            <div className={`p-3 bg-violet-500/10 rounded-lg border border-violet-500/20 ${className}`}>
                <div className="flex items-center gap-2 text-xs text-violet-400 mb-1">
                    <Zap className="w-3 h-3" />
                    <span className="font-bold">{isVDGConnected ? 'VDG 연동' : '기본'}</span>
                </div>
                <div className="flex items-center gap-1">
                    {guideConfig.steps.map((step, idx) => (
                        <span
                            key={idx}
                            className={`flex-1 h-1 rounded-full ${getColorClass(step.color, 'bg')} opacity-60`}
                        />
                    ))}
                </div>
            </div>
        );
    }

    // Full guide mode
    return (
        <div className={`p-4 bg-white/5 rounded-xl border border-white/10 ${className}`}>
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold flex items-center gap-2">
                    <Zap className="w-4 h-4 text-violet-400" />
                    🎬 촬영 가이드
                </h3>
                <span className={`text-[10px] px-2 py-0.5 rounded-full border ${isVDGConnected
                    ? "bg-violet-500/20 text-violet-400 border-violet-500/30"
                    : "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                    }`}>
                    {isVDGConnected ? "VDG 연동" : "기본"}
                </span>
            </div>

            {/* VDG Hook Summary */}
            {hookSummary && (
                <div className="p-3 bg-violet-500/10 rounded-lg border border-violet-500/20 mb-4">
                    <div className="flex items-center gap-2 text-xs text-violet-400 mb-1">
                        <Lightbulb className="w-3.5 h-3.5" />
                        이 영상의 핵심 훅
                    </div>
                    <p className="text-sm text-white/80">{hookSummary}</p>
                </div>
            )}

            {/* 3-Step Guide */}
            <div className="space-y-3">
                {guideConfig.steps.map(({ title, desc, color }, idx) => (
                    <div key={idx} className="flex items-start gap-3 group">
                        <span
                            className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold shrink-0 transition-transform group-hover:scale-110 ${getColorClass(color, 'bg')} ${getColorClass(color, 'shadow')}`}
                        >
                            {idx + 1}
                        </span>
                        <div className="flex-1">
                            <div className="font-bold text-white group-hover:text-violet-300 transition-colors">
                                {title}
                            </div>
                            <div className="text-sm text-white/60">{desc}</div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default FilmingGuide;
