"use client";

/**
 * Session Shoot Page - 촬영 가이드 + CTA
 * 
 * 문서: docs/21_PAGE_IA_REDESIGN.md
 * - 선택한 패턴의 촬영 가이드 표시
 * - FilmingGuide 컴포넌트 재사용
 * - Variable Slot 입력 (미래 확장)
 */
import React, { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ArrowLeft, Camera, Play, CheckCircle, Clock, Music, Lightbulb } from 'lucide-react';
import { useSessionOptional } from '@/contexts/SessionContext';
import { FilmingGuide } from '@/components/FilmingGuide';

// Wrap component that uses useSearchParams
function ShootPageContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const session = useSessionOptional();

    const [isGuideOpen, setIsGuideOpen] = useState(false);
    const [isComplete, setIsComplete] = useState(false);

    // Get pattern from session or URL
    const _patternId = searchParams.get('pattern') || session?.state.selected_pattern?.pattern_id;
    const pattern = session?.state.selected_pattern;

    // Mock guide data based on pattern
    const guideData = {
        title: pattern?.pattern_summary || '2초 텍스트 펀치로 시작하는 숏폼',
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
    };

    const handleRecordingComplete = (blob: Blob, syncOffset: number) => {
        console.log('Recording complete:', blob.size, 'bytes, sync:', syncOffset);
        setIsComplete(true);
        // TODO: Upload to server
    };

    const handleBack = () => {
        if (session) {
            router.push('/session/result');
        } else {
            router.push('/for-you');
        }
    };

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
                    <div className="flex items-center gap-2">
                        <Camera className="w-5 h-5 text-violet-400" />
                        <h1 className="text-lg font-bold">촬영 가이드</h1>
                    </div>
                </div>
            </header>

            <main className="max-w-lg mx-auto px-4 py-6 space-y-6">
                {/* Pattern Summary */}
                <section className="animate-slideUp">
                    <div className="px-4 py-3 rounded-xl bg-violet-500/10 border border-violet-500/20">
                        <h2 className="text-lg font-bold text-white mb-1">
                            {guideData.title}
                        </h2>
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

                {/* Step-by-Step Guide */}
                <section className="space-y-3 animate-slideUp" style={{ animationDelay: '50ms' }}>
                    <h3 className="text-sm font-medium text-white/60 px-1">촬영 순서</h3>
                    <div className="space-y-2">
                        {guideData.steps.map((step, index) => (
                            <div
                                key={index}
                                className="flex items-center gap-3 px-4 py-3 rounded-xl bg-white/5 border border-white/10"
                            >
                                <span className="text-2xl">{step.icon}</span>
                                <div className="flex-1">
                                    <div className="text-xs text-violet-400 font-medium">{step.time}</div>
                                    <div className="text-sm text-white/80">{step.action}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Tips */}
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

                {/* Complete State */}
                {isComplete && (
                    <section className="animate-scaleIn">
                        <div className="flex flex-col items-center gap-3 px-4 py-6 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                            <CheckCircle className="w-12 h-12 text-emerald-400" />
                            <h3 className="text-lg font-bold text-emerald-400">촬영 완료!</h3>
                            <p className="text-sm text-white/60 text-center">
                                영상이 저장되었습니다.<br />
                                성과 분석은 My 페이지에서 확인하세요.
                            </p>
                        </div>
                    </section>
                )}

                {/* Start Recording CTA */}
                {!isComplete && (
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
                <div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
            </div>
        }>
            <ShootPageContent />
        </Suspense>
    );
}
