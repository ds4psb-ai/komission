"use client";

/**
 * useAuthGate - Progressive Authentication Hook
 * 
 * Allows guest browsing but requires login for specific actions.
 * Stores the intended action and redirect path for post-login flow.
 */

import { useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "./auth";

interface AuthGateOptions {
    /** Custom message to show on login page */
    message?: string;
    /** Custom redirect after login (default: current page) */
    redirectTo?: string;
}

export function useAuthGate() {
    const { isAuthenticated, isLoading } = useAuth();
    const router = useRouter();
    const pathname = usePathname();

    /**
     * Check if user is authenticated. If not, redirect to login.
     * @param action - Optional action identifier for analytics/UX
     * @param options - Custom options for redirect behavior
     * @returns true if authenticated, false if redirecting to login
     */
    const requireAuth = useCallback((action?: string, options?: AuthGateOptions) => {
        if (isLoading) {
            // Still loading, don't redirect yet
            return false;
        }

        if (!isAuthenticated) {
            // Store intended destination for post-login redirect
            const redirectPath = options?.redirectTo || pathname;
            sessionStorage.setItem('authRedirect', redirectPath);

            if (action) {
                sessionStorage.setItem('pendingAction', action);
            }

            // Build login URL with query params
            const params = new URLSearchParams();
            params.set('required', 'true');
            if (action) params.set('action', action);
            if (options?.message) params.set('message', options.message);

            router.push(`/login?${params.toString()}`);
            return false;
        }

        return true;
    }, [isAuthenticated, isLoading, router, pathname]);

    /**
     * Get the stored redirect path after login
     */
    const getPostLoginRedirect = useCallback(() => {
        if (typeof window === 'undefined') return '/';
        return sessionStorage.getItem('authRedirect') || '/';
    }, []);

    /**
     * Clear the stored redirect path
     */
    const clearPostLoginRedirect = useCallback(() => {
        if (typeof window === 'undefined') return;
        sessionStorage.removeItem('authRedirect');
        sessionStorage.removeItem('pendingAction');
    }, []);

    /**
     * Get the pending action that triggered login
     */
    const getPendingAction = useCallback(() => {
        if (typeof window === 'undefined') return null;
        return sessionStorage.getItem('pendingAction');
    }, []);

    return {
        requireAuth,
        isAuthenticated,
        isLoading,
        getPostLoginRedirect,
        clearPostLoginRedirect,
        getPendingAction,
    };
}

/**
 * Action type constants for consistent usage
 */
export const AUTH_ACTIONS = {
    ANALYZE: 'analyze',
    FORK: 'fork',
    SAVE: 'save',
    PROMOTE: 'promote',
    ADD_NODE: 'add_node',
    CREATE_BOARD: 'create_board',
    SUBMIT: 'submit',
} as const;

/**
 * Human-readable action labels (Korean)
 */
export const ACTION_LABELS: Record<string, string> = {
    analyze: '비디오 분석',
    fork: '리믹스 생성',
    save: '저장',
    promote: '캔버스 승격',
    add_node: '노드 추가',
    create_board: '보드 생성',
    submit: '제출',
};
