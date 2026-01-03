"use client";

import { useTranslations } from 'next-intl';

/**
 * Session Result Page - 추천 결과 + Evidence
 * 
 * 문서: docs/21_PAGE_IA_REDESIGN.md
 * - PatternAnswerCard + EvidenceBar 통합
 * - 세션 컨텍스트 기반 추천 표시
 * - MCP Tool 연동: Source Pack 생성
 */
import React, { useState, useEffect, useRef, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useSession } from '@/contexts/SessionContext';
import { useConsent } from '@/contexts/ConsentContext';
import { ArrowLeft, Sparkles, FileText, Loader2, Download, CheckCircle2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import PatternAnswerCard from '@/components/PatternAnswerCard';
import EvidenceBar, { BestComment, RiskTag } from '@/components/EvidenceBar';
import FeedbackWidget, { FeedbackData } from '@/components/FeedbackWidget';
import { mcpClient, SourcePackResult } from '@/lib/mcp-client';

// Mock data (fallback)
const MOCK_COMMENTS: BestComment[] = [
    { text: '이거 첫 2초 보고 멈췄다', likes: 1200, lang: 'ko', tag: 'hook' },
    { text: '끝까지 보니까 이해됨', likes: 987, lang: 'ko', tag: 'payoff' },
];


function SessionResultContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { state, setSelectedPattern, markEvidenceViewed, markFeedbackSubmitted, markShootStarted } = useSession();
    const { requestConsent, isPending } = useConsent();

    // i18n
    const t = useTranslations('pages.session.result');
    const tCategories = useTranslations('categories');
    const tPlatforms = useTranslations('platforms');

    const [isEvidenceExpanded, setIsEvidenceExpanded] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [fetchError, setFetchError] = useState<string | null>(null);
    const isMountedRef = useRef(true);


    // Pattern ID from URL
    const patternId = searchParams.get('pattern');

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    useEffect(() => {
        const loadPattern = async () => {
            // 1. If we have a pattern in context and no ID in URL (or same ID), use context
            if (state.selected_pattern && (!patternId || state.selected_pattern.pattern_id === patternId)) {
                if (isMountedRef.current) {
                    setIsLoading(false);
                }
                return;
            }

            // 2. If we have an ID in URL, fetch it
            if (patternId) {
                if (isMountedRef.current) {
                    setIsLoading(true);
                }
                try {
                    const res = await fetch(`/api/v1/for-you/${patternId}`);
                    if (!res.ok) throw new Error(t('patternNotFound'));

                    const data = await res.json();
                    if (!isMountedRef.current) return;

                    // Map API response to SessionPattern
                    const mappedPattern = {
                        pattern_id: data.id,
                        cluster_id: data.cluster_id || data.category,
                        pattern_summary: data.title || `${tPlatforms(data.platform)} ${tCategories(data.category)} Pattern`,
                        signature: {
                            hook: data.tier === 'S' ? 'Strong Hook' : 'Normal Hook',
                            timing: data.evidence.growth_rate || 'N/A',
                            audio: data.platform === 'tiktok' ? 'TikTok Trending Sound' : 'Platform Sound',
                        },
                        fit_score: (data.outlier_score ?? 0) / 1000,
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
                    if (!isMountedRef.current) return;
                    setFetchError(t('loadPatternFailed'));
                } finally {
                    if (isMountedRef.current) {
                        setIsLoading(false);
                    }
                }
            } else {
                // 3. No context, no URL -> Redirect or Show Mock
                // For demo purposes, we'll stop loading but show nothing (or handle redirect)
                if (isMountedRef.current) {
                    setIsLoading(false);
                }
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

    const [isGenerating, setIsGenerating] = useState(false);
    const [packResult, setPackResult] = useState<SourcePackResult | null>(null);

    const handleGenerateSourcePack = async () => {
        if (!patternId) return;

        try {
            const consented = await requestConsent('generate_source_pack', {
                details: [
                    'Include selected Outlier data',
                    'Convert to NotebookLM format',
                    `Target: ${patternId.slice(0, 8)}...`
                ]
            });

            if (!consented) return;

            // 오프라인 체크
            if (!navigator.onLine) {
                alert(t('checkInternet'));
                return;
            }

            setIsGenerating(true);
            setPackResult(null);

            // 실제 MCP API 호출 (재시도 로직 포함)
            let lastError: string | undefined;
            for (let attempt = 1; attempt <= 2; attempt++) {
                const result = await mcpClient.generateSourcePack(
                    [patternId],
                    `Pattern_${patternId.slice(0, 8)}`,
                    {
                        includeComments: true,
                        includeVdg: true,
                        outputFormat: 'json',
                    }
                );

                if (result.success && result.data) {
                    setPackResult(result.data);
                    console.log('✅ 소스팩 생성 완료:', result.data);
                    return;
                }

                lastError = result.error;
                console.warn(`소스팩 생성 시도 ${attempt} 실패:`, result.error);

                if (attempt < 2) {
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
            }

            // 모든 시도 실패
            let userMessage = t('generateSourcePack') + ' failed';
            if (lastError?.includes('network') || lastError?.includes('fetch')) {
                userMessage = t('mcpServerError');
            } else if (lastError?.includes('timeout')) {
                userMessage = t('serverTimeout');
            } else if (lastError) {
                userMessage = `Failed: ${lastError}`;
            }
            alert(userMessage);
        } catch (err) {
            console.error('소스팩 생성 실패:', err);

            let message = t('generateSourcePack') + ' error';
            if (err instanceof Error) {
                if (err.message.includes('network') || err.message.includes('Failed to fetch')) {
                    message = t('mcpServerError');
                }
            }
            alert(message);
        } finally {
            setIsGenerating(false);
        }
    };

    const handleDownloadPack = () => {
        if (!packResult) return;

        const json = JSON.stringify(packResult, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${packResult.name || 'source_pack'}.json`;
        a.click();
        URL.revokeObjectURL(url);
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
                        <h1 className="text-lg font-bold">{t('title')}</h1>
                    </div>
                </div>
            </header>

            <main className="max-w-lg mx-auto px-4 py-6 space-y-6">
                {/* Context Summary */}
                {state.input_context && (
                    <div className="flex items-center gap-2 text-xs text-white/40 animate-fadeIn">
                        <span className="px-2 py-1 rounded-full bg-white/5">
                            {state.input_context.platform === 'tiktok' ? '🎵' : state.input_context.platform === 'youtube' ? '▶️' : '📷'}
                            {' '}{tPlatforms(state.input_context.platform)}
                        </span>
                        <span className="px-2 py-1 rounded-full bg-white/5">
                            {tCategories(state.input_context.category)}
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
                                best_comments={'evidence' in pattern && (pattern as { evidence?: { best_comments?: BestComment[] } }).evidence?.best_comments || MOCK_COMMENTS}
                                recurrence={pattern.recurrence ? {
                                    ancestor_cluster_id: pattern.recurrence.ancestor_cluster_id,
                                    recurrence_score: pattern.recurrence.recurrence_score,
                                    historical_lift: '+127% 평균', // TODO: Map from real data
                                    origin_year: pattern.recurrence.origin_year || 2024,
                                } : undefined}
                                risk_tags={[]}
                                evidence_count={pattern.evidence_strength}
                                confidence_label={pattern.tier === 'S' ? 'strong' : 'moderate'}
                            />

                            {/* MCP Action: Generate Source Pack */}
                            <div className="mt-6 pt-4 border-t border-white/5">
                                {!packResult ? (
                                    <>
                                        <button
                                            onClick={handleGenerateSourcePack}
                                            disabled={isPending || isGenerating}
                                            className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-violet-500/10 hover:bg-violet-500/20 text-violet-300 transition-colors border border-violet-500/20 disabled:opacity-50"
                                        >
                                            {isGenerating ? (
                                                <>
                                                    <Loader2 className="w-4 h-4 animate-spin" />
                                                    <span className="text-sm font-medium">{t('generating')}</span>
                                                </>
                                            ) : (
                                                <>
                                                    <FileText className="w-4 h-4" />
                                                    <span className="text-sm font-medium">
                                                        {t('generateSourcePack')}
                                                    </span>
                                                </>
                                            )}
                                        </button>
                                        <p className="text-[10px] text-center text-white/30 mt-2">
                                            {t('sourcePackDesc')}
                                        </p>
                                    </>
                                ) : (
                                    <div className="space-y-3">
                                        {/* 성공 메시지 */}
                                        <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                                            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                                            <span className="text-sm text-emerald-300">
                                                {t('sourcePackComplete')} ({packResult.outlier_count} sources)
                                            </span>
                                        </div>

                                        {/* 다운로드 버튼 */}
                                        <button
                                            onClick={handleDownloadPack}
                                            className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-violet-500 hover:bg-violet-400 text-white transition-colors"
                                        >
                                            <Download className="w-4 h-4" />
                                            <span className="text-sm font-medium">
                                                {t('downloadJson')}
                                            </span>
                                        </button>
                                        <p className="text-[10px] text-center text-white/30">
                                            {t('notebookLmTip')}
                                        </p>

                                        {/* 다시 생성 */}
                                        <button
                                            onClick={() => setPackResult(null)}
                                            className="w-full text-xs text-white/40 hover:text-white/60 transition-colors"
                                        >
                                            {t('regenerate')}
                                        </button>
                                    </div>
                                )}
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

// Wrap with Suspense for useSearchParams
export default function SessionResultPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-violet-400" />
            </div>
        }>
            <SessionResultContent />
        </Suspense>
    );
}
