"use client";

import React, { createContext, useContext, useEffect, ReactNode } from 'react';
import { useSessionStore } from '@/stores/useSessionStore';
import type { Outlier, QuestRef, RunRef } from '@/lib/types/session';

/**
 * WorkContext: useSessionStore의 호환 레이어
 * - 기존 코드가 useWorkContext()를 사용하므로 API 유지
 * - 내부적으로 Zustand useSessionStore에 위임
 */

// ─────────────────────────────────────────────────────────────
// Legacy Types (for backward compatibility)
// ─────────────────────────────────────────────────────────────

interface OutlierContext {
    id: string;
    title: string;
    thumbnail?: string;
    performanceDelta?: string;
}

interface RecipeContext {
    nodeId: string;
    version?: string;
    title?: string;
}

interface RunContext {
    attemptNumber: number;
    forkedNodeId?: string;
    startedAt?: Date;
}

interface QuestContext {
    questId: string;
    brand?: string;
    rewardPoints: number;
    accepted: boolean;
}

interface WorkContextState {
    outlier: OutlierContext | null;
    recipe: RecipeContext | null;
    run: RunContext | null;
    quest: QuestContext | null;
}

interface WorkContextActions {
    setOutlier: (outlier: OutlierContext | null) => void;
    setRecipe: (recipe: RecipeContext | null) => void;
    setRun: (run: RunContext | null) => void;
    setQuest: (quest: QuestContext | null) => void;
    clearAll: () => void;
}

type WorkContextValue = WorkContextState & WorkContextActions;

const WorkContext = createContext<WorkContextValue | null>(null);

// ─────────────────────────────────────────────────────────────
// Provider (bridges to useSessionStore)
// ─────────────────────────────────────────────────────────────

export function WorkContextProvider({ children }: { children: ReactNode }) {
    const sessionStore = useSessionStore();

    // Convert session store state to legacy format
    const legacyState: WorkContextState = {
        outlier: sessionStore.outlier
            ? {
                id: sessionStore.outlier.nodeId,
                title: sessionStore.outlier.title,
                thumbnail: sessionStore.outlier.thumbnailUrl,
                performanceDelta: sessionStore.outlier.growthRatePct
                    ? `+${sessionStore.outlier.growthRatePct}%`
                    : undefined,
            }
            : null,
        recipe: sessionStore.recipe
            ? {
                nodeId: sessionStore.recipe.recipeId,
                version: sessionStore.recipe.versionId,
                title: sessionStore.recipe.label,
            }
            : null,
        run: sessionStore.run
            ? {
                attemptNumber: 1, // Not tracked in new store yet
                forkedNodeId: sessionStore.run.forkNodeId,
                startedAt: sessionStore.run.startedAt
                    ? new Date(sessionStore.run.startedAt)
                    : undefined,
            }
            : null,
        quest: sessionStore.quest
            ? {
                questId: sessionStore.quest.campaignId,
                brand: sessionStore.quest.title,
                rewardPoints: sessionStore.quest.rewardPoints,
                accepted: sessionStore.quest.status === 'accepted',
            }
            : null,
    };

    // Bridge setters to session store
    const setOutlier = (outlier: OutlierContext | null) => {
        if (outlier) {
            sessionStore.setOutlier({
                nodeId: outlier.id,
                title: outlier.title,
                sourceUrl: '', // Not available in legacy API
                thumbnailUrl: outlier.thumbnail,
                growthRatePct: outlier.performanceDelta
                    ? parseFloat(outlier.performanceDelta.replace(/[^0-9.-]/g, ''))
                    : undefined,
            });
        }
    };

    const setRecipe = (recipe: RecipeContext | null) => {
        if (recipe) {
            sessionStore.setRecipe({
                recipeId: recipe.nodeId,
                versionId: recipe.version,
                label: recipe.title,
            });
        }
    };

    const setRun = (run: RunContext | null) => {
        if (run && run.forkedNodeId) {
            sessionStore.setRunCreated({
                runId: run.forkedNodeId,
                forkNodeId: run.forkedNodeId,
            });
        }
    };

    const setQuest = (quest: QuestContext | null) => {
        if (quest) {
            sessionStore.acceptQuest({
                campaignId: quest.questId,
                title: quest.brand || '',
                rewardPoints: quest.rewardPoints,
                status: quest.accepted ? 'accepted' : 'suggested',
            });
        } else {
            sessionStore.clearQuest();
        }
    };

    const clearAll = () => {
        sessionStore.resetSession();
    };

    return (
        <WorkContext.Provider
            value={{
                ...legacyState,
                setOutlier,
                setRecipe,
                setRun,
                setQuest,
                clearAll,
            }}
        >
            {children}
        </WorkContext.Provider>
    );
}

// ─────────────────────────────────────────────────────────────
// Hooks
// ─────────────────────────────────────────────────────────────

export function useWorkContext() {
    const context = useContext(WorkContext);
    if (!context) {
        throw new Error('useWorkContext must be used within WorkContextProvider');
    }
    return context;
}

// Optional hook that doesn't throw if outside provider (for ContextBar safety)
export function useWorkContextSafe() {
    return useContext(WorkContext);
}

