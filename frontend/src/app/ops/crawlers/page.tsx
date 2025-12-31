"use client";

/**
 * Ops Crawler Dashboard
 * 
 * Features:
 * - Platform status overview
 * - Strategy-based crawl triggers
 * - Job status monitoring
 * - Quota usage display
 */
import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
    ArrowLeft, RefreshCw, Play, CheckCircle, AlertCircle, Clock,
    Loader2, TrendingUp, Zap, Database, Activity
} from "lucide-react";

interface PlatformStatus {
    platform: string;
    is_active: boolean;
    last_crawled: string | null;
    items_count: number;
    last_24h_count: number;
}

interface CrawlerStatus {
    status: string;
    platforms: PlatformStatus[];
    total_items: number;
    pending_count: number;
    promoted_count: number;
}

interface JobStatus {
    status: string;
    started_at?: string;
    completed_at?: string;
    strategy?: string;
    platforms?: string[];
    results?: Record<string, unknown>;
    error?: string;
}

const STRATEGIES = [
    { id: 'meme_reaction', label: '밈/리액션', icon: '😂', description: '밈, 리액션, 표정챌린지' },
    { id: 'product_review', label: '제품 리뷰', icon: '📦', description: '솔직후기, 언박싱, 하울', o2o: true },
    { id: 'food_cafe', label: '맛집/카페', icon: '☕', description: '카페투어, 맛집, 먹방', o2o: true },
    { id: 'beauty', label: '뷰티', icon: '💄', description: 'GRWM, 스킨케어', o2o: true },
    { id: 'fitness', label: '피트니스', icon: '💪', description: '운동루틴, 홈트', o2o: true },
    { id: 'lifestyle', label: '라이프', icon: '🏠', description: '일상브이로그, 루틴', o2o: true },
];

const PLATFORMS = [
    { id: 'youtube', label: 'YouTube', icon: '▶️' },
    { id: 'tiktok', label: 'TikTok', icon: '🎵' },
    { id: 'instagram', label: 'Instagram', icon: '📷' },
];

function formatTimeAgo(dateStr: string | null): string {
    if (!dateStr) return '없음';
    const date = new Date(dateStr);
    if (Number.isNaN(date.getTime())) return '없음';
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    if (diffHours < 1) return '방금 전';
    if (diffHours < 24) return `${diffHours}시간 전`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}일 전`;
}

export default function CrawlerDashboard() {
    const [status, setStatus] = useState<CrawlerStatus | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [runningJobs, setRunningJobs] = useState<Record<string, JobStatus>>({});
    const [triggeringStrategy, setTriggeringStrategy] = useState<string | null>(null);
    const [triggeringPlatform, setTriggeringPlatform] = useState<string | null>(null);
    const isMountedRef = useRef(true);
    const pollTimeoutsRef = useRef<Array<ReturnType<typeof setTimeout>>>([]);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
            pollTimeoutsRef.current.forEach(clearTimeout);
            pollTimeoutsRef.current = [];
        };
    }, []);

    // Fetch crawler status
    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, []);

    async function fetchStatus() {
        try {
            const res = await fetch("/api/v1/crawlers/status");
            if (!isMountedRef.current) return;
            if (res.ok) {
                const data = await res.json();
                if (!isMountedRef.current) return;
                setStatus(data);
            }
        } catch (e) {
            console.error("Failed to fetch status:", e);
        } finally {
            if (isMountedRef.current) {
                setIsLoading(false);
            }
        }
    }

    async function runStrategyCrawl(strategy: string) {
        if (isMountedRef.current) {
            setTriggeringStrategy(strategy);
        }
        try {
            const res = await fetch("/api/v1/crawlers/run/strategy", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ strategy, limit: 50 }),
            });
            const data = await res.json();
            if (!isMountedRef.current) return;
            if (data.job_id) {
                setRunningJobs(prev => ({
                    ...prev,
                    [data.job_id]: { status: "running", strategy }
                }));
                pollJobStatus(data.job_id);
            }
        } catch (e) {
            console.error("Failed to trigger crawl:", e);
        } finally {
            if (isMountedRef.current) {
                setTriggeringStrategy(null);
            }
        }
    }

    async function runPlatformCrawl(platform: string) {
        if (isMountedRef.current) {
            setTriggeringPlatform(platform);
        }
        try {
            const res = await fetch("/api/v1/crawlers/run", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ platforms: [platform], limit: 50 }),
            });
            const data = await res.json();
            if (!isMountedRef.current) return;
            if (data.job_id) {
                setRunningJobs(prev => ({
                    ...prev,
                    [data.job_id]: { status: "running", platforms: [platform] }
                }));
                pollJobStatus(data.job_id);
            }
        } catch (e) {
            console.error("Failed to trigger crawl:", e);
        } finally {
            if (isMountedRef.current) {
                setTriggeringPlatform(null);
            }
        }
    }

    async function pollJobStatus(jobId: string) {
        const poll = async () => {
            if (!isMountedRef.current) return;
            try {
                const res = await fetch(`/api/v1/crawlers/jobs/${jobId}`);
                if (res.ok) {
                    const data = await res.json();
                    if (!isMountedRef.current) return;
                    setRunningJobs(prev => ({ ...prev, [jobId]: data }));
                    if (data.status === "running") {
                        const timeoutId = setTimeout(poll, 3000);
                        pollTimeoutsRef.current.push(timeoutId);
                    } else {
                        fetchStatus(); // Refresh status on complete
                    }
                }
            } catch (e) {
                console.error("Failed to poll job:", e);
            }
        };
        poll();
    }

    const activeJobs = Object.entries(runningJobs).filter(([, job]) => job.status === "running");

    return (
        <div className="min-h-screen bg-[#050505] text-white">
            {/* Header */}
            <header className="sticky top-0 z-40 px-4 py-4 backdrop-blur-xl bg-black/80 border-b border-white/10">
                <div className="max-w-4xl mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link href="/ops" className="p-2 rounded-lg hover:bg-white/10 transition-colors">
                            <ArrowLeft className="w-5 h-5" />
                        </Link>
                        <div>
                            <h1 className="text-lg font-bold flex items-center gap-2">
                                <Database className="w-5 h-5 text-cyan-400" />
                                크롤러 대시보드
                            </h1>
                            <p className="text-xs text-white/50">TikTok, YouTube Shorts, Instagram</p>
                        </div>
                    </div>
                    <button
                        onClick={fetchStatus}
                        disabled={isLoading}
                        className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                    >
                        <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                    </button>
                </div>
            </header>

            <main className="max-w-4xl mx-auto px-4 py-6 space-y-6">
                {/* Active Jobs Banner */}
                {activeJobs.length > 0 && (
                    <div className="p-4 bg-cyan-500/10 border border-cyan-500/30 rounded-xl">
                        <div className="flex items-center gap-2 mb-2">
                            <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
                            <span className="text-sm font-bold text-cyan-300">
                                {activeJobs.length}개 작업 실행 중
                            </span>
                        </div>
                        <div className="space-y-1">
                            {activeJobs.map(([id, job]) => (
                                <div key={id} className="text-xs text-white/60">
                                    {job.strategy ? `📊 ${job.strategy} 전략` : `🔄 ${job.platforms?.join(', ')}`}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Stats Overview */}
                {status && (
                    <div className="grid grid-cols-4 gap-3">
                        <div className="p-4 bg-white/5 border border-white/10 rounded-xl text-center">
                            <div className="text-2xl font-bold text-white">{status.total_items.toLocaleString()}</div>
                            <div className="text-xs text-white/50">전체 아이템</div>
                        </div>
                        <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl text-center">
                            <div className="text-2xl font-bold text-amber-300">{status.pending_count.toLocaleString()}</div>
                            <div className="text-xs text-amber-300/70">대기 중</div>
                        </div>
                        <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-center">
                            <div className="text-2xl font-bold text-emerald-300">{status.promoted_count.toLocaleString()}</div>
                            <div className="text-xs text-emerald-300/70">승격됨</div>
                        </div>
                        <div className="p-4 bg-violet-500/10 border border-violet-500/30 rounded-xl text-center">
                            <div className="text-2xl font-bold text-violet-300">{status.platforms.length}</div>
                            <div className="text-xs text-violet-300/70">플랫폼</div>
                        </div>
                    </div>
                )}

                {/* Platform Status */}
                <section>
                    <h2 className="text-sm font-bold text-white/80 mb-3 flex items-center gap-2">
                        <Activity className="w-4 h-4 text-cyan-400" />
                        플랫폼별 상태
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        {PLATFORMS.map(platform => {
                            const pStatus = status?.platforms.find(p => p.platform.includes(platform.id));
                            const isTriggering = triggeringPlatform === platform.id;

                            return (
                                <div key={platform.id} className="p-4 bg-white/5 border border-white/10 rounded-xl">
                                    <div className="flex items-center justify-between mb-3">
                                        <div className="flex items-center gap-2">
                                            <span className="text-xl">{platform.icon}</span>
                                            <span className="font-bold">{platform.label}</span>
                                        </div>
                                        {pStatus?.is_active ? (
                                            <CheckCircle className="w-4 h-4 text-emerald-400" />
                                        ) : (
                                            <AlertCircle className="w-4 h-4 text-amber-400" />
                                        )}
                                    </div>
                                    <div className="space-y-1 text-xs mb-3">
                                        <div className="flex justify-between">
                                            <span className="text-white/50">마지막 크롤</span>
                                            <span className="text-white/80">{formatTimeAgo(pStatus?.last_crawled || null)}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-white/50">24h 수집</span>
                                            <span className="text-cyan-300">{pStatus?.last_24h_count || 0}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-white/50">전체</span>
                                            <span className="text-white/80">{pStatus?.items_count || 0}</span>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => runPlatformCrawl(platform.id)}
                                        disabled={isTriggering}
                                        className="w-full py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-xs font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-1"
                                    >
                                        {isTriggering ? (
                                            <Loader2 className="w-3 h-3 animate-spin" />
                                        ) : (
                                            <Play className="w-3 h-3" />
                                        )}
                                        크롤 실행
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                </section>

                {/* Strategy Triggers */}
                <section>
                    <h2 className="text-sm font-bold text-white/80 mb-3 flex items-center gap-2">
                        <Zap className="w-4 h-4 text-amber-400" />
                        Shorts 키워드 전략
                    </h2>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                        {STRATEGIES.map(strategy => {
                            const isTriggering = triggeringStrategy === strategy.id;
                            const job = Object.values(runningJobs).find(j => j.strategy === strategy.id);
                            const isRunning = job?.status === "running";
                            const isCompleted = job?.status === "completed";

                            return (
                                <button
                                    key={strategy.id}
                                    onClick={() => runStrategyCrawl(strategy.id)}
                                    disabled={isTriggering || isRunning}
                                    className={`p-3 rounded-xl text-left transition-all ${isCompleted
                                        ? 'bg-emerald-500/10 border border-emerald-500/30'
                                        : isRunning
                                            ? 'bg-cyan-500/10 border border-cyan-500/30'
                                            : 'bg-white/5 border border-white/10 hover:border-white/20'
                                        } disabled:opacity-70`}
                                >
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="text-lg">{strategy.icon}</span>
                                        {isRunning && <Loader2 className="w-3 h-3 text-cyan-400 animate-spin" />}
                                        {isCompleted && <CheckCircle className="w-3 h-3 text-emerald-400" />}
                                    </div>
                                    <div className="text-xs font-bold text-white">{strategy.label}</div>
                                    <div className="text-[10px] text-white/50">{strategy.description}</div>
                                </button>
                            );
                        })}
                    </div>
                </section>

                {/* Quick Links */}
                <section>
                    <h2 className="text-sm font-bold text-white/80 mb-3 flex items-center gap-2">
                        <TrendingUp className="w-4 h-4 text-violet-400" />
                        빠른 링크
                    </h2>
                    <div className="grid grid-cols-2 gap-3">
                        <Link
                            href="/ops/outliers/manual"
                            className="p-4 bg-gradient-to-br from-violet-500/10 to-pink-500/10 border border-violet-500/30 rounded-xl hover:brightness-110 transition-all"
                        >
                            <div className="text-lg mb-1">🔗</div>
                            <div className="text-sm font-bold text-white">수동 URL 등록</div>
                            <div className="text-xs text-white/50">TikTok/Shorts 직접 입력</div>
                        </Link>
                        <Link
                            href="/ops/outliers"
                            className="p-4 bg-gradient-to-br from-cyan-500/10 to-emerald-500/10 border border-cyan-500/30 rounded-xl hover:brightness-110 transition-all"
                        >
                            <div className="text-lg mb-1">📋</div>
                            <div className="text-sm font-bold text-white">아웃라이어 관리</div>
                            <div className="text-xs text-white/50">승격/거부 결정</div>
                        </Link>
                    </div>
                </section>

                {/* Completed Jobs */}
                {Object.entries(runningJobs).filter(([, job]) => job.status === "completed").length > 0 && (
                    <section>
                        <h2 className="text-sm font-bold text-white/80 mb-3 flex items-center gap-2">
                            <Clock className="w-4 h-4 text-emerald-400" />
                            최근 완료된 작업
                        </h2>
                        <div className="space-y-2">
                            {Object.entries(runningJobs)
                                .filter(([, job]) => job.status === "completed")
                                .slice(0, 5)
                                .map(([id, job]) => (
                                    <div key={id} className="p-3 bg-emerald-500/5 border border-emerald-500/20 rounded-lg flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <CheckCircle className="w-4 h-4 text-emerald-400" />
                                            <span className="text-sm text-white">
                                                {job.strategy ? `${job.strategy} 전략` : job.platforms?.join(', ')}
                                            </span>
                                        </div>
                                        <div className="text-xs text-emerald-300">
                                            {(job.results as Record<string, number>)?.inserted || 0} 신규
                                        </div>
                                    </div>
                                ))}
                        </div>
                    </section>
                )}
            </main>
        </div>
    );
}
