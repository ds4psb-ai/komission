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

import { useState, useEffect } from 'react';
import { AppHeader } from '@/components/AppHeader';
import { SessionHUD } from '@/components/SessionHUD';
import {
    Activity, AlertCircle, CheckCircle, Clock,
    RefreshCw, ChevronRight, Database, GitBranch, BarChart3,
    Zap, FlaskConical, ArrowRight, RotateCcw, Upload, BookOpen, ExternalLink
} from 'lucide-react';
import { api, SourcePackItem } from '@/lib/api';

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

export default function OpsConsolePage() {
    const [status, setStatus] = useState<PipelineStatus | null>(null);
    const [runs, setRuns] = useState<RunItem[]>([]);
    const [sourcePacks, setSourcePacks] = useState<SourcePackItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [retrying, setRetrying] = useState<string | null>(null);
    const [uploading, setUploading] = useState<string | null>(null);

    useEffect(() => {
        fetchData();
    }, []);

    async function fetchData() {
        try {
            setLoading(true);

            // SSR 방지
            if (typeof window === 'undefined') {
                setLoading(false);
                return;
            }

            const token = localStorage.getItem('token');
            if (!token) {
                setError('로그인이 필요합니다');
                setLoading(false);
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
                    setError('관리자 권한이 필요합니다');
                } else {
                    setError('데이터를 불러오지 못했습니다');
                }
                setLoading(false);
                return;
            }

            const [statusData, runsData] = await Promise.all([
                statusRes.json(),
                runsRes.json(),
            ]);

            setStatus(statusData);
            setRuns(runsData);

            // Fetch Source Packs (with API fallback)
            try {
                const packsData = await api.getSourcePacks({ limit: 10 });
                setSourcePacks(packsData.source_packs || []);
            } catch (e) {
                console.warn("Source Packs API failed:", e);
                setSourcePacks([]);
            }
        } catch {
            setError('서버 연결 실패');
        } finally {
            setLoading(false);
        }
    }

    async function handleRetry(runId: string) {
        setRetrying(runId);
        try {
            const token = localStorage.getItem('token');
            const res = await fetch(`/api/v1/ops/runs/${runId}/retry`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
            });
            if (res.ok) {
                fetchData();
            }
        } finally {
            setRetrying(null);
        }
    }

    async function handleUploadToNotebook(packId: string) {
        setUploading(packId);
        try {
            const result = await api.uploadSourcePackToNotebook(packId);
            if (result.success) {
                alert(`✅ NotebookLM 업로드 완료: ${result.message}`);
                fetchData(); // Refresh to update notebook_id status
            } else {
                alert(`❌ 업로드 실패: ${result.message}`);
            }
        } catch (e: any) {
            alert(`❌ 오류: ${e.message || '알 수 없는 오류'}`);
        } finally {
            setUploading(null);
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
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-black flex items-center gap-3">
                            <Activity className="w-8 h-8 text-violet-400" />
                            Ops Console
                        </h1>
                        <p className="text-white/50 mt-1">파이프라인 운영 대시보드</p>
                    </div>
                    <button
                        onClick={fetchData}
                        disabled={loading}
                        className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-sm transition-colors"
                    >
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                        새로고침
                    </button>
                </div>

                {/* Error State */}
                {error && (
                    <div className="mb-8 p-6 bg-red-500/10 border border-red-500/20 rounded-2xl text-center">
                        <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
                        <p className="text-red-400 font-bold">{error}</p>
                        <button
                            onClick={() => window.location.href = '/login'}
                            className="mt-4 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 rounded-lg text-red-300 text-sm"
                        >
                            로그인 페이지로 이동
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
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                            {/* Runs */}
                            <div className="p-5 bg-gradient-to-br from-violet-500/10 to-violet-900/10 border border-violet-500/20 rounded-2xl">
                                <div className="flex items-center gap-2 text-violet-400 mb-2">
                                    <Zap className="w-4 h-4" />
                                    <span className="text-xs font-medium">Runs</span>
                                </div>
                                <div className="text-3xl font-black text-white">{status.total_runs}</div>
                                <div className="mt-2 flex gap-2 text-xs">
                                    <span className="text-emerald-400">✓ {status.completed}</span>
                                    <span className="text-red-400">✗ {status.failed}</span>
                                    <span className="text-amber-400">◎ {status.running}</span>
                                </div>
                            </div>

                            {/* Evidence Events */}
                            <div className="p-5 bg-gradient-to-br from-cyan-500/10 to-cyan-900/10 border border-cyan-500/20 rounded-2xl">
                                <div className="flex items-center gap-2 text-cyan-400 mb-2">
                                    <FlaskConical className="w-4 h-4" />
                                    <span className="text-xs font-medium">Evidence</span>
                                </div>
                                <div className="text-3xl font-black text-white">{status.total_evidence_events}</div>
                                <div className="mt-2 flex gap-2 text-xs">
                                    <span className="text-emerald-400">✓ {status.evidence_measured}</span>
                                    <span className="text-amber-400">⏳ {status.evidence_pending}</span>
                                </div>
                            </div>

                            {/* VDG Edges */}
                            <div className="p-5 bg-gradient-to-br from-pink-500/10 to-pink-900/10 border border-pink-500/20 rounded-2xl">
                                <div className="flex items-center gap-2 text-pink-400 mb-2">
                                    <GitBranch className="w-4 h-4" />
                                    <span className="text-xs font-medium">VDG Edges</span>
                                </div>
                                <div className="text-3xl font-black text-white">{status.total_vdg_edges}</div>
                                <div className="mt-2 flex gap-2 text-xs">
                                    <span className="text-emerald-400">✓ {status.edges_confirmed}</span>
                                    <span className="text-amber-400">? {status.edges_candidate}</span>
                                </div>
                            </div>

                            {/* Clusters & Packs */}
                            <div className="p-5 bg-gradient-to-br from-orange-500/10 to-orange-900/10 border border-orange-500/20 rounded-2xl">
                                <div className="flex items-center gap-2 text-orange-400 mb-2">
                                    <Database className="w-4 h-4" />
                                    <span className="text-xs font-medium">Clusters</span>
                                </div>
                                <div className="text-3xl font-black text-white">{status.total_clusters}</div>
                                <div className="mt-2 text-xs text-white/40">
                                    {status.total_source_packs} Source Packs
                                </div>
                            </div>
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
                                                        {run.duration_sec && ` · ${Math.round(run.duration_sec)}s`}
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
                        <div className="mt-8 grid md:grid-cols-3 gap-4">
                            <button className="p-4 bg-violet-500/10 hover:bg-violet-500/20 border border-violet-500/20 rounded-xl text-left transition-colors group">
                                <div className="flex items-center justify-between mb-2">
                                    <Zap className="w-5 h-5 text-violet-400" />
                                    <ArrowRight className="w-4 h-4 text-white/20 group-hover:text-violet-400 transition-colors" />
                                </div>
                                <div className="font-bold text-white">새 크롤 실행</div>
                                <div className="text-xs text-white/50">Outlier 수집 시작</div>
                            </button>

                            <button className="p-4 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/20 rounded-xl text-left transition-colors group">
                                <div className="flex items-center justify-between mb-2">
                                    <FlaskConical className="w-5 h-5 text-cyan-400" />
                                    <ArrowRight className="w-4 h-4 text-white/20 group-hover:text-cyan-400 transition-colors" />
                                </div>
                                <div className="font-bold text-white">Evidence 검토</div>
                                <div className="text-xs text-white/50">대기 중인 이벤트 확인</div>
                            </button>

                            <button className="p-4 bg-pink-500/10 hover:bg-pink-500/20 border border-pink-500/20 rounded-xl text-left transition-colors group">
                                <div className="flex items-center justify-between mb-2">
                                    <GitBranch className="w-5 h-5 text-pink-400" />
                                    <ArrowRight className="w-4 h-4 text-white/20 group-hover:text-pink-400 transition-colors" />
                                </div>
                                <div className="font-bold text-white">Edge 확정</div>
                                <div className="text-xs text-white/50">Candidate Edge 검토</div>
                            </button>
                        </div>
                    </>
                )}
            </main>

            <SessionHUD collapsed={false} />
        </div>
    );
}
