"use client";

/**
 * VirloVideoCard.tsx
 * 
 * Virlo-style video card with:
 * - Thumbnail + Click-to-play embed
 * - Analysis data overlay (hook, patterns, engagement)
 * - Hit section markers
 * - Platform-specific embed support
 */
import React, { useState, useCallback } from 'react';
import {
    Play, X, Eye, Heart, TrendingUp, Zap, Clock,
    Sparkles, Target, Star, Award, Diamond, BarChart,
    ExternalLink, Share2, Bookmark, MoreHorizontal
} from 'lucide-react';

// ==================
// Types
// ==================

export interface VideoAnalysis {
    hook_pattern?: string;
    hook_score?: number;
    hook_duration_sec?: number;
    visual_patterns?: string[];
    audio_pattern?: string;
    pacing?: string;
    engagement_peak_sec?: number;
    best_comment?: string;
}

export interface VirloVideoItem {
    id: string;
    video_url: string;
    platform: 'tiktok' | 'instagram' | 'youtube';
    title: string;
    thumbnail_url?: string;
    creator?: string;
    creator_avatar?: string;
    category: string;
    tags?: string[];

    // Metrics
    view_count: number;
    like_count?: number;
    share_count?: number;
    engagement_rate?: number;

    // Outlier data
    outlier_score?: number;
    outlier_tier?: 'S' | 'A' | 'B' | 'C' | null;
    creator_avg_views?: number;

    // Analysis (from VDG or manual)
    analysis?: VideoAnalysis;

    // Timestamps
    posted_at?: string;
    crawled_at?: string;
}

interface VirloVideoCardProps {
    video: VirloVideoItem;
    onPlay?: (video: VirloVideoItem) => void;
    onPromote?: (video: VirloVideoItem) => void;
    onSave?: (video: VirloVideoItem) => void;
    onShare?: (video: VirloVideoItem) => void;
    showAnalysis?: boolean;
    variant?: 'default' | 'compact' | 'large';
}

// ==================
// Config
// ==================

const TIER_CONFIG = {
    S: { label: 'S', icon: Award, color: 'text-amber-400', bg: 'bg-amber-500/20', border: 'border-amber-500/50', glow: 'shadow-[0_0_20px_rgba(251,191,36,0.3)]' },
    A: { label: 'A', icon: Star, color: 'text-purple-400', bg: 'bg-purple-500/20', border: 'border-purple-500/50', glow: '' },
    B: { label: 'B', icon: Diamond, color: 'text-blue-400', bg: 'bg-blue-500/20', border: 'border-blue-500/50', glow: '' },
    C: { label: 'C', icon: BarChart, color: 'text-zinc-400', bg: 'bg-zinc-500/20', border: 'border-zinc-500/50', glow: '' },
};

const PLATFORM_CONFIG = {
    tiktok: {
        label: 'TikTok',
        icon: '🎵',
        color: 'from-pink-500 to-cyan-500',
        embedUrl: (id: string) => `https://www.tiktok.com/embed/v2/${id}`,
    },
    instagram: {
        label: 'Reels',
        icon: '📷',
        color: 'from-purple-500 to-orange-500',
        embedUrl: (id: string) => `https://www.instagram.com/p/${id}/embed`,
    },
    youtube: {
        label: 'Shorts',
        icon: '▶️',
        color: 'from-red-500 to-gray-500',
        embedUrl: (id: string) => `https://www.youtube.com/embed/${id}`,
    },
};

// ==================
// Helpers
// ==================

function formatNumber(num: number): string {
    if (num >= 1_000_000) return (num / 1_000_000).toFixed(1) + 'M';
    if (num >= 1_000) return (num / 1_000).toFixed(1) + 'K';
    return num.toString();
}

function extractVideoId(url: string, platform: string): string | null {
    try {
        if (platform === 'tiktok') {
            const match = url.match(/video\/(\d+)/);
            return match ? match[1] : null;
        }
        if (platform === 'youtube') {
            const match = url.match(/(?:shorts\/|v=|\/embed\/)([a-zA-Z0-9_-]+)/);
            return match ? match[1] : null;
        }
        if (platform === 'instagram') {
            const match = url.match(/(?:\/p\/|\/reel\/)([a-zA-Z0-9_-]+)/);
            return match ? match[1] : null;
        }
    } catch {
        return null;
    }
    return null;
}

// ==================
// Sub-components
// ==================

/** Analysis Overlay - shows hook, patterns, engagement peak */
function AnalysisOverlay({ analysis, visible }: { analysis?: VideoAnalysis; visible: boolean }) {
    if (!analysis || !visible) return null;

    return (
        <div className="absolute inset-0 bg-black/80 backdrop-blur-sm p-4 flex flex-col justify-end z-10 animate-fadeIn">
            {/* Hook Pattern */}
            {analysis.hook_pattern && (
                <div className="mb-3">
                    <div className="flex items-center gap-1 text-[10px] text-cyan-400 font-bold uppercase mb-1">
                        <Target className="w-3 h-3" />
                        Hook Pattern
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-white">{analysis.hook_pattern}</span>
                        {typeof analysis.hook_score === 'number' && (
                            <span className="px-1.5 py-0.5 bg-cyan-500/20 rounded text-[10px] text-cyan-300 font-mono">
                                {analysis.hook_score < 1
                                    ? `${(analysis.hook_score * 10).toFixed(1)}/10`
                                    : `${analysis.hook_score}/10`}
                            </span>
                        )}
                        {typeof analysis.hook_duration_sec === 'number' && (
                            <span className="text-[10px] text-white/50">
                                <Clock className="w-3 h-3 inline" /> {analysis.hook_duration_sec}s
                            </span>
                        )}
                    </div>
                </div>
            )}

            {/* Visual Patterns */}
            {analysis.visual_patterns && analysis.visual_patterns.length > 0 && (
                <div className="mb-3">
                    <div className="flex flex-wrap gap-1">
                        {analysis.visual_patterns.slice(0, 4).map((pattern, i) => (
                            <span key={i} className="px-1.5 py-0.5 bg-violet-500/20 border border-violet-500/30 rounded text-[9px] text-violet-300">
                                {pattern}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {/* Engagement Peak */}
            {typeof analysis.engagement_peak_sec === 'number' && (
                <div className="flex items-center gap-2 text-[10px] text-emerald-400">
                    <Sparkles className="w-3 h-3" />
                    Peak engagement at {analysis.engagement_peak_sec}s
                </div>
            )}

            {/* Best Comment */}
            {analysis.best_comment && (
                <div className="mt-2 p-2 bg-white/5 rounded-lg border border-white/10">
                    <div className="text-[10px] text-white/40 mb-1">💬 Top Comment</div>
                    <div className="text-xs text-white/80 line-clamp-2">"{analysis.best_comment}"</div>
                </div>
            )}
        </div>
    );
}

/** Video Embed Modal */
function EmbedModal({
    video,
    onClose
}: {
    video: VirloVideoItem;
    onClose: () => void;
}) {
    const videoId = extractVideoId(video.video_url, video.platform);
    const platformConfig = PLATFORM_CONFIG[video.platform];

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-md animate-fadeIn"
            onClick={onClose}
        >
            <div
                className="relative w-full max-w-md mx-4"
                onClick={e => e.stopPropagation()}
            >
                {/* Close Button */}
                <button
                    onClick={onClose}
                    className="absolute -top-12 right-0 p-2 rounded-full bg-white/10 hover:bg-white/20 text-white transition-all"
                >
                    <X className="w-6 h-6" />
                </button>

                {/* Embed Container */}
                <div className="relative aspect-[9/16] w-full bg-black rounded-2xl overflow-hidden border-2 border-white/20">
                    {videoId ? (
                        <iframe
                            src={platformConfig.embedUrl(videoId)}
                            className="absolute inset-0 w-full h-full"
                            allowFullScreen
                            allow="autoplay; encrypted-media"
                        />
                    ) : (
                        <div className="absolute inset-0 flex flex-col items-center justify-center gap-4">
                            <div className="text-4xl">{platformConfig.icon}</div>
                            <div className="text-sm text-white/60 text-center px-4">
                                임베드를 사용할 수 없습니다
                            </div>
                            <a
                                href={video.video_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm text-white flex items-center gap-2"
                            >
                                <ExternalLink className="w-4 h-4" />
                                {platformConfig.label}에서 보기
                            </a>
                        </div>
                    )}
                </div>

                {/* Video Info */}
                <div className="mt-4 text-center">
                    <h3 className="text-sm font-bold text-white line-clamp-2">{video.title}</h3>
                    {video.creator && (
                        <div className="text-xs text-white/50 mt-1">@{video.creator}</div>
                    )}
                </div>
            </div>
        </div>
    );
}

// ==================
// Main Component
// ==================

export function VirloVideoCard({
    video,
    onPlay,
    onPromote,
    onSave,
    onShare,
    showAnalysis = true,
    variant = 'default'
}: VirloVideoCardProps) {
    const [showEmbed, setShowEmbed] = useState(false);
    const [showAnalysisOverlay, setShowAnalysisOverlay] = useState(false);

    const tierConfig = video.outlier_tier ? TIER_CONFIG[video.outlier_tier] : null;
    const platformConfig = PLATFORM_CONFIG[video.platform];
    const TierIcon = tierConfig?.icon || BarChart;

    const multiplier = video.creator_avg_views && video.creator_avg_views > 0
        ? Math.round(video.view_count / video.creator_avg_views)
        : 0;

    const handlePlayClick = useCallback(() => {
        if (onPlay) {
            onPlay(video);
        } else {
            setShowEmbed(true);
        }
    }, [video, onPlay]);

    const isLarge = variant === 'large';
    const isCompact = variant === 'compact';

    return (
        <>
            <div
                className={`
                    group relative overflow-hidden rounded-2xl border transition-all duration-300
                    bg-gradient-to-br from-zinc-900/90 to-zinc-950/90 backdrop-blur
                    ${tierConfig?.border || 'border-white/10'}
                    ${tierConfig?.glow || ''}
                    hover:border-white/30 hover:scale-[1.02] hover:shadow-2xl
                    cursor-pointer
                `}
                onMouseEnter={() => setShowAnalysisOverlay(true)}
                onMouseLeave={() => setShowAnalysisOverlay(false)}
            >
                {/* Thumbnail Area */}
                <div
                    className={`
                        relative overflow-hidden
                        ${isLarge ? 'aspect-[9/16]' : isCompact ? 'aspect-video' : 'aspect-[4/5]'}
                    `}
                    onClick={handlePlayClick}
                >
                    {/* Thumbnail Image */}
                    {video.thumbnail_url ? (
                        <img
                            src={video.thumbnail_url}
                            alt={video.title}
                            className="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                        />
                    ) : (
                        <div className={`absolute inset-0 bg-gradient-to-br ${platformConfig.color} flex items-center justify-center`}>
                            <span className="text-6xl opacity-50">{platformConfig.icon}</span>
                        </div>
                    )}

                    {/* Gradient Overlay */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent" />

                    {/* Top Badges Row */}
                    <div className="absolute top-3 left-3 right-3 flex justify-between items-start">
                        {/* Tier Badge */}
                        {tierConfig && (
                            <div className={`
                                flex items-center gap-1 px-2 py-1 rounded-full text-[10px] font-black uppercase
                                ${tierConfig.bg} ${tierConfig.border} border backdrop-blur-sm
                                ${tierConfig.color}
                            `}>
                                <TierIcon className="w-3 h-3" />
                                {tierConfig.label}
                                {multiplier > 0 && (
                                    <span className="ml-1 font-mono">{multiplier}x</span>
                                )}
                            </div>
                        )}

                        {/* Platform Badge */}
                        <div className="px-2 py-1 rounded-full bg-black/60 backdrop-blur-sm text-[10px] font-bold text-white flex items-center gap-1">
                            <span>{platformConfig.icon}</span>
                            <span className="hidden sm:inline">{platformConfig.label}</span>
                        </div>
                    </div>

                    {/* Play Button (Center) */}
                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300">
                        <div className="w-16 h-16 rounded-full bg-white/20 backdrop-blur-md flex items-center justify-center transform scale-75 group-hover:scale-100 transition-transform duration-300">
                            <Play className="w-8 h-8 text-white fill-white ml-1" />
                        </div>
                    </div>

                    {/* Analysis Overlay */}
                    {showAnalysis && (
                        <AnalysisOverlay
                            analysis={video.analysis}
                            visible={showAnalysisOverlay}
                        />
                    )}

                    {/* Stats Bar (Bottom of thumbnail) */}
                    <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between">
                        <div className="flex items-center gap-2 px-2 py-1 rounded-full bg-black/60 backdrop-blur-sm text-[10px] text-white">
                            <span className="flex items-center gap-1">
                                <Eye className="w-3 h-3" />
                                {formatNumber(video.view_count)}
                            </span>
                            {typeof video.like_count === 'number' && (
                                <span className="flex items-center gap-1">
                                    <Heart className="w-3 h-3" />
                                    {formatNumber(video.like_count)}
                                </span>
                            )}
                            {typeof video.engagement_rate === 'number' && (
                                <span className="flex items-center gap-1 text-emerald-400">
                                    <TrendingUp className="w-3 h-3" />
                                    {(video.engagement_rate * 100).toFixed(1)}%
                                </span>
                            )}
                        </div>

                        {/* Hook Duration Badge */}
                        {typeof video.analysis?.hook_duration_sec === 'number' && (
                            <div className="px-2 py-1 rounded-full bg-cyan-500/20 backdrop-blur-sm text-[10px] text-cyan-300 font-mono">
                                🎯 {video.analysis.hook_duration_sec}s hook
                            </div>
                        )}
                    </div>
                </div>

                {/* Content Area */}
                <div className={`p-4 ${isCompact ? 'p-3' : ''}`}>
                    {/* Title */}
                    <h3 className={`
                        font-bold text-white leading-tight mb-2
                        ${isCompact ? 'text-sm line-clamp-1' : 'text-base line-clamp-2'}
                    `}>
                        {video.title || 'Untitled'}
                    </h3>

                    {/* Creator Row */}
                    {video.creator && !isCompact && (
                        <div className="flex items-center gap-2 mb-3">
                            {video.creator_avatar ? (
                                <img
                                    src={video.creator_avatar}
                                    alt={video.creator}
                                    className="w-5 h-5 rounded-full object-cover"
                                />
                            ) : (
                                <div className="w-5 h-5 rounded-full bg-white/10 flex items-center justify-center text-[10px]">
                                    👤
                                </div>
                            )}
                            <span className="text-xs text-white/60">@{video.creator}</span>
                        </div>
                    )}

                    {/* Tags */}
                    {video.tags && video.tags.length > 0 && !isCompact && (
                        <div className="flex flex-wrap gap-1 mb-3">
                            {video.tags.slice(0, 3).map((tag, i) => (
                                <span
                                    key={i}
                                    className="px-2 py-0.5 bg-white/5 border border-white/10 rounded text-[10px] text-white/60"
                                >
                                    #{tag}
                                </span>
                            ))}
                        </div>
                    )}

                    {/* Footer Actions */}
                    <div className="flex items-center justify-between pt-3 border-t border-white/5">
                        <div className="flex items-center gap-1 text-[10px] text-white/40">
                            <span className="px-2 py-0.5 bg-white/5 rounded">{video.category}</span>
                        </div>

                        <div className="flex items-center gap-1">
                            {onSave && (
                                <button
                                    onClick={(e) => { e.stopPropagation(); onSave(video); }}
                                    className="p-1.5 rounded-lg hover:bg-white/10 text-white/50 hover:text-white transition-all"
                                >
                                    <Bookmark className="w-4 h-4" />
                                </button>
                            )}
                            {onShare && (
                                <button
                                    onClick={(e) => { e.stopPropagation(); onShare(video); }}
                                    className="p-1.5 rounded-lg hover:bg-white/10 text-white/50 hover:text-white transition-all"
                                >
                                    <Share2 className="w-4 h-4" />
                                </button>
                            )}
                            {onPromote && (
                                <button
                                    onClick={(e) => { e.stopPropagation(); onPromote(video); }}
                                    className={`
                                        px-3 py-1 rounded-lg text-[10px] font-bold transition-all
                                        ${tierConfig
                                            ? `${tierConfig.bg} ${tierConfig.border} border ${tierConfig.color}`
                                            : 'bg-violet-500/20 border-violet-500/50 border text-violet-300'
                                        }
                                        hover:brightness-125
                                    `}
                                >
                                    <Zap className="w-3 h-3 inline mr-1" />
                                    Promote
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Embed Modal */}
            {showEmbed && (
                <EmbedModal
                    video={video}
                    onClose={() => setShowEmbed(false)}
                />
            )}
        </>
    );
}

export default VirloVideoCard;
