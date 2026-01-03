"use client";

import { useTranslations } from 'next-intl';

/**
 * 성과 입력 페이지
 * 
 * TikTok/YouTube Shorts URL 입력 → 자동 메타데이터 추출
 * → 패턴 평균과 비교
 */
import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { AppHeader } from "@/components/AppHeader";
import {
    ArrowLeft, Link2, Loader2, Eye, Heart, MessageCircle, Share2,
    TrendingUp, TrendingDown, Minus, Trophy, Sparkles
} from "lucide-react";

interface PerformanceData {
    platform: string;
    video_id: string;
    view_count: number;
    like_count: number;
    comment_count: number;
    share_count: number;
    title?: string;
    author?: string;
    upload_date?: string;
    extracted_at: string;
}

interface ComparisonData {
    pattern_id: string;
    pattern_avg_views: number;
    user_views: number;
    diff_percent: number;
    verdict: 'exceptional' | 'above_average' | 'average' | 'below_average';
    message: string;
}

function PerformanceContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const sessionId = searchParams.get("session_id");
    const patternId = searchParams.get("pattern_id");
    const t = useTranslations('pages.my.performance');

    const [url, setUrl] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [performance, setPerformance] = useState<PerformanceData | null>(null);
    const [comparison, setComparison] = useState<ComparisonData | null>(null);

    // URL에서 플랫폼 감지
    const detectPlatform = (inputUrl: string): string | null => {
        const lower = inputUrl.toLowerCase();
        if (lower.includes("tiktok.com")) return "tiktok";
        if (lower.includes("youtube.com/shorts") || lower.includes("youtu.be")) return "youtube";
        return null;
    };

    const handleExtract = async () => {
        if (!url.trim()) {
            setError(t('errors.enterUrl'));
            return;
        }

        const platform = detectPlatform(url);
        if (!platform) {
            setError(t('errors.invalidUrl'));
            return;
        }

        setLoading(true);
        setError(null);
        setPerformance(null);
        setComparison(null);

        try {
            // 성과 추출 API 호출
            const res = await fetch("/api/v1/performance/extract", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url, session_id: sessionId }),
            });

            const data = await res.json();

            if (!data.success) {
                throw new Error(data.error || t('errors.extractFailed'));
            }

            setPerformance(data.data);

            // 패턴과 비교 (패턴 ID가 있으면)
            if (patternId && data.data.view_count) {
                const compareRes = await fetch(
                    `/api/v1/performance/compare/${patternId}?view_count=${data.data.view_count}`
                );
                if (compareRes.ok) {
                    const compareData = await compareRes.json();
                    setComparison(compareData);
                }
            }
        } catch (err) {
            console.error("Performance extraction failed:", err);
            setError(err instanceof Error ? err.message : t('errors.extractError'));
        } finally {
            setLoading(false);
        }
    };

    const formatCount = (count: number): string => {
        if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M`;
        if (count >= 1000) return `${(count / 1000).toFixed(1)}K`;
        return count.toString();
    };

    const getVerdictStyle = (verdict?: string) => {
        switch (verdict) {
            case 'exceptional':
                return { bg: 'bg-amber-500/20', border: 'border-amber-500/30', text: 'text-amber-400', icon: Trophy };
            case 'above_average':
                return { bg: 'bg-emerald-500/20', border: 'border-emerald-500/30', text: 'text-emerald-400', icon: TrendingUp };
            case 'average':
                return { bg: 'bg-blue-500/20', border: 'border-blue-500/30', text: 'text-blue-400', icon: Minus };
            case 'below_average':
                return { bg: 'bg-orange-500/20', border: 'border-orange-500/30', text: 'text-orange-400', icon: TrendingDown };
            default:
                return { bg: 'bg-white/5', border: 'border-white/10', text: 'text-white', icon: Sparkles };
        }
    };

    return (
        <div className="min-h-screen bg-[#050505] text-white">
            <AppHeader />

            {/* 헤더 */}
            <div className="sticky top-0 z-40 bg-zinc-950/80 backdrop-blur-lg border-b border-white/10">
                <div className="max-w-2xl mx-auto px-4 py-3 flex items-center gap-4">
                    <button onClick={() => router.back()} className="p-2 -ml-2 hover:bg-white/10 rounded-lg">
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <h1 className="text-lg font-bold">{t('title')}</h1>
                </div>
            </div>

            <main className="max-w-2xl mx-auto px-4 py-6 space-y-6">
                {/* 안내 */}
                <div className="text-center py-4">
                    <p className="text-white/60 text-sm whitespace-pre-line">
                        {t('subtitle')}
                    </p>
                </div>

                {/* URL 입력 */}
                <div className="space-y-3">
                    <div className="relative">
                        <Link2 className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                        <input
                            type="url"
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            placeholder={t('inputPlaceholder')}
                            className="w-full pl-12 pr-4 py-4 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-white/30 focus:border-violet-500/50 focus:outline-none"
                            onKeyDown={(e) => e.key === 'Enter' && handleExtract()}
                        />
                    </div>

                    <button
                        onClick={handleExtract}
                        disabled={loading || !url.trim()}
                        className="w-full py-4 bg-[#c1ff00] hover:bg-white text-black font-black uppercase tracking-wider rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(193,255,0,0.3)] hover:shadow-[0_0_25px_rgba(255,255,255,0.5)]"
                    >
                        {loading ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                <span>{t('checking')}</span>
                            </>
                        ) : (
                            <>
                                <Sparkles className="w-5 h-5" />
                                <span>{t('checkButton')}</span>
                            </>
                        )}
                    </button>

                    {/* 지원 플랫폼 */}
                    <div className="flex items-center justify-center gap-4 text-xs text-white/40">
                        <span className="flex items-center gap-1">
                            <span>🎵</span> TikTok
                        </span>
                        <span className="flex items-center gap-1">
                            <span>▶️</span> YouTube Shorts
                        </span>
                    </div>
                </div>

                {/* 에러 */}
                {error && (
                    <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-300 text-sm">
                        {error}
                    </div>
                )}

                {/* 결과 */}
                {performance && (
                    <div className="space-y-4 animate-slideUp">
                        {/* 플랫폼 & 제목 */}
                        <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                            <div className="flex items-center gap-2 text-xs text-white/50 mb-2">
                                <span>{performance.platform === 'tiktok' ? '🎵' : '▶️'}</span>
                                <span>{performance.platform.toUpperCase()}</span>
                                {performance.author && (
                                    <>
                                        <span>•</span>
                                        <span>@{performance.author}</span>
                                    </>
                                )}
                            </div>
                            {performance.title && (
                                <p className="text-sm text-white/80 line-clamp-2">{performance.title}</p>
                            )}
                        </div>

                        {/* 성과 지표 */}
                        <div className="grid grid-cols-2 gap-3">
                            <div className="p-4 bg-violet-500/10 rounded-xl border border-violet-500/20 text-center">
                                <Eye className="w-5 h-5 mx-auto mb-2 text-violet-400" />
                                <div className="text-2xl font-bold text-white">{formatCount(performance.view_count)}</div>
                                <div className="text-xs text-white/50">{t('metrics.views')}</div>
                            </div>
                            <div className="p-4 bg-pink-500/10 rounded-xl border border-pink-500/20 text-center">
                                <Heart className="w-5 h-5 mx-auto mb-2 text-pink-400" />
                                <div className="text-2xl font-bold text-white">{formatCount(performance.like_count)}</div>
                                <div className="text-xs text-white/50">{t('metrics.likes')}</div>
                            </div>
                            <div className="p-4 bg-cyan-500/10 rounded-xl border border-cyan-500/20 text-center">
                                <MessageCircle className="w-5 h-5 mx-auto mb-2 text-cyan-400" />
                                <div className="text-2xl font-bold text-white">{formatCount(performance.comment_count)}</div>
                                <div className="text-xs text-white/50">{t('metrics.comments')}</div>
                            </div>
                            <div className="p-4 bg-emerald-500/10 rounded-xl border border-emerald-500/20 text-center">
                                <Share2 className="w-5 h-5 mx-auto mb-2 text-emerald-400" />
                                <div className="text-2xl font-bold text-white">{formatCount(performance.share_count)}</div>
                                <div className="text-xs text-white/50">{t('metrics.shares')}</div>
                            </div>
                        </div>

                        {/* 패턴 비교 */}
                        {comparison && (
                            <div className={`p-5 rounded-xl border ${getVerdictStyle(comparison.verdict).bg} ${getVerdictStyle(comparison.verdict).border}`}>
                                <div className="flex items-center gap-3 mb-3">
                                    {(() => {
                                        const VerdictIcon = getVerdictStyle(comparison.verdict).icon;
                                        return <VerdictIcon className={`w-6 h-6 ${getVerdictStyle(comparison.verdict).text}`} />;
                                    })()}
                                    <div>
                                        <div className="text-lg font-bold">{comparison.message}</div>
                                        <div className="text-xs text-white/50">
                                            {t('comparison.patternAvg')} {formatCount(comparison.pattern_avg_views)} {t('comparison.vsPatternAvg')}
                                            {comparison.diff_percent > 0 ? ' +' : ' '}{comparison.diff_percent}%
                                        </div>
                                    </div>
                                </div>

                                {/* 비교 바 */}
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between text-xs">
                                        <span className="text-white/50">{t('comparison.patternAvg')}</span>
                                        <span className="text-white/70">{formatCount(comparison.pattern_avg_views)}</span>
                                    </div>
                                    <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-white/30 rounded-full"
                                            style={{ width: '100%' }}
                                        />
                                    </div>
                                    <div className="flex items-center justify-between text-xs">
                                        <span className="text-white/50">{t('comparison.myVideo')}</span>
                                        <span className={`font-bold ${getVerdictStyle(comparison.verdict).text}`}>
                                            {formatCount(comparison.user_views)}
                                        </span>
                                    </div>
                                    <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                                        <div
                                            className={`h-full rounded-full ${comparison.diff_percent >= 0 ? 'bg-emerald-500' : 'bg-orange-500'
                                                }`}
                                            style={{
                                                width: `${Math.min(
                                                    (comparison.user_views / comparison.pattern_avg_views) * 100,
                                                    150
                                                )}%`
                                            }}
                                        />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* 다음 액션 */}
                        <div className="flex gap-3 pt-4">
                            <Link
                                href="/my"
                                className="flex-1 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-center text-sm font-medium"
                            >
                                {t('actions.myPage')}
                            </Link>
                            <Link
                                href="/"
                                className="flex-1 py-3 bg-violet-500 hover:bg-violet-400 rounded-xl text-center text-sm font-medium"
                            >
                                {t('actions.newVideo')}
                            </Link>
                        </div>
                    </div>
                )}

                {/* 첫 방문 안내 */}
                {!performance && !loading && (
                    <div className="text-center py-8 space-y-4">
                        <div className="text-4xl">📈</div>
                        <div className="text-white/40 text-sm whitespace-pre-line">
                            {t('emptyState')}
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}

export default function PerformancePage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-[#050505] flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
            </div>
        }>
            <PerformanceContent />
        </Suspense>
    );
}
