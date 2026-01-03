/**
 * Coaching WebSocket Hook - Phase 1-5+ Complete
 * 
 * Features:
 * - Phase 1: Output Mode + Persona selection
 * - Phase 2: VDG data (shotlist, kicks, mise-en-scene)
 * - Phase 3: Adaptive coaching (LLM feedback)
 * - Phase 4: Persona-based TTS
 * - Phase 5+: Auto-learning with signal promotion
 * 
 * Reference: MOBILE_INTEGRATION_GUIDE.md
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

// ============================================================
// Web Parity Types (H1 Hardening)
// ============================================================

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'recording' | 'error';
export type VoiceStyle = 'strict' | 'friendly' | 'neutral';

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

// ============================================================
// Phase 1: Output Mode + Persona Types
// ============================================================

export type OutputMode = 'graphic' | 'text' | 'audio' | 'graphic_audio';
export type Persona = 'drill_sergeant' | 'bestie' | 'chill_guide' | 'hype_coach';

export interface GraphicGuide {
    type: 'graphic_guide';
    guide_type: 'composition' | 'timing' | 'action';
    rule_id: string;
    priority: 'low' | 'medium' | 'high' | 'critical';
    target_position: [number, number];  // [x, y] normalized 0-1
    grid_type?: 'center' | 'rule_of_thirds' | 'golden_ratio';
    arrow_direction?: 'up' | 'down' | 'left' | 'right';
    action_icon?: 'look_camera' | 'action_now' | 'hold' | 'smile';
    message: string;
    message_duration_ms: number;
    timestamp: string;
}

export interface TextCoach {
    type: 'text_coach';
    message: string;
    priority: 'low' | 'medium' | 'high' | 'critical';
    persona: Persona;
    duration_ms: number;
    timestamp: string;
}

// ============================================================
// Phase 2: VDG Data Types
// ============================================================

export interface ShotGuide {
    index: number;
    t_window: [number, number];  // [start_sec, end_sec]
    guide: string;
}

export interface KickTiming {
    t_sec: number;
    type: 'punch' | 'end';
    cue: string;
    message: string;
    pre_alert_sec: number;
}

export interface MiseEnSceneGuide {
    element: string;
    value: string;
    guide: string;
    priority: 'high' | 'medium';
    evidence?: string;
}

export interface VdgCoachingData {
    type: 'vdg_coaching_data';
    shotlist_sequence: ShotGuide[];
    kick_timings: KickTiming[];
    mise_en_scene_guides: MiseEnSceneGuide[];
    timestamp: string;
}

// ============================================================
// Phase 3: Adaptive Coaching Types
// ============================================================

export interface AdaptiveResponse {
    type: 'adaptive_response';
    accepted: boolean;
    message: string;
    alternative?: string;
    affected_rule_id?: string;
    reason?: string;
    coaching_adjustment?: string;
    error?: string;
    timestamp: string;
}

// ============================================================
// Phase 4: Audio Feedback Types
// ============================================================

export interface AudioFeedback {
    type: 'audio_feedback';
    text: string;
    audio: string | null;  // base64 MP3
    persona: Persona;
    source: 'gemini' | 'gtts_fallback' | 'system';
    timestamp: string;
}

// ============================================================
// Phase 5+: Auto-Learning Types
// ============================================================

export interface AxisMetrics {
    compliance_lift: string;
    outcome_lift: string;
    cluster_count: number;
    persona_count: number;
    negative_rate: string;
    is_ready: boolean;
}

export interface SignalPromotion {
    type: 'signal_promotion';
    new_candidates: number;
    axis_metrics: AxisMetrics;
    failing_axes: string[];
    candidates: Array<{
        signal_key: string;
        metrics: Record<string, any>;
    }>;
    timestamp: string;
}

export interface UseCoachingWebSocketOptions {
    enableStreaming?: boolean;
    streamConfig?: StreamConfig;
    voiceEnabled?: boolean;

    // H1: Web parity params
    language?: string;
    voiceStyle?: VoiceStyle;

    // Phase 1: Output Mode + Persona
    outputMode?: OutputMode;
    persona?: Persona;

    // H2: Callbacks for web parity
    onFeedback?: (feedback: CoachingFeedback) => void;
    onRuleUpdate?: (update: RuleUpdate) => void;
    onStatusChange?: (status: SessionStatus) => void;
    onError?: (error: string) => void;

    // Phase 2: VDG data callback
    onVdgData?: (data: VdgCoachingData) => void;
    // Phase 3: Adaptive coaching callbacks
    onAdaptiveResponse?: (response: AdaptiveResponse) => void;
    // Phase 1: Graphic/Text callbacks
    onGraphicGuide?: (guide: GraphicGuide) => void;
    onTextCoach?: (coach: TextCoach) => void;
    // Phase 4: Audio feedback
    onAudioFeedback?: (audio: AudioFeedback) => void;
    // Phase 5+: Signal promotion
    onSignalPromotion?: (promotion: SignalPromotion) => void;
}

export interface UseCoachingWebSocketReturn {
    // State (H1: Web parity)
    status: ConnectionStatus;
    feedback: CoachingFeedback | null;
    feedbackHistory: CoachingFeedback[];
    isConnected: boolean;
    geminiConnected: boolean;
    stats: SessionStats | null;

    // Actions
    connect: () => void;
    disconnect: () => void;
    sendFrame: (frameBase64: string, width: number, height: number) => Promise<void>;
    sendControl: (action: 'start' | 'stop' | 'pause') => void;

    // H1: Web parity actions
    sendMetric: (ruleId: string, value: number, tSec: number) => void;
    sendAudio: (audioB64: string) => void;
    sendVideoFrame: (frameB64: string, tSec: number) => void;
    sendTiming: (tSec: number) => void;  // NEW: 녹화 시간 동기화

    // Phase 3: Adaptive coaching
    sendUserFeedback: (text: string) => void;

    // Stats (Phase 2)
    streamStats: StreamStats | null;

    // H9: Tier info
    tierInfo: TierInfo;

    // Phase 2: VDG data
    vdgData: VdgCoachingData | null;

    // Phase 1: Current mode/persona
    outputMode: OutputMode;
    persona: Persona;
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
        // H1: Web parity params
        language = 'ko',
        voiceStyle = 'friendly',
        // Phase 1: Output Mode + Persona
        outputMode: initialOutputMode = 'graphic',
        persona: initialPersona = 'chill_guide',
        // H2: Callbacks
        onFeedback,
        onRuleUpdate,
        onStatusChange,
        onError,
        // Phase 1-5+ callbacks
        onVdgData,
        onAdaptiveResponse,
        onGraphicGuide,
        onTextCoach,
        onAudioFeedback,
        onSignalPromotion,
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

    // H1: Web parity state
    const [status, setStatus] = useState<ConnectionStatus>('disconnected');
    const [geminiConnected, setGeminiConnected] = useState(false);
    const [stats, setStats] = useState<SessionStats | null>(null);

    // H9: Tier info for credit calculation
    const [tierInfo, setTierInfo] = useState<TierInfo>({
        coachingTier: 'pro',
        effectiveTier: 'pro',
        tierDowngraded: false,
    });

    // Phase 1: Output Mode + Persona
    const [outputMode] = useState<OutputMode>(initialOutputMode);
    const [persona] = useState<Persona>(initialPersona);

    // Phase 2: VDG Data
    const [vdgData, setVdgData] = useState<VdgCoachingData | null>(null);

    // ============================================================
    // Connection Management
    // ============================================================

    const connect = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            console.log('[WS] Already connected');
            return;
        }

        setStatus('connecting');  // H1: Update status

        // H1: Add language, voice_style, output_mode, persona to URL
        const wsUrl = `${WS_BASE_URL}/api/v1/coaching/live/${sessionId}?language=${language}&voice_style=${voiceStyle}&output_mode=${outputMode}&persona=${persona}`;
        console.log('[WS] Connecting to:', wsUrl);

        try {
            const ws = new WebSocket(wsUrl);
            wsRef.current = ws;

            ws.onopen = () => {
                console.log('[WS] Connected');
                setIsConnected(true);
                setStatus('connected');  // H1: Update status
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
                setStatus('error');  // H1: Update status
                onError?.('WebSocket connection error');
            };

            ws.onclose = (event) => {
                console.log('[WS] Closed:', event.code, event.reason);
                setIsConnected(false);
                setStatus('disconnected');  // H1: Update status
                cleanup();

                // H1: Exponential backoff for reconnect (1s, 2s, 3s)
                if (event.code !== 1000 && reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
                    reconnectAttemptsRef.current++;
                    const backoffDelay = reconnectAttemptsRef.current * 1000;  // 1s, 2s, 3s
                    console.log(`[WS] Reconnecting (attempt ${reconnectAttemptsRef.current}) in ${backoffDelay}ms...`);
                    setTimeout(connect, backoffDelay);
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

                case 'session_status': {
                    // H1: Full session_status parsing for web parity
                    const statusMsg = message as SessionStatus;

                    // Update connection status
                    if (statusMsg.status === 'recording') {
                        setStatus('recording');
                    } else if (statusMsg.status === 'connected' || statusMsg.status === 'paused') {
                        setStatus('connected');
                    }

                    // Update gemini connected state
                    setGeminiConnected(statusMsg.gemini_connected ?? false);

                    // Update session stats
                    if (statusMsg.stats) {
                        setStats(statusMsg.stats);
                    }

                    // H9: Handle tier downgrade info (legacy support)
                    if ((message as any).effective_tier !== undefined) {
                        setTierInfo({
                            coachingTier: (message as any).coaching_tier || 'pro',
                            effectiveTier: (message as any).effective_tier || 'pro',
                            tierDowngraded: (message as any).tier_downgraded || false,
                        });
                        if ((message as any).tier_downgraded) {
                            console.log('[WS] H9: Tier downgraded to basic (Gemini fallback)');
                        }
                    }

                    // H2: Callback
                    onStatusChange?.(statusMsg);
                    break;
                }

                // H1: Rule Update handler
                case 'rule_update':
                    console.log('[WS] Rule update:', message.rule_id, message.status);
                    onRuleUpdate?.(message as RuleUpdate);
                    break;

                case 'error':
                    console.error('[WS] Server error:', message.message);
                    onError?.(message.message || 'Unknown error');
                    break;

                // Phase 1: Graphic Guide
                case 'graphic_guide':
                    console.log('[WS] Graphic guide:', message.guide_type);
                    onGraphicGuide?.(message as GraphicGuide);
                    break;

                // Phase 1: Text Coach
                case 'text_coach':
                    console.log('[WS] Text coach:', message.message);
                    onTextCoach?.(message as TextCoach);
                    break;

                // Phase 2: VDG Coaching Data
                case 'vdg_coaching_data':
                    console.log('[WS] VDG data received:', message.shotlist_sequence?.length, 'shots');
                    setVdgData(message as VdgCoachingData);
                    onVdgData?.(message as VdgCoachingData);
                    break;

                // Phase 3: Adaptive Response
                case 'adaptive_response':
                    const adaptiveMsg = message as AdaptiveResponse;
                    console.log('[WS] Adaptive response:', adaptiveMsg.accepted ? '✅' : '❌');
                    onAdaptiveResponse?.(adaptiveMsg);
                    break;

                // Phase 4: Audio Feedback
                case 'audio_feedback':
                    console.log('[WS] Audio feedback:', message.persona);
                    if (voiceEnabled && message.audio) {
                        playAudio(message.audio);
                    }
                    onAudioFeedback?.(message as AudioFeedback);
                    break;

                // Phase 5+: Signal Promotion
                case 'signal_promotion':
                    console.log('[WS] Signal promotion:', message.new_candidates, 'candidates');
                    onSignalPromotion?.(message as SignalPromotion);
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

        // H2: Fire callback
        onFeedback?.(feedbackData);

        // H3: Audio playback with TTS fallback
        if (voiceEnabled) {
            if (feedbackData.audio_b64) {
                playAudio(feedbackData.audio_b64);
            } else if (feedbackData.message) {
                // Fallback to TTS
                speakText(feedbackData.message);
            }
        }
    }, [voiceEnabled, onFeedback]);

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
    // Phase 3: Adaptive Coaching
    // ============================================================

    const sendUserFeedback = useCallback((text: string) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
                type: 'user_feedback',
                text,
            }));
            console.log('[WS] User feedback sent:', text);
        }
    }, []);

    // ============================================================
    // H1: Web Parity Send Functions
    // ============================================================

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

    const sendAudio = useCallback((audioB64: string) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'audio', data: audioB64 }));
        }
    }, []);

    const sendVideoFrame = useCallback((frameB64: string, tSec: number) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
                type: 'video_frame',
                frame_b64: frameB64,
                t_sec: tSec,
            }));
        }
    }, []);

    // NEW: 녹화 시간 동기화 (세션 통계/자동학습용)
    const sendTiming = useCallback((tSec: number) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'timing', t_sec: tSec }));
        }
    }, []);

    // ============================================================
    // Return
    // ============================================================

    return {
        // H1: Web parity state
        status,
        geminiConnected,
        stats,
        // Core state
        feedback,
        feedbackHistory,
        isConnected,
        // Core actions
        connect,
        disconnect,
        sendFrame,
        sendControl,
        // H1: Web parity actions
        sendMetric,
        sendAudio,
        sendVideoFrame,
        sendTiming,  // NEW
        // Phase 3: Adaptive coaching
        sendUserFeedback,
        // Stats
        streamStats,
        tierInfo,  // H9
        // Phase 1: Mode/Persona
        outputMode,
        persona,
        // Phase 2: VDG Data
        vdgData,
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
