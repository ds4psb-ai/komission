"use client";
import { useTranslations } from 'next-intl';

/**
 * VirloGrid.tsx
 * 
 * Responsive grid layout for Virlo video cards
 * - Masonry-style or standard grid
 * - Infinite scroll ready
 * - Filter/Sort header
 */
import React, { useState } from 'react';
import { VirloVideoCard, VirloVideoItem } from './VirloVideoCard';
import { Grid, LayoutGrid, Filter, SlidersHorizontal, Search, X } from 'lucide-react';

interface VirloGridProps {
    videos: VirloVideoItem[];
    loading?: boolean;
    onLoadMore?: () => void;
    hasMore?: boolean;
    onVideoPlay?: (video: VirloVideoItem) => void;
    onVideoPromote?: (video: VirloVideoItem) => void;
    onVideoSave?: (video: VirloVideoItem) => void;
    showFilters?: boolean;
    title?: string;
}

// Platform filter options
const PLATFORMS = [
    { value: 'all', label: '전체', icon: '🌐' },
    { value: 'tiktok', label: 'TikTok', icon: '🎵' },
    { value: 'instagram', label: 'Reels', icon: '📷' },
    { value: 'youtube', label: 'Shorts', icon: '▶️' },
];

// Tier filter options
const TIERS = [
    { value: 'all', label: '전체' },
    { value: 'S', label: 'S-Tier', color: 'text-amber-400' },
    { value: 'A', label: 'A-Tier', color: 'text-purple-400' },
    { value: 'B', label: 'B-Tier', color: 'text-blue-400' },
];

// Sort options
const SORT_OPTIONS = [
    { value: 'views', label: '조회수' },
    { value: 'engagement', label: '참여율' },
    { value: 'recent', label: '최신순' },
    { value: 'multiplier', label: '아웃라이어' },
];

export function VirloGrid({
    videos,
    loading = false,
    onLoadMore,
    hasMore = false,
    onVideoPlay,
    onVideoPromote,
    onVideoSave,
    showFilters = true,
    title = '아웃라이어'
}: VirloGridProps) {
    const [layout, setLayout] = useState<'grid' | 'compact'>('grid');
    const [platform, setPlatform] = useState('all');
    const [tier, setTier] = useState('all');
    const [sort, setSort] = useState('views');
    const [search, setSearch] = useState('');
    const [showFilterPanel, setShowFilterPanel] = useState(false);

    // Filter videos
    let filteredVideos = videos;

    if (platform !== 'all') {
        filteredVideos = filteredVideos.filter(v => v.platform === platform);
    }

    if (tier !== 'all') {
        filteredVideos = filteredVideos.filter(v => v.outlier_tier === tier);
    }

    if (search) {
        const searchLower = search.toLowerCase();
        filteredVideos = filteredVideos.filter(v =>
            (v.title ?? '').toLowerCase().includes(searchLower) ||
            (v.creator ?? '').toLowerCase().includes(searchLower) ||
            (v.category ?? '').toLowerCase().includes(searchLower)
        );
    }

    const getTimeMs = (value?: string) => {
        const time = value ? Date.parse(value) : NaN;
        return Number.isNaN(time) ? 0 : time;
    };

    // Sort videos
    filteredVideos = [...filteredVideos].sort((a, b) => {
        switch (sort) {
            case 'views':
                return b.view_count - a.view_count;
            case 'engagement':
                return (b.engagement_rate || 0) - (a.engagement_rate || 0);
            case 'recent':
                return getTimeMs(b.crawled_at) - getTimeMs(a.crawled_at);
            case 'multiplier':
                const aMulti = a.creator_avg_views ? a.view_count / a.creator_avg_views : 0;
                const bMulti = b.creator_avg_views ? b.view_count / b.creator_avg_views : 0;
                return bMulti - aMulti;
            default:
                return 0;
        }
    });

    return (
        <div className="w-full">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                <div>
                    <h2 className="text-2xl font-bold text-white">{title}</h2>
                    <p className="text-sm text-white/50 mt-1">
                        {filteredVideos.length}개 발견 {videos.length !== filteredVideos.length && `(전체 ${videos.length}개)`}
                    </p>
                </div>

                <div className="flex items-center gap-2">
                    {/* Search */}
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
                        <input
                            type="text"
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                            placeholder="검색..."
                            className="pl-9 pr-8 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white placeholder-white/30 focus:outline-none focus:border-white/30 w-40 sm:w-48"
                        />
                        {search && (
                            <button
                                onClick={() => setSearch('')}
                                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-white/10 rounded"
                            >
                                <X className="w-3 h-3 text-white/50" />
                            </button>
                        )}
                    </div>

                    {/* Filter Toggle */}
                    {showFilters && (
                        <button
                            onClick={() => setShowFilterPanel(!showFilterPanel)}
                            className={`
                                p-2 rounded-lg border transition-all
                                ${showFilterPanel
                                    ? 'bg-white/10 border-white/30 text-white'
                                    : 'bg-white/5 border-white/10 text-white/60 hover:text-white'
                                }
                            `}
                        >
                            <SlidersHorizontal className="w-4 h-4" />
                        </button>
                    )}

                    {/* Layout Toggle */}
                    <div className="flex border border-white/10 rounded-lg overflow-hidden">
                        <button
                            onClick={() => setLayout('grid')}
                            className={`p-2 ${layout === 'grid' ? 'bg-white/10 text-white' : 'text-white/40 hover:text-white'}`}
                        >
                            <LayoutGrid className="w-4 h-4" />
                        </button>
                        <button
                            onClick={() => setLayout('compact')}
                            className={`p-2 ${layout === 'compact' ? 'bg-white/10 text-white' : 'text-white/40 hover:text-white'}`}
                        >
                            <Grid className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </div>

            {/* Filter Panel */}
            {showFilters && showFilterPanel && (
                <div className="mb-6 p-4 bg-white/5 border border-white/10 rounded-xl animate-fadeIn">
                    <div className="flex flex-wrap gap-6">
                        {/* Platform Filter */}
                        <div>
                            <div className="text-xs text-white/40 uppercase font-bold mb-2">플랫폼</div>
                            <div className="flex gap-2">
                                {PLATFORMS.map(p => (
                                    <button
                                        key={p.value}
                                        onClick={() => setPlatform(p.value)}
                                        className={`
                                            px-3 py-1.5 rounded-lg text-xs font-medium transition-all
                                            ${platform === p.value
                                                ? 'bg-white/20 text-white border border-white/30'
                                                : 'bg-white/5 text-white/60 hover:text-white border border-transparent'
                                            }
                                        `}
                                    >
                                        <span className="mr-1">{p.icon}</span>
                                        {p.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Tier Filter */}
                        <div>
                            <div className="text-xs text-white/40 uppercase font-bold mb-2">티어</div>
                            <div className="flex gap-2">
                                {TIERS.map(t => (
                                    <button
                                        key={t.value}
                                        onClick={() => setTier(t.value)}
                                        className={`
                                            px-3 py-1.5 rounded-lg text-xs font-medium transition-all
                                            ${tier === t.value
                                                ? `bg-white/20 border border-white/30 ${t.color || 'text-white'}`
                                                : 'bg-white/5 text-white/60 hover:text-white border border-transparent'
                                            }
                                        `}
                                    >
                                        {t.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Sort */}
                        <div>
                            <div className="text-xs text-white/40 uppercase font-bold mb-2">정렬</div>
                            <div className="flex gap-2">
                                {SORT_OPTIONS.map(s => (
                                    <button
                                        key={s.value}
                                        onClick={() => setSort(s.value)}
                                        className={`
                                            px-3 py-1.5 rounded-lg text-xs font-medium transition-all
                                            ${sort === s.value
                                                ? 'bg-violet-500/20 text-violet-300 border border-violet-500/30'
                                                : 'bg-white/5 text-white/60 hover:text-white border border-transparent'
                                            }
                                        `}
                                    >
                                        {s.label}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Grid */}
            <div className={`
                grid gap-4
                ${layout === 'grid'
                    ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'
                    : 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5'
                }
            `}>
                {filteredVideos.map(video => (
                    <VirloVideoCard
                        key={video.id}
                        video={video}
                        variant={layout === 'compact' ? 'compact' : 'default'}
                        onPlay={onVideoPlay}
                        onPromote={onVideoPromote}
                        onSave={onVideoSave}
                    />
                ))}
            </div>

            {/* Empty State */}
            {!loading && filteredVideos.length === 0 && (
                <div className="text-center py-20">
                    <div className="text-5xl mb-4">🎬</div>
                    <div className="text-lg text-white/60 mb-2">영상을 찾을 수 없습니다</div>
                    <div className="text-sm text-white/40">필터를 조정하거나 다른 검색어를 시도해보세요</div>
                </div>
            )}

            {/* Loading */}
            {loading && (
                <div className="flex justify-center py-8">
                    <div className="w-8 h-8 border-2 border-white/20 border-t-white/60 rounded-full animate-spin" />
                </div>
            )}

            {/* Load More */}
            {!loading && hasMore && onLoadMore && (
                <div className="flex justify-center mt-8">
                    <button
                        onClick={onLoadMore}
                        className="px-6 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-sm text-white/70 hover:text-white transition-all"
                    >
                        더 불러오기
                    </button>
                </div>
            )}
        </div>
    );
}

export default VirloGrid;
