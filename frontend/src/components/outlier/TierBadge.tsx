'use client';

/**
 * TierBadge - Outlier tier badge component (S/A/B/C)
 */

import { Award, Star, Diamond, BarChart } from 'lucide-react';

type TierType = 'S' | 'A' | 'B' | 'C' | string | null | undefined;

interface TierBadgeProps {
    tier: TierType;
    size?: 'sm' | 'md' | 'lg';
    showIcon?: boolean;
    className?: string;
}

const TIER_CONFIG: Record<string, {
    bgClass: string;
    textClass: string;
    icon: typeof Award;
    glow?: string;
}> = {
    S: {
        bgClass: 'bg-gradient-to-r from-amber-400 to-orange-500',
        textClass: 'text-black',
        icon: Award,
        glow: 'shadow-[0_0_15px_rgba(251,191,36,0.5)]',
    },
    A: {
        bgClass: 'bg-gradient-to-r from-violet-400 to-purple-500',
        textClass: 'text-white',
        icon: Star,
        glow: 'shadow-[0_0_10px_rgba(167,139,250,0.4)]',
    },
    B: {
        bgClass: 'bg-gradient-to-r from-blue-400 to-cyan-500',
        textClass: 'text-white',
        icon: Diamond,
    },
    C: {
        bgClass: 'bg-white/20',
        textClass: 'text-white/70',
        icon: BarChart,
    },
};

const SIZE_CONFIG = {
    sm: 'px-1.5 py-0.5 text-[10px]',
    md: 'px-2 py-1 text-xs',
    lg: 'px-3 py-1.5 text-sm',
};

export function TierBadge({ tier, size = 'sm', showIcon = false, className = '' }: TierBadgeProps) {
    const tierKey = (tier || 'C').toUpperCase();
    const config = TIER_CONFIG[tierKey] || TIER_CONFIG.C;
    const Icon = config.icon;

    return (
        <span
            className={`
                inline-flex items-center gap-1 rounded font-black
                ${config.bgClass} ${config.textClass} ${config.glow || ''}
                ${SIZE_CONFIG[size]} ${className}
            `}
        >
            {showIcon && <Icon className="w-3 h-3" />}
            {tierKey}
        </span>
    );
}

export default TierBadge;
