'use client';

/**
 * OutlierScoreBadge - Virlo-style outlier score badge
 * 
 * Shows outlier multiplier (e.g., "627x 🔥") with tier-based colors
 * Position: top-right of card
 */

interface OutlierScoreBadgeProps {
    score: number | null | undefined;
    tier?: string | null;
    size?: 'sm' | 'md' | 'lg';
    className?: string;
}

// Virlo-style tier colors
const TIER_COLORS: Record<string, string> = {
    S: 'bg-pink-500',           // #e83b88 - Hot pink for S tier
    A: 'bg-orange-500',         // #f97316 - Orange for A tier
    B: 'bg-yellow-500',         // #eab308 - Yellow for B tier
    C: 'bg-green-500',          // #22c55e - Green for C tier
};

const SIZE_CONFIG = {
    sm: 'px-1.5 py-0.5 text-[10px] gap-0.5',
    md: 'px-2 py-1 text-xs gap-1',
    lg: 'px-3 py-1.5 text-sm gap-1.5',
};

export function OutlierScoreBadge({ score, tier, size = 'md', className = '' }: OutlierScoreBadgeProps) {
    if (!score || score <= 0) return null;

    // Format score: 1234.56 → "1234x" or "1.2Kx" for large numbers
    let formattedScore: string;
    if (score >= 1000) {
        formattedScore = `${(score / 1000).toFixed(1)}K`;
    } else if (score >= 100) {
        formattedScore = Math.round(score).toString();
    } else {
        formattedScore = score.toFixed(1);
    }

    const tierKey = (tier || 'C').toUpperCase();
    const bgColor = TIER_COLORS[tierKey] || TIER_COLORS.C;

    return (
        <div
            className={`
                inline-flex items-center rounded-full font-bold text-white
                ${bgColor} ${SIZE_CONFIG[size]} ${className}
            `}
        >
            <span>🔥</span>
            <span>{formattedScore}x</span>
        </div>
    );
}

export default OutlierScoreBadge;
