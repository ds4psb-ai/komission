'use client';

import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { ApiClient, CalibrationPair } from '@/lib/api';

const api = new ApiClient();

export default function TasteCalibrationPage() {
    const router = useRouter();
    const [pairs, setPairs] = useState<CalibrationPair[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [completed, setCompleted] = useState(false);
    const isMountedRef = useRef(true);
    const timeoutRefs = useRef<Array<ReturnType<typeof setTimeout>>>([]);

    const loadPairs = useCallback(async () => {
        try {
            const token = api.getToken();
            if (!token) {
                router.push('/login?next=/calibration');
                return;
            }

            const response = await api.getCalibrationPairs();
            if (!isMountedRef.current) return;
            setPairs(response.pairs);
            setLoading(false);
        } catch (error) {
            console.error('Failed to load pairs:', error);
            if (isMountedRef.current) {
                setLoading(false);
            }
            alert('데이터를 불러오는데 실패했습니다.');
        }
    }, [router]);

    useEffect(() => {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        loadPairs();
    }, [loadPairs]);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
            timeoutRefs.current.forEach(clearTimeout);
            timeoutRefs.current = [];
        };
    }, []);

    const handleChoice = async (selection: 'A' | 'B') => {
        if (submitting) return;
        setSubmitting(true);

        const currentPair = pairs[currentIndex];
        const selectedOption = selection === 'A' ? currentPair.option_a : currentPair.option_b;

        try {
            // API 전송 (비동기 처리하지만 UX는 바로 넘어감)
            await api.submitCalibrationChoice(currentPair.pair_id, selectedOption.id, selection);
            if (!isMountedRef.current) return;

            if (currentIndex < pairs.length - 1) {
                // 다음 문항으로
                const timeoutId = setTimeout(() => {
                    if (!isMountedRef.current) return;
                    setCurrentIndex(prev => prev + 1);
                    setSubmitting(false);
                }, 300); // 약간의 딜레이로 애니메이션 효과
                timeoutRefs.current.push(timeoutId);
            } else {
                // 완료
                setCompleted(true);
                const timeoutId = setTimeout(() => {
                    if (!isMountedRef.current) return;
                    router.push('/remix'); // Remix 메인으로 이동
                }, 1500);
                timeoutRefs.current.push(timeoutId);
            }
        } catch (error) {
            console.error('Failed to submit choice:', error);
            if (isMountedRef.current) {
                setSubmitting(false);
            }
            alert('오류가 발생했습니다. 다시 시도해주세요.');
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-black text-white">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
            </div>
        );
    }

    if (completed) {
        return (
            <div className="flex flex-col items-center justify-center min-h-screen bg-black text-white p-6 text-center animate-fade-in">
                <div className="text-6xl mb-4">✅</div>
                <h1 className="text-2xl font-bold mb-2">설정 완료!</h1>
                <p className="text-gray-400">당신의 취향을 분석하고 있습니다...</p>
            </div>
        );
    }

    const currentPair = pairs[currentIndex];
    if (!currentPair) {
        return (
            <div className="flex flex-col items-center justify-center min-h-screen bg-black text-white p-6 text-center">
                <div className="text-5xl mb-4">🧭</div>
                <h1 className="text-xl font-bold mb-2">표시할 질문이 없습니다</h1>
                <p className="text-white/50 mb-6">잠시 후 다시 시도해주세요.</p>
                <button
                    onClick={() => router.push('/remix')}
                    className="px-6 py-3 bg-violet-500 rounded-xl font-bold"
                >
                    돌아가기
                </button>
            </div>
        );
    }
    const progress = ((currentIndex + 1) / pairs.length) * 100;

    return (
        <div className="flex flex-col min-h-screen bg-black text-white overflow-hidden">
            {/* Header / Progress */}
            <div className="absolute top-0 left-0 right-0 z-20 p-6">
                <div className="flex justify-between items-center mb-4">
                    <span className="text-sm font-mono text-primary">TASTE CALIBRATION</span>
                    <span className="text-sm font-mono text-gray-500">{currentIndex + 1} / {pairs.length}</span>
                </div>
                <div className="w-full bg-gray-800 h-1 rounded-full overflow-hidden">
                    <div
                        className="bg-primary h-full transition-all duration-300 ease-out"
                        style={{ width: `${progress}%` }}
                    />
                </div>
            </div>

            {/* Question */}
            <div className="absolute top-20 left-0 right-0 z-20 text-center px-4">
                <h2 className="text-xl md:text-2xl font-bold break-keep leading-tight">
                    {currentPair.question}
                </h2>
            </div>

            {/* Split Cards */}
            <div className="flex flex-col md:flex-row h-screen pt-32 pb-6 px-4 md:pt-0 md:pb-0 gap-4 md:gap-0">

                {/* Option A */}
                <button
                    onClick={() => handleChoice('A')}
                    className={`
            flex-1 relative group overflow-hidden rounded-2xl md:rounded-none
            transition-all duration-300 md:hover:flex-[1.2] active:scale-[0.98]
            bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-800
            ${submitting ? 'opacity-50 cursor-wait' : 'cursor-pointer'}
          `}
                >
                    <div className="absolute inset-0 bg-red-500/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                    <div className="flex flex-col items-center justify-center h-full p-6 text-center z-10 relative">
                        <span className="text-6xl mb-6 transform group-hover:scale-110 transition-transform duration-300">
                            {currentPair.option_a.icon || 'A'}
                        </span>
                        <h3 className="text-2xl font-bold mb-2">{currentPair.option_a.label}</h3>
                        <p className="text-sm text-gray-400">{currentPair.option_a.description}</p>
                    </div>
                    {/* Mobile Tap Indicator */}
                    <div className="absolute bottom-4 left-0 right-0 text-center text-xs text-gray-600 md:hidden">
                        TAP TO SELECT
                    </div>
                </button>

                {/* VS Divider */}
                <div className="hidden md:flex absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-16 h-16 bg-black rounded-full items-center justify-center z-30 border-2 border-gray-800">
                    <span className="font-bold text-gray-500 italic">VS</span>
                </div>

                {/* Option B */}
                <button
                    onClick={() => handleChoice('B')}
                    className={`
            flex-1 relative group overflow-hidden rounded-2xl md:rounded-none
            transition-all duration-300 md:hover:flex-[1.2] active:scale-[0.98]
            bg-gradient-to-bl from-gray-900 to-gray-800 border border-gray-800
            ${submitting ? 'opacity-50 cursor-wait' : 'cursor-pointer'}
          `}
                >
                    <div className="absolute inset-0 bg-blue-500/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                    <div className="flex flex-col items-center justify-center h-full p-6 text-center z-10 relative">
                        <span className="text-6xl mb-6 transform group-hover:scale-110 transition-transform duration-300">
                            {currentPair.option_b.icon || 'B'}
                        </span>
                        <h3 className="text-2xl font-bold mb-2">{currentPair.option_b.label}</h3>
                        <p className="text-sm text-gray-400">{currentPair.option_b.description}</p>
                    </div>
                    {/* Mobile Tap Indicator */}
                    <div className="absolute bottom-4 left-0 right-0 text-center text-xs text-gray-600 md:hidden">
                        TAP TO SELECT
                    </div>
                </button>

            </div>
        </div>
    );
}
