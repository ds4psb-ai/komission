"use client";
import { useTranslations } from 'next-intl';

import React from 'react';
import { ExternalLink, Zap, Eye, Heart, TrendingUp, Star, Award, Diamond, BarChart } from 'lucide-react';

/**
 * Outlier item from crawler API
 */
export interface CrawlerOutlierItem {
    id: string;
    external_id: string;
    video_url: string;
    platform: 'tiktok' | 'youtube' | 'instagram';
    category: string;
    title: string;
    thumbnail_url?: string;
    view_count: number;
    like_count?: number;
    share_count?: number;
    outlier_score: number;
    outlier_tier: 'S' | 'A' | 'B' | 'C' | null;
    creator_avg_views: number;
    engagement_rate: number;
    crawled_at: string;
    status: 'pending' | 'selected' | 'rejected' | 'promoted';
}

interface CrawlerOutlierCardProps {
    item: CrawlerOutlierItem;
    onView?: (item: CrawlerOutlierItem) => void;
    onPromote?: (item: CrawlerOutlierItem) => void;
    compact?: boolean;
}

/**
 * Tier configuration with colors and icons
 */
const TIER_CONFIG = {
    S: {
        label: 'S-Tier',
        icon: Award,
        bgClass: 'bg-gradient-to-r from-amber-500/20 to-yellow-500/20',
        borderClass: 'border-amber-500/50',
        textClass: 'text-amber-300',
        badgeClass: 'bg-amber-500/20 border-amber-400/50 text-amber-300',
        glowClass: 'shadow-[0_0_20px_rgba(251,191,36,0.3)]',
    },
    A: {
        label: 'A-Tier',
        icon: Star,
        bgClass: 'bg-gradient-to-r from-purple-500/20 to-violet-500/20',
        borderClass: 'border-purple-500/50',
        textClass: 'text-purple-300',
        badgeClass: 'bg-purple-500/20 border-purple-400/50 text-purple-300',
        glowClass: 'shadow-[0_0_15px_rgba(139,92,246,0.2)]',
    },
    B: {
        label: 'B-Tier',
        icon: Diamond,
        bgClass: 'bg-gradient-to-r from-blue-500/20 to-cyan-500/20',
        borderClass: 'border-blue-500/50',
        textClass: 'text-blue-300',
        badgeClass: 'bg-blue-500/20 border-blue-400/50 text-blue-300',
        glowClass: '',
    },
    C: {
        label: 'C-Tier',
        icon: BarChart,
        bgClass: 'bg-gradient-to-r from-zinc-500/20 to-gray-500/20',
        borderClass: 'border-zinc-500/50',
        textClass: 'text-zinc-300',
        badgeClass: 'bg-zinc-500/20 border-zinc-400/50 text-zinc-300',
        glowClass: '',
    },
};

const PLATFORM_CONFIG = {
    tiktok: {
        label: 'TikTok',
        icon: '🎵',
        bgClass: 'from-pink-600/30 to-cyan-600/20',
    },
    youtube: {
        label: 'Shorts',
        icon: '▶️',
        bgClass: 'from-red-600/30 to-gray-600/20',
    },
    instagram: {
        label: 'Reels',
        icon: '📷',
        bgClass: 'from-purple-600/30 to-orange-600/20',
    },
};

/**
 * Format large numbers (e.g., 1500000 -> 1.5M)
 */
function formatNumber(num: number): string {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

/**
 * Format relative time (e.g., "2시간 전")
 */
function formatRelativeTime(dateString: string): string {
    const date = new Date(dateString);
    if (Number.isNaN(date.getTime())) return '-';
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffHours < 1) return '방금 전';
    if (diffHours < 24) return `${diffHours}시간 전`;
    if (diffDays < 7) return `${diffDays}일 전`;
    return date.toLocaleDateString('ko-KR');
}

/**
 * CrawlerOutlierCard
 * 
 * Displays outlier items from 3-platform crawlers with:
 * - Tier badges (S/A/B/C)
 * - Outlier score multiplier
 * - Engagement rate
 * - Creator average comparison
 * - Promote to Parent CTA
 */
export function CrawlerOutlierCard({
    item,
    onView,
    onPromote,
    compact = false
}: CrawlerOutlierCardProps) {
    const t = useTranslations('components.card');
    const tTime = useTranslations('components.time');

    // Tier Config with translated labels
    const tierConfig = item.outlier_tier ? TIER_CONFIG[item.outlier_tier] : null;
    const platformConfig = PLATFORM_CONFIG[item.platform];
    const TierIcon = tierConfig?.icon || BarChart;

    const multiplier = item.creator_avg_views > 0
        ? Math.round(item.view_count / item.creator_avg_views)
        : 0;

    const isPromoted = item.status === 'promoted';

    // Helper for relative time using translations
    const getRelativeTime = (dateString: string) => {
        const date = new Date(dateString);
        if (Number.isNaN(date.getTime())) return '-';
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffHours / 24);

        if (diffHours < 1) return tTime('justNow');
        if (diffHours < 24) return tTime('hoursAgo', { hours: diffHours });
        if (diffDays < 7) return tTime('daysAgo', { days: diffDays });
        return date.toLocaleDateString();
    };

    return (
        <div
            className={`
                group relative overflow-hidden rounded-2xl border transition-all duration-300
                ${tierConfig?.bgClass || 'bg-zinc-900/50'}
                ${tierConfig?.borderClass || 'border-white/10'}
                ${tierConfig?.glowClass || ''}
                hover:border-white/30 hover:scale-[1.02]
                ${compact ? 'p-4' : 'p-5'}
            `}
        >
            {/* Thumbnail / Platform Icon Area */}
            <div className="flex gap-4">
                {/* Thumbnail */}
                <div className={`
                    relative overflow-hidden rounded-xl bg-gradient-to-br ${platformConfig.bgClass}
                    ${compact ? 'w-20 h-20' : 'w-28 h-28'}
                    flex-shrink-0
                `}>
                    {item.thumbnail_url ? (
                        <img
                            src={item.thumbnail_url}
                            alt={item.title}
                            className="w-full h-full object-cover"
                        />
                    ) : (
                        <div className="w-full h-full flex items-center justify-center text-4xl opacity-50">
                            {platformConfig.icon}
                        </div>
                    )}

                    {/* Platform Badge */}
                    <div className="absolute top-2 left-2 px-1.5 py-0.5 rounded bg-black/60 backdrop-blur text-[10px] font-bold text-white flex items-center gap-1">
                        <span>{platformConfig.icon}</span>
                        <span className="hidden sm:inline">{platformConfig.label}</span>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0 flex flex-col">
                    {/* Header: Tier Badge + Score */}
                    <div className="flex items-center gap-2 mb-2">
                        {tierConfig && (
                            <span className={`
                                inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-black uppercase border
                                ${tierConfig.badgeClass}
                            `}>
                                <TierIcon className="w-3 h-3" />
                                {tierConfig.label}
                            </span>
                        )}
                        {multiplier > 0 && (
                            <span className={`
                                flex items-center gap-1 text-xs font-mono font-bold
                                ${tierConfig?.textClass || 'text-white/60'}
                            `}>
                                <Zap className="w-3 h-3" />
                                {multiplier}x
                            </span>
                        )}
                        {isPromoted && (
                            <span className="px-2 py-0.5 rounded bg-emerald-500/20 border border-emerald-500/50 text-[10px] font-bold text-emerald-300">
                                ✓ {t('promoted')}
                            </span>
                        )}
                    </div>

                    {/* Title */}
                    <h3 className={`
                        font-bold text-white leading-tight mb-2
                        ${compact ? 'text-sm line-clamp-1' : 'text-base line-clamp-2'}
                    `}>
                        {item.title || 'Untitled'}
                    </h3>

                    {/* Stats Row */}
                    <div className="flex flex-wrap items-center gap-3 text-xs text-white/60">
                        <span className="flex items-center gap-1">
                            <Eye className="w-3.5 h-3.5" />
                            {formatNumber(item.view_count)}
                        </span>
                        {typeof item.like_count === 'number' && (
                            <span className="flex items-center gap-1">
                                <Heart className="w-3.5 h-3.5" />
                                {formatNumber(item.like_count)}
                            </span>
                        )}
                        {typeof item.engagement_rate === 'number' && (
                            <span className="flex items-center gap-1">
                                <TrendingUp className="w-3.5 h-3.5" />
                                {(item.engagement_rate * 100).toFixed(1)}%
                            </span>
                        )}
                    </div>

                    {/* Creator Baseline Comparison */}
                    {!compact && item.creator_avg_views > 0 && (
                        <div className="mt-2 text-[10px] text-white/40">
                            {t('creatorAvg')}: {formatNumber(item.creator_avg_views)} views
                        </div>
                    )}
                </div>
            </div>

            {/* Footer: Category + Time + Actions */}
            <div className={`
                flex items-center justify-between mt-4 pt-3 border-t border-white/5
                ${compact ? 'text-[10px]' : 'text-xs'}
            `}>
                <div className="flex items-center gap-2 text-white/40">
                    <span className="px-2 py-0.5 bg-white/5 rounded">
                        {item.category}
                    </span>
                    <span>•</span>
                    <span>{getRelativeTime(item.crawled_at)}</span>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center gap-2">
                    {onView && (
                        <button
                            onClick={() => onView(item)}
                            className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-white/70 hover:text-white transition-all"
                        >
                            <ExternalLink className="w-3.5 h-3.5" />
                            <span>{t('view')}</span>
                        </button>
                    )}
                    {onPromote && !isPromoted && (
                        <button
                            onClick={() => onPromote(item)}
                            className={`
                                flex items-center gap-1 px-3 py-1.5 rounded-lg font-bold transition-all
                                ${tierConfig
                                    ? `${tierConfig.badgeClass} hover:brightness-125`
                                    : 'bg-violet-500/20 border border-violet-500/50 text-violet-300 hover:bg-violet-500/30'
                                }
                            `}
                        >
                            <Star className="w-3.5 h-3.5" />
                            <span>{t('promote')}</span>
                        </button>
                    )}
                </div>
            </div>

            {/* Hover Glow Effect */}
            <div className={`
                absolute inset-0 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-500
                bg-gradient-to-t from-transparent via-transparent to-white/5
            `} />
        </div>
    );
}

export default CrawlerOutlierCard;
