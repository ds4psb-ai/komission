'use client';

/**
 * Ops Console Page (PEGL v1.0 P0-7)
 * 
 * 운영자 대시보드
 * - 파이프라인 상태 개요
 * - Run 목록
 * - Evidence 이벤트
 * - VDG Edge 관리
 * - Source Packs & NotebookLM Integration (Phase D)
 */

// SSR 비활성화 - localStorage 사용
export const dynamic = 'force-dynamic';

import { useState, useEffect, useRef } from 'react';
import { usePathname } from 'next/navigation';
import { AppHeader } from '@/components/AppHeader';
import { SessionHUD } from '@/components/SessionHUD';
import {
    Activity, AlertCircle, CheckCircle, Clock,
    RefreshCw, ChevronRight, Database, GitBranch, BarChart3,
    Zap, FlaskConical, ArrowRight, RotateCcw, Upload, BookOpen, ExternalLink,
    Sparkles, Target, TrendingUp, FileVideo, Lock
} from 'lucide-react';
import { api, SourcePackItem } from '@/lib/api';
import Link from 'next/link';
import { useTranslations } from 'next-intl';

interface PipelineStatus {
    total_runs: number;
    running: number;
    completed: number;
    failed: number;
    total_evidence_events: number;
    evidence_pending: number;
    evidence_measured: number;
    evidence_failed: number;
    total_vdg_edges: number;
    edges_candidate: number;
    edges_confirmed: number;
    total_clusters: number;
    total_source_packs: number;
}

interface RunItem {
    id: string;
    run_type: string;
    status: string;
    started_at: string | null;
    ended_at: string | null;
    duration_sec: number | null;
}

interface ClusterInfo {
    cluster_id: string;
    cluster_name: string;
    parent_vdg_id: string;
    kids_count: number;
    distill_ready: boolean;
}

interface P2Progress {
    total_clusters: number;
    distill_ready_clusters: number;
    target: number;
    progress_percent: number;
}

export default function OpsConsolePage() {
    const pathname = usePathname();  // 라우트 변경 감지
    const [status, setStatus] = useState<PipelineStatus | null>(null);
    const [runs, setRuns] = useState<RunItem[]>([]);
    const [sourcePacks, setSourcePacks] = useState<SourcePackItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [retrying, setRetrying] = useState<string | null>(null);
    const [uploading, setUploading] = useState<string | null>(null);
    const [clusters, setClusters] = useState<ClusterInfo[]>([]);
    const [p2Progress, setP2Progress] = useState<P2Progress | null>(null);
    const isMountedRef = useRef(true);

    useEffect(() => {
        fetchData();
    }, [pathname]);  // pathname 추가: 라우트 변경 시 refetch

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    async function fetchData() {
        try {
            if (isMountedRef.current) {
                setLoading(true);
            }

            // SSR 방지
            if (typeof window === 'undefined') {
                if (isMountedRef.current) {
                    setLoading(false);
                }
                return;
            }

            const token = localStorage.getItem('access_token');
            if (!token) {
                if (isMountedRef.current) {
                    setError('로그인이 필요합니다');
                    setLoading(false);
                }
                return;
            }

            const headers = { 'Authorization': `Bearer ${token}` };

            // Fetch status and runs in parallel
            const [statusRes, runsRes] = await Promise.all([
                fetch('/api/v1/ops/status', { headers }),
                fetch('/api/v1/ops/runs?limit=20', { headers }),
            ]);

            if (!statusRes.ok || !runsRes.ok) {
                if (statusRes.status === 401 || runsRes.status === 401) {
                    if (isMountedRef.current) {
                        setError('관리자 권한이 필요합니다');
                    }
                } else {
                    if (isMountedRef.current) {
                        setError('데이터를 불러오지 못했습니다');
                    }
                }
                if (isMountedRef.current) {
                    setLoading(false);
                }
                return;
            }

            const [statusData, runsData] = await Promise.all([
                statusRes.json(),
                runsRes.json(),
            ]);

            if (!isMountedRef.current) return;
            setStatus(statusData);
            setRuns(runsData);
            setError(null);

            // Fetch Source Packs (with API fallback)
            try {
                const packsData = await api.getSourcePacks({ limit: 10 });
                if (!isMountedRef.current) return;
                setSourcePacks(packsData.source_packs || []);
            } catch (e) {
                console.warn("Source Packs API failed:", e);
                if (!isMountedRef.current) return;
                setSourcePacks([]);
            }

            // Fetch P2 Clusters
            try {
                const clustersRes = await fetch('/api/v1/clusters', { headers });
                if (clustersRes.ok) {
                    const clustersData = await clustersRes.json();
                    if (!isMountedRef.current) return;
                    setClusters((clustersData.clusters || []).map((c: any) => ({
                        cluster_id: c.cluster_id,
                        cluster_name: c.cluster_name,
                        parent_vdg_id: c.parent_vdg_id,
                        kids_count: c.kids?.length || 0,
                        distill_ready: c.distill_ready
                    })));
                }
            } catch (e) {
                console.warn("Clusters API failed:", e);
            }

            // Fetch P2 Progress
            try {
                const progressRes = await fetch('/api/v1/clusters/p2-progress', { headers });
                if (progressRes.ok) {
                    const progressData = await progressRes.json();
                    if (!isMountedRef.current) return;
                    setP2Progress(progressData);
                }
            } catch (e) {
                console.warn("P2 Progress API failed:", e);
            }
        } catch {
            if (isMountedRef.current) {
                setError('서버 연결 실패');
            }
        } finally {
            if (isMountedRef.current) {
                setLoading(false);
            }
        }
    }

    async function handleRetry(runId: string) {
        if (isMountedRef.current) {
            setRetrying(runId);
        }
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                if (isMountedRef.current) {
                    setError('로그인이 필요합니다');
                }
                return;
            }
            const res = await fetch(`/api/v1/ops/runs/${runId}/retry`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
            });
            if (res.ok) {
                fetchData();
            }
        } finally {
            if (isMountedRef.current) {
                setRetrying(null);
            }
        }
    }

    async function handleUploadToNotebook(packId: string) {
        if (isMountedRef.current) {
            setUploading(packId);
        }
        try {
            const result = await api.uploadSourcePackToNotebook(packId);
            if (!isMountedRef.current) return;
            if (result.success) {
                alert(`✅ NotebookLM 업로드 완료: ${result.message}`);
                fetchData(); // Refresh to update notebook_id status
            } else {
                alert(`❌ 업로드 실패: ${result.message}`);
            }
        } catch (e: any) {
            if (!isMountedRef.current) return;
            alert(`❌ 오류: ${e.message || '알 수 없는 오류'}`);
        } finally {
            if (isMountedRef.current) {
                setUploading(null);
            }
        }
    }

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'COMPLETED': return 'text-emerald-400 bg-emerald-500/10';
            case 'FAILED': return 'text-red-400 bg-red-500/10';
            case 'RUNNING': return 'text-amber-400 bg-amber-500/10';
            default: return 'text-white/50 bg-white/5';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'COMPLETED': return <CheckCircle className="w-4 h-4" />;
            case 'FAILED': return <AlertCircle className="w-4 h-4" />;
            case 'RUNNING': return <Activity className="w-4 h-4 animate-pulse" />;
            default: return <Clock className="w-4 h-4" />;
        }
    };

    return (
        <div className="min-h-screen bg-[#050505] text-white font-sans">
            <AppHeader />

            <main className="max-w-7xl mx-auto px-6 py-8">
                {/* Header */}
                <div className="flex items-center justify-between mb-12">
                    <div>
                        <h1 className="text-4xl font-black italic tracking-tighter uppercase flex items-center gap-4">
                            <Activity className="w-10 h-10 text-[#c1ff00]" />
                            <span className="text-white">OPS</span>
                            <span className="text-[#c1ff00] drop-shadow-[0_0_10px_rgba(193,255,0,0.5)]">CONSOLE</span>
                        </h1>
                        <p className="text-white/40 mt-2 font-mono text-sm tracking-wide">
                            PIPELINE MONITORING & CONTROL SYSTEM
                        </p>
                    </div>
                    <button
                        onClick={fetchData}
                        disabled={loading}
                        className="flex items-center gap-2 px-5 py-2.5 bg-white/5 hover:bg-[#c1ff00]/10 border border-white/10 hover:border-[#c1ff00]/30 rounded-xl text-sm font-bold text-white/80 hover:text-[#c1ff00] transition-all group"
                    >
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : 'group-hover:rotate-180 transition-transform duration-500'}`} />
                        REFRESH SYSTEM
                    </button>
                </div>

                {/* Error State - Softer Design */}
                {error && (
                    <div className="mb-8 p-8 bg-black/40 border border-[#c1ff00]/20 rounded-2xl text-center relative overflow-hidden group">
                        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-1 bg-gradient-to-r from-transparent via-[#c1ff00]/50 to-transparent" />
                        <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-[#c1ff00]/10 flex items-center justify-center border border-[#c1ff00]/20 shadow-[0_0_15px_rgba(193,255,0,0.1)]">
                            <Lock className="w-8 h-8 text-[#c1ff00]" />
                        </div>
                        <p className="text-white font-black uppercase tracking-wider text-xl mb-2">{error}</p>
                        <p className="text-white/40 text-sm mb-8 font-mono">ACCESS RESTRICTED: ADMIN PRIVILEGES REQUIRED</p>
                        <button
                            onClick={() => window.location.href = '/login?redirect=/ops'}
                            className="px-8 py-3 bg-[#c1ff00] hover:bg-white text-black text-sm font-black uppercase tracking-wider rounded-lg transition-all shadow-[0_0_20px_rgba(193,255,0,0.3)] hover:shadow-[0_0_30px_rgba(255,255,255,0.5)] transform hover:-translate-y-1"
                        >
                            LOGIN TO CONSOLE
                        </button>
                    </div>
                )}

                {/* Loading State */}
                {loading && !error && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                        {[1, 2, 3, 4].map(i => (
                            <div key={i} className="h-24 bg-white/5 rounded-2xl animate-pulse" />
                        ))}
                    </div>
                )}

                {/* Dashboard Content */}
                {!loading && !error && status && (
                    <>
                        {/* Stats Grid */}
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
                            {/* Runs */}
                            <div className="p-5 bg-black/40 border border-violet-500/20 rounded-2xl hover:border-violet-500/50 transition-colors group">
                                <div className="flex items-center gap-2 text-violet-400 mb-2">
                                    <Zap className="w-4 h-4" />
                                    <span className="text-xs font-black uppercase tracking-wider">Runs</span>
                                </div>
                                <div className="text-3xl font-black text-white">{status.total_runs}</div>
                                <div className="mt-2 flex gap-2 text-xs font-mono">
                                    <span className="text-emerald-400">✓ {status.completed}</span>
                                    <span className="text-red-400">✗ {status.failed}</span>
                                    <span className="text-amber-400">◎ {status.running}</span>
                                </div>
                            </div>

                            {/* Evidence Events */}
                            <div className="p-5 bg-black/40 border border-cyan-500/20 rounded-2xl hover:border-cyan-500/50 transition-colors group">
                                <div className="flex items-center gap-2 text-cyan-400 mb-2">
                                    <FlaskConical className="w-4 h-4" />
                                    <span className="text-xs font-black uppercase tracking-wider">Evidence</span>
                                </div>
                                <div className="text-3xl font-black text-white">{status.total_evidence_events}</div>
                                <div className="mt-2 flex gap-2 text-xs font-mono">
                                    <span className="text-emerald-400">✓ {status.evidence_measured}</span>
                                    <span className="text-amber-400">⏳ {status.evidence_pending}</span>
                                </div>
                            </div>

                            {/* VDG Edges */}
                            <div className="p-5 bg-black/40 border border-pink-500/20 rounded-2xl hover:border-pink-500/50 transition-colors group">
                                <div className="flex items-center gap-2 text-pink-400 mb-2">
                                    <GitBranch className="w-4 h-4" />
                                    <span className="text-xs font-black uppercase tracking-wider">VDG Edges</span>
                                </div>
                                <div className="text-3xl font-black text-white">{status.total_vdg_edges}</div>
                                <div className="mt-2 flex gap-2 text-xs font-mono">
                                    <span className="text-emerald-400">✓ {status.edges_confirmed}</span>
                                    <span className="text-amber-400">? {status.edges_candidate}</span>
                                </div>
                            </div>

                            {/* Clusters & Packs */}
                            <div className="p-5 bg-black/40 border border-orange-500/20 rounded-2xl hover:border-orange-500/50 transition-colors group">
                                <div className="flex items-center gap-2 text-orange-400 mb-2">
                                    <Database className="w-4 h-4" />
                                    <span className="text-xs font-black uppercase tracking-wider">P2 Clusters</span>
                                </div>
                                <div className="text-3xl font-black text-white">
                                    {p2Progress?.distill_ready_clusters || 0}
                                    <span className="text-lg text-white/40">/{p2Progress?.target || 10}</span>
                                </div>
                                <div className="mt-2 text-xs text-white/40 font-mono">
                                    {p2Progress?.progress_percent || 0}% Done
                                </div>
                            </div>

                            {/* STPF Engine Status (Ops-Only) */}
                            <div className="p-5 bg-black/40 border border-[#c1ff00]/20 rounded-2xl hover:border-[#c1ff00]/50 transition-colors group relative overflow-hidden">
                                <div className="absolute top-0 right-0 w-16 h-16 bg-[#c1ff00] blur-2xl opacity-10 group-hover:opacity-20 transition-opacity" />
                                <div className="flex items-center gap-2 text-[#c1ff00] mb-2">
                                    <Target className="w-4 h-4" />
                                    <span className="text-xs font-black uppercase tracking-wider">STPF Engine</span>
                                </div>
                                <div className="text-3xl font-black text-white">v3.1</div>
                                <div className="mt-2 flex gap-2 text-xs font-mono">
                                    <span className="text-[#c1ff00]">✓ 14 APIs</span>
                                    <span className="text-cyan-400">7 MCP</span>
                                </div>
                            </div>
                        </div>

                        {/* P2 Clusters Section */}
                        <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden mb-8">
                            <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
                                <h2 className="font-bold text-white flex items-center gap-2">
                                    <Target className="w-5 h-5 text-orange-400" />
                                    P2 Content Clusters
                                    <span className="text-xs text-white/40 ml-2">DistillRun 대상</span>
                                </h2>
                                <div className="flex items-center gap-3">
                                    {/* Progress Bar */}
                                    <div className="flex items-center gap-2">
                                        <div className="w-32 h-2 bg-white/10 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-gradient-to-r from-orange-500 to-[#c1ff00] rounded-full transition-all box-shadow-[0_0_10px_rgba(193,255,0,0.5)]"
                                                style={{ width: `${p2Progress?.progress_percent || 0}%` }}
                                            />
                                        </div>
                                        <span className="text-xs font-mono font-bold text-[#c1ff00]">{p2Progress?.progress_percent || 0}%</span>
                                    </div>
                                    <Link
                                        href="/ops/outliers"
                                        className="px-3 py-1.5 bg-[#c1ff00]/10 hover:bg-[#c1ff00]/20 border border-[#c1ff00]/20 hover:border-[#c1ff00]/40 rounded-lg text-xs font-black text-[#c1ff00] flex items-center gap-1 transition-colors uppercase"
                                    >
                                        <FileVideo className="w-3 h-3" />
                                        Manage Outliers
                                    </Link>
                                </div>
                            </div>

                            {clusters.length === 0 ? (
                                <div className="p-12 text-center text-white/40">
                                    <Target className="w-8 h-8 mx-auto mb-2 opacity-50" />
                                    <p>아직 생성된 클러스터가 없습니다</p>
                                    <p className="text-xs mt-1">Virlo/TikTok에서 아웃라이어를 크롤링하고 클러스터를 생성하세요</p>
                                </div>
                            ) : (
                                <div className="divide-y divide-white/5">
                                    {clusters.map(cluster => (
                                        <div
                                            key={cluster.cluster_id}
                                            className="px-6 py-4 flex items-center justify-between hover:bg-white/[0.02] transition-colors"
                                        >
                                            <div className="flex items-center gap-4">
                                                <div className={`p-2 rounded-lg ${cluster.distill_ready ? 'text-emerald-400 bg-emerald-500/10' : 'text-amber-400 bg-amber-500/10'}`}>
                                                    {cluster.distill_ready ? <CheckCircle className="w-4 h-4" /> : <Clock className="w-4 h-4" />}
                                                </div>
                                                <div>
                                                    <div className="font-medium text-white">{cluster.cluster_name}</div>
                                                    <div className="text-xs text-white/40">
                                                        {cluster.kids_count}개 Kids · Parent: {cluster.parent_vdg_id}
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <span className={`px-2 py-1 rounded text-xs font-medium ${cluster.distill_ready ? 'text-emerald-400 bg-emerald-500/10' : 'text-amber-400 bg-amber-500/10'}`}>
                                                    {cluster.distill_ready ? 'Distill Ready' : 'Pending'}
                                                </span>
                                                <ChevronRight className="w-4 h-4 text-white/20" />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Source Packs Section (Phase D) */}
                        {sourcePacks.length > 0 && (
                            <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden mb-8">
                                <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
                                    <h2 className="font-bold text-white flex items-center gap-2">
                                        <BookOpen className="w-5 h-5 text-sky-400" />
                                        Source Packs
                                        <span className="text-xs text-white/40 ml-2">NotebookLM Integration</span>
                                    </h2>
                                    <span className="text-xs text-white/40">{sourcePacks.length}개</span>
                                </div>

                                <div className="divide-y divide-white/5">
                                    {sourcePacks.map(pack => (
                                        <div
                                            key={pack.id}
                                            className="px-6 py-4 flex items-center justify-between hover:bg-white/[0.02] transition-colors"
                                        >
                                            <div className="flex items-center gap-4">
                                                <div className={`p-2 rounded-lg ${pack.notebook_id ? 'text-emerald-400 bg-emerald-500/10' : 'text-amber-400 bg-amber-500/10'}`}>
                                                    {pack.notebook_id ? <CheckCircle className="w-4 h-4" /> : <Clock className="w-4 h-4" />}
                                                </div>
                                                <div>
                                                    <div className="font-medium text-white">
                                                        {pack.cluster_id}
                                                        <span className="text-white/40 text-sm ml-2">({pack.temporal_phase})</span>
                                                    </div>
                                                    <div className="text-xs text-white/40">
                                                        {pack.entry_count}개 엔트리 · {pack.pack_mode || 'standard'} · {pack.pack_type}
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="flex items-center gap-2">
                                                {pack.notebook_id ? (
                                                    <span className="px-3 py-1.5 rounded-lg text-xs font-medium text-emerald-400 bg-emerald-500/10 flex items-center gap-1">
                                                        <CheckCircle className="w-3 h-3" />
                                                        연동 완료
                                                    </span>
                                                ) : (
                                                    <button
                                                        onClick={() => handleUploadToNotebook(pack.id)}
                                                        disabled={uploading === pack.id}
                                                        className="px-3 py-1.5 bg-sky-500/20 hover:bg-sky-500/30 border border-sky-500/30 rounded-lg text-xs font-medium text-sky-300 flex items-center gap-1 transition-colors"
                                                    >
                                                        {uploading === pack.id ? (
                                                            <>
                                                                <RefreshCw className="w-3 h-3 animate-spin" />
                                                                업로드 중...
                                                            </>
                                                        ) : (
                                                            <>
                                                                <Upload className="w-3 h-3" />
                                                                NotebookLM 업로드
                                                            </>
                                                        )}
                                                    </button>
                                                )}

                                                {pack.drive_url && (
                                                    <a
                                                        href={pack.drive_url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="p-2 hover:bg-white/5 rounded-lg text-white/40 hover:text-white transition-colors"
                                                    >
                                                        <ExternalLink className="w-4 h-4" />
                                                    </a>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Recent Runs */}
                        <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
                            <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
                                <h2 className="font-bold text-white flex items-center gap-2">
                                    <BarChart3 className="w-5 h-5 text-violet-400" />
                                    Recent Runs
                                </h2>
                                <span className="text-xs text-white/40">{runs.length}개</span>
                            </div>

                            {runs.length === 0 ? (
                                <div className="p-12 text-center text-white/40">
                                    <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
                                    <p>아직 실행된 Run이 없습니다</p>
                                </div>
                            ) : (
                                <div className="divide-y divide-white/5">
                                    {runs.map(run => (
                                        <div
                                            key={run.id}
                                            className="px-6 py-4 flex items-center justify-between hover:bg-white/[0.02] transition-colors"
                                        >
                                            <div className="flex items-center gap-4">
                                                <div className={`p-2 rounded-lg ${getStatusColor(run.status)}`}>
                                                    {getStatusIcon(run.status)}
                                                </div>
                                                <div>
                                                    <div className="font-medium text-white">{run.run_type}</div>
                                                    <div className="text-xs text-white/40">
                                                        {run.started_at ? new Date(run.started_at).toLocaleString('ko-KR') : '-'}
                                                        {typeof run.duration_sec === 'number' && ` · ${Math.round(run.duration_sec)}s`}
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="flex items-center gap-2">
                                                <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(run.status)}`}>
                                                    {run.status}
                                                </span>

                                                {run.status === 'FAILED' && (
                                                    <button
                                                        onClick={() => handleRetry(run.id)}
                                                        disabled={retrying === run.id}
                                                        className="p-2 hover:bg-white/5 rounded-lg text-white/40 hover:text-white transition-colors"
                                                    >
                                                        <RotateCcw className={`w-4 h-4 ${retrying === run.id ? 'animate-spin' : ''}`} />
                                                    </button>
                                                )}

                                                <button className="p-2 hover:bg-white/5 rounded-lg text-white/40 hover:text-white transition-colors">
                                                    <ChevronRight className="w-4 h-4" />
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Quick Actions */}
                        <div className="mt-8 grid md:grid-cols-4 gap-4">
                            <Link
                                href="/ops/outliers"
                                className="p-4 bg-violet-500/10 hover:bg-violet-500/20 border border-violet-500/20 rounded-xl text-left transition-colors group"
                            >
                                <div className="flex items-center justify-between mb-2">
                                    <FileVideo className="w-5 h-5 text-violet-400" />
                                    <ArrowRight className="w-4 h-4 text-white/20 group-hover:text-violet-400 transition-colors" />
                                </div>
                                <div className="font-bold text-white">아웃라이어 관리</div>
                                <div className="text-xs text-white/50">Promote & VDG 분석</div>
                            </Link>

                            <button className="p-4 bg-orange-500/10 hover:bg-orange-500/20 border border-orange-500/20 rounded-xl text-left transition-colors group">
                                <div className="flex items-center justify-between mb-2">
                                    <Sparkles className="w-5 h-5 text-orange-400" />
                                    <ArrowRight className="w-4 h-4 text-white/20 group-hover:text-orange-400 transition-colors" />
                                </div>
                                <div className="font-bold text-white">P3 DistillRun</div>
                                <div className="text-xs text-white/50">주간 자동화 실행</div>
                            </button>

                            <button className="p-4 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/20 rounded-xl text-left transition-colors group">
                                <div className="flex items-center justify-between mb-2">
                                    <TrendingUp className="w-5 h-5 text-cyan-400" />
                                    <ArrowRight className="w-4 h-4 text-white/20 group-hover:text-cyan-400 transition-colors" />
                                </div>
                                <div className="font-bold text-white">성과 리포트</div>
                                <div className="text-xs text-white/50">3축 승격 현황</div>
                            </button>

                            <button className="p-4 bg-pink-500/10 hover:bg-pink-500/20 border border-pink-500/20 rounded-xl text-left transition-colors group">
                                <div className="flex items-center justify-between mb-2">
                                    <FlaskConical className="w-5 h-5 text-pink-400" />
                                    <ArrowRight className="w-4 h-4 text-white/20 group-hover:text-pink-400 transition-colors" />
                                </div>
                                <div className="font-bold text-white">로그 품질</div>
                                <div className="text-xs text-white/50">P1 세션 로그 검증</div>
                            </button>
                        </div>
                    </>
                )}
            </main>

            <SessionHUD collapsed={false} />
        </div>
    );
}
