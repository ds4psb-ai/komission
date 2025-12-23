"use client";

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

/**
 * WorkContext: 페이지 간 작업 컨텍스트 유지
 * - Outlier/Recipe → Remix Detail → Canvas → My 간 연결성 제공
 */

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

const initialState: WorkContextState = {
    outlier: null,
    recipe: null,
    run: null,
    quest: null,
};

export function WorkContextProvider({ children }: { children: ReactNode }) {
    const [state, setState] = useState<WorkContextState>(initialState);

    const setOutlier = useCallback((outlier: OutlierContext | null) => {
        setState(prev => ({ ...prev, outlier }));
    }, []);

    const setRecipe = useCallback((recipe: RecipeContext | null) => {
        setState(prev => ({ ...prev, recipe }));
    }, []);

    const setRun = useCallback((run: RunContext | null) => {
        setState(prev => ({ ...prev, run }));
    }, []);

    const setQuest = useCallback((quest: QuestContext | null) => {
        setState(prev => ({ ...prev, quest }));
    }, []);

    const clearAll = useCallback(() => {
        setState(initialState);
    }, []);

    return (
        <WorkContext.Provider value={{ ...state, setOutlier, setRecipe, setRun, setQuest, clearAll }}>
            {children}
        </WorkContext.Provider>
    );
}

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
