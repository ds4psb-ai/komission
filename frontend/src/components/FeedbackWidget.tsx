"use client";

/**
 * FeedbackWidget - 사용자 피드백 수집
 * 
 * 문서: docs/20_UI_COMPONENT_SPEC.md
 * - 👍👎 + 이유 선택으로 L2 리랭커 품질 개선
 * - 간단한 인터랙션으로 피드백 수집
 */
import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, Check } from 'lucide-react';

export type FeedbackReason = 'wrong_category' | 'outdated' | 'too_hard' | 'perfect';

export interface FeedbackData {
    helpful: boolean;
    reason?: FeedbackReason;
}

export interface FeedbackWidgetProps {
    pattern_id: string;
    context: 'answer_card' | 'after_shoot';
    onSubmit: (feedback: FeedbackData) => void;

    // Optional: Already submitted state
    submitted?: boolean;
}

const REASON_OPTIONS: { value: FeedbackReason; label: string }[] = [
    { value: 'wrong_category', label: '카테고리가 안 맞아' },
    { value: 'outdated', label: '이미 지난 트렌드' },
    { value: 'too_hard', label: '너무 어려워' },
    { value: 'perfect', label: '완벽해!' },
];

export function FeedbackWidget({
    pattern_id: _pattern_id,
    context: _context,
    onSubmit,
    submitted = false,
}: FeedbackWidgetProps) {
    const [helpfulChoice, setHelpfulChoice] = useState<boolean | null>(null);
    const [_reason, setReason] = useState<FeedbackReason | null>(null);
    const [isSubmitted, setIsSubmitted] = useState(submitted);
    const [showReasons, setShowReasons] = useState(false);

    const handleChoice = (helpful: boolean) => {
        setHelpfulChoice(helpful);
        if (helpful) {
            // If helpful, submit immediately
            handleSubmit(helpful, null);
        } else {
            // If not helpful, show reason options
            setShowReasons(true);
        }
    };

    const handleReasonSelect = (selectedReason: FeedbackReason) => {
        setReason(selectedReason);
        if (helpfulChoice !== null) {
            handleSubmit(helpfulChoice, selectedReason);
        }
    };

    const handleSubmit = (helpful: boolean, selectedReason: FeedbackReason | null) => {
        const feedback: FeedbackData = {
            helpful,
            ...(selectedReason && { reason: selectedReason }),
        };
        onSubmit(feedback);
        setIsSubmitted(true);
    };

    // Already submitted state
    if (isSubmitted) {
        return (
            <div className="flex items-center justify-center gap-2 py-3 text-xs text-white/40">
                <Check className="w-4 h-4 text-emerald-400" />
                <span>피드백 감사합니다!</span>
            </div>
        );
    }

    return (
        <div className="py-3 space-y-2">
            {!showReasons ? (
                <>
                    <p className="text-xs text-white/60 text-center">
                        이 추천이 도움이 됐나요?
                    </p>
                    <div className="flex items-center justify-center gap-3">
                        <button
                            onClick={() => handleChoice(true)}
                            className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 text-emerald-400 text-sm font-medium transition-colors"
                        >
                            <ThumbsUp className="w-4 h-4" />
                            맞아
                        </button>
                        <button
                            onClick={() => handleChoice(false)}
                            className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-orange-500/10 hover:bg-orange-500/20 border border-orange-500/20 text-orange-400 text-sm font-medium transition-colors"
                        >
                            <ThumbsDown className="w-4 h-4" />
                            아니야
                        </button>
                    </div>
                </>
            ) : (
                <>
                    <div className="flex items-center justify-between">
                        <p className="text-xs text-white/60">
                            어떤 점이 안 맞았나요? <span className="text-white/40">(선택)</span>
                        </p>
                        <button
                            onClick={() => {
                                if (helpfulChoice !== null) {
                                    handleSubmit(helpfulChoice, null);
                                }
                            }}
                            className="text-xs text-white/40 hover:text-white/60"
                        >
                            건너뛰기
                        </button>
                    </div>
                    <div className="flex flex-wrap gap-2 justify-center">
                        {REASON_OPTIONS.map((option) => (
                            <button
                                key={option.value}
                                onClick={() => handleReasonSelect(option.value)}
                                className={`
                                    px-3 py-1.5 rounded-full text-xs font-medium transition-colors
                                    ${option.value === 'perfect'
                                        ? 'bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 text-emerald-400'
                                        : 'bg-white/5 hover:bg-white/10 border border-white/10 text-white/70'
                                    }
                                `}
                            >
                                {option.label}
                            </button>
                        ))}
                    </div>
                </>
            )}
        </div>
    );
}

export default FeedbackWidget;
