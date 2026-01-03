"use client";
import { useTranslations } from 'next-intl';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { X, Filter, Loader2, AlertCircle, Inbox } from 'lucide-react';
import { CrawlerOutlierCard, CrawlerOutlierItem } from '@/components/CrawlerOutlierCard';

interface CrawlerOutlierSelectorProps {
    isOpen: boolean;
    onClose: () => void;
    onSelect: (item: CrawlerOutlierItem) => void;
}

// Filter options
const PLATFORMS = [
    { id: 'all', label: '전체', icon: '🌐' },
    { id: 'tiktok', label: 'TikTok', icon: '🎵' },
    { id: 'youtube', label: 'Shorts', icon: '▶️' },
    { id: 'instagram', label: 'Reels', icon: '📷' },
];

const TIERS = [
    { id: 'all', label: '전체' },
    { id: 'S', label: 'S-Tier' },
    { id: 'A', label: 'A-Tier' },
    { id: 'B', label: 'B-Tier' },
    { id: 'C', label: 'C-Tier' },
];

// Mock data for development
const MOCK_OUTLIERS: CrawlerOutlierItem[] = [
    {
        id: '1',
        external_id: 'yt_abc123',
        video_url: 'https://youtube.com/shorts/abc123',
        platform: 'youtube',
        category: 'K-Beauty',
        title: '한국 스킨케어 루틴 🧴 글로우 업 비밀',
        thumbnail_url: 'https://picsum.photos/seed/kbeauty1/400/600',
        view_count: 2500000,
        like_count: 180000,
        outlier_score: 523,
        outlier_tier: 'S',
        creator_avg_views: 4800,
        engagement_rate: 0.123,
        crawled_at: new Date(Date.now() - 3600000 * 2).toISOString(),
        status: 'pending',
    },
    {
        id: '2',
        external_id: 'tt_xyz789',
        video_url: 'https://tiktok.com/@user/video/xyz789',
        platform: 'tiktok',
        category: 'K-Food',
        title: '분식집 떡볶이 레시피 🍜 엄마표 비법',
        thumbnail_url: 'https://picsum.photos/seed/kfood1/400/600',
        view_count: 1800000,
        like_count: 250000,
        outlier_score: 312,
        outlier_tier: 'A',
        creator_avg_views: 5700,
        engagement_rate: 0.156,
        crawled_at: new Date(Date.now() - 3600000 * 5).toISOString(),
        status: 'pending',
    },
    {
        id: '3',
        external_id: 'ig_def456',
        video_url: 'https://instagram.com/reel/def456',
        platform: 'instagram',
        category: 'K-Meme',
        title: '한국 직장인 일상 be like... 😂',
        thumbnail_url: 'https://picsum.photos/seed/kmeme1/400/600',
        view_count: 980000,
        like_count: 89000,
        outlier_score: 156,
        outlier_tier: 'B',
        creator_avg_views: 6200,
        engagement_rate: 0.098,
        crawled_at: new Date(Date.now() - 3600000 * 12).toISOString(),
        status: 'pending',
    },
    {
        id: '4',
        external_id: 'yt_short456',
        video_url: 'https://youtube.com/shorts/short456',
        platform: 'youtube',
        category: 'K-Pop Dance',
        title: 'NewJeans Ditto 안무 튜토리얼 💃',
        thumbnail_url: 'https://picsum.photos/seed/kpop1/400/600',
        view_count: 4200000,
        like_count: 320000,
        outlier_score: 847,
        outlier_tier: 'S',
        creator_avg_views: 4950,
        engagement_rate: 0.089,
        crawled_at: new Date(Date.now() - 3600000 * 8).toISOString(),
        status: 'pending',
    },
    {
        id: '5',
        external_id: 'tt_trend789',
        video_url: 'https://tiktok.com/@creator/video/trend789',
        platform: 'tiktok',
        category: 'ASMR',
        title: '한국 편의점 먹방 ASMR 🏪',
        thumbnail_url: 'https://picsum.photos/seed/asmr1/400/600',
        view_count: 750000,
        like_count: 95000,
        outlier_score: 98,
        outlier_tier: 'C',
        creator_avg_views: 7600,
        engagement_rate: 0.142,
        crawled_at: new Date(Date.now() - 3600000 * 24).toISOString(),
        status: 'pending',
    },
    {
        id: '6',
        external_id: 'ig_style999',
        video_url: 'https://instagram.com/reel/style999',
        platform: 'instagram',
        category: 'K-Fashion',
        title: '명동 스트릿 패션 스냅 👗',
        thumbnail_url: 'https://picsum.photos/seed/kfashion1/400/600',
        view_count: 1200000,
        like_count: 145000,
        outlier_score: 203,
        outlier_tier: 'A',
        creator_avg_views: 5900,
        engagement_rate: 0.134,
        crawled_at: new Date(Date.now() - 3600000 * 18).toISOString(),
        status: 'pending',
    },
];

/**
 * CrawlerOutlierSelector
 * Modal for selecting crawler outliers to add to canvas
 */
export function CrawlerOutlierSelector({
    isOpen,
    onClose,
    onSelect,
}: CrawlerOutlierSelectorProps) {
    const [items, setItems] = useState<CrawlerOutlierItem[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const isMountedRef = useRef(true);

    // Filters
    const [platform, setPlatform] = useState('all');
    const [tier, setTier] = useState('all');

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    // Load data (mock for now)
    const loadData = useCallback(async () => {
        if (isMountedRef.current) {
            setLoading(true);
            setError(null);
        }
        try {
            // TODO: Replace with actual API call
            // const response = await fetch('/api/v1/outliers?platform=...&tier=...');
            await new Promise((r) => setTimeout(r, 300)); // Simulate network
            if (!isMountedRef.current) return;
            setItems(MOCK_OUTLIERS);
        } catch (err) {
            if (!isMountedRef.current) return;
            setError('Failed to load outliers');
        } finally {
            if (isMountedRef.current) {
                setLoading(false);
            }
        }
    }, []);

    useEffect(() => {
        if (isOpen) {
            loadData();
        }
    }, [isOpen, loadData]);

    // Apply filters
    const filteredItems = items.filter((item) => {
        if (platform !== 'all' && item.platform !== platform) return false;
        if (tier !== 'all' && item.outlier_tier !== tier) return false;
        return true;
    });

    if (!isOpen) return null;

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
            onClick={(e) => e.target === e.currentTarget && onClose()}
        >
            <div className="w-full max-w-4xl max-h-[80vh] bg-zinc-900 border border-white/10 rounded-2xl overflow-hidden flex flex-col shadow-2xl">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
                    <div>
                        <h2 className="text-lg font-bold text-white">Crawler Outliers</h2>
                        <p className="text-xs text-white/50">3-플랫폼 아웃라이어에서 선택하여 Canvas에 추가</p>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5 text-white/60" />
                    </button>
                </div>

                {/* Filters */}
                <div className="px-6 py-3 border-b border-white/5 flex items-center gap-4 bg-black/20">
                    <Filter className="w-4 h-4 text-white/40" />

                    {/* Platform Filter */}
                    <div className="flex gap-1">
                        {PLATFORMS.map((p) => (
                            <button
                                key={p.id}
                                onClick={() => setPlatform(p.id)}
                                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${platform === p.id
                                        ? 'bg-violet-500/20 text-violet-300 border border-violet-500/40'
                                        : 'bg-white/5 text-white/50 hover:bg-white/10 border border-transparent'
                                    }`}
                            >
                                {p.icon} {p.label}
                            </button>
                        ))}
                    </div>

                    <div className="w-px h-6 bg-white/10" />

                    {/* Tier Filter */}
                    <div className="flex gap-1">
                        {TIERS.map((t) => (
                            <button
                                key={t.id}
                                onClick={() => setTier(t.id)}
                                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${tier === t.id
                                        ? 'bg-violet-500/20 text-violet-300 border border-violet-500/40'
                                        : 'bg-white/5 text-white/50 hover:bg-white/10 border border-transparent'
                                    }`}
                            >
                                {t.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6">
                    {loading && (
                        <div className="flex flex-col items-center justify-center py-12">
                            <Loader2 className="w-8 h-8 text-violet-400 animate-spin" />
                            <p className="mt-3 text-sm text-white/50">Loading outliers...</p>
                        </div>
                    )}

                    {error && (
                        <div className="flex flex-col items-center justify-center py-12">
                            <AlertCircle className="w-8 h-8 text-red-400" />
                            <p className="mt-3 text-sm text-red-400">{error}</p>
                        </div>
                    )}

                    {!loading && !error && filteredItems.length === 0 && (
                        <div className="flex flex-col items-center justify-center py-12">
                            <Inbox className="w-8 h-8 text-white/20" />
                            <p className="mt-3 text-sm text-white/40">No outliers found</p>
                        </div>
                    )}

                    {!loading && !error && filteredItems.length > 0 && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {filteredItems.map((item) => (
                                <div
                                    key={item.id}
                                    onClick={() => onSelect(item)}
                                    className="cursor-pointer transform hover:scale-[1.02] transition-transform"
                                >
                                    <CrawlerOutlierCard
                                        item={item}
                                        compact
                                    />
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="px-6 py-3 border-t border-white/10 bg-black/20 flex justify-between items-center">
                    <span className="text-xs text-white/40">
                        {filteredItems.length}개 항목
                    </span>
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-xs font-medium text-white/60 hover:text-white transition-colors"
                    >
                        취소
                    </button>
                </div>
            </div>
        </div>
    );
}

export default CrawlerOutlierSelector;
