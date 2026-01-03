"use client";

/**
 * usePipelineHandlers - Canvas Pipeline Save/Load/Export Hook
 * 
 * Extracted from canvas/page.tsx for code organization
 * Handles all persistence operations for canvas pipelines
 */

import { useCallback, useState } from 'react';
import { useTranslations } from 'next-intl';
import { api, Pipeline } from '@/lib/api';
import { useAuthGate, AUTH_ACTIONS } from '@/lib/useAuthGate';
import { Node, Edge } from '@xyflow/react';

export interface PipelineState {
    pipelineId: string | null;
    pipelineTitle: string;
    isPublic: boolean;
    isDirty: boolean;
    isSaving: boolean;
    isLoading: boolean;
    showLoadModal: boolean;
    savedPipelines: Pipeline[];
}

export interface UsePipelineHandlersProps {
    nodes: Node[];
    edges: Edge[];
    setNodes: (nodes: Node[] | ((nodes: Node[]) => Node[])) => void;
    setEdges: (edges: Edge[] | ((edges: Edge[]) => Edge[])) => void;
    reactFlowInstance: any;
    showToast: (message: string, type: 'success' | 'error' | 'info') => void;
    onNavigate: (path: string) => void;
}

export function usePipelineHandlers({
    nodes,
    setNodes,
    setEdges,
    reactFlowInstance,
    showToast,
    onNavigate,
}: UsePipelineHandlersProps) {
    const t = useTranslations('components.pipeline');

    // Pipeline state
    const [pipelineId, setPipelineId] = useState<string | null>(null);
    const [pipelineTitle, setPipelineTitle] = useState<string>('');
    const [isPublic, setIsPublic] = useState<boolean>(false);
    const [isDirty, setIsDirty] = useState<boolean>(false);

    // Loading states
    const [isSaving, setIsSaving] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    // Modal state
    const [showLoadModal, setShowLoadModal] = useState(false);
    const [savedPipelines, setSavedPipelines] = useState<Pipeline[]>([]);

    // Auth gate
    const { requireAuth } = useAuthGate();

    // Save handler
    const handleSave = useCallback(async () => {
        if (!requireAuth(AUTH_ACTIONS.SAVE)) return;

        if (!nodes.length) {
            showToast(t('emptyCanvas'), 'error');
            return;
        }

        let title = pipelineTitle || t('untitled');
        if (!pipelineId) {
            const input = window.prompt(t('enterName'), title);
            if (!input) return;
            title = input;
            setPipelineTitle(title);
        }

        let publicStatus = isPublic;
        if (!pipelineId) {
            publicStatus = window.confirm(t('confirmPublic'));
            setIsPublic(publicStatus);
        }

        setIsSaving(true);
        try {
            const graphData = reactFlowInstance?.toObject();

            if (pipelineId) {
                await api.updatePipeline(pipelineId, {
                    graph_data: graphData,
                    is_public: publicStatus
                });
                showToast(t('updateSuccess'), 'success');
            } else {
                const newPipeline = await api.savePipeline({
                    title,
                    graph_data: graphData,
                    is_public: publicStatus
                });
                setPipelineId(newPipeline.id);
                showToast(t('saveSuccess'), 'success');
            }
            setIsDirty(false);
        } catch (e) {
            showToast(t('saveFail'), 'error');
            console.error(e);
        } finally {
            setIsSaving(false);
        }
    }, [nodes, pipelineId, pipelineTitle, isPublic, reactFlowInstance, showToast, requireAuth, t]);

    // Load list handler
    const handleLoadList = useCallback(async () => {
        setIsLoading(true);
        try {
            const list = await api.listPipelines();
            setSavedPipelines(list);
            setShowLoadModal(true);
        } catch (e) {
            showToast(t('loadListFail'), 'error');
        } finally {
            setIsLoading(false);
        }
    }, [showToast, t]);

    // Load single pipeline
    const handleLoad = useCallback(async (id: string) => {
        if (isDirty && !window.confirm(t('confirmLoad'))) {
            return;
        }

        setIsLoading(true);
        try {
            const pipeline = await api.loadPipeline(id);
            const { nodes: loadedNodes, edges: loadedEdges } = pipeline.graph_data as any;

            setNodes(loadedNodes || []);
            setEdges(loadedEdges || []);
            setPipelineId(pipeline.id);
            setPipelineTitle(pipeline.title);
            setIsPublic(pipeline.is_public);
            setShowLoadModal(false);
            setIsDirty(false);
            showToast(`${t('loadSuccess')}: ${pipeline.title}`, 'success');
        } catch (e) {
            showToast(t('loadFail'), 'error');
        } finally {
            setIsLoading(false);
        }
    }, [setNodes, setEdges, isDirty, showToast, t]);

    // Export handler
    const handleExport = useCallback((nodeId: string) => {
        onNavigate(`/remix/${nodeId}`);
    }, [onNavigate]);

    // Close load modal
    const closeLoadModal = useCallback(() => {
        setShowLoadModal(false);
    }, []);

    // Mark as dirty
    const markDirty = useCallback(() => {
        setIsDirty(true);
    }, []);

    return {
        // State
        pipelineId,
        pipelineTitle,
        isPublic,
        isDirty,
        isSaving,
        isLoading,
        showLoadModal,
        savedPipelines,

        // Setters
        setPipelineId,
        setPipelineTitle,
        setIsPublic,
        setIsDirty,

        // Handlers
        handleSave,
        handleLoadList,
        handleLoad,
        handleExport,
        closeLoadModal,
        markDirty,
    };
}
