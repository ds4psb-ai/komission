"use client";

import { useEffect, useRef, useState, useCallback } from 'react';

export interface RealTimeMetrics {
    user_id?: string;
    total_views: number;
    k_points: number;
    pending_royalty: number;
    total_royalty_received?: number;
    node_count: number;
    today_views: number;
    today_revenue: number;
    error?: string;
}

interface WebSocketMessage {
    type: 'initial' | 'refresh' | 'pong' | 'keepalive' | 'view_increment' | 'points_update';
    data?: RealTimeMetrics | Record<string, unknown>;
    timestamp: string;
}

interface UseRealTimeMetricsOptions {
    userId: string | null;
    enabled?: boolean;
    onMetricsUpdate?: (metrics: RealTimeMetrics) => void;
}

export function useRealTimeMetrics({
    userId,
    enabled = true,
    onMetricsUpdate,
}: UseRealTimeMetricsOptions) {
    const [metrics, setMetrics] = useState<RealTimeMetrics | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);

    const connect = useCallback(() => {
        if (!userId || !enabled) return;

        // Use relative WebSocket URL for Next.js proxy
        const protocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = typeof window !== 'undefined' ? window.location.host : 'localhost:8000';
        // For development, connect directly to backend
        const wsUrl = process.env.NODE_ENV === 'development'
            ? `ws://localhost:8000/ws/metrics/${userId}`
            : `${protocol}//${host}/ws/metrics/${userId}`;

        console.log(`🔌 Connecting to WebSocket: ${wsUrl}`);

        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
            console.log('✅ WebSocket connected');
            setIsConnected(true);

            // Start ping interval
            pingIntervalRef.current = setInterval(() => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send('ping');
                }
            }, 25000);
        };

        ws.onmessage = (event) => {
            try {
                const message: WebSocketMessage = JSON.parse(event.data);
                setLastUpdate(new Date(message.timestamp));

                if (message.type === 'initial' || message.type === 'refresh') {
                    const newMetrics = message.data as RealTimeMetrics;
                    setMetrics(newMetrics);
                    onMetricsUpdate?.(newMetrics);
                } else if (message.type === 'view_increment') {
                    // Handle incremental update
                    setMetrics(prev => {
                        if (!prev) return prev;
                        const data = message.data as { node_id: string; new_views: number };
                        return {
                            ...prev,
                            total_views: prev.total_views + 1,
                            today_views: prev.today_views + 1,
                        };
                    });
                } else if (message.type === 'points_update') {
                    // Handle points update
                    setMetrics(prev => {
                        if (!prev) return prev;
                        const data = message.data as { k_points: number };
                        return {
                            ...prev,
                            k_points: data.k_points,
                        };
                    });
                }
            } catch (err) {
                console.error('WebSocket message parse error:', err);
            }
        };

        ws.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
        };

        ws.onclose = () => {
            console.log('👋 WebSocket disconnected');
            setIsConnected(false);

            // Clear ping interval
            if (pingIntervalRef.current) {
                clearInterval(pingIntervalRef.current);
            }

            // Attempt reconnect after 5 seconds
            if (enabled) {
                reconnectTimeoutRef.current = setTimeout(() => {
                    console.log('🔄 Attempting reconnect...');
                    connect();
                }, 5000);
            }
        };
    }, [userId, enabled, onMetricsUpdate]);

    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }
        if (pingIntervalRef.current) {
            clearInterval(pingIntervalRef.current);
        }
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        setIsConnected(false);
    }, []);

    const refresh = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send('refresh');
        }
    }, []);

    useEffect(() => {
        if (enabled && userId) {
            connect();
        }
        return () => {
            disconnect();
        };
    }, [connect, disconnect, enabled, userId]);

    return {
        metrics,
        isConnected,
        lastUpdate,
        refresh,
        disconnect,
    };
}
