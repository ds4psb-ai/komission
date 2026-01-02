/**
 * Coaching WebSocket Hook - Phase 2 Optimized
 * 
 * Features:
 * - H.264 streaming instead of JPEG (50% latency reduction)
 * - Adaptive bitrate based on network conditions
 * - Frame throttling to prevent overload
 * - Round-trip latency measurement
 * 
 * Reference: Gemini Live API Best Practices 2025
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { Platform } from 'react-native';
import {
    FrameProcessor,
    FrameData,
    buildFrameMessage,
    getRecommendedStreamConfig,
    StreamConfig,
} from '@/services/videoStreamService';

// ============================================================
// Types
// ============================================================

export interface CoachingFeedback {
    type: 'feedback';
    message: string;
    audio_b64?: string;
    rule_id?: string;
    priority: 'low' | 'medium' | 'high' | 'critical';
    server_timestamp?: number;
}

export interface CoachingStatus {
    type: 'status';
    status: 'connected' | 'processing' | 'ready';
    session_id?: string;
}

export interface StreamStats {
    framesSent: number;
    framesDropped: number;
    avgLatency: number;
    currentBitrate: number;
    qualityTier: 'low' | 'medium' | 'high';
}

// H9: Tier info for credit calculation
export interface TierInfo {
    coachingTier: 'basic' | 'pro';
    effectiveTier: 'basic' | 'pro';
    tierDowngraded: boolean;
}

export interface UseCoachingWebSocketOptions {
    enableStreaming?: boolean;
    streamConfig?: StreamConfig;
    voiceEnabled?: boolean;
}

export interface UseCoachingWebSocketReturn {
    // State
    feedback: CoachingFeedback | null;
    feedbackHistory: CoachingFeedback[];
    isConnected: boolean;

    // Actions
    connect: () => void;
    disconnect: () => void;
    sendFrame: (frameBase64: string, width: number, height: number) => Promise<void>;
    sendControl: (action: 'start' | 'stop' | 'pause') => void;

    // Stats (Phase 2)
    streamStats: StreamStats | null;

    // H9: Tier info
    tierInfo: TierInfo;
}

// ============================================================
// Constants
// ============================================================

const WS_BASE_URL = process.env.EXPO_PUBLIC_WS_URL || 'ws://localhost:8000';
const RECONNECT_DELAY_MS = 2000;
const MAX_RECONNECT_ATTEMPTS = 3;
const PING_INTERVAL_MS = 30000;

// ============================================================
// Hook Implementation
// ============================================================

export function useCoachingWebSocket(
    sessionId: string,
    options: UseCoachingWebSocketOptions = {}
): UseCoachingWebSocketReturn {
    const {
        enableStreaming = true,
        streamConfig = getRecommendedStreamConfig(),
        voiceEnabled = true,
    } = options;

    // WebSocket ref
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectAttemptsRef = useRef(0);
    const pingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

    // Frame processor (Phase 2)
    const frameProcessorRef = useRef<FrameProcessor>(
        new FrameProcessor(streamConfig)
    );

    // Latency tracking
    const pendingFramesRef = useRef<Map<number, number>>(new Map());
    const latenciesRef = useRef<number[]>([]);

    // State
    const [isConnected, setIsConnected] = useState(false);
    const [feedback, setFeedback] = useState<CoachingFeedback | null>(null);
    const [feedbackHistory, setFeedbackHistory] = useState<CoachingFeedback[]>([]);
    const [streamStats, setStreamStats] = useState<StreamStats | null>(null);

    // H9: Tier info for credit calculation
    const [tierInfo, setTierInfo] = useState<TierInfo>({
        coachingTier: 'pro',
        effectiveTier: 'pro',
        tierDowngraded: false,
    });

    // ============================================================
    // Connection Management
    // ============================================================

    const connect = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            console.log('[WS] Already connected');
            return;
        }

        const wsUrl = `${WS_BASE_URL}/api/v1/coaching/live/${sessionId}`;
        console.log('[WS] Connecting to:', wsUrl);

        try {
            const ws = new WebSocket(wsUrl);
            wsRef.current = ws;

            ws.onopen = () => {
                console.log('[WS] Connected');
                setIsConnected(true);
                reconnectAttemptsRef.current = 0;

                // Send initial config
                ws.send(JSON.stringify({
                    type: 'config',
                    platform: Platform.OS,
                    streaming: {
                        codec: streamConfig.codec,
                        fps: streamConfig.targetFps,
                        resolution: `${streamConfig.maxWidth}x${streamConfig.maxHeight}`,
                    },
                }));

                // Start ping interval
                pingIntervalRef.current = setInterval(() => {
                    if (ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({ type: 'ping', t: Date.now() }));
                    }
                }, PING_INTERVAL_MS);
            };

            ws.onmessage = (event) => {
                handleMessage(event.data);
            };

            ws.onerror = (error) => {
                console.error('[WS] Error:', error);
            };

            ws.onclose = (event) => {
                console.log('[WS] Closed:', event.code, event.reason);
                setIsConnected(false);
                cleanup();

                // Auto-reconnect if not intentional close
                if (event.code !== 1000 && reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
                    reconnectAttemptsRef.current++;
                    console.log(`[WS] Reconnecting (attempt ${reconnectAttemptsRef.current})...`);
                    setTimeout(connect, RECONNECT_DELAY_MS);
                }
            };
        } catch (error) {
            console.error('[WS] Connection error:', error);
        }
    }, [sessionId, streamConfig]);

    const disconnect = useCallback(() => {
        console.log('[WS] Disconnecting...');

        if (wsRef.current) {
            // Send stop before closing
            if (wsRef.current.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify({ type: 'control', action: 'stop' }));
            }
            wsRef.current.close(1000, 'User disconnected');
            wsRef.current = null;
        }

        cleanup();
        setIsConnected(false);
        setFeedback(null);
    }, []);

    const cleanup = useCallback(() => {
        if (pingIntervalRef.current) {
            clearInterval(pingIntervalRef.current);
            pingIntervalRef.current = null;
        }
        frameProcessorRef.current.reset();
        pendingFramesRef.current.clear();
        latenciesRef.current = [];
    }, []);

    // ============================================================
    // Message Handling
    // ============================================================

    const handleMessage = useCallback((data: string) => {
        try {
            const message = JSON.parse(data);

            switch (message.type) {
                case 'feedback':
                    handleFeedback(message);
                    break;

                case 'pong':
                    // Measure round-trip latency
                    if (message.client_t) {
                        const latency = Date.now() - message.client_t;
                        recordLatency(latency);
                    }
                    break;

                case 'frame_ack':
                    // Frame was processed - measure latency
                    if (message.frame_t && pendingFramesRef.current.has(message.frame_t)) {
                        const sendTime = pendingFramesRef.current.get(message.frame_t)!;
                        const latency = Date.now() - sendTime;
                        recordLatency(latency);
                        pendingFramesRef.current.delete(message.frame_t);

                        // Update frame processor with latency
                        frameProcessorRef.current.recordResponseLatency(latency);
                    }
                    break;

                case 'status':
                    console.log('[WS] Status:', message.status);
                    break;

                case 'session_status':
                    // H9: Handle tier downgrade info
                    if (message.effective_tier !== undefined) {
                        setTierInfo({
                            coachingTier: message.coaching_tier || 'pro',
                            effectiveTier: message.effective_tier || 'pro',
                            tierDowngraded: message.tier_downgraded || false,
                        });
                        if (message.tier_downgraded) {
                            console.log('[WS] H9: Tier downgraded to basic (Gemini fallback)');
                        }
                    }
                    break;

                case 'error':
                    console.error('[WS] Server error:', message.message);
                    break;

                default:
                    console.log('[WS] Unknown message type:', message.type);
            }
        } catch (error) {
            console.error('[WS] Parse error:', error);
        }
    }, []);

    const handleFeedback = useCallback((message: any) => {
        const feedbackData: CoachingFeedback = {
            type: 'feedback',
            message: message.message || '',
            audio_b64: message.audio_b64,
            rule_id: message.rule_id,
            priority: message.priority || 'medium',
            server_timestamp: message.t,
        };

        setFeedback(feedbackData);
        setFeedbackHistory((prev: CoachingFeedback[]) => [...prev.slice(-9), feedbackData]);

        // Play audio if enabled
        if (voiceEnabled && feedbackData.audio_b64) {
            playAudio(feedbackData.audio_b64);
        }
    }, [voiceEnabled]);

    const recordLatency = useCallback((latency: number) => {
        latenciesRef.current.push(latency);
        if (latenciesRef.current.length > 20) {
            latenciesRef.current.shift();
        }

        // Update stats
        const processorStats = frameProcessorRef.current.getStats();
        const avgLatency = latenciesRef.current.reduce((a: number, b: number) => a + b, 0) /
            latenciesRef.current.length;

        setStreamStats({
            framesSent: processorStats.frameStats.sent,
            framesDropped: processorStats.frameStats.dropped,
            avgLatency: Math.round(avgLatency),
            currentBitrate: processorStats.bitrate,
            qualityTier: processorStats.qualityTier as 'low' | 'medium' | 'high',
        });
    }, []);

    // ============================================================
    // Frame Sending (Phase 2 Optimized)
    // ============================================================

    const sendFrame = useCallback(async (
        frameBase64: string,
        width: number,
        height: number
    ) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
            return;
        }

        if (!enableStreaming) {
            return;
        }

        // Process frame (throttling + optimization)
        const processedFrame = await frameProcessorRef.current.processFrame(
            frameBase64,
            width,
            height
        );

        if (!processedFrame) {
            // Frame was throttled
            return;
        }

        // Track pending frame for latency measurement
        pendingFramesRef.current.set(processedFrame.timestamp, Date.now());

        // Build and send message
        const message = buildFrameMessage(processedFrame);
        wsRef.current.send(JSON.stringify(message));
    }, [enableStreaming]);

    // ============================================================
    // Control Commands
    // ============================================================

    const sendControl = useCallback((action: 'start' | 'stop' | 'pause') => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
                type: 'control',
                action,
                t: Date.now(),
            }));

            if (action === 'start') {
                frameProcessorRef.current.reset();
            }
        }
    }, []);

    // ============================================================
    // Cleanup on Unmount
    // ============================================================

    useEffect(() => {
        return () => {
            disconnect();
        };
    }, [disconnect]);

    // ============================================================
    // Return
    // ============================================================

    return {
        feedback,
        feedbackHistory,
        isConnected,
        connect,
        disconnect,
        sendFrame,
        sendControl,
        streamStats,
        tierInfo,  // H9
    };
}

// ============================================================
// Audio Playback Helper
// ============================================================

async function playAudio(base64Audio: string) {
    try {
        // Import expo-av dynamically to avoid issues on web
        const { Audio } = await import('expo-av');

        const { sound } = await Audio.Sound.createAsync({
            uri: `data:audio/mp3;base64,${base64Audio}`,
        });

        await sound.playAsync();

        // Cleanup after playback
        sound.setOnPlaybackStatusUpdate((status: { isLoaded: boolean; didJustFinish?: boolean }) => {
            if (status.isLoaded && status.didJustFinish) {
                sound.unloadAsync();
            }
        });
    } catch (error) {
        console.error('[Audio] Playback error:', error);

        // Fallback to speech synthesis
        try {
            const Speech = await import('expo-speech');
            // Can't speak base64, would need to decode first
            console.log('[Audio] Would use Speech fallback');
        } catch {
            // Speech not available
        }
    }
}

// ============================================================
// Export helpers
// ============================================================

export { getRecommendedStreamConfig } from '@/services/videoStreamService';
