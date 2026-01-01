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

type WebSocketMessage = CoachingFeedback | RuleUpdate | SessionStatus | { type: 'pong' | 'error'; message?: string };

interface UseCoachingWebSocketOptions {
    language?: string;
    voiceStyle?: 'strict' | 'friendly' | 'neutral';
    onFeedback?: (feedback: CoachingFeedback) => void;
    onRuleUpdate?: (update: RuleUpdate) => void;
    onStatusChange?: (status: SessionStatus) => void;
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
        onFeedback,
        onRuleUpdate,
        onStatusChange,
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

        const wsUrl = `${WS_BASE_URL}/ws/coaching/${sessionId}?language=${language}&voice_style=${voiceStyle}`;
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
                        // Auto-play TTS if available
                        if (feedbackMsg.audio_b64) {
                            playAudioB64(feedbackMsg.audio_b64);
                        } else {
                            // Fallback to Web Speech API
                            speakText(feedbackMsg.message);
                        }
                        break;

                    case 'rule_update':
                        onRuleUpdate?.(msg as RuleUpdate);
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
