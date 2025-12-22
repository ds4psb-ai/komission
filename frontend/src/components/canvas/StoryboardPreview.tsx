"use client";

import React, { useState, useEffect } from 'react';

interface StoryboardFrame {
    timestamp: string;
    description: string;
    overlay?: string;
}

interface StoryboardPreviewProps {
    nodeId?: string;
    isOpen: boolean;
    onClose: () => void;
    frames?: StoryboardFrame[];
}

// Default sample frames for demo
const defaultFrames: StoryboardFrame[] = [
    { timestamp: '0:00', description: 'Hook - 시선 끌기', overlay: '🎯 오프닝' },
    { timestamp: '0:03', description: '문제 제기', overlay: '❓ 공감' },
    { timestamp: '0:08', description: '솔루션 소개', overlay: '💡 해결책' },
    { timestamp: '0:14', description: 'CTA - 행동 유도', overlay: '🔥 마무리' },
];

export function StoryboardPreview({ nodeId, isOpen, onClose, frames = defaultFrames }: StoryboardPreviewProps) {
    const [activeFrame, setActiveFrame] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);

    // Auto-play simulation
    useEffect(() => {
        if (!isPlaying) return;

        const interval = setInterval(() => {
            setActiveFrame(prev => (prev + 1) % frames.length);
        }, 1500);

        return () => clearInterval(interval);
    }, [isPlaying, frames.length]);

    // ESC to close
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose();
        };
        if (isOpen) {
            window.addEventListener('keydown', handleKeyDown);
            return () => window.removeEventListener('keydown', handleKeyDown);
        }
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm"
            onClick={(e) => e.target === e.currentTarget && onClose()}
        >
            <div className="w-full max-w-4xl mx-4 bg-[#111] border border-white/10 rounded-2xl overflow-hidden shadow-2xl">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
                    <div className="flex items-center gap-3">
                        <span className="text-2xl">🎬</span>
                        <div>
                            <h2 className="font-bold text-white">스토리보드 미리보기</h2>
                            <p className="text-xs text-white/50">키프레임 미리보기 (렌더링 없이 빠른 확인)</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="text-white/40 hover:text-white text-xl">✕</button>
                </div>

                {/* Main Preview Area */}
                <div className="p-6">
                    {/* Active Frame Display */}
                    <div className="aspect-video bg-gradient-to-br from-violet-900/30 to-pink-900/30 rounded-xl flex items-center justify-center relative overflow-hidden mb-6">
                        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10" />

                        {/* Frame Content */}
                        <div className="text-center z-10">
                            <div className="text-6xl mb-4">{frames[activeFrame].overlay}</div>
                            <div className="text-xl font-bold text-white mb-2">{frames[activeFrame].description}</div>
                            <div className="text-white/50 text-sm">타임스탬프: {frames[activeFrame].timestamp}</div>
                        </div>

                        {/* Overlay Text Simulation */}
                        <div className="absolute bottom-4 left-4 right-4 p-3 bg-black/60 backdrop-blur rounded-lg">
                            <div className="text-xs text-white/70 font-mono">
                                프레임 {activeFrame + 1}/{frames.length} • {frames[activeFrame].timestamp}
                            </div>
                        </div>
                    </div>

                    {/* Timeline / Frame Selector */}
                    <div className="flex gap-3 justify-center mb-6">
                        {frames.map((frame, i) => (
                            <button
                                key={i}
                                onClick={() => { setActiveFrame(i); setIsPlaying(false); }}
                                className={`flex-1 max-w-[120px] p-3 rounded-xl transition-all ${i === activeFrame
                                    ? 'bg-violet-500/30 border-2 border-violet-500'
                                    : 'bg-white/5 border border-white/10 hover:border-white/30'
                                    }`}
                            >
                                <div className="text-2xl mb-1">{frame.overlay}</div>
                                <div className="text-[10px] text-white/50">{frame.timestamp}</div>
                            </button>
                        ))}
                    </div>

                    {/* Playback Controls */}
                    <div className="flex justify-center gap-4">
                        <button
                            onClick={() => setActiveFrame(prev => Math.max(0, prev - 1))}
                            disabled={activeFrame === 0}
                            className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm disabled:opacity-30 transition-all"
                        >
                            ← 이전
                        </button>
                        <button
                            onClick={() => setIsPlaying(!isPlaying)}
                            className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${isPlaying
                                ? 'bg-red-500/20 border border-red-500/30 text-red-400'
                                : 'bg-emerald-500/20 border border-emerald-500/30 text-emerald-400'
                                }`}
                        >
                            {isPlaying ? '⏸ 일시정지' : '▶ 재생'}
                        </button>
                        <button
                            onClick={() => setActiveFrame(prev => Math.min(frames.length - 1, prev + 1))}
                            disabled={activeFrame === frames.length - 1}
                            className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm disabled:opacity-30 transition-all"
                        >
                            다음 →
                        </button>
                    </div>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-white/10 flex justify-between items-center bg-white/5">
                    <div className="text-xs text-white/40">
                        💡 Tip: 전체 영상 렌더링 대신 키프레임으로 빠르게 구조를 확인하세요
                    </div>
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-violet-500 hover:bg-violet-400 rounded-lg text-sm font-bold transition-colors"
                    >
                        확인
                    </button>
                </div>
            </div>
        </div>
    );
}
