"use client";

/**
 * Trending Page - 뉴스 모드 (아웃라이어 피드)
 * 
 * 문서: docs/21_PAGE_IA_REDESIGN.md
 * - 엄선된 아웃라이어를 뉴스처럼 훑어보는 가치
 * - 기존 메인 페이지 피드 재사용
 */
import { useState, useEffect } from "react";
import { api, OutlierItem } from "@/lib/api";
import { UnifiedOutlierCard, OutlierCardItem } from "@/components/UnifiedOutlierCard";
import {
    TrendingUp, RefreshCw, Loader2, Award, Star,
    Film, Smile, Palette, Utensils, Dumbbell, ShoppingBag
} from "lucide-react";

const PLATFORMS = [
    { id: 'all', label: '전체', icon: '🌐' },
    { id: 'tiktok', label: 'TikTok', icon: '🎵' },
    { id: 'youtube', label: 'Shorts', icon: '▶️' },
    { id: 'instagram', label: 'Reels', icon: '📷' },
];

const CATEGORIES = [
    { id: 'all', label: '전체', icon: Film },
    { id: 'meme', label: '밈', icon: Smile },
    { id: 'beauty', label: '뷰티', icon: Palette },
    { id: 'food', label: 'F&B', icon: Utensils },
    { id: 'fitness', label: '피트니스', icon: Dumbbell },
    { id: 'lifestyle', label: '라이프', icon: ShoppingBag },
];

// Empty fallback - no more hardcoded demo data
const DEMO_ITEMS: OutlierCardItem[] = [];

function mapToCardItem(item: OutlierItem): OutlierCardItem {
    return {
        id: item.id,
        external_id: item.external_id,
        video_url: item.video_url,
        platform: item.platform as 'tiktok' | 'instagram' | 'youtube',
        title: item.title || 'Untitled',
        thumbnail_url: item.thumbnail_url || undefined,
        category: item.category,
        view_count: item.view_count,
        like_count: item.like_count,
        share_count: item.share_count,
        outlier_score: item.outlier_score,
        outlier_tier: item.outlier_tier as 'S' | 'A' | 'B' | 'C' | null,
        creator_avg_views: item.creator_avg_views,
        engagement_rate: item.engagement_rate,
        crawled_at: item.crawled_at || undefined,
        status: item.status as 'pending' | 'selected' | 'rejected' | 'promoted',
        vdg_analysis: item.vdg_analysis,
    };
}

export default function TrendingPage() {
    const [items, setItems] = useState<OutlierCardItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [platform, setPlatform] = useState('all');
    const [category, setCategory] = useState('all');

    useEffect(() => {
        fetchOutliers();
    }, [platform]);

    async function fetchOutliers() {
        setIsLoading(true);
        try {
            const params: Record<string, string> = { limit: '50' };
            if (platform !== 'all') params.platform = platform;
            const response = await api.listOutliers(params);
            if (response.items && response.items.length > 0) {
                setItems(response.items.map(mapToCardItem));
            } else {
                setItems(DEMO_ITEMS);
            }
        } catch {
            setItems(DEMO_ITEMS);
        } finally {
            setIsLoading(false);
        }
    }

    const filteredItems = items.filter(item => {
        if (category !== 'all' && item.category !== category) return false;
        return true;
    });

    const tierCounts = {
        S: items.filter(i => i.outlier_tier === 'S').length,
        A: items.filter(i => i.outlier_tier === 'A').length,
    };

    return (
        <div className="min-h-screen bg-background pb-24">
            {/* Header */}
            <header className="sticky top-0 z-40 px-4 py-4 backdrop-blur-xl bg-background/80 border-b border-white/5">
                <div className="flex items-center justify-between max-w-7xl mx-auto">
                    <div className="flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-emerald-400" />
                        <h1 className="text-lg font-bold">Trending</h1>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                        <span className="flex items-center gap-1 px-2 py-1 bg-amber-500/10 rounded-lg text-amber-300">
                            <Award className="w-3 h-3" />S: {tierCounts.S}
                        </span>
                        <span className="flex items-center gap-1 px-2 py-1 bg-purple-500/10 rounded-lg text-purple-300">
                            <Star className="w-3 h-3" />A: {tierCounts.A}
                        </span>
                        <button
                            onClick={fetchOutliers}
                            disabled={isLoading}
                            className="p-1.5 bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
                        >
                            <RefreshCw className={`w-3.5 h-3.5 text-white/50 ${isLoading ? 'animate-spin' : ''}`} />
                        </button>
                    </div>
                </div>
            </header>

            {/* Filters */}
            <section className="px-4 py-3 max-w-7xl mx-auto border-b border-white/5">
                <div className="flex flex-col sm:flex-row gap-3">
                    {/* Platform */}
                    <div className="flex items-center gap-1 p-1 bg-white/5 rounded-xl overflow-x-auto">
                        {PLATFORMS.map(p => (
                            <button
                                key={p.id}
                                onClick={() => setPlatform(p.id)}
                                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all whitespace-nowrap ${platform === p.id
                                    ? 'bg-white text-black'
                                    : 'text-white/50 hover:text-white hover:bg-white/10'
                                    }`}
                            >
                                <span>{p.icon}</span>
                                <span>{p.label}</span>
                            </button>
                        ))}
                    </div>

                    {/* Category */}
                    <div className="flex items-center gap-1 overflow-x-auto">
                        {CATEGORIES.map(cat => (
                            <button
                                key={cat.id}
                                onClick={() => setCategory(cat.id)}
                                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${category === cat.id
                                    ? 'bg-violet-500/20 text-violet-300 border border-violet-500/30'
                                    : 'text-white/50 hover:text-white hover:bg-white/5'
                                    }`}
                            >
                                <cat.icon className="w-3 h-3" />{cat.label}
                            </button>
                        ))}
                    </div>
                </div>
            </section>

            {/* Grid */}
            <main className="max-w-7xl mx-auto px-4 py-6">
                <div className="text-xs text-white/50 mb-4">
                    {filteredItems.length}개 발견
                </div>

                {isLoading ? (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
                    </div>
                ) : filteredItems.length === 0 ? (
                    <div className="text-center py-16">
                        <div className="text-3xl mb-3">🔍</div>
                        <div className="text-white/50 text-sm">결과가 없습니다</div>
                        <button
                            onClick={() => { setPlatform('all'); setCategory('all'); }}
                            className="mt-3 text-xs text-violet-400"
                        >
                            필터 초기화
                        </button>
                    </div>
                ) : (
                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                        {filteredItems.map(item => (
                            <UnifiedOutlierCard key={item.id} item={item} />
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}
