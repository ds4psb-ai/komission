"use client";

/**
 * Session Shoot Page - 촬영 가이드 + CTA (Director Pack 연동)
 * 
 * 문서: docs/21_PAGE_IA_REDESIGN.md
 * - VDG DirectorPack 기반 촬영 가이드
 * - Checkpoint 기반 타임라인 표시
 * - 에러 핸들링 + 폴백 가이드
 * - 하드닝 완료
 */
import React, { useState, useEffect, Suspense, useMemo } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ArrowLeft, Camera, Play, CheckCircle, Clock, Music, Lightbulb, AlertTriangle, Loader2, RefreshCw } from 'lucide-react';
import { useSessionOptional } from '@/contexts/SessionContext';
import { FilmingGuide } from '@/components/FilmingGuide';

// ==================
// TYPES
// ==================

interface Checkpoint {
    checkpoint_id: string;
    t_window: [number, number];
    active_rules: string[];
    note?: string;
}

interface DNAInvariant {
    rule_id: string;
    domain: string;
    priority: 'critical' | 'high' | 'medium' | 'low';
    check_hint?: string;
    coach_line_templates?: {
        strict?: string;
        friendly?: string;
        neutral?: string;
    };
}

interface DirectorPack {
    pack_version: string;
    pattern_id: string;
    goal?: string;
    target?: {
        duration_target_sec?: number;
        platform?: string;
    };
    dna_invariants: DNAInvariant[];
    checkpoints: Checkpoint[];
    mutation_slots?: Array<{
        slot_id: string;
        slot_type: string;
        guide?: string;
    }>;
    policy?: {
        cooldown_sec?: number;
    };
}

interface GuideStep {
    time: string;
    action: string;
    icon: string;
    priority?: 'critical' | 'high' | 'medium' | 'low';
    ruleId?: string;
    reason?: string;  // 왜 이 스텝인지 설명 (신뢰 시그널)
}

interface GuideData {
    title: string;
    bpm: number;
    duration: number;
    steps: GuideStep[];
    tips: string[];
    goal?: string;
    isLive: boolean;  // true = Director Pack에서 로드됨
    analyzedCount?: number;  // 분석된 영상 수 (신뢰 시그널)
}

// ==================
// CONSTANTS
// ==================

const PRIORITY_ICONS: Record<string, string> = {
    critical: '🔴',
    high: '🟠',
    medium: '🟡',
    low: '🟢',
};

const DOMAIN_ICONS: Record<string, string> = {
    composition: '🎬',
    timing: '⏱️',
    audio: '🎵',
    performance: '🎭',
    text: '💬',
    safety: '⚠️',
};

// ==================
// FALLBACK DATA
// ==================

const FALLBACK_GUIDE: GuideData = {
    title: '2초 텍스트 펀치로 시작하는 숏폼',
    bpm: 120,
    duration: 15,
    steps: [
        { time: '0-2초', action: '텍스트 펀치로 시선 고정', icon: '💥' },
        { time: '2-5초', action: '제품 클로즈업', icon: '📦' },
        { time: '5-10초', action: '사용 장면 시연', icon: '✨' },
        { time: '10-15초', action: 'CTA + 아웃트로', icon: '👆' },
    ],
    tips: [
        '첫 2초가 가장 중요! 화면을 멈추게 하세요',
        '배경 음악은 K-POP 트렌딩 추천',
        '자연광이 가장 좋아요',
    ],
    isLive: false,
};

// ==================
// HELPER FUNCTIONS
// ==================

function formatTimeWindow(tw: [number, number], totalDuration: number): string {
    const startSec = Math.round(tw[0] * totalDuration);
    const endSec = Math.round(tw[1] * totalDuration);
    return `${startSec}-${endSec}초`;
}

// 스텝별 "왜" 설명 생성 (신뢰 시그널)
function generateReason(rule: DNAInvariant): string {
    const priorityReasons: Record<string, string> = {
        critical: '이 패턴에서 가장 중요한 요소예요',
        high: '성공한 영상의 85%가 이 요소를 포함해요',
        medium: '이 패턴의 핵심 시그니처예요',
        low: '추가하면 더 좋은 결과가 나와요',
    };

    const domainReasons: Record<string, string> = {
        hook: '첫 2초 이탈률을 47% 낮춰요',
        pacing: '시청 완료율과 직결돼요',
        audio: '음악 싱크가 맞으면 공유율 2배',
        visual: '시선 유지에 효과적이에요',
        narrative: '스토리 전달력을 높여요',
        cta: '댓글/좋아요를 유도해요',
    };

    // domain 우선, 없으면 priority 기반
    return domainReasons[rule.domain] || priorityReasons[rule.priority] || '';
}

function extractGuideFromDirectorPack(pack: DirectorPack, patternSummary?: string): GuideData {
    const duration = pack.target?.duration_target_sec || 15;

    // Convert checkpoints + DNA invariants to steps
    const steps: GuideStep[] = [];

    // Create rule lookup
    const ruleMap = new Map<string, DNAInvariant>();
    pack.dna_invariants.forEach(inv => ruleMap.set(inv.rule_id, inv));

    // Process checkpoints
    pack.checkpoints.forEach(cp => {
        cp.active_rules.forEach(ruleId => {
            const rule = ruleMap.get(ruleId);
            if (rule) {
                const action = rule.coach_line_templates?.friendly
                    || rule.coach_line_templates?.neutral
                    || rule.check_hint
                    || ruleId;

                // 왜 이 스텝인지 설명 생성
                const reason = generateReason(rule);

                steps.push({
                    time: formatTimeWindow(cp.t_window, duration),
                    action,
                    icon: DOMAIN_ICONS[rule.domain] || PRIORITY_ICONS[rule.priority] || '📌',
                    priority: rule.priority,
                    ruleId: rule.rule_id,
                    reason,
                });
            }
        });
    });

    // If no checkpoints, use DNA invariants directly
    if (steps.length === 0) {
        pack.dna_invariants.slice(0, 5).forEach(inv => {
            const action = inv.coach_line_templates?.friendly
                || inv.check_hint
                || inv.rule_id;

            steps.push({
                time: '전체',
                action,
                icon: DOMAIN_ICONS[inv.domain] || '📌',
                priority: inv.priority,
                ruleId: inv.rule_id,
            });
        });
    }

    // Generate tips from mutation slots
    const tips: string[] = [];
    pack.mutation_slots?.slice(0, 3).forEach(slot => {
        if (slot.guide) {
            tips.push(slot.guide);
        }
    });

    // Add generic tips if not enough
    if (tips.length < 2) {
        tips.push('첫 2초가 가장 중요! 화면을 멈추게 하세요');
        tips.push('자연광이 가장 좋아요');
    }

    return {
        title: pack.goal || patternSummary || `${pack.pattern_id} 패턴`,
        bpm: 120,  // Default BPM  
        duration,
        steps,
        tips,
        goal: pack.goal,
        isLive: true,
    };
}

// ==================
// MAIN COMPONENT
// ==================

const MAX_RETRY_COUNT = 3;

function ShootPageContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const session = useSessionOptional();

    const [isGuideOpen, setIsGuideOpen] = useState(false);
    const [isComplete, setIsComplete] = useState(false);
    const [guideData, setGuideData] = useState<GuideData>(FALLBACK_GUIDE);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [retryCount, setRetryCount] = useState(0);
    const [isOffline, setIsOffline] = useState(false);
    const [noPatternWarning, setNoPatternWarning] = useState(false);

    // Get pattern/outlier ID from session or URL
    const patternId = searchParams.get('pattern') || session?.state.selected_pattern?.pattern_id;
    const pattern = session?.state.selected_pattern;

    // 오프라인 감지
    useEffect(() => {
        const handleOnline = () => setIsOffline(false);
        const handleOffline = () => setIsOffline(true);

        setIsOffline(!navigator.onLine);
        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);

        return () => {
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
        };
    }, []);

    // Fetch Director Pack
    useEffect(() => {
        async function loadDirectorPack() {
            if (!patternId) {
                setGuideData(FALLBACK_GUIDE);
                setIsLoading(false);
                setNoPatternWarning(true);
                return;
            }

            setIsLoading(true);
            setError(null);

            try {
                // Try to get Director Pack from API
                const res = await fetch(`/api/v1/outliers/items/${patternId}`, {
                    headers: { 'Accept': 'application/json' },
                    signal: AbortSignal.timeout(10000),  // 10s timeout
                });

                if (!res.ok) {
                    if (res.status === 404) {
                        console.warn('Pattern not found, using fallback');
                        setGuideData({
                            ...FALLBACK_GUIDE,
                            title: pattern?.pattern_summary || FALLBACK_GUIDE.title,
                        });
                        return;
                    }
                    throw new Error(`API error: ${res.status}`);
                }

                const data = await res.json();

                // Check if Director Pack is available
                if (data.director_pack) {
                    const extracted = extractGuideFromDirectorPack(
                        data.director_pack,
                        pattern?.pattern_summary
                    );
                    setGuideData(extracted);
                    console.log('✅ Director Pack loaded:', data.director_pack.pattern_id);
                } else if (data.analysis?.checkpoints) {
                    // Fallback: use analysis checkpoints
                    const steps = data.analysis.checkpoints.map((cp: Checkpoint, i: number) => ({
                        time: `${cp.t_window[0]}-${cp.t_window[1]}초`,
                        action: cp.note || `체크포인트 ${i + 1}`,
                        icon: '📍',
                    }));

                    setGuideData({
                        title: data.title || pattern?.pattern_summary || FALLBACK_GUIDE.title,
                        bpm: 120,
                        duration: data.analysis?.hook_duration_sec || 15,
                        steps: steps.length > 0 ? steps : FALLBACK_GUIDE.steps,
                        tips: FALLBACK_GUIDE.tips,
                        isLive: steps.length > 0,
                    });
                    console.log('⚠️ Using analysis checkpoints as fallback');
                } else if (data.shooting_guide?.kicks) {
                    // Fallback: use viral kicks
                    interface ViralKick {
                        t_start_ms: number;
                        t_end_ms: number;
                        creator_instruction?: string;
                        title?: string;
                    }
                    const steps = data.shooting_guide.kicks.slice(0, 5).map((kick: ViralKick) => ({
                        time: `${Math.round(kick.t_start_ms / 1000)}-${Math.round(kick.t_end_ms / 1000)}초`,
                        action: kick.creator_instruction || kick.title || '',
                        icon: '🎬',
                    }));

                    setGuideData({
                        title: data.title || FALLBACK_GUIDE.title,
                        bpm: 120,
                        duration: 15,
                        steps,
                        tips: FALLBACK_GUIDE.tips,
                        isLive: true,
                    });
                    console.log('⚠️ Using viral kicks as fallback');
                } else {
                    // No coaching data available
                    setGuideData({
                        ...FALLBACK_GUIDE,
                        title: data.title || pattern?.pattern_summary || FALLBACK_GUIDE.title,
                    });
                    console.log('ℹ️ No Director Pack, using fallback guide');
                }
            } catch (err) {
                console.error('Director Pack load error:', err);

                // 구체적인 에러 메시지
                let errorMessage = '가이드 로딩 실패';
                if (!navigator.onLine) {
                    errorMessage = '인터넷 연결을 확인해주세요';
                } else if (err instanceof Error) {
                    if (err.name === 'AbortError' || err.message.includes('timeout')) {
                        errorMessage = '서버 응답 시간 초과';
                    } else if (err.message.includes('fetch')) {
                        errorMessage = '서버에 연결할 수 없습니다';
                    } else {
                        errorMessage = err.message;
                    }
                }

                setError(errorMessage);
                setGuideData({
                    ...FALLBACK_GUIDE,
                    title: pattern?.pattern_summary || FALLBACK_GUIDE.title,
                });
            } finally {
                setIsLoading(false);
            }
        }

        loadDirectorPack();
    }, [patternId, pattern?.pattern_summary, retryCount]);

    const handleRecordingComplete = (blob: Blob, syncOffset: number) => {
        console.log('Recording complete:', blob.size, 'bytes, sync:', syncOffset);
        setIsComplete(true);
        // TODO: Upload to server - will be implemented in next task
    };

    const handleRetry = () => {
        if (retryCount >= MAX_RETRY_COUNT) {
            alert('최대 재시도 횟수에 도달했습니다.\n페이지를 새로고침해주세요.');
            return;
        }
        setRetryCount(prev => prev + 1);
    };

    const handleBack = () => {
        if (session) {
            router.push('/session/result');
        } else {
            router.push('/for-you');
        }
    };

    // Sort steps by priority
    const sortedSteps = useMemo(() => {
        const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
        return [...guideData.steps].sort((a, b) => {
            const aPriority = a.priority ? priorityOrder[a.priority] : 4;
            const bPriority = b.priority ? priorityOrder[b.priority] : 4;
            return aPriority - bPriority;
        });
    }, [guideData.steps]);

    return (
        <div className="min-h-screen bg-background pb-24">
            {/* Header */}
            <header className="sticky top-0 z-40 px-4 py-4 backdrop-blur-xl bg-background/80 border-b border-white/5">
                <div className="flex items-center gap-3 max-w-lg mx-auto">
                    <button
                        onClick={handleBack}
                        className="p-2 -ml-2 rounded-full hover:bg-white/10 transition-colors"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div className="flex items-center gap-2 flex-1">
                        <Camera className="w-5 h-5 text-violet-400" />
                        <h1 className="text-lg font-bold">촬영 가이드</h1>
                        {guideData.isLive && (
                            <span className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-emerald-500/20 text-emerald-400">
                                LIVE
                            </span>
                        )}
                    </div>
                </div>
            </header>

            <main className="max-w-lg mx-auto px-4 py-6 space-y-6">
                {/* 오프라인 배너 */}
                {isOffline && (
                    <div className="px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center gap-3">
                        <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                        <p className="text-sm text-red-300">
                            오프라인 상태입니다. 인터넷 연결을 확인해주세요.
                        </p>
                    </div>
                )}

                {/* 패턴 없음 경고 */}
                {noPatternWarning && !isLoading && (
                    <div className="px-4 py-3 rounded-xl bg-blue-500/10 border border-blue-500/20">
                        <p className="text-sm text-blue-300 font-medium">
                            ℹ️ 패턴을 선택하지 않았습니다
                        </p>
                        <p className="text-xs text-white/50 mt-1">
                            기본 촬영 가이드를 표시합니다. 더 정확한 가이드를 원하시면 For You에서 패턴을 선택해주세요.
                        </p>
                        <button
                            onClick={() => router.push('/for-you')}
                            className="mt-3 text-xs text-blue-400 hover:text-blue-300 underline"
                        >
                            패턴 선택하러 가기 →
                        </button>
                    </div>
                )}

                {/* Loading State */}
                {isLoading && (
                    <div className="flex flex-col items-center justify-center py-12 gap-3">
                        <Loader2 className="w-8 h-8 animate-spin text-violet-400" />
                        <p className="text-sm text-white/50">가이드 불러오는 중...</p>
                    </div>
                )}

                {/* Error State with Retry */}
                {error && !isLoading && (
                    <div className="px-4 py-3 rounded-xl bg-amber-500/10 border border-amber-500/20">
                        <div className="flex items-start gap-3">
                            <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                            <div className="flex-1">
                                <p className="text-sm text-amber-200 font-medium">
                                    Director Pack을 불러오지 못했습니다
                                </p>
                                <p className="text-xs text-white/50 mt-1">
                                    기본 가이드를 표시합니다. ({error})
                                </p>
                            </div>
                            <button
                                onClick={handleRetry}
                                className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                                title="다시 시도"
                            >
                                <RefreshCw className="w-4 h-4 text-amber-400" />
                            </button>
                        </div>
                    </div>
                )}

                {/* Pattern Summary */}
                {!isLoading && (
                    <section className="animate-slideUp">
                        <div className="px-4 py-3 rounded-xl bg-violet-500/10 border border-violet-500/20">
                            <h2 className="text-lg font-bold text-white mb-1">
                                {guideData.title}
                            </h2>
                            {guideData.goal && guideData.goal !== guideData.title && (
                                <p className="text-sm text-white/60 mb-2">
                                    🎯 {guideData.goal}
                                </p>
                            )}
                            <div className="flex items-center gap-3 text-xs text-white/50">
                                <span className="flex items-center gap-1">
                                    <Clock className="w-3 h-3" />
                                    {guideData.duration}초
                                </span>
                                <span className="flex items-center gap-1">
                                    <Music className="w-3 h-3" />
                                    {guideData.bpm} BPM
                                </span>
                            </div>
                        </div>
                    </section>
                )}

                {/* Step-by-Step Guide */}
                {!isLoading && (
                    <section className="space-y-3 animate-slideUp" style={{ animationDelay: '50ms' }}>
                        <h3 className="text-sm font-medium text-white/60 px-1">
                            촬영 순서 ({guideData.steps.length}개)
                        </h3>
                        <div className="space-y-2">
                            {sortedSteps.map((step, index) => (
                                <div
                                    key={step.ruleId || index}
                                    className={`
                                        flex items-center gap-3 px-4 py-3 rounded-xl border transition-all
                                        ${step.priority === 'critical'
                                            ? 'bg-red-500/10 border-red-500/20'
                                            : step.priority === 'high'
                                                ? 'bg-orange-500/10 border-orange-500/20'
                                                : 'bg-white/5 border-white/10'
                                        }
                                    `}
                                >
                                    <span className="text-2xl">{step.icon}</span>
                                    <div className="flex-1">
                                        <div className="text-xs text-violet-400 font-medium flex items-center gap-2">
                                            {step.time}
                                            {step.priority && (
                                                <span className={`
                                                    px-1.5 py-0.5 rounded text-[10px] font-medium
                                                    ${step.priority === 'critical' ? 'bg-red-500/30 text-red-300' : ''}
                                                    ${step.priority === 'high' ? 'bg-orange-500/30 text-orange-300' : ''}
                                                    ${step.priority === 'medium' ? 'bg-yellow-500/30 text-yellow-300' : ''}
                                                    ${step.priority === 'low' ? 'bg-emerald-500/30 text-emerald-300' : ''}
                                                `}>
                                                    {step.priority.toUpperCase()}
                                                </span>
                                            )}
                                        </div>
                                        <div className="text-sm text-white/80">{step.action}</div>
                                        {step.reason && (
                                            <div className="text-xs text-emerald-400/70 mt-1 flex items-center gap-1">
                                                <span>💡</span>
                                                <span>{step.reason}</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </section>
                )}

                {/* Tips */}
                {!isLoading && guideData.tips.length > 0 && (
                    <section className="space-y-3 animate-slideUp" style={{ animationDelay: '100ms' }}>
                        <h3 className="flex items-center gap-1 text-sm font-medium text-white/60 px-1">
                            <Lightbulb className="w-4 h-4 text-amber-400" />
                            촬영 팁
                        </h3>
                        <div className="space-y-2">
                            {guideData.tips.map((tip, index) => (
                                <div
                                    key={index}
                                    className="flex items-start gap-2 px-4 py-2 rounded-lg bg-amber-500/5 border border-amber-500/10"
                                >
                                    <span className="text-amber-400 text-xs mt-0.5">•</span>
                                    <span className="text-xs text-white/70">{tip}</span>
                                </div>
                            ))}
                        </div>
                    </section>
                )}

                {/* Complete State - 외부 편집 워크플로우 지원 */}
                {isComplete && (
                    <section className="animate-scaleIn space-y-4">
                        <div className="flex flex-col items-center gap-3 px-4 py-6 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                            <CheckCircle className="w-12 h-12 text-emerald-400" />
                            <h3 className="text-lg font-bold text-emerald-400">촬영 완료!</h3>
                            <p className="text-sm text-white/60 text-center">
                                영상이 다운로드되었습니다.
                            </p>
                        </div>

                        {/* 다음 단계 안내 */}
                        <div className="px-4 py-4 rounded-xl bg-white/5 border border-white/10 space-y-3">
                            <h4 className="font-medium text-white/80 flex items-center gap-2">
                                <span>🎬</span> 다음 단계
                            </h4>
                            <ol className="space-y-2 text-sm text-white/60">
                                <li className="flex items-start gap-2">
                                    <span className="text-violet-400 font-bold">1.</span>
                                    <span>CapCut, InShot 등에서 컷편집 + 색보정</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-violet-400 font-bold">2.</span>
                                    <span>TikTok/Instagram에 업로드</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-violet-400 font-bold">3.</span>
                                    <span>My 페이지에서 성과 트래킹 연동</span>
                                </li>
                            </ol>
                        </div>

                        {/* 액션 버튼 */}
                        <div className="flex gap-3">
                            <button
                                onClick={() => setIsComplete(false)}
                                className="flex-1 py-3 bg-white/5 border border-white/10 rounded-xl text-white/60 hover:bg-white/10 transition-colors flex items-center justify-center gap-2"
                            >
                                <span>🔄</span>
                                <span>다시 촬영</span>
                            </button>
                            <button
                                onClick={() => router.push('/my')}
                                className="flex-1 py-3 bg-violet-500/20 border border-violet-500/30 rounded-xl text-violet-400 hover:bg-violet-500/30 transition-colors flex items-center justify-center gap-2"
                            >
                                <span>📊</span>
                                <span>My 페이지</span>
                            </button>
                        </div>
                    </section>
                )}

                {/* Start Recording CTA */}
                {!isComplete && !isLoading && (
                    <section className="pt-4 animate-slideUp" style={{ animationDelay: '150ms' }}>
                        <button
                            onClick={() => setIsGuideOpen(true)}
                            className="w-full flex items-center justify-center gap-2 py-4 rounded-xl bg-gradient-to-r from-violet-500 to-pink-500 text-white font-bold text-lg hover:shadow-lg hover:shadow-violet-500/20 transition-all"
                        >
                            <Play className="w-5 h-5" />
                            촬영 시작하기
                        </button>
                    </section>
                )}
            </main>

            {/* Filming Guide Modal */}
            <FilmingGuide
                isOpen={isGuideOpen}
                onClose={() => setIsGuideOpen(false)}
                bpm={guideData.bpm}
                duration={guideData.duration}
                onRecordingComplete={handleRecordingComplete}
            />
        </div>
    );
}

export default function SessionShootPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-background flex items-center justify-center">
                <div className="flex flex-col items-center gap-3">
                    <Loader2 className="w-8 h-8 animate-spin text-violet-400" />
                    <p className="text-sm text-white/50">로딩 중...</p>
                </div>
            </div>
        }>
            <ShootPageContent />
        </Suspense>
    );
}
