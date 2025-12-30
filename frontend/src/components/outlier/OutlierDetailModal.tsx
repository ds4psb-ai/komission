'use client';

/**
 * OutlierDetailModal - Unified detail view modal for outlier items
 * 
 * Combines:
 * - TikTok video player with unmute
 * - Outlier metadata and metrics
 * - VDG-based filming guide (empty when pending, filled when completed)
 * - Pipeline actions (promote, approve VDG, etc.)
 */

import { ExternalLink, X, ArrowUpRight, Play, RefreshCw, Gift } from 'lucide-react';
import { OutlierItem } from '@/lib/api';
import {
    TikTokPlayer,
    TierBadge,
    OutlierMetrics,
    PipelineStatus,
    FilmingGuide,
    getPipelineStage,
} from './index';
import { VDGCard, VDGData } from '@/components/canvas/VDGCard';

interface OutlierDetailModalProps {
    item: OutlierItem;
    onClose: () => void;
    onPromote?: (id: string, campaignEligible?: boolean) => void;
    onApprove?: (id: string) => void;
    actionLoading?: string | null;
}

export function OutlierDetailModal({
    item,
    onClose,
    onPromote,
    onApprove,
    actionLoading,
}: OutlierDetailModalProps) {
    const stage = getPipelineStage(item.status, item.analysis_status);
    const vdgData = item.vdg_analysis as VDGData | undefined;

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-md"
            onClick={onClose}
        >
            <div
                className="relative flex max-w-5xl w-full mx-4 gap-6"
                onClick={e => e.stopPropagation()}
            >
                {/* Close Button */}
                <button
                    onClick={onClose}
                    className="absolute -top-12 right-0 p-2 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
                >
                    <X className="w-6 h-6" />
                </button>

                {/* Left: Video Player */}
                <TikTokPlayer
                    videoUrl={item.video_url}
                    thumbnailUrl={item.thumbnail_url ?? undefined}
                    size="lg"
                    showUnmute={true}
                    className="flex-shrink-0"
                />

                {/* Right: Metadata Panel */}
                <div className="flex-1 bg-zinc-900/90 rounded-2xl p-6 border border-white/10 overflow-y-auto max-h-[80vh]">
                    {/* Header: Tier + Outlier Score + Status */}
                    <div className="flex items-center gap-3 mb-4 flex-wrap">
                        <TierBadge tier={item.outlier_tier} size="md" />
                        <span className="text-pink-400 font-mono text-sm">
                            {item.outlier_score?.toFixed(1)}x 아웃라이어
                        </span>
                        <PipelineStatus
                            status={item.status as 'pending' | 'promoted'}
                            analysisStatus={item.analysis_status}
                            size="sm"
                        />
                    </div>

                    {/* Title */}
                    <h2 className="text-xl font-bold text-white mb-4 leading-tight">
                        {item.title || '(제목 없음)'}
                    </h2>

                    {/* Performance Metrics */}
                    <OutlierMetrics
                        viewCount={item.view_count}
                        likeCount={item.like_count}
                        shareCount={item.share_count}
                        commentCount={item.best_comments_count}
                        layout="grid"
                        className="mb-6"
                    />

                    {/* Filming Guide - VDG based or empty */}
                    <FilmingGuide
                        vdgAnalysis={vdgData as any}
                        analysisStatus={item.analysis_status}
                        className="mb-6"
                    />

                    {/* VDG Analysis Card (when completed) */}
                    {stage === 'completed' && vdgData && (
                        <div className="mb-6">
                            <h3 className="text-sm font-bold text-white/60 mb-2">🧬 VDG 분석 상세</h3>
                            <VDGCard vdg={vdgData} className="border-0" />
                        </div>
                    )}

                    {/* Details */}
                    <div className="space-y-3 mb-6 text-sm border-t border-white/10 pt-4">
                        <div className="flex justify-between">
                            <span className="text-white/50">플랫폼</span>
                            <span className="text-white font-medium">{item.platform}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-white/50">카테고리</span>
                            <span className="text-white font-medium">{item.category}</span>
                        </div>
                        {item.external_id && (
                            <div className="flex justify-between">
                                <span className="text-white/50">External ID</span>
                                <span className="text-white/40 font-mono text-xs">{item.external_id}</span>
                            </div>
                        )}
                    </div>

                    {/* Actions */}
                    <div className="flex gap-3 pt-4 border-t border-white/10">
                        {/* Promote Button (pending stage) */}
                        {stage === 'pending' && onPromote && (
                            <div className="flex-1 flex gap-2">
                                <button
                                    onClick={() => onPromote(item.id, false)}
                                    disabled={actionLoading === item.id}
                                    className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 rounded-xl font-bold transition-colors disabled:opacity-50"
                                >
                                    {actionLoading === item.id ? (
                                        <RefreshCw className="w-4 h-4 animate-spin" />
                                    ) : (
                                        <ArrowUpRight className="w-4 h-4" />
                                    )}
                                    승격
                                </button>
                                <button
                                    onClick={() => onPromote(item.id, true)}
                                    disabled={actionLoading === item.id}
                                    className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-pink-500/20 hover:bg-pink-500/30 text-pink-300 rounded-xl font-bold transition-colors disabled:opacity-50"
                                    title="체험단 캠페인 후보로 등록"
                                >
                                    <Gift className="w-4 h-4" />
                                    체험단 선정
                                </button>
                            </div>
                        )}

                        {/* Approve VDG Button (promoted stage) */}
                        {stage === 'promoted' && onApprove && (
                            <button
                                onClick={() => onApprove(item.id)}
                                disabled={actionLoading === item.id}
                                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-violet-500/30 to-pink-500/30 hover:from-violet-500/40 hover:to-pink-500/40 text-white rounded-xl font-bold transition-all disabled:opacity-50"
                            >
                                {actionLoading === item.id ? (
                                    <RefreshCw className="w-4 h-4 animate-spin" />
                                ) : (
                                    <Play className="w-4 h-4" />
                                )}
                                VDG 분석 시작
                            </button>
                        )}

                        {/* View Original */}
                        <a
                            href={item.video_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center justify-center gap-2 px-4 py-3 bg-white/5 hover:bg-white/10 text-white/70 rounded-xl transition-colors"
                        >
                            <ExternalLink className="w-4 h-4" />
                            원본 보기
                        </a>
                    </div>

                    {/* Promoted Node Link */}
                    {item.promoted_to_node_id && stage === 'completed' && (
                        <a
                            href={`/remix/${item.promoted_to_node_id}`}
                            className="mt-4 block text-center text-sm text-emerald-400 hover:text-emerald-300 py-2"
                        >
                            🎬 리믹스 스튜디오에서 열기 →
                        </a>
                    )}
                </div>
            </div>
        </div>
    );
}

export default OutlierDetailModal;
