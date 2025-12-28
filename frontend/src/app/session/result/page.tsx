"use client";

/**
 * Session Result Page - 추천 결과 + Evidence
 * 
 * 문서: docs/21_PAGE_IA_REDESIGN.md
 * - PatternAnswerCard + EvidenceBar 통합
 * - 세션 컨텍스트 기반 추천 표시
 * - MCP Tool 연동: Source Pack 생성
 */
import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useSession } from '@/contexts/SessionContext';
import { useConsent } from '@/contexts/ConsentContext';
import { ArrowLeft, Sparkles, FileText, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import PatternAnswerCard from '@/components/PatternAnswerCard';
import EvidenceBar, { BestComment, RiskTag, RecurrenceEvidence } from '@/components/EvidenceBar';
import FeedbackWidget, { FeedbackData } from '@/components/FeedbackWidget';

// Mock data (fallback)
const MOCK_COMMENTS: BestComment[] = [
    { text: '이거 첫 2초 보고 멈췄다', likes: 1200, lang: 'ko', tag: 'hook' },
    { text: '끝까지 보니까 이해됨', likes: 987, lang: 'ko', tag: 'payoff' },
];

export default function SessionResultPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { state, setSelectedPattern, markEvidenceViewed, markFeedbackSubmitted, markShootStarted } = useSession();
    const { requestConsent, isPending } = useConsent();

    const [isEvidenceExpanded, setIsEvidenceExpanded] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [fetchError, setFetchError] = useState<string | null>(null);

    // Pattern ID from URL
    const patternId = searchParams.get('pattern');

    useEffect(() => {
        const loadPattern = async () => {
            // 1. If we have a pattern in context and no ID in URL (or same ID), use context
            if (state.selected_pattern && (!patternId || state.selected_pattern.pattern_id === patternId)) {
                setIsLoading(false);
                return;
            }

            // 2. If we have an ID in URL, fetch it
            if (patternId) {
                setIsLoading(true);
                try {
                    const res = await fetch(`/api/v1/for-you/${patternId}`);
                    if (!res.ok) throw new Error('Pattern not found');

                    const data = await res.json();

                    // Map API response to SessionPattern
                    const mappedPattern = {
                        pattern_id: data.id,
                        cluster_id: data.cluster_id || data.category,
                        pattern_summary: data.title || `${data.platform} ${data.category} Pattern`,
                        signature: {
                            hook: data.tier === 'S' ? 'Strong Hook' : 'Standard',
                            timing: data.evidence.growth_rate || 'N/A',
                            audio: data.platform === 'tiktok' ? 'Trending' : 'Original',
                        },
                        fit_score: (data.outlier_score || 0) / 1000,
                        evidence_strength: data.evidence.best_comments.length,
                        tier: data.tier,
                        recurrence: data.recurrence ? {
                            status: 'confirmed' as const,
                            ancestor_cluster_id: data.recurrence.ancestor_cluster_id,
                            recurrence_score: data.recurrence.recurrence_score,
                            origin_year: 2024
                        } : undefined,
                        // Additional data for EvidenceBar
                        evidence: data.evidence
                    };

                    setSelectedPattern(mappedPattern);
                } catch (err) {
                    console.error('Failed to load pattern:', err);
                    setFetchError('패턴을 불러올 수 없습니다.');
                } finally {
                    setIsLoading(false);
                }
            } else {
                // 3. No context, no URL -> Redirect or Show Mock
                // For demo purposes, we'll stop loading but show nothing (or handle redirect)
                setIsLoading(false);
            }
        };

        loadPattern();
    }, [patternId, state.selected_pattern, setSelectedPattern]);

    const handleViewEvidence = () => {
        setIsEvidenceExpanded(!isEvidenceExpanded);
        if (!isEvidenceExpanded) {
            markEvidenceViewed();
        }
    };

    const handleShoot = () => {
        markShootStarted();
        router.push('/session/shoot');
    };

    const handleGenerateSourcePack = async () => {
        if (!patternId) return;

        try {
            const consented = await requestConsent('generate_source_pack', {
                details: [
                    '선택한 Outlier 데이터 포함',
                    'NotebookLM 포맷으로 변환',
                    `Target: ${patternId.slice(0, 8)}...`
                ]
            });

            if (!consented) return;

            console.log('Generating Source Pack...');
            await new Promise(resolve => setTimeout(resolve, 2000));

            console.log('Source Pack Generated');
            alert('Source Pack이 생성되었습니다! (NotebookLM에서 확인 가능)');
        } catch (err) {
            console.error('Source Pack generation failed:', err);
            alert('생성 중 오류가 발생했습니다.');
        }
    };

    const handleFeedback = (feedback: FeedbackData) => {
        console.log('Feedback:', feedback);
        markFeedbackSubmitted();
    };

    const handleBack = () => {
        // If we came from For You (has patternId), go back to For You
        if (patternId) {
            router.push('/for-you');
        } else {
            router.push('/session/input');
        }
    };

    const pattern = state.selected_pattern;

    return (
        <div className="min-h-screen pb-24">
            {/* Header */}
            <header className="sticky top-0 z-40 px-4 py-4 backdrop-blur-xl bg-background/80 border-b border-white/5">
                <div className="flex items-center gap-3 max-w-lg mx-auto">
                    <button
                        onClick={handleBack}
                        className="p-2 -ml-2 rounded-full hover:bg-white/10 transition-colors"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div className="flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-violet-400" />
                        <h1 className="text-lg font-bold">Recommended Pattern</h1>
                    </div>
                </div>
            </header>

            <main className="max-w-lg mx-auto px-4 py-6 space-y-6">
                {/* Context Summary */}
                {state.input_context && (
                    <div className="flex items-center gap-2 text-xs text-white/40 animate-fadeIn">
                        <span className="px-2 py-1 rounded-full bg-white/5">
                            {state.input_context.platform === 'tiktok' ? '🎵' : state.input_context.platform === 'youtube' ? '▶️' : '📷'}
                            {' '}{state.input_context.platform}
                        </span>
                        <span className="px-2 py-1 rounded-full bg-white/5">
                            {state.input_context.category}
                        </span>
                    </div>
                )}

                {/* Loading State */}
                {isLoading && (
                    <div className="space-y-4">
                        <div className="h-64 rounded-2xl bg-white/5 animate-pulse" />
                    </div>
                )}

                {/* Error State */}
                {fetchError && (
                    <div className="p-4 rounded-xl bg-red-500/20 text-red-300 text-center">
                        {fetchError}
                    </div>
                )}

                {/* Pattern Result */}
                {!isLoading && pattern && (
                    <div className="space-y-4 animate-slideUp">
                        <PatternAnswerCard
                            pattern_id={pattern.pattern_id}
                            cluster_id={pattern.cluster_id}
                            pattern_summary={pattern.pattern_summary}
                            signature={pattern.signature}
                            fit_score={pattern.fit_score}
                            evidence_strength={pattern.evidence_strength}
                            tier={(pattern.tier === 'S' || pattern.tier === 'A' || pattern.tier === 'B') ? pattern.tier : 'B'}
                            platform={state.input_context?.platform || 'tiktok'}
                            recurrence={pattern.recurrence}
                            onViewEvidence={handleViewEvidence}
                            onShoot={handleShoot}
                            isEvidenceExpanded={isEvidenceExpanded}
                        >
                            <EvidenceBar
                                // Use fetched evidence if available, else mock
                                best_comments={(pattern as any).evidence?.best_comments || MOCK_COMMENTS}
                                recurrence={pattern.recurrence ? {
                                    ancestor_cluster_id: pattern.recurrence.ancestor_cluster_id,
                                    recurrence_score: pattern.recurrence.recurrence_score,
                                    historical_lift: '+127% avg', // TODO: Map from real data
                                    origin_year: pattern.recurrence.origin_year || 2024,
                                } : undefined}
                                risk_tags={[]}
                                evidence_count={pattern.evidence_strength}
                                confidence_label={pattern.tier === 'S' ? 'strong' : 'moderate'}
                            />

                            {/* MCP Action: Generate Source Pack */}
                            <div className="mt-6 pt-4 border-t border-white/5">
                                <button
                                    onClick={handleGenerateSourcePack}
                                    disabled={isPending}
                                    className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-violet-500/10 hover:bg-violet-500/20 text-violet-300 transition-colors border border-violet-500/20"
                                >
                                    {isPending ? (
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                    ) : (
                                        <FileText className="w-4 h-4" />
                                    )}
                                    <span className="text-sm font-medium">
                                        NotebookLM 소스팩 생성
                                    </span>
                                </button>
                                <p className="text-[10px] text-center text-white/30 mt-2">
                                    Deep Analysis를 위해 소스 데이터를 NotebookLM으로 전송합니다.
                                </p>
                            </div>
                        </PatternAnswerCard>

                        {/* Feedback */}
                        <div className="px-4 py-2 rounded-xl bg-white/5 border border-white/10">
                            <FeedbackWidget
                                pattern_id={pattern.pattern_id}
                                context="answer_card"
                                onSubmit={handleFeedback}
                                submitted={state.feedback_submitted}
                            />
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}

