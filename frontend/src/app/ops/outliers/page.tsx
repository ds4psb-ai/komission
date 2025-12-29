'use client';

/**
 * Outlier Manager - Complete Pipeline Curation UI
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
import {
    RefreshCw, TrendingUp, ExternalLink, Play, Sparkles, Check,
    ArrowUpRight, Eye, MessageCircle, Filter, ChevronDown
} from 'lucide-react';
import Link from 'next/link';

type StatusFilter = 'all' | 'pending' | 'promoted' | 'analyzing' | 'completed';

export default function OutliersPage() {
    const [outliers, setOutliers] = useState<OutlierItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [sortBy, setSortBy] = useState<'outlier_score' | 'view_count' | 'crawled_at'>('outlier_score');

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

    // Step 1: Promote to Node (pending → promoted)
    async function handlePromote(itemId: string) {
        setActionLoading(itemId);
        try {
            const result = await api.promoteOutlier(itemId);
            if (result.promoted) {
                await fetchOutliers();
            } else {
                alert('승격 실패');
            }
        } catch (e: any) {
            alert(`오류: ${e.message}`);
        } finally {
            setActionLoading(null);
        }
    }

    // Step 2: Approve VDG Analysis (promoted+pending → approved → analyzing → completed)
    async function handleApprove(itemId: string) {
        setActionLoading(itemId);
        try {
            await api.approveVDGAnalysis(itemId);
            await fetchOutliers();
        } catch (e: any) {
            alert(`오류: ${e.message}`);
        } finally {
            setActionLoading(null);
        }
    }

    // Filter logic based on pipeline status
    const filteredOutliers = outliers.filter(item => {
        if (statusFilter === 'all') return true;
        if (statusFilter === 'pending') {
            return item.status === 'pending';
        }
        if (statusFilter === 'promoted') {
            return item.status === 'promoted' && item.analysis_status === 'pending';
        }
        if (statusFilter === 'analyzing') {
            return item.analysis_status === 'approved' || item.analysis_status === 'analyzing';
        }
        if (statusFilter === 'completed') {
            return item.analysis_status === 'completed';
        }
        return true;
    });

    // Count by pipeline stage
    const stageCounts = {
        all: outliers.length,
        pending: outliers.filter(o => o.status === 'pending').length,
        promoted: outliers.filter(o => o.status === 'promoted' && o.analysis_status === 'pending').length,
        analyzing: outliers.filter(o => o.analysis_status === 'approved' || o.analysis_status === 'analyzing').length,
        completed: outliers.filter(o => o.analysis_status === 'completed').length,
    };

    // Determine item's pipeline stage
    const getPipelineStage = (item: OutlierItem) => {
        if (item.analysis_status === 'completed') return 'completed';
        if (item.analysis_status === 'approved' || item.analysis_status === 'analyzing') return 'analyzing';
        if (item.status === 'promoted') return 'promoted';
        return 'pending';
    };

    // Render stage badge
    const getStageBadge = (item: OutlierItem) => {
        const stage = getPipelineStage(item);
        switch (stage) {
            case 'pending':
                return <span className="px-2 py-0.5 bg-white/10 text-white/50 text-[10px] rounded-full font-bold">크롤됨</span>;
            case 'promoted':
                return <span className="px-2 py-0.5 bg-blue-500/20 text-blue-300 text-[10px] rounded-full font-bold">승격됨</span>;
            case 'analyzing':
                return <span className="px-2 py-0.5 bg-purple-500/20 text-purple-300 text-[10px] rounded-full font-bold animate-pulse">분석중</span>;
            case 'completed':
                return <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-300 text-[10px] rounded-full font-bold">완료</span>;
            default:
                return null;
        }
    };

    const getTierBadge = (tier: string) => {
        const colors: Record<string, string> = {
            'S': 'bg-gradient-to-r from-amber-400 to-orange-500 text-black',
            'A': 'bg-gradient-to-r from-violet-400 to-purple-500 text-white',
            'B': 'bg-gradient-to-r from-blue-400 to-cyan-500 text-white',
            'C': 'bg-white/20 text-white/70',
        };
        return (
            <span className={`px-1.5 py-0.5 rounded text-[10px] font-black ${colors[tier] || colors['C']}`}>
                {tier}
            </span>
        );
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
                        <p className="text-white/50 mt-1">바이럴 아웃라이어 큐레이션 → 분석 파이프라인</p>
                    </div>
                    <div className="flex items-center gap-3">
                        {/* Sort Dropdown */}
                        <div className="relative">
                            <select
                                value={sortBy}
                                onChange={(e) => setSortBy(e.target.value as any)}
                                className="appearance-none px-4 py-2 pr-8 bg-white/5 border border-white/10 rounded-xl text-sm text-white/70 cursor-pointer hover:bg-white/10 transition-colors"
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
                            className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-sm transition-colors"
                        >
                            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                            새로고침
                        </button>
                    </div>
                </div>

                {/* Pipeline Stage Tabs */}
                <div className="flex items-center gap-2 mb-6 overflow-x-auto pb-2">
                    {[
                        { key: 'all', label: '전체', icon: null },
                        { key: 'pending', label: '🆕 크롤됨', icon: null },
                        { key: 'promoted', label: '📦 승격됨', icon: null },
                        { key: 'analyzing', label: '🔬 분석중', icon: null },
                        { key: 'completed', label: '✅ 완료', icon: null },
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
                        <button
                            onClick={fetchOutliers}
                            className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm"
                        >
                            다시 시도
                        </button>
                    </div>
                ) : filteredOutliers.length === 0 ? (
                    <div className="p-20 text-center text-white/30 border border-dashed border-white/10 rounded-2xl">
                        {statusFilter === 'all' ? '수집된 아웃라이어가 없습니다.' : `'${statusFilter}' 단계의 항목이 없습니다.`}
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                        {filteredOutliers.map((item) => {
                            const stage = getPipelineStage(item);
                            return (
                                <div
                                    key={item.id}
                                    className="group relative p-5 bg-white/5 hover:bg-white/[0.07] border border-white/10 rounded-2xl transition-all"
                                >
                                    {/* Top Row: Platform + Tier + Stage */}
                                    <div className="flex items-center justify-between mb-3">
                                        <div className="flex items-center gap-2">
                                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${item.platform === 'youtube' ? 'bg-red-500/20 text-red-300' :
                                                    item.platform === 'instagram' ? 'bg-pink-500/20 text-pink-300' :
                                                        item.platform === 'tiktok' ? 'bg-black/40 text-white border border-white/20' :
                                                            'bg-white/10 text-white/50'
                                                }`}>
                                                {item.platform}
                                            </span>
                                            {getTierBadge(item.outlier_tier)}
                                        </div>
                                        <div className="flex items-center gap-2">
                                            {getStageBadge(item)}
                                            <a
                                                href={item.video_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-white/30 hover:text-white transition-colors"
                                            >
                                                <ExternalLink className="w-4 h-4" />
                                            </a>
                                        </div>
                                    </div>

                                    {/* Title */}
                                    <h3 className="font-bold text-sm mb-3 line-clamp-2 group-hover:text-pink-300 transition-colors leading-snug">
                                        {item.title || '(제목 없음)'}
                                    </h3>

                                    {/* Stats */}
                                    <div className="flex items-center gap-3 text-[11px] text-white/40 font-mono mb-4">
                                        <span className="flex items-center gap-1">
                                            <Eye className="w-3 h-3" />
                                            {item.view_count?.toLocaleString()}
                                        </span>
                                        <span>📊 {item.outlier_score?.toFixed(1)}</span>
                                        <span className="flex items-center gap-1">
                                            <MessageCircle className="w-3 h-3" />
                                            {item.best_comments_count || 0}
                                        </span>
                                    </div>

                                    {/* Action Buttons based on Pipeline Stage */}
                                    <div className="flex items-center gap-2 pt-3 border-t border-white/5">
                                        {/* Stage 1: Pending → Promote */}
                                        {stage === 'pending' && (
                                            <button
                                                onClick={() => handlePromote(item.id)}
                                                disabled={actionLoading === item.id}
                                                className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 rounded-lg text-xs font-bold transition-colors disabled:opacity-50"
                                            >
                                                {actionLoading === item.id ? (
                                                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                                                ) : (
                                                    <ArrowUpRight className="w-3.5 h-3.5" />
                                                )}
                                                노드로 승격
                                            </button>
                                        )}

                                        {/* Stage 2: Promoted → Approve Analysis */}
                                        {stage === 'promoted' && (
                                            <button
                                                onClick={() => handleApprove(item.id)}
                                                disabled={actionLoading === item.id}
                                                className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-gradient-to-r from-violet-500/30 to-pink-500/30 hover:from-violet-500/40 hover:to-pink-500/40 text-white rounded-lg text-xs font-bold transition-all disabled:opacity-50"
                                            >
                                                {actionLoading === item.id ? (
                                                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                                                ) : (
                                                    <Play className="w-3.5 h-3.5" />
                                                )}
                                                VDG 분석 시작
                                            </button>
                                        )}

                                        {/* Stage 3: Analyzing */}
                                        {stage === 'analyzing' && (
                                            <div className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-purple-500/10 text-purple-300 rounded-lg text-xs font-bold">
                                                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                                                분석 진행중...
                                            </div>
                                        )}

                                        {/* Stage 4: Completed → View Details */}
                                        {stage === 'completed' && (
                                            <Link
                                                href={`/video/${item.id}`}
                                                className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 rounded-lg text-xs font-bold transition-colors"
                                            >
                                                <Sparkles className="w-3.5 h-3.5" />
                                                분석 결과 보기
                                            </Link>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </main>
        </div>
    );
}
