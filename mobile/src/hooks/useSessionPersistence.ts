/**
 * Coaching Session Persistence Hook
 *
 * Handles:
 * - Creating coaching sessions in backend DB
 * - Logging interventions and outcomes
 * - Uploading session results for RL/recursive improvement
 *
 * Backend Integration:
 * - POST /coaching/sessions → create session
 * - POST /coaching/sessions/{id}/events/intervention → log intervention
 * - POST /coaching/sessions/{id}/events/outcome → log outcome
 * - POST /coaching/sessions/{id}/end → end session with summary
 *
 * This enables:
 * - DB-backed coaching history
 * - Reinforcement learning from user behavior
 * - Pattern effectiveness measurement
 */

import { useRef, useCallback, useState } from 'react';
import { Platform } from 'react-native';

// ============================================================
// Types
// ============================================================

export interface SessionConfig {
    mode: 'homage' | 'mutation' | 'campaign';
    patternId: string;
    packId?: string;
    videoId?: string;
}

export interface SessionData {
    sessionId: string;
    assignment: 'coached' | 'control';
    holdoutGroup: boolean;
    patternId: string;
    packId?: string;
    createdAt: string;
}

export interface InterventionEvent {
    ruleId: string;
    tSec: number;
    message: string;
    priority: 'low' | 'medium' | 'high' | 'critical';
}

export interface OutcomeEvent {
    interventionId: string;
    ruleId: string;
    tSec: number;
    result: 'complied' | 'violated' | 'unknown';
    evidenceType?: 'frame' | 'audio' | 'text';
}

export interface SessionSummary {
    durationSec: number;
    interventionCount: number;
    complianceRate: number;
    unknownRate: number;
}

export interface UseSessionPersistenceReturn {
    // State
    session: SessionData | null;
    isCreating: boolean;
    error: string | null;

    // Actions
    createSession: (config: SessionConfig) => Promise<SessionData | null>;
    logIntervention: (event: InterventionEvent) => Promise<string | null>;
    logOutcome: (event: OutcomeEvent) => Promise<void>;
    endSession: (summary: SessionSummary) => Promise<void>;
}

// ============================================================
// Constants
// ============================================================

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

// ============================================================
// Hook Implementation
// ============================================================

export function useSessionPersistence(): UseSessionPersistenceReturn {
    const [session, setSession] = useState<SessionData | null>(null);
    const [isCreating, setIsCreating] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Pending interventions for batch upload
    const pendingInterventions = useRef<InterventionEvent[]>([]);
    const pendingOutcomes = useRef<OutcomeEvent[]>([]);

    // ============================================================
    // Create Session
    // ============================================================

    const createSession = useCallback(async (
        config: SessionConfig
    ): Promise<SessionData | null> => {
        setIsCreating(true);
        setError(null);

        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/coaching/sessions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    mode: config.mode,
                    pattern_id: config.patternId,
                    pack_id: config.packId,
                    video_id: config.videoId,
                    device_type: Platform.OS,
                    user_id_hash: await getUserIdHash(),
                }),
            });

            if (!response.ok) {
                throw new Error(`Failed to create session: ${response.status}`);
            }

            const data = await response.json();

            const sessionData: SessionData = {
                sessionId: data.session_id,
                assignment: data.assignment || 'coached',
                holdoutGroup: data.holdout_group || false,
                patternId: config.patternId,
                packId: config.packId,
                createdAt: new Date().toISOString(),
            };

            setSession(sessionData);
            console.log('[Session] Created:', sessionData.sessionId, sessionData.assignment);

            return sessionData;
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Unknown error';
            console.error('[Session] Create error:', message);
            setError(message);
            return null;
        } finally {
            setIsCreating(false);
        }
    }, []);

    // ============================================================
    // Log Intervention
    // ============================================================

    const logIntervention = useCallback(async (
        event: InterventionEvent
    ): Promise<string | null> => {
        if (!session) {
            console.warn('[Session] No active session for intervention');
            return null;
        }

        // Add to pending for potential batch upload
        pendingInterventions.current.push(event);

        try {
            const response = await fetch(
                `${API_BASE_URL}/api/v1/coaching/sessions/${session.sessionId}/events/intervention`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        rule_id: event.ruleId,
                        t_sec: event.tSec,
                        message: event.message,
                        priority: event.priority,
                    }),
                }
            );

            if (!response.ok) {
                console.warn('[Session] Failed to log intervention:', response.status);
                return null;
            }

            const data = await response.json();
            console.log('[Session] Intervention logged:', event.ruleId);

            return data.intervention_id || null;
        } catch (err) {
            console.error('[Session] Intervention log error:', err);
            return null;
        }
    }, [session]);

    // ============================================================
    // Log Outcome
    // ============================================================

    const logOutcome = useCallback(async (event: OutcomeEvent): Promise<void> => {
        if (!session) {
            console.warn('[Session] No active session for outcome');
            return;
        }

        // Add to pending
        pendingOutcomes.current.push(event);

        try {
            await fetch(
                `${API_BASE_URL}/api/v1/coaching/sessions/${session.sessionId}/events/outcome`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        intervention_id: event.interventionId,
                        rule_id: event.ruleId,
                        t_sec: event.tSec,
                        result: event.result,
                        evidence_type: event.evidenceType,
                    }),
                }
            );

            console.log('[Session] Outcome logged:', event.ruleId, event.result);
        } catch (err) {
            console.error('[Session] Outcome log error:', err);
        }
    }, [session]);

    // ============================================================
    // End Session
    // ============================================================

    const endSession = useCallback(async (
        summary: SessionSummary
    ): Promise<void> => {
        if (!session) {
            console.warn('[Session] No active session to end');
            return;
        }

        try {
            await fetch(
                `${API_BASE_URL}/api/v1/coaching/sessions/${session.sessionId}/end`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        duration_sec: summary.durationSec,
                        intervention_count: summary.interventionCount,
                        compliance_rate: summary.complianceRate,
                        unknown_rate: summary.unknownRate,
                    }),
                }
            );

            console.log('[Session] Ended:', session.sessionId, summary);

            // Clear pending
            pendingInterventions.current = [];
            pendingOutcomes.current = [];
            setSession(null);
        } catch (err) {
            console.error('[Session] End error:', err);
        }
    }, [session]);

    return {
        session,
        isCreating,
        error,
        createSession,
        logIntervention,
        logOutcome,
        endSession,
    };
}

// ============================================================
// Helpers
// ============================================================

/**
 * Generate anonymous user ID hash for privacy
 * Uses device info + random seed, no PII
 */
async function getUserIdHash(): Promise<string> {
    const base = `${Platform.OS}_${Date.now()}_${Math.random().toString(36)}`;

    // Simple hash (not crypto-secure, just for anonymization)
    let hash = 0;
    for (let i = 0; i < base.length; i++) {
        const char = base.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32bit integer
    }

    return Math.abs(hash).toString(16).padStart(8, '0');
}
