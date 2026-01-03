'use client';

import { useTranslations } from 'next-intl';

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
import { useRouter, usePathname } from 'next/navigation';
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
    OutlierCardFooter,
    ViewCountBadge,
} from '@/components/outlier';

type StatusFilter = 'all' | 'pending' | 'promoted' | 'analyzing' | 'completed';

export default function OutliersPage() {
    const router = useRouter();
    const pathname = usePathname();  // 라우트 변경 감지
    const { user, isAuthenticated, isLoading: authLoading } = useAuth();
    const t = useTranslations('pages.ops.outliersPage');

    const [outliers, setOutliers] = useState<OutlierItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [sortBy, setSortBy] = useState<'outlier_score' | 'view_count' | 'crawled_at'>('outlier_score');
    const [platformFilter, setPlatformFilter] = useState<'all' | 'tiktok' | 'youtube' | 'instagram'>('all');
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
    }, [sortBy, authLoading, isAuthenticated, isAuthorized, pathname]);  // pathname 추가: 라우트 변경 시 refetch

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
            const data = await api.listOutliers({ limit: 1000, sortBy });
            if (!isMountedRef.current) return;
            setOutliers(data.items || []);
            setError(null);
        } catch (e) {
            console.error(e);
            if (!isMountedRef.current) return;
            setError('Failed to load outliers list.');
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
                alert(t('promotionFailed'));
            }
        } catch (e: any) {
            alert(`${t('error')}: ${e.message}`);
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
            alert(`${t('error')}: ${e.message}`);
        } finally {
            if (isMountedRef.current) {
                setActionLoading(null);
            }
        }
    }

    async function handleReject(itemId: string) {
        if (isMountedRef.current) {
            setActionLoading(itemId);
        }
        try {
            const result = await api.rejectOutlier(itemId);
            if (result.rejected) {
                await fetchOutliers();
                if (isMountedRef.current) {
                    setSelectedItem(null);
                }
            } else {
                alert(t('rejectionFailed'));
            }
        } catch (e: any) {
            alert(`${t('error')}: ${e.message}`);
        } finally {
            if (isMountedRef.current) {
                setActionLoading(null);
            }
        }
    }


    const filteredOutliers = outliers.filter(item => {
        // Always exclude rejected items from the main view
        if (item.status === 'rejected') return false;

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
        all: outliers.filter(o => o.status !== 'rejected').length,
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
            alert(t('urlSubmitFailed'));
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
                    <h1 className="text-2xl font-bold mb-2">{t('accessDenied')}</h1>
                    <p className="text-white/60 mb-6">
                        {t('accessDeniedDesc')}
                    </p>
                    <button
                        onClick={() => router.push('/')}
                        className="px-6 py-3 bg-pink-500 hover:bg-pink-400 rounded-xl font-bold transition-colors"
                    >
                        {t('goHome')}
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
                            {t('title')}
                        </h1>
                        <p className="text-white/50 mt-1">{t('subtitle')}</p>
                    </div>

                    {/* Manual URL Input */}
                    <form onSubmit={handleManualSubmit} className="flex-1 max-w-lg">
                        <div className="flex items-center bg-white/5 border border-white/10 rounded-xl px-3 py-2 focus-within:border-pink-500/50 transition-colors">
                            {isLinkMode ? <LinkIcon className="w-4 h-4 text-pink-400 mr-2" /> : <Plus className="w-4 h-4 text-white/40 mr-2" />}
                            <input
                                type="text"
                                value={urlInput}
                                onChange={e => setUrlInput(e.target.value)}
                                placeholder={t('inputPlaceholder')}
                                className="flex-1 bg-transparent text-sm text-white placeholder-white/40 focus:outline-none"
                                disabled={isSubmittingUrl}
                            />
                            {urlInput && <button type="button" onClick={() => setUrlInput('')} className="p-1 text-white/40 hover:text-white"><X className="w-3 h-3" /></button>}
                            {isLinkMode && (
                                <button type="submit" disabled={isSubmittingUrl} className="ml-2 px-3 py-1 bg-pink-500 hover:bg-pink-400 rounded-lg text-xs font-bold text-white flex items-center gap-1">
                                    {isSubmittingUrl ? <div className="w-3 h-3 border border-current border-t-transparent rounded-full animate-spin" /> : <Sparkles className="w-3 h-3" />}
                                    {t('register')}
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
                            <button
                                onClick={() => setPlatformFilter('instagram')}
                                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold transition-all ${platformFilter === 'instagram' ? 'bg-gradient-to-r from-[#f09433] via-[#e6683c] to-[#dc2743] text-white shadow-lg' : 'text-white/50 hover:text-white hover:bg-white/5'}`}
                            >
                                <div className="w-3.5 h-3.5">
                                    <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full">
                                        <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" />
                                    </svg>
                                </div>
                                <span className="hidden sm:inline">Instagram</span>
                            </button>
                        </div>
                        {/* Sort Filter */}
                        <div className="relative">
                            <select
                                value={sortBy}
                                onChange={(e) => setSortBy(e.target.value as any)}
                                className="appearance-none px-4 py-2 pr-8 bg-white/5 border border-white/10 rounded-xl text-sm text-white/70"
                            >
                                <option value="outlier_score">{t('sort.outlierScore')}</option>
                                <option value="view_count">{t('sort.viewCount')}</option>
                                <option value="crawled_at">{t('sort.latest')}</option>
                            </select>
                            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40 pointer-events-none" />
                        </div>
                        <button
                            onClick={fetchOutliers}
                            disabled={loading}
                            className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-sm"
                        >
                            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                            {t('refresh')}
                        </button>
                    </div>
                </div>

                {/* Pipeline Stage Tabs */}
                <div className="flex items-center gap-2 mb-6 overflow-x-auto pb-2">
                    {[
                        { key: 'all', label: t('stages.all') },
                        { key: 'pending', label: t('stages.pending') },
                        { key: 'promoted', label: t('stages.promoted') },
                        { key: 'analyzing', label: t('stages.analyzing') },
                        { key: 'completed', label: t('stages.completed') },
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
                        <button onClick={fetchOutliers} className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm">{t('retry')}</button>
                    </div>
                ) : filteredOutliers.length === 0 ? (
                    <div className="p-20 text-center text-white/30 border border-dashed border-white/10 rounded-2xl">
                        {statusFilter === 'all' ? t('noOutliers') : t('noItemsInStage', { stage: t(`stages.${statusFilter}`) })}
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
                                            showMuteOnHover={true}
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
                                            <ViewCountBadge viewCount={item.view_count || 0} size="sm" />
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

                                    {/* Title & Creator Info */}
                                    <div className="p-3">
                                        <h3 className="font-bold text-xs line-clamp-2 text-white/90 group-hover:text-pink-300 transition-colors">
                                            {item.title || '(No title)'}
                                        </h3>
                                        {/* Creator Info */}
                                        <OutlierCardFooter
                                            creatorUsername={item.creator_username}
                                            uploadDate={item.upload_date}
                                            crawledAt={item.crawled_at}
                                            className="mt-1.5"
                                        />
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
                    onReject={handleReject}
                    actionLoading={actionLoading}
                />
            )}
        </div>
    );
}
