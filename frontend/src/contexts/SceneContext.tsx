"use client";

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

/**
 * Scene synchronization context for canvas-outlier integration
 * 
 * This context enables:
 * 1. Shared selected node between canvas and main page
 * 2. Synchronized timestamp for scene highlighting
 * 3. Gemini analysis data sharing
 */

export interface TimeSegment {
    start_time: number;
    end_time: number;
    description: string;
    visual_tags: string[];
    audio_tags: string[];
    viral_score: number;
}

export interface ViralHook {
    timestamp: number;
    hook_type: string;
    description: string;
}

export interface GeminiAnalysis {
    metadata?: {
        music_drop_timestamps?: number[];
        bpm?: number;
        mood?: string;
    };
    visual_dna?: {
        setting_description?: string;
        color_palette?: string[];
    };
    commerce_context?: {
        primary_category?: string;
        keywords?: string[];
    };
    meme_dna?: {
        key_action?: string;
        catchphrase?: string;
    };
    // Advanced Temporal Data
    timeline?: TimeSegment[];
    viral_hooks?: ViralHook[];
    virality_score?: number;
    imitability_level?: string;
}

interface SceneState {
    // Selected node ID
    selectedNodeId: string | null;

    // Current playback/hover timestamp
    currentTimestamp: number;

    // Selected drop index from music_drop_timestamps
    selectedDropIndex: number | null;

    // Gemini analysis for current selection
    geminiAnalysis: GeminiAnalysis | null;

    // Canvas visibility
    isCanvasOpen: boolean;
}

interface SceneContextType extends SceneState {
    // Actions
    selectNode: (nodeId: string, analysis?: GeminiAnalysis) => void;
    setTimestamp: (timestamp: number) => void;
    selectDrop: (index: number | null) => void;
    setGeminiAnalysis: (analysis: GeminiAnalysis | null) => void;
    openCanvas: (nodeId?: string) => void;
    closeCanvas: () => void;
    reset: () => void;
}

const initialState: SceneState = {
    selectedNodeId: null,
    currentTimestamp: 0,
    selectedDropIndex: null,
    geminiAnalysis: null,
    isCanvasOpen: false,
};

const SceneContext = createContext<SceneContextType | null>(null);

export function SceneProvider({ children }: { children: ReactNode }) {
    const [state, setState] = useState<SceneState>(initialState);

    const selectNode = useCallback((nodeId: string, analysis?: GeminiAnalysis) => {
        setState(prev => ({
            ...prev,
            selectedNodeId: nodeId,
            geminiAnalysis: analysis || prev.geminiAnalysis,
            currentTimestamp: 0,
            selectedDropIndex: null,
        }));
    }, []);

    const setTimestamp = useCallback((timestamp: number) => {
        setState(prev => ({ ...prev, currentTimestamp: timestamp }));
    }, []);

    const selectDrop = useCallback((index: number | null) => {
        setState(prev => {
            const drops = prev.geminiAnalysis?.metadata?.music_drop_timestamps || [];
            const timestamp = index !== null && drops[index] ? drops[index] : prev.currentTimestamp;
            return {
                ...prev,
                selectedDropIndex: index,
                currentTimestamp: timestamp,
            };
        });
    }, []);

    const setGeminiAnalysis = useCallback((analysis: GeminiAnalysis | null) => {
        setState(prev => ({ ...prev, geminiAnalysis: analysis }));
    }, []);

    const openCanvas = useCallback((nodeId?: string) => {
        setState(prev => ({
            ...prev,
            isCanvasOpen: true,
            selectedNodeId: nodeId || prev.selectedNodeId,
        }));
    }, []);

    const closeCanvas = useCallback(() => {
        setState(prev => ({ ...prev, isCanvasOpen: false }));
    }, []);

    const reset = useCallback(() => {
        setState(initialState);
    }, []);

    const value: SceneContextType = {
        ...state,
        selectNode,
        setTimestamp,
        selectDrop,
        setGeminiAnalysis,
        openCanvas,
        closeCanvas,
        reset,
    };

    return (
        <SceneContext.Provider value={value}>
            {children}
        </SceneContext.Provider>
    );
}

export function useScene() {
    const context = useContext(SceneContext);
    if (!context) {
        throw new Error('useScene must be used within a SceneProvider');
    }
    return context;
}

export function useSceneOptional() {
    return useContext(SceneContext);
}

export default SceneContext;
