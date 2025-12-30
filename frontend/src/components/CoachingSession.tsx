"use client";

/**
 * CoachingSession - Real-time AI Audio Coaching
 * 
 * Flow:
 * 1. Camera preview (portrait mode)
 * 2. Audio feedback from AudioCoach API
 * 3. Rule checklist from DirectorPack
 * 4. Progress indicator (R_ES based)
 * 
 * Backend Integration:
 * - POST /coaching/sessions → create session
 * - WebSocket /coaching/live → real-time feedback
 */
import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
    X, Mic, MicOff, Camera, CameraOff,
    CheckCircle, Circle, AlertCircle, Volume2,
    Play, Square, RotateCcw, Sparkles
} from 'lucide-react';

// ==================
// Types
// ==================

interface CoachingRule {
    rule_id: string;
    description: string;
    priority: 'critical' | 'high' | 'medium' | 'low';
    status: 'pending' | 'passed' | 'failed';
}

interface CoachingFeedback {
    message: string;
    type: 'instruction' | 'praise' | 'warning';
    rule_id?: string;
    timestamp: number;
}

interface CoachingSessionProps {
    isOpen: boolean;
    onClose: () => void;
    videoId: string;
    packId?: string;
    mode: 'homage' | 'variation' | 'campaign';  // 오마쥬/변주/체험단
    onComplete?: (sessionId: string) => void;
}

// ==================
// Component
// ==================

export function CoachingSession({
    isOpen,
    onClose,
    videoId,
    packId,
    mode = 'variation',
    onComplete
}: CoachingSessionProps) {
    // State
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [isRecording, setIsRecording] = useState(false);
    const [isMuted, setIsMuted] = useState(false);
    const [currentFeedback, setCurrentFeedback] = useState<CoachingFeedback | null>(null);
    const [feedbackHistory, setFeedbackHistory] = useState<CoachingFeedback[]>([]);
    const [rules, setRules] = useState<CoachingRule[]>([]);
    const [progress, setProgress] = useState(0);  // 0-100 (R_ES score)
    const [recordingTime, setRecordingTime] = useState(0);
    const [isMobile, setIsMobile] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Refs
    const videoRef = useRef<HTMLVideoElement>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const timerRef = useRef<NodeJS.Timeout | null>(null);

    // Mobile detection
    useEffect(() => {
        if (typeof window === "undefined") return;
        const media = window.matchMedia("(max-width: 768px)");
        setIsMobile(media.matches);

        const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches);
        media.addEventListener("change", handler);
        return () => media.removeEventListener("change", handler);
    }, []);

    // Initialize session and camera
    useEffect(() => {
        if (!isOpen) return;

        initSession();

        return () => {
            cleanup();
        };
    }, [isOpen]);

    const initSession = async () => {
        try {
            // 1. Start camera
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'user', width: { ideal: 1080 }, height: { ideal: 1920 } },
                audio: true
            });
            streamRef.current = stream;
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
            }

            // 2. Create coaching session
            const token = localStorage.getItem('token');
            const res = await fetch('/api/v1/coaching/sessions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token && { 'Authorization': `Bearer ${token}` })
                },
                body: JSON.stringify({
                    video_id: videoId,
                    pack_id: packId,
                    mode
                })
            });

            if (!res.ok) {
                // Fallback: create dummy session for demo
                setSessionId(`demo-session-${Date.now()}`);
                setRules(getDemoRules(mode));
                return;
            }

            const data = await res.json();
            setSessionId(data.session_id);
            setRules(data.rules || getDemoRules(mode));

            // 3. Connect WebSocket for real-time feedback
            // connectWebSocket(data.session_id);

        } catch (err) {
            console.error('Failed to init session:', err);
            setError('카메라 접근이 거부되었습니다.');
        }
    };

    const getDemoRules = (mode: string): CoachingRule[] => {
        const baseRules: CoachingRule[] = [
            { rule_id: 'hook_timing', description: '첫 0.5초에 훅 시작', priority: 'critical', status: 'pending' },
            { rule_id: 'center_subject', description: '주 피사체 중앙 배치', priority: 'high', status: 'pending' },
            { rule_id: 'eye_contact', description: '카메라 시선 유지', priority: 'medium', status: 'pending' },
        ];

        if (mode === 'homage') {
            baseRules.push({ rule_id: 'exact_timing', description: '원본 타이밍 정확히 따르기', priority: 'critical', status: 'pending' });
        } else if (mode === 'campaign') {
            baseRules.push({ rule_id: 'product_visible', description: '제품 노출 3초 이상', priority: 'critical', status: 'pending' });
        }

        return baseRules;
    };

    const cleanup = () => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        if (timerRef.current) {
            clearInterval(timerRef.current);
            timerRef.current = null;
        }
        setIsRecording(false);
        setRecordingTime(0);
    };

    const startRecording = useCallback(() => {
        setIsRecording(true);
        setRecordingTime(0);

        // Start timer
        timerRef.current = setInterval(() => {
            setRecordingTime(prev => prev + 1);
        }, 1000);

        // Simulate coaching feedback (demo mode)
        simulateCoaching();
    }, []);

    const stopRecording = useCallback(() => {
        setIsRecording(false);
        if (timerRef.current) {
            clearInterval(timerRef.current);
            timerRef.current = null;
        }

        if (sessionId && onComplete) {
            onComplete(sessionId);
        }
    }, [sessionId, onComplete]);

    const simulateCoaching = () => {
        // Demo: simulate coaching feedback
        const feedbacks = [
            { message: "좋아요! 카메라를 정면으로 봐주세요", type: 'instruction' as const, delay: 2000 },
            { message: "훌륭해요! 첫 훅이 잘 걸렸어요 ✨", type: 'praise' as const, delay: 4000 },
            { message: "조금 더 가까이 와주세요", type: 'instruction' as const, delay: 7000 },
            { message: "완벽해요! 자연스럽게 마무리하세요", type: 'praise' as const, delay: 12000 },
        ];

        feedbacks.forEach(({ message, type, delay }) => {
            setTimeout(() => {
                if (!isRecording) return;
                const feedback: CoachingFeedback = { message, type, timestamp: Date.now() };
                setCurrentFeedback(feedback);
                setFeedbackHistory(prev => [...prev.slice(-4), feedback]);

                // Update progress
                setProgress(prev => Math.min(prev + 20, 100));

                // Update rule status
                setRules(prev => {
                    const updated = [...prev];
                    const pendingIdx = updated.findIndex(r => r.status === 'pending');
                    if (pendingIdx >= 0) {
                        updated[pendingIdx].status = 'passed';
                    }
                    return updated;
                });
            }, delay);
        });
    };

    if (!isOpen) return null;

    // Desktop blocker
    if (!isMobile) {
        return (
            <div className="fixed inset-0 z-50 bg-black flex flex-col items-center justify-center p-6">
                <div className="text-6xl mb-6">📱</div>
                <h2 className="text-2xl font-bold text-white mb-2">모바일에서만 촬영 가능</h2>
                <p className="text-white/50 text-center mb-8 max-w-sm">
                    AI 코칭 촬영은 모바일 웹에서만 사용할 수 있습니다.
                </p>
                <button onClick={onClose} className="px-8 py-3 bg-white/10 border border-white/20 rounded-xl text-white font-bold">
                    닫기
                </button>
            </div>
        );
    }

    // Error state
    if (error) {
        return (
            <div className="fixed inset-0 z-50 bg-black flex flex-col items-center justify-center p-6">
                <AlertCircle className="w-16 h-16 text-red-400 mb-4" />
                <h2 className="text-xl font-bold text-white mb-2">오류 발생</h2>
                <p className="text-white/50 text-center mb-6">{error}</p>
                <button onClick={onClose} className="px-8 py-3 bg-white/10 border border-white/20 rounded-xl text-white font-bold">
                    닫기
                </button>
            </div>
        );
    }

    const modeLabels = {
        homage: { label: '오마쥬', color: 'bg-orange-500/20 text-orange-300 border-orange-500/50' },
        variation: { label: '변주', color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50' },
        campaign: { label: '체험단', color: 'bg-violet-500/20 text-violet-300 border-violet-500/50' }
    };

    return (
        <div className="fixed inset-0 z-50 bg-black flex flex-col">
            {/* Header */}
            <div className="absolute top-0 left-0 right-0 z-10 p-4 bg-gradient-to-b from-black/80 to-transparent">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <span className={`px-2 py-1 text-xs font-bold rounded border ${modeLabels[mode].color}`}>
                            {modeLabels[mode].label}
                        </span>
                        {isRecording && (
                            <div className="flex items-center gap-2">
                                <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                                <span className="text-white font-mono text-sm">
                                    {Math.floor(recordingTime / 60)}:{(recordingTime % 60).toString().padStart(2, '0')}
                                </span>
                            </div>
                        )}
                    </div>
                    <button onClick={onClose} className="p-2 bg-white/10 rounded-full">
                        <X className="w-5 h-5 text-white" />
                    </button>
                </div>

                {/* Progress bar */}
                <div className="mt-3 h-1 bg-white/20 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-gradient-to-r from-cyan-400 to-emerald-400 transition-all duration-500"
                        style={{ width: `${progress}%` }}
                    />
                </div>
            </div>

            {/* Camera Preview */}
            <div className="flex-1 relative">
                <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className="absolute inset-0 w-full h-full object-cover"
                    style={{ transform: 'scaleX(-1)' }}
                />

                {/* Audio Feedback Display */}
                {currentFeedback && (
                    <div className="absolute top-24 left-4 right-4">
                        <div className={`p-4 rounded-xl backdrop-blur-lg ${currentFeedback.type === 'praise'
                                ? 'bg-emerald-500/30 border border-emerald-500/50'
                                : currentFeedback.type === 'warning'
                                    ? 'bg-red-500/30 border border-red-500/50'
                                    : 'bg-white/20 border border-white/30'
                            }`}>
                            <div className="flex items-center gap-2">
                                <Volume2 className="w-5 h-5 text-white animate-pulse" />
                                <p className="text-white font-medium">{currentFeedback.message}</p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Rule Checklist (bottom overlay) */}
                <div className="absolute bottom-32 left-4 right-4">
                    <div className="p-3 bg-black/60 backdrop-blur-lg rounded-xl border border-white/10">
                        <div className="text-xs text-white/60 mb-2 flex items-center gap-1">
                            <Sparkles className="w-3 h-3" />
                            체크리스트
                        </div>
                        <div className="space-y-2">
                            {rules.slice(0, 4).map((rule) => (
                                <div key={rule.rule_id} className="flex items-center gap-2">
                                    {rule.status === 'passed' ? (
                                        <CheckCircle className="w-4 h-4 text-emerald-400" />
                                    ) : rule.status === 'failed' ? (
                                        <AlertCircle className="w-4 h-4 text-red-400" />
                                    ) : (
                                        <Circle className="w-4 h-4 text-white/40" />
                                    )}
                                    <span className={`text-xs ${rule.status === 'passed' ? 'text-emerald-300' :
                                            rule.status === 'failed' ? 'text-red-300' :
                                                'text-white/70'
                                        }`}>
                                        {rule.description}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Bottom Controls */}
            <div className="p-6 bg-gradient-to-t from-black via-black/80 to-transparent">
                <div className="flex items-center justify-center gap-6">
                    {/* Mute */}
                    <button
                        onClick={() => setIsMuted(!isMuted)}
                        className="w-12 h-12 rounded-full bg-white/10 border border-white/20 flex items-center justify-center"
                    >
                        {isMuted ? <MicOff className="w-5 h-5 text-white/60" /> : <Mic className="w-5 h-5 text-white" />}
                    </button>

                    {/* Record */}
                    <button
                        onClick={isRecording ? stopRecording : startRecording}
                        className={`w-20 h-20 rounded-full flex items-center justify-center transition-all ${isRecording
                                ? 'bg-red-500 hover:bg-red-400'
                                : 'bg-gradient-to-r from-cyan-500 to-emerald-500 hover:brightness-110'
                            }`}
                    >
                        {isRecording ? (
                            <Square className="w-8 h-8 text-white" />
                        ) : (
                            <Play className="w-8 h-8 text-white ml-1" />
                        )}
                    </button>

                    {/* Reset */}
                    <button
                        onClick={() => {
                            setProgress(0);
                            setRules(getDemoRules(mode));
                            setFeedbackHistory([]);
                            setCurrentFeedback(null);
                        }}
                        className="w-12 h-12 rounded-full bg-white/10 border border-white/20 flex items-center justify-center"
                    >
                        <RotateCcw className="w-5 h-5 text-white/60" />
                    </button>
                </div>

                {!isRecording && (
                    <p className="text-center text-white/40 text-xs mt-3">
                        🎙️ AI 코치가 실시간으로 촬영을 도와드립니다
                    </p>
                )}
            </div>
        </div>
    );
}

export default CoachingSession;
