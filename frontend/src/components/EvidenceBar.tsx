"use client";

/**
 * EvidenceBar - 댓글 5개 + 재등장 근거 + 리스크 표시
 * 
 * 문서: docs/20_UI_COMPONENT_SPEC.md
 * - Best Comments 5개로 "왜 이 패턴인가"를 증명
 * - Recurrence 근거 표시
 * - Risk 태그 표시
 * - Confidence 레벨 표시
 */
import React from 'react';
import {
    MessageCircle, ThumbsUp, RefreshCw, AlertTriangle,
    CheckCircle, AlertCircle, Eye
} from 'lucide-react';

// Comment tag types
export type CommentTag = 'hook' | 'payoff' | 'product_curiosity' | 'confusion' | 'controversy';

// Types
export interface BestComment {
    text: string;
    likes: number;
    lang: 'ko' | 'en' | 'other';
    tag?: CommentTag;  // Optional - not all comments have tags
}

export interface RecurrenceEvidence {
    ancestor_cluster_id: string;
    recurrence_score: number;
    historical_lift: string;
    origin_year: number;
}

export interface RiskTag {
    type: 'confusion' | 'controversy' | 'weak_evidence';
    label: string;
}

export interface EvidenceBarProps {
    // Best Comments 5
    best_comments: BestComment[];

    // Recurrence Evidence (optional)
    recurrence?: RecurrenceEvidence;

    // Risk Tags
    risk_tags?: RiskTag[];

    // Confidence
    evidence_count: number;
    confidence_label: 'strong' | 'moderate' | 'weak';

    // Collapsible state
    collapsed?: boolean;
    onToggle?: () => void;
}

// Tag styling config
const TAG_CONFIG: Record<CommentTag, { label: string; color: string; icon: typeof MessageCircle }> = {
    hook: { label: '훅', color: 'text-emerald-400 bg-emerald-500/20', icon: MessageCircle },
    payoff: { label: '보상', color: 'text-cyan-400 bg-cyan-500/20', icon: MessageCircle },
    product_curiosity: { label: '제품', color: 'text-amber-400 bg-amber-500/20', icon: MessageCircle },
    confusion: { label: '혼란', color: 'text-orange-400 bg-orange-500/20', icon: AlertCircle },
    controversy: { label: '논란', color: 'text-red-400 bg-red-500/20', icon: AlertTriangle },
};

const CONFIDENCE_CONFIG = {
    strong: { label: '높음', color: 'text-emerald-400', icon: CheckCircle },
    moderate: { label: '보통', color: 'text-yellow-400', icon: Eye },
    weak: { label: '낮음', color: 'text-orange-400', icon: AlertCircle },
};

function formatLikes(likes: number): string {
    if (likes >= 1000) return (likes / 1000).toFixed(1) + 'K';
    return likes.toString();
}

export function EvidenceBar({
    best_comments,
    recurrence,
    risk_tags = [],
    evidence_count,
    confidence_label,
}: EvidenceBarProps) {
    const confidenceConfig = CONFIDENCE_CONFIG[confidence_label];
    const ConfidenceIcon = confidenceConfig.icon;

    return (
        <div className="space-y-3">
            {/* Best Comments Section */}
            <div className="space-y-2">
                <div className="flex items-center gap-2 text-xs text-white/60">
                    <MessageCircle className="w-3.5 h-3.5" />
                    <span className="font-medium">베스트 댓글</span>
                </div>

                <div className="space-y-1.5">
                    {best_comments.length > 0 ? (
                        best_comments.slice(0, 5).map((comment, index) => {
                            const tagConfig = comment.tag ? TAG_CONFIG[comment.tag] : null;
                            const isNegative = comment.tag === 'confusion' || comment.tag === 'controversy';

                            return (
                                <div
                                    key={index}
                                    className={`
                                        flex items-start gap-2 px-3 py-2 rounded-lg 
                                        ${isNegative ? 'bg-orange-500/5 border border-orange-500/10' : 'bg-white/5'}
                                    `}
                                >
                                    {tagConfig && (
                                        <span className={`shrink-0 px-1.5 py-0.5 rounded text-[10px] font-bold ${tagConfig.color}`}>
                                            {tagConfig.label}
                                        </span>
                                    )}
                                    <p className="flex-1 text-xs text-white/80 leading-relaxed">
                                        &ldquo;{comment.text}&rdquo;
                                    </p>
                                    <span className="shrink-0 flex items-center gap-0.5 text-[10px] text-white/40">
                                        <ThumbsUp className="w-2.5 h-2.5" />
                                        {formatLikes(comment.likes)}
                                    </span>
                                </div>
                            );
                        })
                    ) : (
                        <div className="px-3 py-2 rounded-lg bg-white/5 text-xs text-white/40">
                            댓글 증거 수집 중...
                        </div>
                    )}
                </div>
            </div>

            {/* Recurrence Evidence */}
            {recurrence && (
                <div className="px-3 py-2.5 rounded-lg bg-violet-500/10 border border-violet-500/20">
                    <div className="flex items-center gap-2 text-xs">
                        <RefreshCw className="w-3.5 h-3.5 text-violet-400" />
                        <span className="font-medium text-violet-300">재등장</span>
                    </div>
                    <div className="mt-1 text-xs text-white/70">
                        {recurrence.origin_year} 패턴과 <span className="text-violet-400 font-bold">{Math.round(recurrence.recurrence_score * 100)}%</span> 유사
                    </div>
                    <div className="mt-1 text-[10px] text-white/50">
                        과거 성과: <span className="text-emerald-400">{recurrence.historical_lift}</span>
                    </div>
                </div>
            )}

            {/* Risk Tags */}
            {risk_tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                    {risk_tags.map((risk, index) => (
                        <div
                            key={index}
                            className="flex items-center gap-1 px-2 py-1 rounded-full bg-orange-500/10 border border-orange-500/20"
                        >
                            <AlertTriangle className="w-3 h-3 text-orange-400" />
                            <span className="text-[10px] text-orange-300">{risk.label}</span>
                        </div>
                    ))}
                </div>
            )}

            {/* Confidence Footer */}
            <div className="flex items-center justify-between pt-2 border-t border-white/10">
                <div className="flex items-center gap-1.5">
                    <ConfidenceIcon className={`w-3.5 h-3.5 ${confidenceConfig.color}`} />
                    <span className={`text-xs font-medium ${confidenceConfig.color}`}>
                        증거 신뢰도: {confidenceConfig.label}
                    </span>
                </div>
                <span className="text-[10px] text-white/40">
                    {evidence_count}개 증거
                </span>
            </div>
        </div>
    );
}

export default EvidenceBar;
