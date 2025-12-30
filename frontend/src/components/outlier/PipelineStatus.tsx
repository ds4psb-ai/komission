'use client';

/**
 * PipelineStatus - Outlier pipeline stage badge
 * 
 * Flow: pending → promoted → analyzing → completed
 */

type PipelineStage = 'pending' | 'promoted' | 'analyzing' | 'completed';

interface PipelineStatusProps {
    status: PipelineStage;
    analysisStatus?: 'pending' | 'approved' | 'analyzing' | 'completed' | 'skipped';
    showLabel?: boolean;
    size?: 'sm' | 'md';
    className?: string;
}

const STAGE_CONFIG: Record<PipelineStage, {
    label: string;
    emoji: string;
    bgClass: string;
    textClass: string;
    animate?: boolean;
}> = {
    pending: {
        label: '크롤됨',
        emoji: '🆕',
        bgClass: 'bg-white/10',
        textClass: 'text-white/50',
    },
    promoted: {
        label: '승격됨',
        emoji: '📦',
        bgClass: 'bg-blue-500/20',
        textClass: 'text-blue-300',
    },
    analyzing: {
        label: '분석중',
        emoji: '🔬',
        bgClass: 'bg-purple-500/20',
        textClass: 'text-purple-300',
        animate: true,
    },
    completed: {
        label: '완료',
        emoji: '✅',
        bgClass: 'bg-emerald-500/20',
        textClass: 'text-emerald-300',
    },
};

// Helper to compute pipeline stage from outlier item
export function getPipelineStage(status: string, analysisStatus?: string): PipelineStage {
    if (analysisStatus === 'completed') return 'completed';
    if (analysisStatus === 'approved' || analysisStatus === 'analyzing') return 'analyzing';
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
    // Compute actual stage if analysisStatus is provided
    const stage = analysisStatus
        ? getPipelineStage(status, analysisStatus)
        : status as PipelineStage;

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
            {showLabel ? config.label : config.emoji}
        </span>
    );
}

export default PipelineStatus;
