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
 * - POST /coaching/sessions → create session (with control group assignment)
 * - POST /coaching/sessions/{id}/events/* → event logging
 * - WebSocket /coaching/live → real-time feedback
 * 
 * P1 Features:
 * - Control Group (10%): No coaching, for causal inference
 * - 3-event logging: rule_evaluated, intervention, outcome
 */
import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
    X, Mic, MicOff, Camera, CameraOff,
    CheckCircle, Circle, AlertCircle, Volume2,
    Play, Square, RotateCcw, Sparkles, FlaskConical
} from 'lucide-react';
import { api } from '@/lib/api';
import { useCoachingWebSocket, CoachingFeedback as WSFeedback, RuleUpdate, SessionStatus } from '@/hooks/useCoachingWebSocket';
import { useAudioCapture } from '@/hooks/useAudioCapture';

// ==================
// Types
// ==================

interface CoachingRule {
    rule_id: string;
    description: string;
    priority: 'critical' | 'high' | 'medium' | 'low';
    status: 'pending' | 'passed' | 'failed';
    checkpoint_id?: string;
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
    const [useRealCoaching, setUseRealCoaching] = useState(true);  // Toggle for real vs demo
    const [isSessionReady, setIsSessionReady] = useState(false);  // Prevent record before session created

    // P1: Control Group State
    const [assignment, setAssignment] = useState<'coached' | 'control'>('coached');
    const [holdoutGroup, setHoldoutGroup] = useState(false);
    const [currentInterventionId, setCurrentInterventionId] = useState<string | null>(null);
    const [currentCheckpoint, setCurrentCheckpoint] = useState<string>('hook_punch');

    // Real-time WebSocket Hook
    const {
        status: wsStatus,
        lastFeedback: wsFeedback,
        geminiConnected,
        stats: wsStats,
        connect: wsConnect,
        disconnect: wsDisconnect,
        sendControl,
        sendMetric,
        sendAudio,
        sendVideoFrame,  // P3: Real-time video analysis
    } = useCoachingWebSocket(sessionId, {
        voiceStyle: 'friendly',
        onFeedback: (feedback) => {
            if (assignment === 'control') return;  // Skip for control group
            setCurrentFeedback({
                message: feedback.message,
                type: feedback.priority === 'critical' ? 'warning' : 'instruction',
                rule_id: feedback.rule_id,
                timestamp: Date.now(),
            });
            setFeedbackHistory(prev => [...prev.slice(-4), {
                message: feedback.message,
                type: 'instruction',
                rule_id: feedback.rule_id,
                timestamp: Date.now(),
            }]);
            setProgress(prev => Math.min(prev + 15, 100));
        },
        onRuleUpdate: (update) => {
            setRules(prev => prev.map(r =>
                r.rule_id === update.rule_id
                    ? { ...r, status: update.status }
                    : r
            ));
        },
        onStatusChange: (status) => {
            if (status.stats?.res_score) {
                setProgress(Math.round(status.stats.res_score * 100));
            }
        },
        onError: (err) => console.error('Coaching WebSocket error:', err),
    });

    // Audio Capture Hook - streams microphone PCM to WebSocket
    const {
        start: startAudioCapture,
        stop: stopAudioCapture,
        isCapturing: isAudioCapturing,
        isSpeaking,
        audioLevel,
        error: audioError,
    } = useAudioCapture({
        onAudioData: (pcmBase64) => {
            // Stream audio to WebSocket if connected and recording
            if (useRealCoaching && wsStatus === 'recording') {
                sendAudio(pcmBase64);
            }
        },
        onSpeechDetected: () => {
            console.log('🗣️ Speech detected');
        },
        onSilenceDetected: () => {
            console.log('🔇 Silence detected');
        },
    });

    // Refs
    const videoRef = useRef<HTMLVideoElement>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const timerRef = useRef<NodeJS.Timeout | null>(null);
    const timeoutRefs = useRef<Array<ReturnType<typeof setTimeout>>>([]);
    const isRecordingRef = useRef(false);
    const recordingTimeRef = useRef(0);
    const isMountedRef = useRef(true);

    // P3: Video frame capture refs
    const canvasRef = useRef<HTMLCanvasElement | null>(null);
    const frameIntervalRef = useRef<NodeJS.Timeout | null>(null);

    // P0: MediaRecorder for video file recording
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const recordedChunksRef = useRef<Blob[]>([]);

    // P1: Wake Lock for mobile (prevent screen sleep during recording)
    const wakeLockRef = useRef<WakeLockSentinel | null>(null);

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

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    const initSession = async () => {
        console.log('🚀 initSession started');

        try {
            // 1. Create coaching session FIRST (doesn't need camera)
            try {
                console.log('📡 Creating coaching session...');
                const sessionData = await api.createCoachingSession({
                    video_id: videoId,  // Server-side DirectorPack loading
                    language: 'ko',
                    voice_style: 'friendly'
                });

                console.log('📥 API response received');

                // React 18+ safely ignores state updates on unmounted components
                console.log('✅ Session created:', sessionData.session_id);

                setSessionId(sessionData.session_id);
                setIsSessionReady(true);
                setAssignment(sessionData.assignment);
                setHoldoutGroup(sessionData.holdout_group);
                setRules(getDemoRules(mode));

                // Log if control group
                if (sessionData.assignment === 'control') {
                    console.log('🔬 Control Group: 코칭 없이 촬영 (인과 추론용)');
                }
                if (sessionData.holdout_group) {
                    console.log('📊 Holdout Group: 승격 판단 제외');
                }

            } catch (apiErr) {
                // Fallback: create dummy session for demo
                console.error('❌ API failed:', apiErr);
                setSessionId(`demo-session-${Date.now()}`);
                setIsSessionReady(true);
                setRules(getDemoRules(mode));
            }

            // 2. Start camera (can fail without breaking session)
            try {
                console.log('📷 Requesting camera...');
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: { facingMode: 'user', width: { ideal: 1080 }, height: { ideal: 1920 } },
                    audio: true
                });
                streamRef.current = stream;
                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                }
                console.log('✅ Camera ready');
            } catch (cameraErr) {
                console.warn('⚠️ Camera access denied, coaching will work without preview:', cameraErr);
                // Coaching still works, just no camera preview
            }

        } catch (err) {
            console.error('Failed to init session:', err);
            if (isMountedRef.current) {
                setError('세션 초기화 실패');
            }
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
        if (timeoutRefs.current.length > 0) {
            timeoutRefs.current.forEach(clearTimeout);
            timeoutRefs.current = [];
        }
        // P0: Cleanup MediaRecorder
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
            mediaRecorderRef.current.stop();
            mediaRecorderRef.current = null;
        }
        recordedChunksRef.current = [];
        // P1: Release Wake Lock on cleanup
        if (wakeLockRef.current) {
            wakeLockRef.current.release().catch(() => { });
            wakeLockRef.current = null;
        }
        isRecordingRef.current = false;
        recordingTimeRef.current = 0;
        if (isMountedRef.current) {
            setIsRecording(false);
            setRecordingTime(0);
        }
    };

    const simulateCoaching = useCallback(() => {
        // P1: Demo coaching with event logging
        const feedbacks = [
            { message: "좋아요! 카메라를 정면으로 봐주세요", type: 'instruction' as const, delay: 2000, rule: rules[0] },
            { message: "훌륭해요! 첫 훅이 잘 걸렸어요 ✨", type: 'praise' as const, delay: 4000, rule: rules[0] },
            { message: "조금 더 가까이 와주세요", type: 'instruction' as const, delay: 7000, rule: rules[1] },
            { message: "완벽해요! 자연스럽게 마무리하세요", type: 'praise' as const, delay: 12000, rule: rules[2] },
        ];

        feedbacks.forEach(({ message, type, delay, rule }, index) => {
            const timeoutId = setTimeout(async () => {
                if (!isRecordingRef.current || !sessionId) return;
                if (!isMountedRef.current) return;

                const currentRule = rule || rules[index % rules.length];
                if (!currentRule) return;

                // Always log rule evaluation (even for control group)
                const ruleResult = type === 'praise' ? 'passed' : 'violated';
                const shouldIntervene = type === 'instruction';

                const tVideo = recordingTimeRef.current;

                try {
                    // P1: Log rule_evaluated (ALWAYS, even without intervention)
                    await api.logRuleEvaluated(sessionId, {
                        rule_id: currentRule.rule_id,
                        ap_id: `ap_${currentRule.rule_id}_${tVideo}`,
                        checkpoint_id: currentCheckpoint,
                        result: ruleResult,
                        t_video: tVideo,
                        intervention_triggered: shouldIntervene && assignment !== 'control',
                    });

                    if (!isMountedRef.current) return;

                    // P1: Only deliver coaching for non-control group
                    if (assignment === 'control') {
                        // Control group: silent evaluation only
                        console.log(`🔬 Control: ${currentRule.rule_id} = ${ruleResult} (no coaching)`);
                        if (isMountedRef.current) {
                            setProgress(prev => Math.min(prev + 20, 100));
                        }
                        return;
                    }

                    // Coached group: deliver feedback
                    if (shouldIntervene) {
                        const interventionId = `iv_${Date.now()}_${index}`;
                        if (isMountedRef.current) {
                            setCurrentInterventionId(interventionId);
                        }

                        // Log intervention
                        await api.logIntervention(sessionId, {
                            intervention_id: interventionId,
                            rule_id: currentRule.rule_id,
                            ap_id: `ap_${currentRule.rule_id}_${tVideo}`,
                            checkpoint_id: currentCheckpoint,
                            t_video: tVideo,
                            command_text: message,
                        });
                        if (!isMountedRef.current) return;
                    }

                    // Update UI
                    const feedback: CoachingFeedback = { message, type, rule_id: currentRule.rule_id, timestamp: Date.now() };
                    if (isMountedRef.current) {
                        setCurrentFeedback(feedback);
                        setFeedbackHistory(prev => [...prev.slice(-4), feedback]);
                        setProgress(prev => Math.min(prev + 20, 100));
                    }

                    // Update rule status
                    if (isMountedRef.current) {
                        setRules(prev => {
                            const updated = [...prev];
                            const idx = updated.findIndex(r => r.rule_id === currentRule.rule_id);
                            if (idx >= 0) {
                                updated[idx].status = type === 'praise' ? 'passed' : 'pending';
                            }
                            return updated;
                        });
                    }

                    // Log outcome for praised rules (compliance detected)
                    if (type === 'praise' && currentInterventionId) {
                        await api.logOutcome(sessionId, {
                            intervention_id: currentInterventionId,
                            compliance_detected: true,
                            user_response: 'complied',
                        });
                    }

                } catch (err) {
                    console.error('Event logging failed:', err);
                }
            }, delay);
            timeoutRefs.current.push(timeoutId);
        });
    }, [assignment, currentCheckpoint, rules, sessionId, isMountedRef]);

    const startRecording = useCallback(() => {
        setIsRecording(true);
        setRecordingTime(0);
        isRecordingRef.current = true;
        recordingTimeRef.current = 0;

        // P0: Start MediaRecorder for video file recording
        const stream = streamRef.current;
        if (stream) {
            recordedChunksRef.current = [];  // Clear previous chunks

            // iOS Safari compatible mimeType (video/mp4 preferred, webm fallback)
            const mimeType = MediaRecorder.isTypeSupported('video/mp4;codecs=avc1')
                ? 'video/mp4;codecs=avc1'
                : MediaRecorder.isTypeSupported('video/webm;codecs=vp9')
                    ? 'video/webm;codecs=vp9'
                    : 'video/webm';

            try {
                const recorder = new MediaRecorder(stream, { mimeType });
                recorder.ondataavailable = (e) => {
                    if (e.data.size > 0) recordedChunksRef.current.push(e.data);
                };
                recorder.start(1000);  // Capture in 1-second chunks
                mediaRecorderRef.current = recorder;
                console.log(`🎬 MediaRecorder started: ${mimeType}`);
            } catch (err) {
                console.warn('MediaRecorder failed, continuing without video file:', err);
            }
        }

        // P1: Request Wake Lock to prevent screen sleep during recording (mobile)
        if ('wakeLock' in navigator) {
            navigator.wakeLock.request('screen')
                .then(lock => {
                    wakeLockRef.current = lock;
                    console.log('🔆 Wake Lock acquired (screen will stay on)');
                })
                .catch(err => console.warn('Wake Lock failed:', err));
        }

        // Start timer
        timerRef.current = setInterval(() => {
            setRecordingTime(prev => {
                const next = prev + 1;
                recordingTimeRef.current = next;

                // Real-time WebSocket: Send periodic metric updates
                if (useRealCoaching && wsStatus === 'recording') {
                    // Example: send current recording time as a metric
                    sendMetric('recording_progress', next / 60, next);
                }

                return next;
            });
        }, 1000);

        // Real WebSocket mode vs Demo mode
        console.log(`🎬 startRecording: sessionId=${sessionId}, useRealCoaching=${useRealCoaching}, wsStatus=${wsStatus}`);

        if (useRealCoaching && sessionId) {
            // Connect and start real-time coaching
            console.log('🔌 Calling wsConnect()...');
            wsConnect();
            // Give WebSocket time to connect, then send start control + start audio capture
            setTimeout(() => {
                console.log(`📤 Sending control.start, wsStatus=${wsStatus}`);
                sendControl('start');
                startAudioCapture();  // Start streaming microphone to server
                console.log('🎙️ Real-time coaching started with audio capture');

                // P3: Start video frame capture at 1fps
                startFrameCapture();
            }, 500);
        } else {
            // Fallback: Simulate coaching feedback (demo mode)
            console.log('⚠️ Demo mode: sessionId missing or useRealCoaching=false');
            simulateCoaching();
        }
    }, [useRealCoaching, sessionId, wsConnect, sendControl, sendMetric, wsStatus, simulateCoaching, startAudioCapture]);

    // P3: Capture video frame and send to WebSocket
    const captureAndSendFrame = useCallback(() => {
        const video = videoRef.current;
        if (!video || video.paused || video.ended) return;

        // Create canvas if not exists
        if (!canvasRef.current) {
            canvasRef.current = document.createElement('canvas');
        }
        const canvas = canvasRef.current;

        // Set canvas size to match video (scaled down for efficiency)
        const scale = 0.5;  // 50% size for bandwidth efficiency
        canvas.width = video.videoWidth * scale || 320;
        canvas.height = video.videoHeight * scale || 240;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Draw video frame to canvas
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Convert to base64 JPEG (quality 0.6 for bandwidth)
        const frameB64 = canvas.toDataURL('image/jpeg', 0.6).split(',')[1];

        // Send to WebSocket
        const tSec = recordingTimeRef.current;
        sendVideoFrame(frameB64, tSec);
        console.log(`📸 Frame captured and sent: t=${tSec}s`);
    }, [sendVideoFrame]);

    // P3: Start 1fps video frame capture
    const startFrameCapture = useCallback(() => {
        console.log('📹 Starting video frame capture at 1fps');

        // Clear existing interval if any
        if (frameIntervalRef.current) {
            clearInterval(frameIntervalRef.current);
        }

        // Capture frame every 1000ms (1fps)
        frameIntervalRef.current = setInterval(() => {
            if (isRecordingRef.current) {
                captureAndSendFrame();
            }
        }, 1000);
    }, [captureAndSendFrame]);

    // P3: Stop video frame capture
    const stopFrameCapture = useCallback(() => {
        if (frameIntervalRef.current) {
            clearInterval(frameIntervalRef.current);
            frameIntervalRef.current = null;
            console.log('📹 Stopped video frame capture');
        }
    }, []);

    // P0: Download recorded video as file
    const downloadRecording = useCallback((blob: Blob, mimeType: string) => {
        const ext = mimeType.includes('mp4') ? 'mp4' : 'webm';
        // Safe filename: remove colons and other invalid characters
        const now = new Date();
        const timestamp = now.toISOString().replace(/[:.]/g, '-').slice(0, 19);
        const safeSessionId = (sessionId || 'session').replace(/[^a-zA-Z0-9-_]/g, '');
        const filename = `coaching_${safeSessionId}_${timestamp}.${ext}`;

        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        console.log(`📥 Video downloaded: ${filename} (${(blob.size / 1024 / 1024).toFixed(2)}MB)`);
    }, [sessionId]);

    const stopRecording = useCallback(() => {
        setIsRecording(false);
        if (timerRef.current) {
            clearInterval(timerRef.current);
            timerRef.current = null;
        }
        if (timeoutRefs.current.length > 0) {
            timeoutRefs.current.forEach(clearTimeout);
            timeoutRefs.current = [];
        }
        isRecordingRef.current = false;
        recordingTimeRef.current = 0;

        // P0: Stop MediaRecorder and download video file
        const recorder = mediaRecorderRef.current;
        if (recorder && recorder.state !== 'inactive') {
            recorder.stop();
            recorder.onstop = () => {
                if (recordedChunksRef.current.length > 0) {
                    const blob = new Blob(recordedChunksRef.current, { type: recorder.mimeType });
                    downloadRecording(blob, recorder.mimeType);
                }
                recordedChunksRef.current = [];
            };
            mediaRecorderRef.current = null;
        }

        // P1: Release Wake Lock when stopping recording
        if (wakeLockRef.current) {
            wakeLockRef.current.release()
                .then(() => console.log('🔅 Wake Lock released'))
                .catch(() => { });  // Ignore already-released errors
            wakeLockRef.current = null;
        }

        // Real WebSocket mode: send stop control and disconnect
        if (useRealCoaching && wsStatus !== 'disconnected') {
            stopAudioCapture();  // Stop microphone capture
            stopFrameCapture();  // P3: Stop video frame capture
            sendControl('stop');
            setTimeout(() => wsDisconnect(), 500);
        }

        if (sessionId && onComplete) {
            onComplete(sessionId);
        }
    }, [sessionId, onComplete, useRealCoaching, wsStatus, sendControl, wsDisconnect, stopAudioCapture, stopFrameCapture, downloadRecording]);

    if (!isOpen) return null;

    // Web/Desktop: Use responsive layout instead of blocking
    // Previously blocked desktop users, now we allow both mobile and web

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
                        {/* P1: Control Group Badge */}
                        {assignment === 'control' && (
                            <span className="px-2 py-1 text-xs font-bold rounded border bg-amber-500/20 text-amber-300 border-amber-500/50 flex items-center gap-1">
                                <FlaskConical className="w-3 h-3" />
                                실험군
                            </span>
                        )}
                        {isRecording && (
                            <div className="flex items-center gap-2">
                                <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                                <span className="text-white font-mono text-sm">
                                    {Math.floor(recordingTime / 60)}:{(recordingTime % 60).toString().padStart(2, '0')}
                                </span>

                                {/* H5: Audio Level Meter */}
                                {isAudioCapturing && (
                                    <div className="flex items-center gap-1">
                                        {[0.2, 0.4, 0.6, 0.8, 1.0].map((threshold, i) => (
                                            <div
                                                key={i}
                                                className={`w-1 rounded-full transition-all ${audioLevel >= threshold
                                                    ? isSpeaking ? 'bg-emerald-400' : 'bg-cyan-400'
                                                    : 'bg-white/20'
                                                    }`}
                                                style={{ height: `${6 + i * 3}px` }}
                                            />
                                        ))}
                                    </div>
                                )}

                                {/* H6: Gemini Connection Status */}
                                {useRealCoaching && (
                                    <span className={`ml-2 px-2 py-0.5 text-[10px] font-bold rounded ${geminiConnected
                                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                                        : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                                        }`}>
                                        {geminiConnected ? 'AI 연결' : '로컬'}
                                    </span>
                                )}
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

            {/* Main Content Area: Desktop = 3-column, Mobile = fullscreen */}
            <div className={`flex-1 relative ${!isMobile ? 'flex items-center justify-center gap-4 px-4' : ''}`}>

                {/* LEFT SIDE PANEL - Desktop Only: Coaching Feedback */}
                {!isMobile && (
                    <div className="w-64 h-full max-h-[70vh] flex flex-col gap-4">
                        {/* Current Coaching Command */}
                        <div className="flex-1 p-4 bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 overflow-y-auto">
                            <div className="text-xs text-cyan-400 mb-3 flex items-center gap-1">
                                <Volume2 className="w-3 h-3" />
                                현재 코칭
                            </div>
                            {currentFeedback && assignment !== 'control' ? (
                                <div className={`p-3 rounded-xl ${currentFeedback.type === 'praise' ? 'bg-emerald-500/20 border border-emerald-500/30' :
                                    currentFeedback.type === 'warning' ? 'bg-red-500/20 border border-red-500/30' :
                                        'bg-white/10 border border-white/20'
                                    }`}>
                                    <p className="text-sm text-white">{currentFeedback.message}</p>
                                </div>
                            ) : (
                                <p className="text-white/40 text-sm">대기 중...</p>
                            )}
                        </div>

                        {/* Feedback History */}
                        <div className="p-4 bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 max-h-48 overflow-y-auto">
                            <div className="text-xs text-white/60 mb-2">피드백 히스토리</div>
                            {feedbackHistory.length > 0 ? (
                                <div className="space-y-2">
                                    {feedbackHistory.slice(-5).map((fb, i) => (
                                        <div key={i} className="text-xs text-white/50 p-2 bg-white/5 rounded-lg">
                                            {fb.message}
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-white/30 text-xs">아직 피드백이 없습니다</p>
                            )}
                        </div>
                    </div>
                )}

                {/* CENTER: Camera Preview (9:16 on desktop, fullscreen on mobile) */}
                <div className={`relative ${!isMobile
                    ? 'aspect-[9/16] h-full max-h-[70vh] rounded-2xl overflow-hidden border border-white/20'
                    : 'absolute inset-0'
                    }`}>
                    <video
                        ref={videoRef}
                        autoPlay
                        playsInline
                        muted
                        className="absolute inset-0 w-full h-full object-cover"
                        style={{ transform: 'scaleX(-1)' }}
                    />

                    {/* Audio Feedback Display - DESKTOP ONLY (mobile = TTS only) */}
                    {currentFeedback && assignment !== 'control' && !isMobile && (
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

                    {/* Control Group: Silent evaluation notice */}
                    {assignment === 'control' && isRecording && (
                        <div className="absolute top-24 left-4 right-4">
                            <div className="p-4 rounded-xl backdrop-blur-lg bg-amber-500/20 border border-amber-500/30">
                                <div className="flex items-center gap-2">
                                    <FlaskConical className="w-5 h-5 text-amber-300" />
                                    <p className="text-amber-200 font-medium text-sm">
                                        🔬 인과 추론용 대조군 촬영 중
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Rule Checklist - Mobile ONLY (bottom overlay) */}
                    {isMobile && (
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
                    )}
                </div>

                {/* RIGHT SIDE PANEL - Desktop Only: Rules Checklist */}
                {!isMobile && (
                    <div className="w-64 h-full max-h-[70vh] flex flex-col gap-4">
                        {/* Rules Checklist */}
                        <div className="flex-1 p-4 bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 overflow-y-auto">
                            <div className="text-xs text-white/60 mb-3 flex items-center gap-1">
                                <Sparkles className="w-3 h-3" />
                                코칭 체크리스트
                            </div>
                            <div className="space-y-3">
                                {rules.map((rule) => (
                                    <div key={rule.rule_id} className="flex items-start gap-2">
                                        {rule.status === 'passed' ? (
                                            <CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5" />
                                        ) : rule.status === 'failed' ? (
                                            <AlertCircle className="w-4 h-4 text-red-400 mt-0.5" />
                                        ) : (
                                            <Circle className="w-4 h-4 text-white/40 mt-0.5" />
                                        )}
                                        <span className={`text-xs ${rule.status === 'passed' ? 'text-emerald-300' :
                                            rule.status === 'failed' ? 'text-red-300' : 'text-white/70'
                                            }`}>
                                            {rule.description}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Session Stats */}
                        <div className="p-4 bg-white/5 backdrop-blur-md rounded-2xl border border-white/10">
                            <div className="text-xs text-white/60 mb-2">세션 통계</div>
                            <div className="grid grid-cols-2 gap-2 text-xs">
                                <div className="p-2 bg-white/5 rounded-lg">
                                    <div className="text-white/40">녹화시간</div>
                                    <div className="text-white font-mono">
                                        {Math.floor(recordingTime / 60)}:{(recordingTime % 60).toString().padStart(2, '0')}
                                    </div>
                                </div>
                                <div className="p-2 bg-white/5 rounded-lg">
                                    <div className="text-white/40">진행률</div>
                                    <div className="text-cyan-400 font-mono">{progress}%</div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
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
                        disabled={!isSessionReady && !isRecording}
                        className={`w-20 h-20 rounded-full flex items-center justify-center transition-all ${isRecording
                            ? 'bg-red-500 hover:bg-red-400'
                            : isSessionReady
                                ? 'bg-gradient-to-r from-cyan-500 to-emerald-500 hover:brightness-110'
                                : 'bg-gray-500 cursor-wait opacity-50'
                            }`}
                    >
                        {!isSessionReady && !isRecording ? (
                            <div className="w-8 h-8 border-4 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : isRecording ? (
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
