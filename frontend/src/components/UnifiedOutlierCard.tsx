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
import { Heart, TrendingUp, Star, Gift, ArrowUpRight } from 'lucide-react';
import { PlatformBadge, OutlierScoreBadge } from '@/components/outlier';

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
    campaign_eligible?: boolean;
}

interface UnifiedOutlierCardProps {
    item: OutlierCardItem;
    onPromote?: (item: OutlierCardItem, campaignEligible?: boolean) => void;
}

// TIER_CONFIG and PLATFORM_CONFIG removed - handled by PlatformBadge and OutlierScoreBadge

function formatNumber(num: number): string {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

function formatRelativeTime(dateString?: string): string {
    if (!dateString) return '';
    const date = new Date(dateString);
    if (Number.isNaN(date.getTime())) return '';
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

    const isPromoted = item.status === 'promoted';
    const hasVDG = !!item.vdg_analysis;

    const handleClick = () => {
        // Use hard navigation to avoid Next.js client-side routing state issues
        window.location.href = `/video/${item.id}`;
    };

    // Determine border color based on tier (optional, or keep generic)
    const tier = item.outlier_tier || 'C';
    let borderColor = 'border-white/10';
    if (tier === 'S') borderColor = 'border-pink-500/30';
    if (tier === 'A') borderColor = 'border-orange-500/30';

    return (
        <div
            onClick={handleClick}
            className={`
                group relative cursor-pointer overflow-hidden rounded-2xl border transition-all duration-300
                bg-zinc-900/50 ${borderColor}
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
                    <div className="w-full h-full bg-zinc-800 flex items-center justify-center">
                        <span className="text-4xl opacity-20">🎬</span>
                    </div>
                )}

                {/* Gradient Overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/30 to-transparent" />

                {/* Top Right: Outlier Score (Virlo-style) */}
                <div className="absolute top-3 right-3 z-[4]">
                    <OutlierScoreBadge
                        score={item.outlier_score}
                        tier={item.outlier_tier}
                        size="md"
                    />
                </div>

                {/* Top Left: View Check */}
                <div className="absolute top-3 left-3 z-[4]">
                    <div className="flex items-center gap-1 px-2 py-1 bg-black/70 rounded-full text-[11px] text-white backdrop-blur-sm">
                        <span>👁️</span>
                        <span>{formatNumber(item.view_count)}</span>
                    </div>
                </div>

                {/* Bottom Left: Platform Badge */}
                <div className="absolute bottom-[4.5rem] left-3 z-[4]">
                    <PlatformBadge platform={item.platform} size="md" />
                </div>

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

                    {/* Stats Row (view count removed - shown in top-left badge) */}
                    <div className="flex items-center gap-3 text-[10px] text-white/70">
                        {typeof item.like_count === 'number' && (
                            <span className="flex items-center gap-1">
                                <Heart className="w-3 h-3" />
                                {formatNumber(item.like_count)}
                            </span>
                        )}
                        {typeof item.engagement_rate === 'number' && (
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
                <div className="flex border-t border-white/5 divide-x divide-white/5">
                    <button
                        onClick={(e) => { e.stopPropagation(); onPromote(item, false); }}
                        className={`
                            flex-1 py-2.5 text-xs font-bold flex items-center justify-center gap-1.5 transition-all
                            text-violet-300 hover:bg-violet-500/10
                        `}
                    >
                        <Star className="w-3.5 h-3.5" />
                        리믹스 승격
                    </button>
                    <button
                        onClick={(e) => { e.stopPropagation(); onPromote(item, true); }}
                        className="flex-1 py-2.5 text-xs font-bold flex items-center justify-center gap-1.5 text-emerald-400 hover:bg-emerald-500/10 transition-all"
                        title="오거닉 바이럴 후보로 등록"
                    >
                        <Gift className="w-3.5 h-3.5" />
                        오거닉 바이럴
                    </button>
                </div>
            )}
        </div>
    );
}

export default UnifiedOutlierCard;
