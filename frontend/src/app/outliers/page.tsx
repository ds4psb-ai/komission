"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
    Filter,
    RefreshCw,
    Loader2,
    AlertCircle,
    Inbox,
    ChevronDown,
    Star,
    Award,
    Diamond,
    BarChart
} from 'lucide-react';
import { CrawlerOutlierCard, CrawlerOutlierItem } from '@/components/CrawlerOutlierCard';
import { api } from '@/lib/api';

type LoadingState = 'loading' | 'success' | 'error' | 'empty';

// Filter options
const PLATFORMS = [
    { id: 'all', label: '전체', icon: '🌐' },
    { id: 'tiktok', label: 'TikTok', icon: '🎵' },
    { id: 'youtube', label: 'Shorts', icon: '▶️' },
    { id: 'instagram', label: 'Reels', icon: '📷' },
];

const TIERS = [
    { id: 'all', label: '모든 티어', icon: Filter },
    { id: 'S', label: 'S-Tier', icon: Award },
    { id: 'A', label: 'A-Tier', icon: Star },
    { id: 'B', label: 'B-Tier', icon: Diamond },
    { id: 'C', label: 'C-Tier', icon: BarChart },
];

const FRESHNESS = [
    { id: '24h', label: '24시간' },
    { id: '7d', label: '7일' },
    { id: '30d', label: '30일' },
    { id: 'all', label: '전체 기간' },
];

const SORT_OPTIONS = [
    { id: 'outlier_score', label: 'Outlier Score' },
    { id: 'view_count', label: '조회수' },
    { id: 'engagement_rate', label: '참여율' },
    { id: 'crawled_at', label: '최신순' },
];

export default function OutliersPage() {
    const router = useRouter();
    const [items, setItems] = useState<CrawlerOutlierItem[]>([]);
    const [loadingState, setLoadingState] = useState<LoadingState>('loading');
    const [errorMessage, setErrorMessage] = useState('');
    const [promoting, setPromoting] = useState<string | null>(null);

    // Filters
    const [platform, setPlatform] = useState('all');
    const [tier, setTier] = useState('all');
    const [freshness, setFreshness] = useState('7d');
    const [sortBy, setSortBy] = useState('outlier_score');

    // Fetch outlier items
    const fetchOutliers = useCallback(async () => {
        setLoadingState('loading');
        setErrorMessage('');

        try {
            // Build query params
            const params = new URLSearchParams();
            if (platform !== 'all') params.set('platform', platform);
            if (tier !== 'all') params.set('tier', tier);
            params.set('freshness', freshness);
            params.set('sort_by', sortBy);
            params.set('limit', '50');

            const response = await fetch(`/api/v1/outliers/?${params.toString()}`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (!data.items || data.items.length === 0) {
                setLoadingState('empty');
                setItems([]);
            } else {
                setItems(data.items);
                setLoadingState('success');
            }
        } catch (e) {
            console.error('Failed to fetch outliers:', e);
            setLoadingState('error');
            setErrorMessage(e instanceof Error ? e.message : '데이터 로딩에 실패했습니다');

            // For demo: load mock data when API fails
            loadMockData();
        }
    }, [platform, tier, freshness, sortBy]);

    // Load mock data for development/demo
    const loadMockData = () => {
        const mockItems: CrawlerOutlierItem[] = [
            {
                id: '1',
                external_id: 'yt_abc123',
                video_url: 'https://youtube.com/shorts/abc123',
                platform: 'youtube',
                category: 'entertainment',
                title: '이 영상이 2500만뷰를 달성한 비결 🔥 초반 훅이 미쳤다',
                thumbnail_url: undefined,
                view_count: 25000000,
                like_count: 2100000,
                share_count: 350000,
                outlier_score: 523.5,
                outlier_tier: 'S',
                creator_avg_views: 48000,
                engagement_rate: 0.084,
                crawled_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
                status: 'pending',
            },
            {
                id: '2',
                external_id: 'tt_def456',
                video_url: 'https://tiktok.com/@user/video/def456',
                platform: 'tiktok',
                category: 'comedy',
                title: '😂 이게 왜 터짐 ㅋㅋㅋ 반전 개웃김',
                thumbnail_url: undefined,
                view_count: 8500000,
                like_count: 890000,
                share_count: 125000,
                outlier_score: 245.2,
                outlier_tier: 'A',
                creator_avg_views: 35000,
                engagement_rate: 0.105,
                crawled_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
                status: 'pending',
            },
            {
                id: '3',
                external_id: 'ig_ghi789',
                video_url: 'https://instagram.com/reel/ghi789',
                platform: 'instagram',
                category: 'beauty',
                title: '5초만에 완성하는 글로우 메이크업 ✨',
                thumbnail_url: undefined,
                view_count: 3200000,
                like_count: 420000,
                share_count: 28000,
                outlier_score: 128.0,
                outlier_tier: 'B',
                creator_avg_views: 25000,
                engagement_rate: 0.131,
                crawled_at: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
                status: 'pending',
            },
            {
                id: '4',
                external_id: 'yt_jkl012',
                video_url: 'https://youtube.com/shorts/jkl012',
                platform: 'youtube',
                category: 'gaming',
                title: '이 게임 꿀팁 모르면 손해 🎮',
                thumbnail_url: undefined,
                view_count: 1500000,
                like_count: 95000,
                share_count: 12000,
                outlier_score: 68.5,
                outlier_tier: 'C',
                creator_avg_views: 22000,
                engagement_rate: 0.063,
                crawled_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
                status: 'pending',
            },
            {
                id: '5',
                external_id: 'tt_mno345',
                video_url: 'https://tiktok.com/@creator/video/mno345',
                platform: 'tiktok',
                category: 'lifestyle',
                title: '아침 루틴 브이로그 ☀️ 생산성 200% 올리는 법',
                thumbnail_url: undefined,
                view_count: 950000,
                like_count: 78000,
                share_count: 8500,
                outlier_score: 52.3,
                outlier_tier: 'C',
                creator_avg_views: 18000,
                engagement_rate: 0.082,
                crawled_at: new Date(Date.now() - 36 * 60 * 60 * 1000).toISOString(),
                status: 'promoted',
            },
        ];

        // Apply filters
        let filtered = [...mockItems];

        if (platform !== 'all') {
            filtered = filtered.filter(i => i.platform === platform);
        }
        if (tier !== 'all') {
            filtered = filtered.filter(i => i.outlier_tier === tier);
        }

        // Apply sort
        filtered.sort((a, b) => {
            switch (sortBy) {
                case 'view_count': return b.view_count - a.view_count;
                case 'engagement_rate': return b.engagement_rate - a.engagement_rate;
                case 'crawled_at': return new Date(b.crawled_at).getTime() - new Date(a.crawled_at).getTime();
                default: return b.outlier_score - a.outlier_score;
            }
        });

        setItems(filtered);
        setLoadingState(filtered.length > 0 ? 'success' : 'empty');
    };

    useEffect(() => {
        fetchOutliers();
    }, [fetchOutliers]);

    // Handlers
    const handleView = (item: CrawlerOutlierItem) => {
        window.open(item.video_url, '_blank');
    };

    const handlePromote = async (item: CrawlerOutlierItem) => {
        if (promoting) return; // Prevent double-click

        setPromoting(item.id);
        try {
            const response = await fetch(`/api/v1/outliers/items/${item.id}/promote`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
                },
            });

            if (!response.ok) {
                throw new Error('승격 실패');
            }

            const result = await response.json();

            // Update item status locally
            setItems(prev => prev.map(i =>
                i.id === item.id ? { ...i, status: 'promoted' } : i
            ));

            // Redirect to canvas with the new node
            router.push(`/canvas?nodeId=${result.node_id}`);

        } catch (e) {
            console.error('Promote failed:', e);
            alert('승격에 실패했습니다. 다시 시도해주세요.');
        } finally {
            setPromoting(null);
        }
    };

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white">
            {/* Header */}
            <div className="border-b border-white/5 bg-black/40 sticky top-0 z-50 backdrop-blur-xl">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-2xl font-black flex items-center gap-3">
                                <span className="text-3xl">📡</span>
                                Outlier Discovery
                            </h1>
                            <p className="text-sm text-white/40 mt-1">
                                3-Platform에서 수집된 바이럴 아웃라이어
                            </p>
                        </div>
                        <button
                            onClick={fetchOutliers}
                            disabled={loadingState === 'loading'}
                            className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm transition-all disabled:opacity-50"
                        >
                            <RefreshCw className={`w-4 h-4 ${loadingState === 'loading' ? 'animate-spin' : ''}`} />
                            새로고침
                        </button>
                    </div>
                </div>
            </div>

            {/* Filters */}
            <div className="border-b border-white/5 bg-black/20">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <div className="flex flex-wrap gap-4 items-center">
                        {/* Platform Filter */}
                        <div className="flex items-center gap-2 bg-white/5 rounded-xl p-1">
                            {PLATFORMS.map((p) => (
                                <button
                                    key={p.id}
                                    onClick={() => setPlatform(p.id)}
                                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${platform === p.id
                                        ? 'bg-violet-500/20 text-violet-300 border border-violet-500/30'
                                        : 'text-white/50 hover:text-white/80 hover:bg-white/5'
                                        }`}
                                >
                                    <span>{p.icon}</span>
                                    <span className="hidden sm:inline">{p.label}</span>
                                </button>
                            ))}
                        </div>

                        {/* Tier Filter */}
                        <div className="relative">
                            <select
                                value={tier}
                                onChange={(e) => setTier(e.target.value)}
                                className="appearance-none bg-white/5 border border-white/10 rounded-lg px-4 py-2 pr-8 text-sm text-white focus:outline-none focus:border-violet-500/50"
                            >
                                {TIERS.map((t) => (
                                    <option key={t.id} value={t.id} className="bg-zinc-900">
                                        {t.label}
                                    </option>
                                ))}
                            </select>
                            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40 pointer-events-none" />
                        </div>

                        {/* Freshness Filter */}
                        <div className="relative">
                            <select
                                value={freshness}
                                onChange={(e) => setFreshness(e.target.value)}
                                className="appearance-none bg-white/5 border border-white/10 rounded-lg px-4 py-2 pr-8 text-sm text-white focus:outline-none focus:border-violet-500/50"
                            >
                                {FRESHNESS.map((f) => (
                                    <option key={f.id} value={f.id} className="bg-zinc-900">
                                        {f.label}
                                    </option>
                                ))}
                            </select>
                            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40 pointer-events-none" />
                        </div>

                        {/* Sort */}
                        <div className="relative ml-auto">
                            <select
                                value={sortBy}
                                onChange={(e) => setSortBy(e.target.value)}
                                className="appearance-none bg-white/5 border border-white/10 rounded-lg px-4 py-2 pr-8 text-sm text-white focus:outline-none focus:border-violet-500/50"
                            >
                                {SORT_OPTIONS.map((s) => (
                                    <option key={s.id} value={s.id} className="bg-zinc-900">
                                        정렬: {s.label}
                                    </option>
                                ))}
                            </select>
                            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40 pointer-events-none" />
                        </div>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-7xl mx-auto px-6 py-8">
                {/* Loading State */}
                {loadingState === 'loading' && (
                    <div className="flex flex-col items-center justify-center py-20 text-white/30 gap-4">
                        <Loader2 className="w-10 h-10 animate-spin text-violet-500" />
                        <p className="text-sm">아웃라이어 로딩중...</p>
                    </div>
                )}

                {/* Error State */}
                {loadingState === 'error' && (
                    <div className="flex flex-col items-center justify-center py-20 text-center">
                        <AlertCircle className="w-12 h-12 text-red-400 mb-4" />
                        <h3 className="text-lg font-bold text-white mb-2">로딩 실패</h3>
                        <p className="text-sm text-white/40 mb-6 max-w-sm">{errorMessage}</p>
                        <button
                            onClick={fetchOutliers}
                            className="px-6 py-2.5 bg-violet-500/20 hover:bg-violet-500/30 text-violet-300 border border-violet-500/30 rounded-xl text-sm font-bold transition-all"
                        >
                            🔄 다시 시도
                        </button>
                    </div>
                )}

                {/* Empty State */}
                {loadingState === 'empty' && (
                    <div className="flex flex-col items-center justify-center py-20 text-center">
                        <Inbox className="w-12 h-12 text-white/20 mb-4" />
                        <h3 className="text-lg font-bold text-white mb-2">아웃라이어 없음</h3>
                        <p className="text-sm text-white/40 max-w-sm">
                            현재 필터 조건에 해당하는 아웃라이어가 없습니다.<br />
                            필터를 변경하거나 크롤러를 실행해주세요.
                        </p>
                    </div>
                )}

                {/* Success State - Grid */}
                {loadingState === 'success' && (
                    <>
                        <div className="flex items-center justify-between mb-6">
                            <p className="text-sm text-white/40">
                                {items.length}개의 아웃라이어
                            </p>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {items.map((item) => (
                                <CrawlerOutlierCard
                                    key={item.id}
                                    item={item}
                                    onView={handleView}
                                    onPromote={handlePromote}
                                />
                            ))}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
