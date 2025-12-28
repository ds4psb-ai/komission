'use client';

/**
 * SessionHUD - 운영자 헤드업 디스플레이 (PEGL v1.0)
 * 
 * 문서: 15_FINAL_ARCHITECTURE.md Phase 6
 * - 현재 진행 상태 표시
 * - 단일 CTA (다음 액션)
 * - 실패/대기 항목 요약
 */
import { useState, useEffect } from 'react';
import {
    Activity, AlertCircle, CheckCircle, Clock, Play,
    RefreshCw, ChevronUp, ChevronDown, Loader2
} from 'lucide-react';

interface HUDData {
    current_action: string | null;
    pending_items: number;
    failed_items: number;
    next_cta: string | null;
    last_run?: {
        id: string;
        run_type: string;
        status: string;
        started_at: string | null;
        ended_at: string | null;
    };
}

interface SessionHUDProps {
    className?: string;
    collapsed?: boolean;
}

export function SessionHUD({ className = '', collapsed: initialCollapsed = true }: SessionHUDProps) {
    const [data, setData] = useState<HUDData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [collapsed, setCollapsed] = useState(initialCollapsed);
    const [hasToken, setHasToken] = useState(false);

    // SSR 안전 토큰 확인
    useEffect(() => {
        if (typeof window !== 'undefined') {
            setHasToken(!!localStorage.getItem('token'));
        }
    }, []);

    useEffect(() => {
        if (!hasToken) return;
        fetchHUD();
        // Auto-refresh every 30 seconds
        const interval = setInterval(fetchHUD, 30000);
        return () => clearInterval(interval);
    }, [hasToken]);

    async function fetchHUD() {
        if (typeof window === 'undefined') return;

        try {
            setLoading(true);
            const token = localStorage.getItem('token');
            if (!token) return;

            const response = await fetch('/api/v1/ops/hud', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) throw new Error('Failed to fetch HUD');
            const hudData = await response.json();
            setData(hudData);
            setError(null);
        } catch {
            if (typeof window !== 'undefined' && localStorage.getItem('token')) {
                setError('HUD unavailable');
            }
        } finally {
            setLoading(false);
        }
    }

    // Don't show if no token
    if (!hasToken) return null;

    // Collapsed state - just show indicator
    if (collapsed) {
        const hasIssues = data && (data.failed_items > 0 || data.pending_items > 0);

        return (
            <button
                onClick={() => setCollapsed(false)}
                className={`fixed bottom-4 right-4 z-50 flex items-center gap-2 px-3 py-2 rounded-full 
                    ${hasIssues ? 'bg-amber-500/20 border-amber-500/50' : 'bg-white/5 border-white/10'} 
                    border backdrop-blur-sm hover:bg-white/10 transition-all ${className}`}
            >
                {loading ? (
                    <Loader2 className="w-4 h-4 animate-spin text-white/50" />
                ) : hasIssues ? (
                    <AlertCircle className="w-4 h-4 text-amber-400" />
                ) : (
                    <Activity className="w-4 h-4 text-emerald-400" />
                )}
                <span className="text-xs text-white/70">{data?.current_action || 'Idle'}</span>
                <ChevronUp className="w-3 h-3 text-white/40" />
            </button>
        );
    }

    // Expanded HUD
    return (
        <div className={`fixed bottom-4 right-4 z-50 w-80 bg-[#0a0a0a]/95 border border-white/10 rounded-xl backdrop-blur-md shadow-2xl ${className}`}>
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
                <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-violet-400" />
                    <span className="text-sm font-medium text-white">Session HUD</span>
                </div>
                <button onClick={() => setCollapsed(true)} className="p-1 hover:bg-white/5 rounded">
                    <ChevronDown className="w-4 h-4 text-white/40" />
                </button>
            </div>

            {/* Content */}
            <div className="px-4 py-3 space-y-3">
                {error ? (
                    <div className="text-xs text-red-400">{error}</div>
                ) : loading && !data ? (
                    <div className="flex items-center gap-2 text-white/50">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span className="text-xs">Loading...</span>
                    </div>
                ) : data ? (
                    <>
                        {/* Current Status */}
                        <div className="flex items-center gap-2">
                            {data.failed_items > 0 ? (
                                <AlertCircle className="w-4 h-4 text-red-400" />
                            ) : data.pending_items > 0 ? (
                                <Clock className="w-4 h-4 text-amber-400" />
                            ) : (
                                <CheckCircle className="w-4 h-4 text-emerald-400" />
                            )}
                            <span className="text-sm text-white">{data.current_action || 'All clear'}</span>
                        </div>

                        {/* Stats */}
                        <div className="flex gap-3 text-xs">
                            {data.pending_items > 0 && (
                                <div className="flex items-center gap-1 px-2 py-1 bg-amber-500/10 rounded text-amber-300">
                                    <Clock className="w-3 h-3" />
                                    <span>{data.pending_items} pending</span>
                                </div>
                            )}
                            {data.failed_items > 0 && (
                                <div className="flex items-center gap-1 px-2 py-1 bg-red-500/10 rounded text-red-300">
                                    <AlertCircle className="w-3 h-3" />
                                    <span>{data.failed_items} failed</span>
                                </div>
                            )}
                            {data.pending_items === 0 && data.failed_items === 0 && (
                                <div className="flex items-center gap-1 px-2 py-1 bg-emerald-500/10 rounded text-emerald-300">
                                    <CheckCircle className="w-3 h-3" />
                                    <span>No issues</span>
                                </div>
                            )}
                        </div>

                        {/* Last Run */}
                        {data.last_run && (
                            <div className="text-xs text-white/40 border-t border-white/5 pt-2">
                                Last: {data.last_run.run_type}
                                <span className={`ml-1 ${data.last_run.status === 'COMPLETED' ? 'text-emerald-400' :
                                        data.last_run.status === 'FAILED' ? 'text-red-400' :
                                            'text-amber-400'
                                    }`}>
                                    {data.last_run.status}
                                </span>
                            </div>
                        )}

                        {/* CTA Button */}
                        {data.next_cta && (
                            <button className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-violet-500 hover:bg-violet-400 rounded-lg text-sm font-medium text-white transition-colors">
                                <Play className="w-4 h-4" />
                                {data.next_cta}
                            </button>
                        )}
                    </>
                ) : null}
            </div>

            {/* Refresh */}
            <div className="px-4 py-2 border-t border-white/5 flex justify-end">
                <button
                    onClick={fetchHUD}
                    disabled={loading}
                    className="text-xs text-white/40 hover:text-white/70 flex items-center gap-1"
                >
                    <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
                    Refresh
                </button>
            </div>
        </div>
    );
}

export default SessionHUD;
