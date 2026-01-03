"use client";

import { useTranslations } from 'next-intl';
/**
 * Kick Curation Page (P1-2)
 * 
 * Operators can:
 * 1. View all kicks with filters
 * 2. Approve/reject kicks
 * 3. See kick details + keyframes
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
    Check, X, AlertCircle, Filter, RefreshCw,
    ChevronDown, Eye, Clock, Zap, MessageCircle
} from 'lucide-react';
import { api } from '@/lib/api';

interface Kick {
    id: string;
    kick_id: string;
    node_id: string;
    kick_index: number;
    title: string;
    mechanism: string;
    creator_instruction: string;
    start_ms: number;
    end_ms: number;
    confidence: number;
    proof_ready: boolean;
    missing_reason: string | null;
    status: string;
    comment_evidence_count: number;
    frame_evidence_count: number;
    created_at: string;
}

interface KickStats {
    total: number;
    by_status: {
        pending: number;
        approved: number;
        rejected: number;
        needs_review: number;
    };
    proof_ready: number;
    avg_confidence: number;
}

export default function KickCurationPage() {
    const router = useRouter();
    const [kicks, setKicks] = useState<Kick[]>([]);
    const [stats, setStats] = useState<KickStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Filters
    const [statusFilter, setStatusFilter] = useState<string>('pending');
    const [proofReadyFilter, setProofReadyFilter] = useState<boolean | null>(null);
    const [minConfidence, setMinConfidence] = useState(0.6);

    // Action state
    const [actionLoading, setActionLoading] = useState<string | null>(null);

    const fetchKicks = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const params = new URLSearchParams();
            if (statusFilter) params.append('status', statusFilter);
            if (proofReadyFilter !== null) params.append('proof_ready', String(proofReadyFilter));
            if (minConfidence > 0) params.append('min_confidence', String(minConfidence));

            const response = await fetch(`/api/v1/outliers/kicks?${params}`, {
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error('Failed to fetch kicks');
            }

            const data = await response.json();
            setKicks(data.kicks || []);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    }, [statusFilter, proofReadyFilter, minConfidence]);

    const fetchStats = useCallback(async () => {
        try {
            const response = await fetch('/api/v1/outliers/kicks/stats/summary', {
                credentials: 'include'
            });
            if (response.ok) {
                const data = await response.json();
                setStats(data);
            }
        } catch (err) {
            console.error('Failed to fetch stats:', err);
        }
    }, []);

    useEffect(() => {
        fetchKicks();
        fetchStats();
    }, [fetchKicks, fetchStats]);

    const handleReview = async (kickId: string, action: 'approve' | 'reject' | 'needs_review') => {
        setActionLoading(kickId);
        try {
            const response = await fetch(`/api/v1/outliers/kicks/${kickId}/review`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ action }),
            });

            if (!response.ok) {
                throw new Error('Failed to review kick');
            }

            // Refresh list
            await fetchKicks();
            await fetchStats();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Review failed');
        } finally {
            setActionLoading(null);
        }
    };

    const formatTime = (ms: number) => {
        const seconds = Math.floor(ms / 1000);
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const getStatusBadge = (status: string) => {
        const styles: Record<string, string> = {
            pending: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
            approved: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
            rejected: 'bg-red-500/20 text-red-300 border-red-500/30',
            needs_review: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
        };
        return styles[status] || 'bg-gray-500/20 text-gray-300 border-gray-500/30';
    };

    return (
        <div className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-black">🎯 Kick Curation</h1>
                        <p className="text-white/50 mt-1">Proof-Grade 킥 검토 및 승인</p>
                    </div>
                    <button
                        onClick={() => { fetchKicks(); fetchStats(); }}
                        className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/15 rounded-lg transition-colors"
                    >
                        <RefreshCw className="w-4 h-4" />
                        새로고침
                    </button>
                </div>

                {/* Stats Cards */}
                {stats && (
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
                        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                            <div className="text-3xl font-black">{stats.total}</div>
                            <div className="text-white/50 text-sm">전체</div>
                        </div>
                        <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-4">
                            <div className="text-3xl font-black text-yellow-300">{stats.by_status.pending}</div>
                            <div className="text-white/50 text-sm">대기중</div>
                        </div>
                        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4">
                            <div className="text-3xl font-black text-emerald-300">{stats.by_status.approved}</div>
                            <div className="text-white/50 text-sm">승인됨</div>
                        </div>
                        <div className="bg-cyan-500/10 border border-cyan-500/20 rounded-xl p-4">
                            <div className="text-3xl font-black text-cyan-300">{stats.proof_ready}</div>
                            <div className="text-white/50 text-sm">Proof Ready</div>
                        </div>
                        <div className="bg-violet-500/10 border border-violet-500/20 rounded-xl p-4">
                            <div className="text-3xl font-black text-violet-300">{(stats.avg_confidence * 100).toFixed(0)}%</div>
                            <div className="text-white/50 text-sm">평균 신뢰도</div>
                        </div>
                    </div>
                )}

                {/* Filters */}
                <div className="flex flex-wrap gap-4 mb-6 p-4 bg-white/5 rounded-xl border border-white/10">
                    <div className="flex items-center gap-2">
                        <Filter className="w-4 h-4 text-white/50" />
                        <span className="text-white/50 text-sm">필터:</span>
                    </div>

                    <select
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                        className="bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-sm"
                    >
                        <option value="">모든 상태</option>
                        <option value="pending">대기중</option>
                        <option value="approved">승인됨</option>
                        <option value="rejected">거부됨</option>
                        <option value="needs_review">검토필요</option>
                    </select>

                    <select
                        value={proofReadyFilter === null ? '' : String(proofReadyFilter)}
                        onChange={(e) => setProofReadyFilter(e.target.value === '' ? null : e.target.value === 'true')}
                        className="bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-sm"
                    >
                        <option value="">Proof 상태</option>
                        <option value="true">Proof Ready</option>
                        <option value="false">Not Ready</option>
                    </select>

                    <div className="flex items-center gap-2">
                        <span className="text-white/50 text-sm">신뢰도 ≥</span>
                        <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.1"
                            value={minConfidence}
                            onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
                            className="w-24"
                        />
                        <span className="text-sm font-mono">{(minConfidence * 100).toFixed(0)}%</span>
                    </div>
                </div>

                {/* Error */}
                {error && (
                    <div className="mb-6 p-4 bg-red-500/20 border border-red-500/30 rounded-xl flex items-center gap-3">
                        <AlertCircle className="w-5 h-5 text-red-400" />
                        <span className="text-red-300">{error}</span>
                    </div>
                )}

                {/* Loading */}
                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <RefreshCw className="w-8 h-8 animate-spin text-white/50" />
                    </div>
                ) : (
                    /* Kick List */
                    <div className="space-y-4">
                        {kicks.length === 0 ? (
                            <div className="text-center py-20 text-white/40">
                                필터 조건에 맞는 킥이 없습니다.
                            </div>
                        ) : (
                            kicks.map((kick) => (
                                <div
                                    key={kick.id}
                                    className="bg-white/5 border border-white/10 rounded-xl p-5 hover:border-white/20 transition-colors"
                                >
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                            {/* Header */}
                                            <div className="flex items-center gap-3 mb-2">
                                                <span className={`px-2 py-1 text-xs font-bold rounded border ${getStatusBadge(kick.status)}`}>
                                                    {kick.status.toUpperCase()}
                                                </span>
                                                {kick.proof_ready && (
                                                    <span className="px-2 py-1 text-xs font-bold rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                                                        ✓ PROOF READY
                                                    </span>
                                                )}
                                                <span className="text-white/40 text-xs font-mono">
                                                    {kick.kick_id}
                                                </span>
                                            </div>

                                            {/* Title */}
                                            <h3 className="text-lg font-bold mb-1">{kick.title}</h3>

                                            {/* Mechanism */}
                                            <p className="text-white/60 text-sm mb-3">{kick.mechanism}</p>

                                            {/* Instruction */}
                                            {kick.creator_instruction && (
                                                <div className="p-3 bg-violet-500/10 border border-violet-500/20 rounded-lg mb-3">
                                                    <span className="text-violet-300 text-sm">"{kick.creator_instruction}"</span>
                                                </div>
                                            )}

                                            {/* Meta */}
                                            <div className="flex flex-wrap gap-4 text-xs text-white/40">
                                                <div className="flex items-center gap-1">
                                                    <Clock className="w-3 h-3" />
                                                    {formatTime(kick.start_ms)} - {formatTime(kick.end_ms)}
                                                </div>
                                                <div className="flex items-center gap-1">
                                                    <Zap className="w-3 h-3" />
                                                    신뢰도 {(kick.confidence * 100).toFixed(0)}%
                                                </div>
                                                <div className="flex items-center gap-1">
                                                    <MessageCircle className="w-3 h-3" />
                                                    댓글 증거 {kick.comment_evidence_count}개
                                                </div>
                                                <div className="flex items-center gap-1">
                                                    <Eye className="w-3 h-3" />
                                                    프레임 증거 {kick.frame_evidence_count}개
                                                </div>
                                            </div>

                                            {/* Missing Reason */}
                                            {kick.missing_reason && (
                                                <div className="mt-2 text-orange-400 text-xs">
                                                    ⚠️ {kick.missing_reason}
                                                </div>
                                            )}
                                        </div>

                                        {/* Actions */}
                                        {kick.status === 'pending' && (
                                            <div className="flex gap-2 ml-4">
                                                <button
                                                    onClick={() => handleReview(kick.kick_id, 'approve')}
                                                    disabled={actionLoading === kick.kick_id}
                                                    className="p-2 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 rounded-lg transition-colors disabled:opacity-50"
                                                >
                                                    {actionLoading === kick.kick_id ? (
                                                        <RefreshCw className="w-5 h-5 animate-spin" />
                                                    ) : (
                                                        <Check className="w-5 h-5" />
                                                    )}
                                                </button>
                                                <button
                                                    onClick={() => handleReview(kick.kick_id, 'reject')}
                                                    disabled={actionLoading === kick.kick_id}
                                                    className="p-2 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg transition-colors disabled:opacity-50"
                                                >
                                                    <X className="w-5 h-5" />
                                                </button>
                                                <button
                                                    onClick={() => handleReview(kick.kick_id, 'needs_review')}
                                                    disabled={actionLoading === kick.kick_id}
                                                    className="p-2 bg-orange-500/20 hover:bg-orange-500/30 text-orange-300 rounded-lg transition-colors disabled:opacity-50"
                                                >
                                                    <AlertCircle className="w-5 h-5" />
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
