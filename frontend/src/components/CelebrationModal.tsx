"use client";

import React from 'react';
import Link from 'next/link';

interface CelebrationModalProps {
    isOpen: boolean;
    onClose: () => void;
    nodeTitle: string;
    estimatedViews?: { min: number; max: number };
    estimatedRevenue?: { min: number; max: number };
    earnedPoints: number;
    questBonus?: number;
}

export function CelebrationModal({
    isOpen,
    onClose,
    nodeTitle,
    estimatedViews = { min: 50000, max: 100000 },
    estimatedRevenue = { min: 10, max: 30 },
    earnedPoints,
    questBonus = 0,
}: CelebrationModalProps) {
    if (!isOpen) return null;

    const totalPoints = earnedPoints + questBonus;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/80 backdrop-blur-md"
                onClick={onClose}
            />

            {/* Modal */}
            <div className="relative bg-[#0a0a0a] border border-white/10 rounded-[32px] p-10 max-w-md w-full shadow-2xl animate-[scaleIn_0.3s_ease-out]">
                {/* Background Ambient Glow */}
                <div className="absolute -inset-10 bg-gradient-to-r from-violet-600/30 via-pink-600/30 to-orange-600/30 blur-3xl opacity-50 rounded-[50px] pointer-events-none" />

                {/* Confetti Effect (CSS) */}
                <div className="absolute inset-0 overflow-hidden rounded-[32px] pointer-events-none">
                    <div className="absolute top-0 left-1/4 w-2 h-2 bg-yellow-400 rounded-full animate-[confetti_1s_ease-out_infinite]" style={{ animationDelay: '0s' }} />
                    <div className="absolute top-0 left-1/2 w-2 h-2 bg-pink-400 rounded-full animate-[confetti_1s_ease-out_infinite]" style={{ animationDelay: '0.1s' }} />
                    <div className="absolute top-0 left-3/4 w-2 h-2 bg-emerald-400 rounded-full animate-[confetti_1s_ease-out_infinite]" style={{ animationDelay: '0.2s' }} />
                    <div className="absolute top-0 left-1/3 w-2 h-2 bg-violet-400 rounded-full animate-[confetti_1s_ease-out_infinite]" style={{ animationDelay: '0.15s' }} />
                    <div className="absolute top-0 left-2/3 w-2 h-2 bg-orange-400 rounded-full animate-[confetti_1s_ease-out_infinite]" style={{ animationDelay: '0.25s' }} />
                </div>

                {/* Header */}
                <div className="text-center mb-8">
                    <div className="text-6xl mb-4 animate-bounce">🎉</div>
                    <h2 className="text-3xl font-black text-white mb-2">축하합니다!</h2>
                    <p className="text-white/60 text-sm">리믹스가 성공적으로 등록되었어요</p>
                </div>

                {/* Stats */}
                <div className="space-y-4 mb-8">
                    {/* Estimated Views */}
                    <div className="flex items-center justify-between p-4 bg-white/5 rounded-2xl border border-white/10">
                        <div className="flex items-center gap-3">
                            <span className="text-2xl">👁️</span>
                            <span className="text-white/60 text-sm font-medium">예상 조회수</span>
                        </div>
                        <span className="text-white font-bold text-lg">
                            {(estimatedViews.min / 1000).toFixed(0)}K ~ {(estimatedViews.max / 1000).toFixed(0)}K
                        </span>
                    </div>

                    {/* Estimated Revenue */}
                    <div className="flex items-center justify-between p-4 bg-yellow-500/10 rounded-2xl border border-yellow-500/20">
                        <div className="flex items-center gap-3">
                            <span className="text-2xl">💰</span>
                            <span className="text-yellow-400/80 text-sm font-medium">예상 로열티</span>
                        </div>
                        <span className="text-yellow-400 font-black text-xl">
                            ${estimatedRevenue.min} ~ ${estimatedRevenue.max}
                        </span>
                    </div>

                    {/* K-Points */}
                    <div className="flex items-center justify-between p-4 bg-violet-500/10 rounded-2xl border border-violet-500/20">
                        <div className="flex items-center gap-3">
                            <span className="text-2xl">🎁</span>
                            <span className="text-violet-400/80 text-sm font-medium">K-Points 적립</span>
                        </div>
                        <div className="text-right">
                            <span className="text-violet-400 font-black text-xl">{totalPoints.toLocaleString()} P</span>
                            {questBonus > 0 && (
                                <div className="text-[10px] text-violet-300/60">
                                    (기본 {earnedPoints}P + 퀘스트 {questBonus}P)
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Info */}
                <div className="text-center mb-8 p-3 bg-white/5 rounded-xl border border-white/5">
                    <p className="text-white/40 text-xs">
                        ⏰ 실시간 조회수와 수익은 <span className="text-white/70 font-bold">[내 수익]</span>에서 확인할 수 있어요!
                    </p>
                </div>

                {/* Actions */}
                <div className="space-y-3">
                    <Link
                        href="/my"
                        className="block w-full py-4 px-6 bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-400 hover:to-orange-400 rounded-2xl text-center text-black font-bold text-lg shadow-[0_0_30px_rgba(234,179,8,0.3)] hover:shadow-[0_0_40px_rgba(234,179,8,0.5)] transition-all"
                    >
                        💎 내 수익 확인하기
                    </Link>
                    <button
                        onClick={onClose}
                        className="block w-full py-3 px-6 bg-white/5 hover:bg-white/10 border border-white/10 rounded-2xl text-center text-white/60 hover:text-white font-medium text-sm transition-all"
                    >
                        다음 리믹스 시작하기
                    </button>
                </div>
            </div>

            {/* CSS Keyframes (inline style tag for Next.js) */}
            <style jsx global>{`
                @keyframes scaleIn {
                    from {
                        opacity: 0;
                        transform: scale(0.9);
                    }
                    to {
                        opacity: 1;
                        transform: scale(1);
                    }
                }
                @keyframes confetti {
                    0% {
                        transform: translateY(0) rotate(0deg);
                        opacity: 1;
                    }
                    100% {
                        transform: translateY(300px) rotate(720deg);
                        opacity: 0;
                    }
                }
            `}</style>
        </div>
    );
}
