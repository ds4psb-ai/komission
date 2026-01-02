/**
 * useDirectorPack Hook - Phase 1.2
 * 
 * Ported from frontend: session/shoot/page.tsx state management
 * 
 * Features:
 * - DirectorPack loading with retry
 * - Offline detection
 * - Error handling with specific messages
 * - Real-time step tracking
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { AppState, AppStateStatus } from 'react-native';
import NetInfo from '@react-native-community/netinfo';
import {
    loadDirectorPack,
    getCurrentStep,
    getUpcomingStep,
    GuideData,
    GuideStep,
    DirectorPack,
    FALLBACK_GUIDE,
} from '../services/directorPackService';

// ============================================================
// Types
// ============================================================

export interface UseDirectorPackOptions {
    /** Auto-load on mount */
    autoLoad?: boolean;
    /** Pre-alert time for upcoming steps */
    preAlertSec?: number;
}

export interface UseDirectorPackReturn {
    // Data
    guideData: GuideData;
    pack: DirectorPack | null;

    // Loading state
    isLoading: boolean;
    error: string | null;

    // Network state
    isOffline: boolean;

    // Actions
    retry: () => void;

    // Real-time tracking (call with current recording time)
    getCurrentGuideStep: (currentTimeSec: number) => GuideStep | null;
    getUpcomingGuideStep: (currentTimeSec: number) => GuideStep | null;
}

// ============================================================
// Constants
// ============================================================

const MAX_RETRY_COUNT = 3;

// ============================================================
// Hook Implementation
// ============================================================

export function useDirectorPack(
    patternId: string | null,
    options: UseDirectorPackOptions = {}
): UseDirectorPackReturn {
    const {
        autoLoad = true,
        preAlertSec = 2,
    } = options;

    // State
    const [guideData, setGuideData] = useState<GuideData>(FALLBACK_GUIDE);
    const [pack, setPack] = useState<DirectorPack | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isOffline, setIsOffline] = useState(false);
    const [retryCount, setRetryCount] = useState(0);

    // Refs
    const isMountedRef = useRef(true);

    // ============================================================
    // Offline Detection
    // ============================================================

    useEffect(() => {
        const unsubscribe = NetInfo.addEventListener(state => {
            if (isMountedRef.current) {
                setIsOffline(!state.isConnected);
            }
        });

        // Check initial state
        NetInfo.fetch().then(state => {
            if (isMountedRef.current) {
                setIsOffline(!state.isConnected);
            }
        });

        return () => {
            unsubscribe();
        };
    }, []);

    // ============================================================
    // App State (reload on foreground)
    // ============================================================

    useEffect(() => {
        const handleAppStateChange = (nextState: AppStateStatus) => {
            if (nextState === 'active' && error && !isLoading) {
                // Auto-retry on app foreground if there was an error
                loadPack();
            }
        };

        const subscription = AppState.addEventListener('change', handleAppStateChange);
        return () => subscription.remove();
    }, [error, isLoading]);

    // ============================================================
    // Load DirectorPack
    // ============================================================

    const loadPack = useCallback(async () => {
        if (!patternId) {
            setGuideData(FALLBACK_GUIDE);
            setIsLoading(false);
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const result = await loadDirectorPack(patternId);

            if (isMountedRef.current) {
                setPack(result.pack);
                setGuideData(result.guide);

                if (result.error) {
                    // Non-fatal error (using fallback)
                    setError(result.error);
                }
            }
        } catch (err) {
            if (isMountedRef.current) {
                let errorMessage = '가이드 로딩 실패';

                if (isOffline) {
                    errorMessage = '인터넷 연결을 확인해주세요';
                } else if (err instanceof Error) {
                    errorMessage = err.message;
                }

                setError(errorMessage);
                setGuideData(FALLBACK_GUIDE);
            }
        } finally {
            if (isMountedRef.current) {
                setIsLoading(false);
            }
        }
    }, [patternId, isOffline]);

    // Auto-load on mount
    useEffect(() => {
        if (autoLoad) {
            loadPack();
        }
    }, [autoLoad, loadPack, retryCount]);

    // Cleanup
    useEffect(() => {
        isMountedRef.current = true;
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    // ============================================================
    // Actions
    // ============================================================

    const retry = useCallback(() => {
        if (retryCount >= MAX_RETRY_COUNT) {
            console.warn('[useDirectorPack] Max retries reached');
            return;
        }
        setRetryCount(prev => prev + 1);
    }, [retryCount]);

    // ============================================================
    // Real-time Step Tracking
    // ============================================================

    const getCurrentGuideStep = useCallback((currentTimeSec: number): GuideStep | null => {
        return getCurrentStep(guideData, currentTimeSec);
    }, [guideData]);

    const getUpcomingGuideStep = useCallback((currentTimeSec: number): GuideStep | null => {
        return getUpcomingStep(guideData, currentTimeSec, preAlertSec);
    }, [guideData, preAlertSec]);

    // ============================================================
    // Return
    // ============================================================

    return {
        guideData,
        pack,
        isLoading,
        error,
        isOffline,
        retry,
        getCurrentGuideStep,
        getUpcomingGuideStep,
    };
}

export default useDirectorPack;
