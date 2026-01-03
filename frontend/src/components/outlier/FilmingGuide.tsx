'use client';
import { useTranslations } from 'next-intl';

/**
 * FilmingGuide - VDG-based filming guide component
 * 
 * Shows 3-step filming guide based on VDG hook_genome.pattern
 * - If VDG analysis complete: Shows pattern-specific steps
 * - If pending: Shows empty/waiting state
 */

import { Lightbulb, Zap } from 'lucide-react';

// VDG Data types (VDGv4 schema support)
interface HookGenome {
    pattern?: string;
    delivery?: string;
    strength?: number;
    hook_summary?: string;
    // VDGv4 fields
    hook_start_ms?: number;
    hook_end_ms?: number;
}

interface Keyframe {
    t_ms: number;
    role: 'start' | 'peak' | 'end';
    what_to_see: string;
}

interface ViralKick {
    kick_index: number;
    title: string;
    mechanism: string;
    creator_instruction: string;
    keyframes?: Keyframe[];
    window?: { start_ms: number; end_ms: number };
}

interface VDGData {
    // OLD VDG format
    hook_genome?: HookGenome;
    summary?: string;
    // VDGv4 format
    semantic?: {
        hook_genome?: HookGenome;
    };
    provenance?: {
        viral_kicks?: ViralKick[];
    };
    [key: string]: unknown;
}

interface FilmingGuideProps {
    vdgAnalysis?: VDGData | null;
    analysisStatus?: 'pending' | 'promoted' | 'approved' | 'analyzing' | 'completed' | 'skipped' | 'comments_pending_review' | 'comments_failed' | 'comments_ready';
    compact?: boolean;
    className?: string;
}

// Helper: Get viral kicks from VDGv4 or fall back to hook pattern
function getGuideSteps(vdgAnalysis: VDGData | null | undefined, t: any): { title: string; desc: string; color: string }[] {
    // VDGv4: Use viral_kicks if available
    const viralKicks = vdgAnalysis?.provenance?.viral_kicks;
    if (viralKicks && viralKicks.length >= 3) {
        const colors = ['violet', 'pink', 'orange'];
        return viralKicks.slice(0, 3).map((kick, idx) => ({
            title: kick.title || `Kick ${kick.kick_index}`,
            desc: kick.creator_instruction || kick.mechanism || '',
            color: colors[idx % colors.length],
        }));
    }

    // Fall back to hook_genome.pattern based guide
    const hookPattern = (vdgAnalysis?.hook_genome?.pattern || vdgAnalysis?.semantic?.hook_genome?.pattern || '')
        .toLowerCase().replace(/\s+/g, "_");

    const patternKey = ['pattern_break', 'visual_reaction', 'transformation', 'reveal', 'challenge'].includes(hookPattern)
        ? hookPattern
        : 'default';

    return [
        {
            title: t(`steps.${patternKey}.step1.title`),
            desc: t(`steps.${patternKey}.step1.desc`),
            color: "violet"
        },
        {
            title: t(`steps.${patternKey}.step2.title`),
            desc: t(`steps.${patternKey}.step2.desc`),
            color: "pink"
        },
        {
            title: t(`steps.${patternKey}.step3.title`),
            desc: t(`steps.${patternKey}.step3.desc`),
            color: "orange"
        }
    ];
}

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
    const t = useTranslations('components.filmingGuide');

    // Get guide steps from VDGv4 viral_kicks or fallback to hook pattern
    const guideSteps = getGuideSteps(vdgAnalysis, t);

    // Check if VDGv4 viral_kicks are used
    const hasViralKicks = (vdgAnalysis?.provenance?.viral_kicks?.length ?? 0) >= 3;
    const hookSummary = vdgAnalysis?.hook_genome?.hook_summary || vdgAnalysis?.semantic?.hook_genome?.hook_summary;
    const isVDGConnected = hasViralKicks || !!hookSummary;

    // Guideconfig wrapper for compatibility
    const guideConfig = { steps: guideSteps };

    // Pending/Analyzing state
    if (analysisStatus !== 'completed' || !vdgAnalysis) {
        return (
            <div className={`p-4 bg-white/5 rounded-xl border border-dashed border-white/10 ${className}`}>
                <div className="flex items-center gap-2 text-white/40 mb-3">
                    <Zap className="w-4 h-4" />
                    <span className="text-sm font-bold">🎬 {t('title')}</span>
                </div>
                <div className="text-center py-6">
                    {analysisStatus === 'analyzing' || analysisStatus === 'approved' ? (
                        <>
                            <div className="w-6 h-6 mx-auto border-2 border-purple-500 border-t-transparent rounded-full animate-spin mb-2" />
                            <p className="text-xs text-purple-400">{t('vdg.analyzing')}</p>
                        </>
                    ) : (
                        <>
                            <span className="text-3xl mb-2 block opacity-30">📋</span>
                            <p className="text-xs text-white/30">{t('vdg.pending')}</p>
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
                    <span className="font-bold">{isVDGConnected ? t('vdg.label') : t('vdg.default')}</span>
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
                    🎬 {t('title')}
                </h3>
                <span className={`text-[10px] px-2 py-0.5 rounded-full border ${isVDGConnected
                    ? "bg-violet-500/20 text-violet-400 border-violet-500/30"
                    : "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                    }`}>
                    {isVDGConnected ? t('vdg.label') : t('vdg.default')}
                </span>
            </div>

            {/* VDG Hook Summary */}
            {hookSummary && (
                <div className="p-3 bg-violet-500/10 rounded-lg border border-violet-500/20 mb-4">
                    <div className="flex items-center gap-2 text-xs text-violet-400 mb-1">
                        <Lightbulb className="w-3.5 h-3.5" />
                        {t('vdg.hookSummary')}
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
