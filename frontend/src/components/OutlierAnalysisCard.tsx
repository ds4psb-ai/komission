"use client";

import React, { useState } from "react";
import { api, OutlierItem } from "@/lib/api";
import { VDGCard } from "@/components/canvas/VDGCard";

interface AnalysisStatusBadgeProps {
    status: OutlierItem["analysis_status"];
    size?: "sm" | "md";
}

/**
 * Analysis Status Badge
 * Shows the current VDG analysis status with appropriate styling
 */
export function AnalysisStatusBadge({ status, size = "sm" }: AnalysisStatusBadgeProps) {
    const styles = {
        pending: "bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
        approved: "bg-blue-500/20 text-blue-300 border-blue-500/30",
        analyzing: "bg-purple-500/20 text-purple-300 border-purple-500/30 animate-pulse",
        completed: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
        skipped: "bg-zinc-500/20 text-zinc-400 border-zinc-500/30",
    };

    const labels = {
        pending: "⏳ 대기",
        approved: "✅ 승인됨",
        analyzing: "🔄 분석중",
        completed: "🎉 완료",
        skipped: "⏭️ 스킵",
    };

    const sizeClass = size === "sm" ? "text-[10px] px-1.5 py-0.5" : "text-xs px-2 py-1";

    return (
        <span className={`${sizeClass} rounded border font-medium ${styles[status]}`}>
            {labels[status]}
        </span>
    );
}

interface VDGApprovalButtonProps {
    item: OutlierItem;
    onApproved?: (item: OutlierItem) => void;
}

/**
 * VDG Approval Button
 * Admin-only button to approve VDG analysis for a promoted outlier
 */
export function VDGApprovalButton({ item, onApproved }: VDGApprovalButtonProps) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Only show for promoted items with pending analysis
    if (item.status !== "promoted" || item.analysis_status !== "pending") {
        return null;
    }

    const handleApprove = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await api.approveVDGAnalysis(item.id);
            if (response.approved) {
                // Update local state
                const updatedItem = {
                    ...item,
                    analysis_status: "approved" as OutlierItem["analysis_status"],
                };
                onApproved?.(updatedItem);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "승인 실패");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col gap-1">
            <button
                onClick={handleApprove}
                disabled={loading}
                className={`
                    px-3 py-1.5 rounded-lg text-xs font-bold
                    bg-gradient-to-r from-violet-600 to-purple-600
                    hover:from-violet-500 hover:to-purple-500
                    disabled:opacity-50 disabled:cursor-not-allowed
                    text-white shadow-lg transition-all duration-200
                    hover:scale-105 active:scale-95
                `}
            >
                {loading ? (
                    <span className="flex items-center gap-1">
                        <span className="animate-spin">⏳</span> 처리중...
                    </span>
                ) : (
                    <span className="flex items-center gap-1">
                        🚀 VDG 분석 승인
                    </span>
                )}
            </button>
            {error && (
                <span className="text-[10px] text-red-400">{error}</span>
            )}
        </div>
    );
}

interface OutlierAnalysisCardProps {
    item: OutlierItem;
    onUpdate?: (item: OutlierItem) => void;
}

/**
 * Outlier Analysis Card
 * Shows outlier with VDG analysis status and approval controls
 */
export function OutlierAnalysisCard({ item, onUpdate }: OutlierAnalysisCardProps) {
    return (
        <div className="bg-zinc-900/50 rounded-xl border border-white/10 p-4 hover:border-white/20 transition-all">
            {/* Header */}
            <div className="flex items-start justify-between gap-3 mb-3">
                <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-bold text-white truncate">
                        {item.title || "Untitled"}
                    </h3>
                    <div className="flex items-center gap-2 mt-1">
                        <span className="text-[10px] text-white/50 uppercase">
                            {item.platform}
                        </span>
                        <span className="text-[10px] text-white/30">•</span>
                        <span className="text-[10px] text-white/50">
                            {item.category}
                        </span>
                    </div>
                </div>
                <AnalysisStatusBadge status={item.analysis_status} />
            </div>

            {/* Metrics */}
            <div className="flex items-center gap-4 text-xs text-white/60 mb-3">
                <span>👁️ {(item.view_count / 1000).toFixed(0)}K</span>
                <span>❤️ {(item.like_count / 1000).toFixed(1)}K</span>
                {item.outlier_tier && (
                    <span className={`
                        px-1.5 py-0.5 rounded text-[10px] font-bold
                        ${item.outlier_tier === 'S' ? 'bg-amber-500/20 text-amber-300' :
                            item.outlier_tier === 'A' ? 'bg-purple-500/20 text-purple-300' :
                                'bg-zinc-500/20 text-zinc-400'}
                    `}>
                        {item.outlier_tier}
                    </span>
                )}
            </div>

            {/* Best Comments Count */}
            {item.best_comments_count > 0 && (
                <div className="text-[10px] text-cyan-400 mb-3">
                    💬 베스트 댓글 {item.best_comments_count}개 수집됨
                </div>
            )}

            {/* Action */}
            <div className="flex items-center justify-between">
                <a
                    href={item.video_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[10px] text-white/40 hover:text-white/70 transition-colors"
                >
                    🔗 원본 보기
                </a>
                <VDGApprovalButton item={item} onApproved={onUpdate} />
            </div>

            {/* Promoted Node Link */}
            {item.promoted_to_node_id && item.analysis_status === "completed" && (
                <a
                    href={`/remix/${item.promoted_to_node_id}`}
                    className="mt-3 block text-center text-xs text-emerald-400 hover:text-emerald-300"
                >
                    🎬 분석 결과 보기 →
                </a>
            )}

            {/* VDG Analysis Card (when data available) */}
            {item.vdg_analysis && (
                <div className="mt-4">
                    <VDGCard vdg={item.vdg_analysis} className="border-0" />
                </div>
            )}
        </div>
    );
}

export default OutlierAnalysisCard;
