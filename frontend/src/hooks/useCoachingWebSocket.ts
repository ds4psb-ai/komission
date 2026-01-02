/**
 * useCoachingWebSocket - Real-time Audio Coaching WebSocket Hook
 * 
 * Connects to backend WebSocket for real-time Gemini Live coaching
 * 
 * Usage:
 *   const { connect, disconnect, sendControl, sendMetric, feedback, status } = useCoachingWebSocket(sessionId);
 */

import { useState, useCallback, useRef, useEffect } from 'react';

// Types
export interface CoachingFeedback {
    type: 'feedback';
    rule_id?: string;
    message: string;
    priority?: string;
    audio_b64?: string | null;
    t_sec: number;
    timestamp: string;
}

export interface RuleUpdate {
    type: 'rule_update';
    rule_id: string;
    status: 'pending' | 'passed' | 'failed';
    t_sec: number;
}

export interface SessionStatus {
    type: 'session_status';
    session_id?: string;
    status: 'connected' | 'recording' | 'paused' | 'ended';
    gemini_connected?: boolean;
    fallback_mode?: boolean;
    stats?: SessionStats;
    timestamp: string;
}

export interface SessionStats {
    total_time: number;
    rules_evaluated: number;
    interventions_sent: number;
    commands_delivered: number;
    violations_detected: number;
    res_score: number;
    res_grade: string;
}

// Phase 1: 새 메시지 타입
export interface GraphicGuide {
    type: 'graphic_guide';
    guide_type: 'composition' | 'timing' | 'action';
    rule_id?: string;
    priority?: string;
    target_position?: [number, number];
    grid_type?: string;
    arrow_direction?: string;
    action_icon?: string;
    message?: string;
    message_duration_ms?: number;
    timestamp: string;
}

export interface TextCoach {
    type: 'text_coach';
    message: string;
    priority?: string;
    persona?: string;
    duration_ms?: number;
    timestamp: string;
}

export interface AudioFeedback {
    type: 'audio_feedback';
    text: string;
    audio?: string | null;
    source?: string;
    timestamp: string;
}

// Phase 2.5: VDG 코칭 데이터
export interface VdgCoachingData {
    type: 'vdg_coaching_data';
    shotlist_sequence: Array<{
        index: number;
        t_window: [number, number];
        guide: string;
    }>;
    kick_timings: Array<{
        t_sec: number;
        type: 'punch' | 'end';
        cue: string;
        message: string;
        pre_alert_sec: number;
    }>;
    mise_en_scene_guides: Array<{
        element: string;
        value: string;
        guide: string;
        priority: 'high' | 'medium';
        evidence?: string;
    }>;
    timestamp: string;
}

// Phase 3: 적응형 코칭 응답
export interface AdaptiveResponse {
    type: 'adaptive_response';
    accepted: boolean;
    message: string;
    alternative?: string;
    affected_rule_id?: string;
    reason?: string;
    coaching_adjustment?: string;  // Phase 3.5: 허용 시 코칭 조정 내용
    error?: string;
    timestamp: string;
}

type WebSocketMessage =
    | CoachingFeedback
    | RuleUpdate
    | SessionStatus
    | GraphicGuide
    | TextCoach
    | AudioFeedback
    | VdgCoachingData
    | AdaptiveResponse
    | { type: 'pong' | 'error'; message?: string };

interface UseCoachingWebSocketOptions {
    language?: string;
    voiceStyle?: 'strict' | 'friendly' | 'neutral';
    voiceEnabled?: boolean;  // P2: Toggle voice coaching on/off
    // Phase 1: 출력 모드 + 페르소나
    outputMode?: 'graphic' | 'text' | 'audio' | 'graphic_audio';
    persona?: 'strict_pd' | 'close_friend' | 'calm_mentor' | 'energetic';
    onFeedback?: (feedback: CoachingFeedback) => void;
    onRuleUpdate?: (update: RuleUpdate) => void;
    onStatusChange?: (status: SessionStatus) => void;
    // Phase 1: 새 콜백
    onGraphicGuide?: (guide: GraphicGuide) => void;
    onTextCoach?: (coach: TextCoach) => void;
    // Phase 2.5: VDG 데이터 콜백
    onVdgData?: (data: VdgCoachingData) => void;
    // Phase 3: 적응형 코칭 콜백
    onAdaptiveResponse?: (response: AdaptiveResponse) => void;
    onError?: (error: string) => void;
}

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/api/v1';

export function useCoachingWebSocket(
    sessionId: string | null,
    options: UseCoachingWebSocketOptions = {}
) {
    const {
        language = 'ko',
        voiceStyle = 'friendly',
        voiceEnabled = true,  // Default: voice enabled
        // Phase 1: 출력 모드 + 페르소나
        outputMode = 'graphic',  // 디폴트: 그래픽 (잡음 방지)
        persona = 'chill_guide',  // 힙한 네이밍: 릴렉스 가이드
        onFeedback,
        onRuleUpdate,
        onStatusChange,
        // Phase 1: 새 콜백
        onGraphicGuide,
        onTextCoach,
        // Phase 2.5: VDG 데이터 콜백
        onVdgData,
        // Phase 3: 적응형 코칭 콜백
        onAdaptiveResponse,
        onError,
    } = options;

    const [status, setStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'recording' | 'error'>('disconnected');
    const [lastFeedback, setLastFeedback] = useState<CoachingFeedback | null>(null);
    const [geminiConnected, setGeminiConnected] = useState(false);
    const [stats, setStats] = useState<SessionStats | null>(null);

    const wsRef = useRef<WebSocket | null>(null);
    const reconnectAttempts = useRef(0);
    const maxReconnectAttempts = 3;
    const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);

    // Connect to WebSocket
    const connect = useCallback(() => {
        if (!sessionId) return;
        if (wsRef.current?.readyState === WebSocket.OPEN) return;

        setStatus('connecting');

        // Phase 1: output_mode, persona 파라미터 추가
        const wsUrl = `${WS_BASE_URL}/ws/coaching/${sessionId}?language=${language}&voice_style=${voiceStyle}&output_mode=${outputMode}&persona=${persona}`;
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
            console.log('✅ Coaching WebSocket connected');
            setStatus('connected');
            reconnectAttempts.current = 0;

            // Start ping interval
            pingIntervalRef.current = setInterval(() => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ type: 'ping' }));
                }
            }, 30000);
        };

        ws.onmessage = (event) => {
            try {
                const msg: WebSocketMessage = JSON.parse(event.data);

                switch (msg.type) {
                    case 'session_status':
                        const statusMsg = msg as SessionStatus;
                        setStatus(statusMsg.status === 'recording' ? 'recording' : 'connected');
                        setGeminiConnected(statusMsg.gemini_connected ?? false);
                        if (statusMsg.stats) setStats(statusMsg.stats);
                        onStatusChange?.(statusMsg);
                        break;

                    case 'feedback':
                        const feedbackMsg = msg as CoachingFeedback;
                        setLastFeedback(feedbackMsg);
                        onFeedback?.(feedbackMsg);
                        // Auto-play TTS if available AND voiceEnabled
                        if (voiceEnabled) {
                            if (feedbackMsg.audio_b64) {
                                playAudioB64(feedbackMsg.audio_b64);
                            } else {
                                // Fallback to Web Speech API
                                speakText(feedbackMsg.message);
                            }
                        }
                        break;

                    case 'rule_update':
                        onRuleUpdate?.(msg as RuleUpdate);
                        break;

                    // Phase 1: 새 메시지 타입
                    case 'graphic_guide':
                        onGraphicGuide?.(msg as GraphicGuide);
                        break;

                    case 'text_coach':
                        onTextCoach?.(msg as TextCoach);
                        break;

                    case 'audio_feedback':
                        const audioMsg = msg as AudioFeedback;
                        if (voiceEnabled && audioMsg.audio) {
                            playAudioB64(audioMsg.audio);
                        } else if (voiceEnabled && audioMsg.text) {
                            speakText(audioMsg.text);
                        }
                        break;

                    // Phase 2.5: VDG 코칭 데이터
                    case 'vdg_coaching_data':
                        console.log('📋 Received VDG coaching data:', (msg as VdgCoachingData).shotlist_sequence?.length, 'shots');
                        onVdgData?.(msg as VdgCoachingData);
                        break;

                    // Phase 3: 적응형 코칭 응답
                    case 'adaptive_response':
                        const adaptiveMsg = msg as AdaptiveResponse;
                        console.log('🎯 Adaptive response:', adaptiveMsg.accepted ? '✅' : '❌', adaptiveMsg.message);
                        onAdaptiveResponse?.(adaptiveMsg);
                        break;

                    case 'pong':
                        // Heartbeat acknowledged
                        break;

                    case 'error':
                        console.error('WebSocket error:', (msg as any).message);
                        onError?.((msg as any).message || 'Unknown error');
                        break;
                }
            } catch (e) {
                console.error('Failed to parse WebSocket message:', e);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            setStatus('error');
        };

        ws.onclose = () => {
            console.log('❌ Coaching WebSocket closed');
            setStatus('disconnected');

            if (pingIntervalRef.current) {
                clearInterval(pingIntervalRef.current);
            }

            // Auto-reconnect
            if (reconnectAttempts.current < maxReconnectAttempts) {
                reconnectAttempts.current++;
                console.log(`Reconnecting (${reconnectAttempts.current}/${maxReconnectAttempts})...`);
                setTimeout(connect, 1000 * reconnectAttempts.current);
            }
        };
    }, [sessionId, language, voiceStyle, onFeedback, onRuleUpdate, onStatusChange, onError]);

    // Disconnect
    const disconnect = useCallback(() => {
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        if (pingIntervalRef.current) {
            clearInterval(pingIntervalRef.current);
        }
        setStatus('disconnected');
    }, []);

    // Send control message (start/pause/stop)
    const sendControl = useCallback((action: 'start' | 'pause' | 'stop') => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'control', action }));
        }
    }, []);

    // Send metric measurement
    const sendMetric = useCallback((ruleId: string, value: number, tSec: number) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
                type: 'metric',
                rule_id: ruleId,
                value,
                t_sec: tSec,
            }));
        }
    }, []);

    // Send audio chunk (base64 encoded PCM)
    const sendAudio = useCallback((audioB64: string) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'audio', data: audioB64 }));
        }
    }, []);

    // P3: Send video frame for real-time analysis (1fps)
    const sendVideoFrame = useCallback((frameB64: string, tSec: number) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
                type: 'video_frame',
                frame_b64: frameB64,
                t_sec: tSec,
            }));
        }
    }, []);

    // Phase 3: 적응형 코칭 - 사용자 피드백 전송
    const sendUserFeedback = useCallback((text: string) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
                type: 'user_feedback',
                text,
            }));
            console.log('📤 User feedback sent:', text);
        }
    }, []);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            disconnect();
        };
    }, [disconnect]);

    return {
        status,
        lastFeedback,
        geminiConnected,
        stats,
        connect,
        disconnect,
        sendControl,
        sendMetric,
        sendAudio,
        sendVideoFrame,  // P3: Real-time video analysis
        sendUserFeedback,  // Phase 3: 적응형 코칭
    };
}

// ==================
// Audio Utilities
// ==================

function playAudioB64(audioB64: string): void {
    try {
        const byteCharacters = atob(audioB64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: 'audio/mp3' });
        const audioUrl = URL.createObjectURL(blob);
        const audio = new Audio(audioUrl);
        audio.play().catch(console.error);
    } catch (e) {
        console.error('Failed to play audio:', e);
    }
}

function speakText(text: string): void {
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'ko-KR';
        utterance.rate = 1.1;
        window.speechSynthesis.speak(utterance);
    }
}

export default useCoachingWebSocket;
