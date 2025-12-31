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

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { AppHeader } from '@/components/AppHeader';
import { api, OutlierItem } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { RefreshCw, TrendingUp, ChevronDown, Play, ShieldAlert, Loader2, Link as LinkIcon, Sparkles, X, Plus } from 'lucide-react';

// Import shared outlier components
import {
    TikTokHoverPreview,
    TierBadge,
    OutlierMetrics,
    PipelineStatus,
    OutlierDetailModal,
    extractTikTokVideoId,
    getPipelineStage,
    PlatformBadge,
    OutlierScoreBadge,
} from '@/components/outlier';

type StatusFilter = 'all' | 'pending' | 'promoted' | 'analyzing' | 'completed';

export default function OutliersPage() {
    const router = useRouter();
    const { user, isAuthenticated, isLoading: authLoading } = useAuth();

    const [outliers, setOutliers] = useState<OutlierItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [sortBy, setSortBy] = useState<'outlier_score' | 'view_count' | 'crawled_at'>('outlier_score');
    const [platformFilter, setPlatformFilter] = useState<'all' | 'tiktok' | 'youtube'>('all');
    const [selectedItem, setSelectedItem] = useState<OutlierItem | null>(null);
    const [hoveredCard, setHoveredCard] = useState<string | null>(null);
    const isMountedRef = useRef(true);

    // Manual URL input
    const [urlInput, setUrlInput] = useState('');
    const [isSubmittingUrl, setIsSubmittingUrl] = useState(false);

    // Check authorization - superadmin by email or by role
    const SUPERADMIN_EMAILS = ['ted.taeeun.kim@gmail.com'];
    const isSuperAdmin = user?.email && SUPERADMIN_EMAILS.includes(user.email);
    const isAuthorized = isSuperAdmin || user?.role === 'admin' || user?.role === 'curator';

    useEffect(() => {
        // Redirect to login if not authenticated (after auth loading completes)
        if (!authLoading && !isAuthenticated) {
            router.push('/login?redirect=/ops/outliers');
            return;
        }
        // Only fetch if authorized
        if (isAuthorized) {
            fetchOutliers();
        }
    }, [sortBy, authLoading, isAuthenticated, isAuthorized]);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    async function fetchOutliers() {
        try {
            if (isMountedRef.current) {
                setLoading(true);
            }
            const data = await api.listOutliers({ limit: 100, sortBy });
            if (!isMountedRef.current) return;
            setOutliers(data.items || []);
            setError(null);
        } catch (e) {
            console.error(e);
            if (!isMountedRef.current) return;
            setError('아웃라이어 목록을 불러오지 못했습니다.');
        } finally {
            if (isMountedRef.current) {
                setLoading(false);
            }
        }
    }

    async function handlePromote(itemId: string, campaignEligible: boolean = false) {
        if (isMountedRef.current) {
            setActionLoading(itemId);
        }
        try {
            const result = await api.promoteOutlier(itemId, campaignEligible);
            if (result.promoted) {
                await fetchOutliers();
                if (isMountedRef.current) {
                    setSelectedItem(null);
                }
            } else {
                alert('승격 실패');
            }
        } catch (e: any) {
            alert(`오류: ${e.message}`);
        } finally {
            if (isMountedRef.current) {
                setActionLoading(null);
            }
        }
    }

    async function handleApprove(itemId: string) {
        if (isMountedRef.current) {
            setActionLoading(itemId);
        }
        try {
            await api.approveVDGAnalysis(itemId);
            await fetchOutliers();
            if (isMountedRef.current) {
                setSelectedItem(null);
            }
        } catch (e: any) {
            alert(`오류: ${e.message}`);
        } finally {
            if (isMountedRef.current) {
                setActionLoading(null);
            }
        }
    }

    const filteredOutliers = outliers.filter(item => {
        // Platform filter
        if (platformFilter !== 'all' && item.platform !== platformFilter) return false;

        // Status filter
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
    }

    // Manual URL submission
    function isVideoUrl(input: string): boolean {
        return input.includes('tiktok.com') || input.includes('instagram.com') || input.includes('youtube.com');
    }

    function detectPlatform(url: string): 'tiktok' | 'instagram' | 'youtube' {
        if (url.includes('tiktok')) return 'tiktok';
        if (url.includes('instagram')) return 'instagram';
        return 'youtube';
    }

    async function handleManualSubmit(e: React.FormEvent) {
        e.preventDefault();
        if (!urlInput.trim() || !isVideoUrl(urlInput)) return;

        if (isMountedRef.current) {
            setIsSubmittingUrl(true);
        }
        try {
            const url = urlInput.trim();
            const platform = detectPlatform(url);

            // Create manual outlier item via API
            await api.createOutlierManual({
                video_url: url,
                platform: platform,
                category: 'trending',
            });

            if (isMountedRef.current) {
                setUrlInput('');
            }
            fetchOutliers(); // Refresh list
        } catch (error) {
            console.error('Manual URL submission failed:', error);
            alert('URL 등록 실패');
        } finally {
            if (isMountedRef.current) {
                setIsSubmittingUrl(false);
            }
        }
    }

    const isLinkMode = isVideoUrl(urlInput);

    // Auth Loading
    if (authLoading) {
        return (
            <div className="min-h-screen bg-[#050505] flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-pink-500 animate-spin" />
            </div>
        );
    }

    // Access Denied - authenticated but not curator/admin
    if (isAuthenticated && !isAuthorized) {
        return (
            <div className="min-h-screen bg-[#050505] text-white flex items-center justify-center">
                <div className="text-center p-8 bg-white/5 rounded-2xl border border-white/10 max-w-md">
                    <ShieldAlert className="w-16 h-16 text-red-400 mx-auto mb-4" />
                    <h1 className="text-2xl font-bold mb-2">접근 권한 없음</h1>
                    <p className="text-white/60 mb-6">
                        이 페이지는 Curator 또는 Admin 권한이 필요합니다.
                    </p>
                    <button
                        onClick={() => router.push('/')}
                        className="px-6 py-3 bg-pink-500 hover:bg-pink-400 rounded-xl font-bold transition-colors"
                    >
                        홈으로 돌아가기
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#050505] text-white font-sans">
            <AppHeader />

            <main className="max-w-7xl mx-auto px-6 py-8">
                {/* Header */}
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
                    <div>
                        <h1 className="text-3xl font-black flex items-center gap-3">
                            <TrendingUp className="w-8 h-8 text-pink-400" />
                            아웃라이어 관리
                        </h1>
                        <p className="text-white/50 mt-1">클릭하여 TikTok 영상 재생 + 메타데이터 확인</p>
                    </div>

                    {/* Manual URL Input */}
                    <form onSubmit={handleManualSubmit} className="flex-1 max-w-lg">
                        <div className="flex items-center bg-white/5 border border-white/10 rounded-xl px-3 py-2 focus-within:border-pink-500/50 transition-colors">
                            {isLinkMode ? <LinkIcon className="w-4 h-4 text-pink-400 mr-2" /> : <Plus className="w-4 h-4 text-white/40 mr-2" />}
                            <input
                                type="text"
                                value={urlInput}
                                onChange={e => setUrlInput(e.target.value)}
                                placeholder="TikTok/Instagram/YouTube 링크 붙여넣기..."
                                className="flex-1 bg-transparent text-sm text-white placeholder-white/40 focus:outline-none"
                                disabled={isSubmittingUrl}
                            />
                            {urlInput && <button type="button" onClick={() => setUrlInput('')} className="p-1 text-white/40 hover:text-white"><X className="w-3 h-3" /></button>}
                            {isLinkMode && (
                                <button type="submit" disabled={isSubmittingUrl} className="ml-2 px-3 py-1 bg-pink-500 hover:bg-pink-400 rounded-lg text-xs font-bold text-white flex items-center gap-1">
                                    {isSubmittingUrl ? <div className="w-3 h-3 border border-current border-t-transparent rounded-full animate-spin" /> : <Sparkles className="w-3 h-3" />}
                                    등록
                                </button>
                            )}
                        </div>
                    </form>
                    <div className="flex items-center gap-3">
                        {/* Platform Filter Toggle */}
                        <div className="flex bg-white/5 border border-white/10 rounded-xl p-1 gap-1">
                            <button
                                onClick={() => setPlatformFilter('all')}
                                className={`px-3 py-2 rounded-lg text-xs font-bold transition-all ${platformFilter === 'all' ? 'bg-white text-black shadow-lg' : 'text-white/50 hover:text-white hover:bg-white/5'}`}
                            >
                                ALL
                            </button>
                            <button
                                onClick={() => setPlatformFilter('tiktok')}
                                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold transition-all ${platformFilter === 'tiktok' ? 'bg-black text-white shadow-lg border border-white/20' : 'text-white/50 hover:text-white hover:bg-white/5'}`}
                            >
                                <div className="w-3.5 h-3.5">
                                    <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full">
                                        <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z" />
                                    </svg>
                                </div>
                                <span className="hidden sm:inline">TikTok</span>
                            </button>
                            <button
                                onClick={() => setPlatformFilter('youtube')}
                                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold transition-all ${platformFilter === 'youtube' ? 'bg-[#FF0000] text-white shadow-lg' : 'text-white/50 hover:text-white hover:bg-white/5'}`}
                            >
                                <div className="w-3.5 h-3.5">
                                    <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full">
                                        <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
                                    </svg>
                                </div>
                                <span className="hidden sm:inline">YouTube</span>
                            </button>
                        </div>
                        {/* Sort Filter */}
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

                                        {/* Top-right: Outlier Score (Virlo-style) */}
                                        <div className="absolute top-2 right-2 z-[4]">
                                            <OutlierScoreBadge
                                                score={item.outlier_score}
                                                tier={item.outlier_tier}
                                                size="sm"
                                            />
                                        </div>

                                        {/* Top-left: View count */}
                                        <div className="absolute top-2 left-2 z-[4]">
                                            <div className="flex items-center gap-1 px-2 py-1 bg-black/70 rounded-full text-[10px] text-white">
                                                <span>👁️</span>
                                                <span>{item.view_count ? (item.view_count >= 1000000 ? `${(item.view_count / 1000000).toFixed(1)}M` : item.view_count >= 1000 ? `${(item.view_count / 1000).toFixed(1)}K` : item.view_count) : '0'}</span>
                                            </div>
                                        </div>

                                        {/* Bottom-left: Platform badge */}
                                        <div className="absolute bottom-2 left-2 z-[4]">
                                            <PlatformBadge platform={item.platform} size="sm" />
                                        </div>

                                        {/* Bottom-right: Pipeline status */}
                                        <div className="absolute bottom-2 right-2 z-[4]">
                                            <PipelineStatus
                                                status={item.status as 'pending' | 'promoted'}
                                                analysisStatus={item.analysis_status}
                                                size="sm"
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
