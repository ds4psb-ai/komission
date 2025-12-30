'use client';

/**
 * Outlier Manager - Complete Pipeline Curation UI with TikTok Embed
 * 
 * Uses shared components from /components/outlier for consistent UI
 * 
 * Pipeline Flow:
 * 1. [Crawl] → status: pending, analysis_status: pending
 * 2. [Promote] → status: promoted, analysis_status: pending (Node created)
 * 3. [Approve] → analysis_status: approved → (Background analysis starts)
 * 4. [Complete] → analysis_status: completed
 */

import { useState, useEffect } from 'react';
import { AppHeader } from '@/components/AppHeader';
import { api, OutlierItem } from '@/lib/api';
import { RefreshCw, TrendingUp, ChevronDown, Play } from 'lucide-react';

// Import shared outlier components
import {
    TikTokHoverPreview,
    TierBadge,
    OutlierMetrics,
    PipelineStatus,
    OutlierDetailModal,
    extractTikTokVideoId,
    getPipelineStage,
} from '@/components/outlier';

type StatusFilter = 'all' | 'pending' | 'promoted' | 'analyzing' | 'completed';

export default function OutliersPage() {
    const [outliers, setOutliers] = useState<OutlierItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [sortBy, setSortBy] = useState<'outlier_score' | 'view_count' | 'crawled_at'>('outlier_score');
    const [selectedItem, setSelectedItem] = useState<OutlierItem | null>(null);
    const [hoveredCard, setHoveredCard] = useState<string | null>(null);

    useEffect(() => {
        fetchOutliers();
    }, [sortBy]);

    async function fetchOutliers() {
        try {
            setLoading(true);
            const data = await api.listOutliers({ limit: 100, sortBy });
            setOutliers(data.items || []);
            setError(null);
        } catch (e) {
            console.error(e);
            setError('아웃라이어 목록을 불러오지 못했습니다.');
        } finally {
            setLoading(false);
        }
    }

    async function handlePromote(itemId: string, campaignEligible: boolean = false) {
        setActionLoading(itemId);
        try {
            const result = await api.promoteOutlier(itemId, campaignEligible);
            if (result.promoted) {
                await fetchOutliers();
                setSelectedItem(null);
            } else {
                alert('승격 실패');
            }
        } catch (e: any) {
            alert(`오류: ${e.message}`);
        } finally {
            setActionLoading(null);
        }
    }

    async function handleApprove(itemId: string) {
        setActionLoading(itemId);
        try {
            await api.approveVDGAnalysis(itemId);
            await fetchOutliers();
            setSelectedItem(null);
        } catch (e: any) {
            alert(`오류: ${e.message}`);
        } finally {
            setActionLoading(null);
        }
    }

    const filteredOutliers = outliers.filter(item => {
        if (statusFilter === 'all') return true;
        if (statusFilter === 'pending') return item.status === 'pending';
        if (statusFilter === 'promoted') return item.status === 'promoted' && item.analysis_status === 'pending';
        if (statusFilter === 'analyzing') return item.analysis_status === 'approved' || item.analysis_status === 'analyzing';
        if (statusFilter === 'completed') return item.analysis_status === 'completed';
        return true;
    });

    const stageCounts = {
        all: outliers.length,
        pending: outliers.filter(o => o.status === 'pending').length,
        promoted: outliers.filter(o => o.status === 'promoted' && o.analysis_status === 'pending').length,
        analyzing: outliers.filter(o => o.analysis_status === 'approved' || o.analysis_status === 'analyzing').length,
        completed: outliers.filter(o => o.analysis_status === 'completed').length,
    };

    return (
        <div className="min-h-screen bg-[#050505] text-white font-sans">
            <AppHeader />

            <main className="max-w-7xl mx-auto px-6 py-8">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h1 className="text-3xl font-black flex items-center gap-3">
                            <TrendingUp className="w-8 h-8 text-pink-400" />
                            Outlier Manager
                        </h1>
                        <p className="text-white/50 mt-1">클릭하여 TikTok 영상 재생 + 메타데이터 확인</p>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="relative">
                            <select
                                value={sortBy}
                                onChange={(e) => setSortBy(e.target.value as any)}
                                className="appearance-none px-4 py-2 pr-8 bg-white/5 border border-white/10 rounded-xl text-sm text-white/70"
                            >
                                <option value="outlier_score">아웃라이어 점수</option>
                                <option value="view_count">조회수</option>
                                <option value="crawled_at">최신순</option>
                            </select>
                            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40 pointer-events-none" />
                        </div>
                        <button
                            onClick={fetchOutliers}
                            disabled={loading}
                            className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-sm"
                        >
                            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                            새로고침
                        </button>
                    </div>
                </div>

                {/* Pipeline Stage Tabs */}
                <div className="flex items-center gap-2 mb-6 overflow-x-auto pb-2">
                    {[
                        { key: 'all', label: '전체' },
                        { key: 'pending', label: '🆕 크롤됨' },
                        { key: 'promoted', label: '📦 승격됨' },
                        { key: 'analyzing', label: '🔬 분석중' },
                        { key: 'completed', label: '✅ 완료' },
                    ].map(({ key, label }) => (
                        <button
                            key={key}
                            onClick={() => setStatusFilter(key as StatusFilter)}
                            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${statusFilter === key
                                ? 'bg-pink-500/20 text-pink-300 border border-pink-500/30'
                                : 'bg-white/5 text-white/50 hover:text-white hover:bg-white/10 border border-transparent'
                                }`}
                        >
                            {label}
                            <span className="text-xs opacity-60">({stageCounts[key as StatusFilter]})</span>
                        </button>
                    ))}
                </div>

                {/* Content */}
                {loading ? (
                    <div className="flex justify-center p-20">
                        <div className="w-8 h-8 border-4 border-pink-500 border-t-transparent rounded-full animate-spin" />
                    </div>
                ) : error ? (
                    <div className="p-8 text-center text-white/50 bg-white/5 rounded-2xl border border-white/10">
                        <p className="mb-4">{error}</p>
                        <button onClick={fetchOutliers} className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm">다시 시도</button>
                    </div>
                ) : filteredOutliers.length === 0 ? (
                    <div className="p-20 text-center text-white/30 border border-dashed border-white/10 rounded-2xl">
                        {statusFilter === 'all' ? '수집된 아웃라이어가 없습니다.' : `'${statusFilter}' 단계의 항목이 없습니다.`}
                    </div>
                ) : (
                    <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
                        {filteredOutliers.map((item) => {
                            const stage = getPipelineStage(item.status, item.analysis_status);
                            const videoId = extractTikTokVideoId(item.video_url);
                            const hasVideoId = !!videoId;

                            return (
                                <div
                                    key={item.id}
                                    onClick={() => setSelectedItem(item)}
                                    onMouseEnter={() => setHoveredCard(item.id)}
                                    onMouseLeave={() => setHoveredCard(null)}
                                    className={`group relative bg-white/5 hover:bg-white/[0.08] border rounded-2xl overflow-hidden cursor-pointer transition-all hover:scale-[1.02] ${hasVideoId ? 'border-white/10 hover:border-pink-500/30' : 'border-red-500/30 hover:border-red-500/50'
                                        }`}
                                >
                                    {/* Thumbnail with Hover Preview */}
                                    <div className="relative">
                                        <TikTokHoverPreview
                                            videoUrl={item.video_url}
                                            thumbnailUrl={item.thumbnail_url ?? undefined}
                                            isHovering={hoveredCard === item.id}
                                        />

                                        {/* Play button overlay */}
                                        {hoveredCard !== item.id && (
                                            <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity z-[3]">
                                                <div className="w-14 h-14 rounded-full bg-white/20 backdrop-blur-md flex items-center justify-center">
                                                    <Play className="w-7 h-7 text-white fill-white ml-1" />
                                                </div>
                                            </div>
                                        )}

                                        {/* No video ID warning */}
                                        {!hasVideoId && (
                                            <div className="absolute top-2 left-2 px-2 py-1 bg-red-500/80 rounded text-[9px] text-white font-bold z-[4]">
                                                ⚠️ NO VIDEO ID
                                            </div>
                                        )}

                                        {/* Top badges */}
                                        <div className="absolute top-2 right-2 flex items-center gap-1 z-[4]">
                                            <TierBadge tier={item.outlier_tier} size="sm" />
                                            <PipelineStatus
                                                status={item.status as 'pending' | 'promoted'}
                                                analysisStatus={item.analysis_status}
                                                size="sm"
                                            />
                                        </div>

                                        {/* Bottom metrics */}
                                        <div className="absolute bottom-2 left-2 right-2 z-[4]">
                                            <OutlierMetrics
                                                viewCount={item.view_count}
                                                outlierScore={item.outlier_score}
                                                layout="compact"
                                            />
                                        </div>
                                    </div>

                                    {/* Title */}
                                    <div className="p-3">
                                        <h3 className="font-bold text-xs line-clamp-2 text-white/90 group-hover:text-pink-300 transition-colors">
                                            {item.title || '(제목 없음)'}
                                        </h3>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </main>

            {/* OutlierDetailModal with VDG-based FilmingGuide */}
            {selectedItem && (
                <OutlierDetailModal
                    item={selectedItem}
                    onClose={() => setSelectedItem(null)}
                    onPromote={handlePromote}
                    onApprove={handleApprove}
                    actionLoading={actionLoading}
                />
            )}
        </div>
    );
}
