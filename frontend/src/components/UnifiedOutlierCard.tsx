"use client";
import { useTranslations } from 'next-intl';
import Image from 'next/image';

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
 * - Next.js Image Optimization for stable thumbnail loading
 */
import React, { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Heart, TrendingUp, Star, Gift, Play, Volume2, VolumeX, Maximize2 } from 'lucide-react';
import { PlatformBadge, OutlierScoreBadge, OutlierCardFooter, ViewCountBadge } from '@/components/outlier';

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
    creator_username?: string | null;
    upload_date?: string | null;  // Original video upload date
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

export function UnifiedOutlierCard({ item, onPromote }: UnifiedOutlierCardProps) {
    const router = useRouter();

    const isPromoted = item.status === 'promoted';
    const hasVDG = !!item.vdg_analysis;

    const handleClick = () => {
        // Use hard navigation to avoid Next.js client-side routing state issues
        window.location.href = `/video/${item.id}`;
    };

    const [isHovered, setIsHovered] = useState(false);
    const [isVideoLoaded, setIsVideoLoaded] = useState(false);
    const [thumbnailError, setThumbnailError] = useState(false);
    const videoRef = useRef<HTMLVideoElement>(null);
    let hoverTimeout: NodeJS.Timeout;

    const handleMouseEnter = () => {
        hoverTimeout = setTimeout(() => {
            setIsHovered(true);
            if (videoRef.current) {
                videoRef.current.play().catch(() => { });
            }
        }, 150); // Slight delay to prevent flickering
    };

    const handleMouseLeave = () => {
        clearTimeout(hoverTimeout);
        setIsHovered(false);
        if (videoRef.current) {
            videoRef.current.pause();
            videoRef.current.currentTime = 0;
        }
    };

    // Determine border color based on tier (optional, or keep generic)
    // Determine border color based on tier
    const tier = item.outlier_tier || 'C';
    let borderColor = 'border-white/5';
    let shadowColor = 'shadow-transparent';

    if (tier === 'S') {
        borderColor = 'border-[#c1ff00]/30';
        shadowColor = 'group-hover:shadow-[0_0_30px_rgba(193,255,0,0.3)]';
    }
    if (tier === 'A') {
        borderColor = 'border-purple-500/30';
        shadowColor = 'group-hover:shadow-[0_0_20px_rgba(168,85,247,0.3)]';
    }

    return (
        <div
            onClick={handleClick}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
            className={`
                group relative cursor-pointer overflow-hidden rounded-3xl border
                bg-black ${borderColor} ${shadowColor} transition-all duration-500 hover:scale-[1.02] hover:-translate-y-1
            `}
        >
            {/* Thumbnail & Video Area */}
            <div className="relative aspect-[9/16] overflow-hidden bg-zinc-900">
                {/* Video Preview (Hidden until hovered) */}
                <video
                    ref={videoRef}
                    src={item.video_url} // Ensure video_url is a direct playable link
                    muted
                    loop
                    playsInline
                    className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-500 ${isHovered ? 'opacity-100' : 'opacity-0'}`}
                    onLoadedData={() => setIsVideoLoaded(true)}
                />

                {/* Thumbnail (Fades out on hover if video is ready) - using Next.js Image for stable loading */}
                {/* For Instagram: If thumbnail fails, show embed iframe as fallback */}
                {item.platform === 'instagram' && (!item.thumbnail_url || thumbnailError) ? (
                    <iframe
                        src={`https://www.instagram.com/reel/${item.video_url?.match(/\/(reel|p|reels)\/([A-Za-z0-9_-]+)/)?.[2]}/embed/`}
                        className="absolute inset-0 w-full h-full"
                        allow="encrypted-media"
                        frameBorder="0"
                        loading="lazy"
                    />
                ) : item.thumbnail_url ? (
                    <Image
                        src={`https://images.weserv.nl/?url=${encodeURIComponent(item.thumbnail_url)}&output=jpg&default=404`}
                        alt={item.title}
                        fill
                        className={`object-cover transition-opacity duration-500 ${isHovered && isVideoLoaded ? 'opacity-0' : 'opacity-100'}`}
                        sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
                        unoptimized={false}
                        onError={() => setThumbnailError(true)}
                    />
                ) : (
                    <div className="w-full h-full flex items-center justify-center">
                        <span className="text-4xl opacity-20">🎬</span>
                    </div>
                )}

                {/* Gradient Overlay - Dynamic */}
                <div className={`absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent transition-opacity duration-300 ${isHovered ? 'opacity-90' : 'opacity-60'}`} />

                {/* Smart Metadata Overlay */}
                <div className="absolute inset-0 p-4 flex flex-col justify-between">

                    {/* Top Section */}
                    <div className="flex justify-between items-start">
                        {/* View Badge */}
                        <ViewCountBadge viewCount={item.view_count} size="md" />

                        {/* Outlier Score */}
                        <OutlierScoreBadge
                            score={item.outlier_score}
                            tier={item.outlier_tier}
                            size="md"
                        />
                    </div>

                    {/* Bottom Section - Slide Up on Hover */}
                    <div className="transform transition-transform duration-300 translate-y-2 group-hover:translate-y-0">
                        {/* Platform & Promoted */}
                        <div className="flex items-center gap-2 mb-2">
                            <PlatformBadge platform={item.platform} size="sm" />
                            {isPromoted && (
                                <span className="px-1.5 py-0.5 bg-[#c1ff00]/20 border border-[#c1ff00]/30 rounded text-[9px] font-black text-[#c1ff00] uppercase">
                                    PROMOTED
                                </span>
                            )}
                        </div>

                        {/* Title */}
                        <h3 className={`text-sm font-bold text-white leading-tight line-clamp-2 mb-2 transition-colors ${isHovered ? 'text-white' : 'text-white/80'}`}>
                            {item.title || 'Untitled'}
                        </h3>

                        {/* Creator Info - Always Visible */}
                        <OutlierCardFooter
                            creatorUsername={item.creator_username}
                            uploadDate={item.upload_date}
                            crawledAt={item.crawled_at}
                            className="mb-1"
                        />

                        {/* Extended Stats (Only visible on hover) */}
                        <div className={`space-y-2 overflow-hidden transition-all duration-300 ${isHovered ? 'max-h-20 opacity-100' : 'max-h-0 opacity-0'}`}>
                            <div className="flex items-center gap-3 text-[10px] font-mono text-white/60">
                                {typeof item.like_count === 'number' && (
                                    <span className="flex items-center gap-1">
                                        <Heart className={`w-3 h-3 ${isHovered ? 'text-pink-500 fill-pink-500' : ''}`} />
                                        {formatNumber(item.like_count)}
                                    </span>
                                )}
                                {typeof item.engagement_rate === 'number' && (
                                    <span className="flex items-center gap-1">
                                        <TrendingUp className={`w-3 h-3 ${isHovered ? 'text-[#c1ff00]' : ''}`} />
                                        <span className={isHovered ? 'text-[#c1ff00]' : ''}>{(item.engagement_rate * 100).toFixed(1)}%</span>
                                    </span>
                                )}
                            </div>

                            <div className="flex items-center gap-2">
                                <span className="px-1.5 py-0.5 bg-white/10 rounded text-[9px] text-white/40 uppercase tracking-wide">
                                    {item.category}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Play Icon Overlay (Only on hover) */}
                <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 transition-all duration-300 ${isHovered ? 'opacity-100 scale-100' : 'opacity-0 scale-50'}`}>
                    <div className="w-14 h-14 rounded-full bg-[#c1ff00]/90 backdrop-blur flex items-center justify-center shadow-[0_0_30px_rgba(193,255,0,0.5)]">
                        <Play className="w-6 h-6 text-black fill-black ml-1" />
                    </div>
                </div>
            </div>

            {/* Promote Button (if callback provided and not promoted) */}
            {onPromote && !isPromoted && (
                <div className="flex border-t border-white/5 divide-x divide-white/5">
                    <button
                        onClick={(e) => { e.stopPropagation(); onPromote(item, false); }}
                        className={`
                            flex-1 py-3 text-xs font-bold flex items-center justify-center gap-1.5 transition-all
                            text-violet-300 hover:bg-violet-500/10 hover:text-white uppercase tracking-wider
                        `}
                    >
                        <Star className="w-3.5 h-3.5" />
                        PROMOTE
                    </button>
                    <button
                        onClick={(e) => { e.stopPropagation(); onPromote(item, true); }}
                        className="flex-1 py-3 text-xs font-bold flex items-center justify-center gap-1.5 text-[#c1ff00] hover:bg-[#c1ff00]/10 transition-all uppercase tracking-wider"
                        title="오거닉 바이럴 후보로 등록"
                    >
                        <Gift className="w-3.5 h-3.5" />
                        Organic
                    </button>
                </div>
            )}
        </div>
    );
}

export default UnifiedOutlierCard;
