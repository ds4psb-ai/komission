"use client";

/**
 * SessionContext - 세션 기반 작업 흐름 상태 관리
 * 
 * 문서: docs/21_PAGE_IA_REDESIGN.md
 * - 상황 입력 → 추천 결과 → 촬영 가이드 흐름의 상태 유지
 * - /for-you, /session/* 페이지에서 사용
 */
import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

// Types
export interface SessionInputContext {
    product?: string;
    category: string;
    platform: 'tiktok' | 'youtube' | 'instagram';
}

export interface SessionPattern {
    pattern_id: string;
    cluster_id: string;
    pattern_summary: string;
    signature: {
        hook: string;
        timing: string;
        audio: string;
    };
    fit_score: number;
    evidence_strength: number;
    tier?: 'S' | 'A' | 'B' | 'C';
    recurrence?: {
        status: 'confirmed' | 'candidate';
        ancestor_cluster_id: string;
        recurrence_score: number;
        origin_year?: number;
    };
}

export interface SessionState {
    // Current step
    step: 'input' | 'result' | 'shoot';

    // Input context
    input_context: SessionInputContext | null;

    // Selected pattern
    selected_pattern: SessionPattern | null;

    // Tracking
    evidence_viewed: boolean;
    shoot_started: boolean;
    feedback_submitted: boolean;
}

export interface SessionContextValue {
    state: SessionState;

    // Actions
    setInputContext: (context: SessionInputContext) => void;
    setSelectedPattern: (pattern: SessionPattern) => void;
    setStep: (step: SessionState['step']) => void;
    markEvidenceViewed: () => void;
    markShootStarted: () => void;
    markFeedbackSubmitted: () => void;
    resetSession: () => void;
}

const initialState: SessionState = {
    step: 'input',
    input_context: null,
    selected_pattern: null,
    evidence_viewed: false,
    shoot_started: false,
    feedback_submitted: false,
};

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
    const [state, setState] = useState<SessionState>(initialState);

    const setInputContext = useCallback((context: SessionInputContext) => {
        setState(prev => ({
            ...prev,
            input_context: context,
            step: 'result',
        }));
    }, []);

    const setSelectedPattern = useCallback((pattern: SessionPattern) => {
        setState(prev => ({
            ...prev,
            selected_pattern: pattern,
        }));
    }, []);

    const setStep = useCallback((step: SessionState['step']) => {
        setState(prev => ({
            ...prev,
            step,
        }));
    }, []);

    const markEvidenceViewed = useCallback(() => {
        setState(prev => ({
            ...prev,
            evidence_viewed: true,
        }));
    }, []);

    const markShootStarted = useCallback(() => {
        setState(prev => ({
            ...prev,
            shoot_started: true,
            step: 'shoot',
        }));
    }, []);

    const markFeedbackSubmitted = useCallback(() => {
        setState(prev => ({
            ...prev,
            feedback_submitted: true,
        }));
    }, []);

    const resetSession = useCallback(() => {
        setState(initialState);
    }, []);

    const value: SessionContextValue = {
        state,
        setInputContext,
        setSelectedPattern,
        setStep,
        markEvidenceViewed,
        markShootStarted,
        markFeedbackSubmitted,
        resetSession,
    };

    return (
        <SessionContext.Provider value={value}>
            {children}
        </SessionContext.Provider>
    );
}

export function useSession(): SessionContextValue {
    const context = useContext(SessionContext);
    if (!context) {
        throw new Error('useSession must be used within a SessionProvider');
    }
    return context;
}

// Optional hook that doesn't throw
export function useSessionOptional(): SessionContextValue | null {
    return useContext(SessionContext);
}

export default SessionContext;
