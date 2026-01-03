'use client';
import { useTranslations } from 'next-intl';

/**
 * PipelineStatus - Outlier pipeline stage badge
 *
 * Flow: pending → promoted → comments → analyzing → completed
 */

type PipelineStage = 'pending' | 'promoted' | 'comments' | 'analyzing' | 'completed';

interface PipelineStatusProps {
    status: PipelineStage;
    analysisStatus?: 'pending' | 'approved' | 'analyzing' | 'completed' | 'skipped' | 'comments_pending_review' | 'comments_failed' | 'comments_ready';
    showLabel?: boolean;
    size?: 'sm' | 'md';
    className?: string;
}

const STAGE_CONFIG: Record<PipelineStage, {
    labelKey: string;
    emoji: string;
    bgClass: string;
    textClass: string;
    animate?: boolean;
}> = {
    pending: {
        labelKey: 'pending',
        emoji: '🆕',
        bgClass: 'bg-white/10',
        textClass: 'text-white/50',
    },
    promoted: {
        labelKey: 'promoted',
        emoji: '📦',
        bgClass: 'bg-blue-500/20',
        textClass: 'text-blue-300',
    },
    comments: {
        labelKey: 'comments',
        emoji: '💬',
        bgClass: 'bg-amber-500/20',
        textClass: 'text-amber-300',
    },
    analyzing: {
        labelKey: 'analyzing',
        emoji: '🔬',
        bgClass: 'bg-purple-500/20',
        textClass: 'text-purple-300',
        animate: true,
    },
    completed: {
        labelKey: 'completed',
        emoji: '✅',
        bgClass: 'bg-emerald-500/20',
        textClass: 'text-emerald-300',
    },
};

// Helper to compute pipeline stage from outlier item
export function getPipelineStage(status: string, analysisStatus?: string): PipelineStage {
    if (analysisStatus === 'completed') return 'completed';
    if (analysisStatus === 'comments_pending_review' || analysisStatus === 'comments_failed' || analysisStatus === 'comments_ready') {
        return 'comments';
    }
    if (analysisStatus === 'approved' || analysisStatus === 'analyzing') return 'analyzing';
    if (analysisStatus === 'skipped') return 'promoted';
    if (status === 'promoted') return 'promoted';
    return 'pending';
}

export function PipelineStatus({
    status,
    analysisStatus,
    showLabel = true,
    size = 'sm',
    className = '',
}: PipelineStatusProps) {
    const stage = analysisStatus
        ? getPipelineStage(status, analysisStatus)
        : status as PipelineStage;

    const t = useTranslations('components.pipelineStatus');
    const config = STAGE_CONFIG[stage] || STAGE_CONFIG.pending;
    const sizeClass = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-3 py-1 text-xs';

    return (
        <span
            className={`
                inline-flex items-center gap-1 rounded-full font-bold
                ${config.bgClass} ${config.textClass}
                ${config.animate ? 'animate-pulse' : ''}
                ${sizeClass} ${className}
            `}
        >
            {showLabel ? t(config.labelKey) : config.emoji}
        </span>
    );
}

export default PipelineStatus;
