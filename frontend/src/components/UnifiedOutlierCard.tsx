"use client";

/**
 * UnifiedOutlierCard - Vertical Card for Shorts Discovery
 * 
 * Features:
 * - 9:16 aspect ratio thumbnail (shorts-optimized)
 * - Tier badges (S/A/B/C) with glow
 * - Platform indicator
 * - Outlier score multiplier
 * - View/Promote actions
 * - Click to navigate to detail page
 */
import React from 'react';
import { useRouter } from 'next/navigation';
import { Eye, Heart, TrendingUp, Zap, Star, Award, Diamond, BarChart, ArrowUpRight, Sparkles } from 'lucide-react';

export interface OutlierCardItem {
    id: string;
    external_id?: string;
    video_url: string;
    platform: 'tiktok' | 'youtube' | 'instagram';
    category: string;
    title: string;
    thumbnail_url?: string;
    view_count: number;
    like_count?: number;
    share_count?: number;
    outlier_score?: number;
    outlier_tier: 'S' | 'A' | 'B' | 'C' | null;
    creator_avg_views?: number;
    engagement_rate?: number;
    crawled_at?: string;
    status?: 'pending' | 'selected' | 'rejected' | 'promoted';
    // VDG Analysis data (indicates completed analysis)
    vdg_analysis?: unknown;
}

interface UnifiedOutlierCardProps {
    item: OutlierCardItem;
    onPromote?: (item: OutlierCardItem) => void;
}

const TIER_CONFIG = {
    S: {
        label: 'S',
        icon: Award,
        bgClass: 'bg-gradient-to-br from-amber-500/30 to-yellow-600/20',
        borderClass: 'border-amber-500/60',
        textClass: 'text-amber-300',
        badgeClass: 'bg-amber-500/30 text-amber-300',
        glowClass: 'shadow-[0_0_25px_rgba(251,191,36,0.4)]',
    },
    A: {
        label: 'A',
        icon: Star,
        bgClass: 'bg-gradient-to-br from-purple-500/30 to-violet-600/20',
        borderClass: 'border-purple-500/50',
        textClass: 'text-purple-300',
        badgeClass: 'bg-purple-500/30 text-purple-300',
        glowClass: 'shadow-[0_0_20px_rgba(139,92,246,0.3)]',
    },
    B: {
        label: 'B',
        icon: Diamond,
        bgClass: 'bg-gradient-to-br from-blue-500/20 to-cyan-600/10',
        borderClass: 'border-blue-500/40',
        textClass: 'text-blue-300',
        badgeClass: 'bg-blue-500/20 text-blue-300',
        glowClass: '',
    },
    C: {
        label: 'C',
        icon: BarChart,
        bgClass: 'bg-zinc-900/50',
        borderClass: 'border-zinc-600/30',
        textClass: 'text-zinc-400',
        badgeClass: 'bg-zinc-700/50 text-zinc-400',
        glowClass: '',
    },
};

const PLATFORM_CONFIG = {
    tiktok: { label: 'TikTok', icon: '🎵', color: 'from-pink-500 to-cyan-500' },
    youtube: { label: 'Shorts', icon: '▶️', color: 'from-red-500 to-orange-500' },
    instagram: { label: 'Reels', icon: '📷', color: 'from-purple-500 to-pink-500' },
};

function formatNumber(num: number): string {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

function formatRelativeTime(dateString?: string): string {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);
    if (diffHours < 1) return '방금';
    if (diffHours < 24) return `${diffHours}h`;
    if (diffDays < 7) return `${diffDays}d`;
    return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
}

export function UnifiedOutlierCard({ item, onPromote }: UnifiedOutlierCardProps) {
    const router = useRouter();
    const tierConfig = item.outlier_tier ? TIER_CONFIG[item.outlier_tier] : null;
    const platformConfig = PLATFORM_CONFIG[item.platform];
    const TierIcon = tierConfig?.icon || BarChart;

    const multiplier = item.creator_avg_views && item.creator_avg_views > 0
        ? Math.round(item.view_count / item.creator_avg_views)
        : 0;

    const isPromoted = item.status === 'promoted';
    const hasVDG = !!item.vdg_analysis;

    const handleClick = () => {
        router.push(`/video/${item.id}`);
    };

    return (
        <div
            onClick={handleClick}
            className={`
                group relative cursor-pointer overflow-hidden rounded-2xl border transition-all duration-300
                ${tierConfig?.bgClass || 'bg-zinc-900/50'}
                ${tierConfig?.borderClass || 'border-white/10'}
                ${tierConfig?.glowClass || ''}
                hover:scale-[1.02] hover:border-white/30
            `}
        >
            {/* Thumbnail - 9:16 Aspect Ratio */}
            <div className="relative aspect-[9/16] overflow-hidden">
                {item.thumbnail_url ? (
                    <img
                        src={item.thumbnail_url}
                        alt={item.title}
                        className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                    />
                ) : (
                    <div className={`w-full h-full bg-gradient-to-br ${platformConfig.color} opacity-30 flex items-center justify-center`}>
                        <span className="text-4xl opacity-50">{platformConfig.icon}</span>
                    </div>
                )}

                {/* Gradient Overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/30 to-transparent" />

                {/* Top Left: Platform Badge */}
                <div className="absolute top-3 left-3 flex items-center gap-1 px-2 py-1 bg-black/60 backdrop-blur rounded-lg">
                    <span className="text-xs">{platformConfig.icon}</span>
                    <span className="text-[10px] font-bold text-white/80">{platformConfig.label}</span>
                </div>

                {/* Top Right: Tier Badge */}
                {tierConfig && (
                    <div className={`absolute top-3 right-3 flex items-center gap-1 px-2 py-1 rounded-lg ${tierConfig.badgeClass} backdrop-blur-sm`}>
                        <TierIcon className="w-3 h-3" />
                        <span className="text-xs font-black">{tierConfig.label}</span>
                        {multiplier > 1 && (
                            <span className="flex items-center text-[10px] font-mono">
                                <Zap className="w-2.5 h-2.5" />{multiplier}x
                            </span>
                        )}
                    </div>
                )}

                {/* VDG Analysis Badge - Show when VDG completed */}
                {hasVDG && (
                    <div className="absolute top-12 right-3 px-2 py-0.5 bg-gradient-to-r from-violet-500/30 to-pink-500/30 backdrop-blur rounded text-[9px] font-bold text-violet-300 flex items-center gap-1 border border-violet-500/30">
                        <Sparkles className="w-2.5 h-2.5" />
                        VDG
                    </div>
                )}

                {/* Promoted Badge */}
                {isPromoted && (
                    <div className={`absolute ${hasVDG ? 'top-[4.5rem]' : 'top-12'} right-3 px-2 py-0.5 bg-emerald-500/30 backdrop-blur rounded text-[9px] font-bold text-emerald-300`}>
                        ✓ Promoted
                    </div>
                )}

                {/* Bottom Content */}
                <div className="absolute bottom-0 left-0 right-0 p-3">
                    {/* Title */}
                    <h3 className="text-sm font-bold text-white leading-tight line-clamp-2 mb-2">
                        {item.title || 'Untitled'}
                    </h3>

                    {/* Stats Row */}
                    <div className="flex items-center gap-3 text-[10px] text-white/70">
                        <span className="flex items-center gap-1">
                            <Eye className="w-3 h-3" />
                            {formatNumber(item.view_count)}
                        </span>
                        {item.like_count && (
                            <span className="flex items-center gap-1">
                                <Heart className="w-3 h-3" />
                                {formatNumber(item.like_count)}
                            </span>
                        )}
                        {item.engagement_rate && (
                            <span className="flex items-center gap-1 text-emerald-400">
                                <TrendingUp className="w-3 h-3" />
                                {(item.engagement_rate * 100).toFixed(1)}%
                            </span>
                        )}
                    </div>

                    {/* Category + Time */}
                    <div className="flex items-center gap-2 mt-2 text-[9px] text-white/50">
                        <span className="px-1.5 py-0.5 bg-white/10 rounded">{item.category}</span>
                        {item.crawled_at && <span>{formatRelativeTime(item.crawled_at)}</span>}
                    </div>
                </div>

                {/* View Arrow (on hover) */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="w-12 h-12 rounded-full bg-white/20 backdrop-blur flex items-center justify-center">
                        <ArrowUpRight className="w-5 h-5 text-white" />
                    </div>
                </div>
            </div>

            {/* Promote Button (if callback provided and not promoted) */}
            {onPromote && !isPromoted && (
                <button
                    onClick={(e) => { e.stopPropagation(); onPromote(item); }}
                    className={`
                        w-full py-2.5 text-xs font-bold flex items-center justify-center gap-1.5 transition-all
                        ${tierConfig ? `${tierConfig.textClass} hover:bg-white/10` : 'text-violet-300 hover:bg-violet-500/10'}
                    `}
                >
                    <Star className="w-3.5 h-3.5" />
                    Promote
                </button>
            )}
        </div>
    );
}

export default UnifiedOutlierCard;
