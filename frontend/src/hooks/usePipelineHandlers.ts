"use client";

/**
 * usePipelineHandlers - Canvas Pipeline Save/Load/Export Hook
 * 
 * Extracted from canvas/page.tsx for code organization
 * Handles all persistence operations for canvas pipelines
 */

import { useCallback, useState } from 'react';
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
            showToast('캔버스가 비어있습니다!', 'error');
            return;
        }

        let title = pipelineTitle || '제목 없는 파이프라인';
        if (!pipelineId) {
            const input = window.prompt('파이프라인 이름을 입력하세요:', title);
            if (!input) return;
            title = input;
            setPipelineTitle(title);
        }

        let publicStatus = isPublic;
        if (!pipelineId) {
            publicStatus = window.confirm('이 파이프라인을 커뮤니티에 공개할까요?');
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
                showToast('파이프라인 업데이트 완료!', 'success');
            } else {
                const newPipeline = await api.savePipeline({
                    title,
                    graph_data: graphData,
                    is_public: publicStatus
                });
                setPipelineId(newPipeline.id);
                showToast('파이프라인 저장 완료!', 'success');
            }
            setIsDirty(false);
        } catch (e) {
            showToast('파이프라인 저장 실패', 'error');
            console.error(e);
        } finally {
            setIsSaving(false);
        }
    }, [nodes, pipelineId, pipelineTitle, isPublic, reactFlowInstance, showToast, requireAuth]);

    // Load list handler
    const handleLoadList = useCallback(async () => {
        setIsLoading(true);
        try {
            const list = await api.listPipelines();
            setSavedPipelines(list);
            setShowLoadModal(true);
        } catch (e) {
            showToast('파이프라인 목록 로드 실패', 'error');
        } finally {
            setIsLoading(false);
        }
    }, [showToast]);

    // Load single pipeline
    const handleLoad = useCallback(async (id: string) => {
        if (isDirty && !window.confirm('저장하지 않은 변경사항이 있습니다. 그래도 로드할까요?')) {
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
            showToast(`로드 완료: ${pipeline.title}`, 'success');
        } catch (e) {
            showToast('파이프라인 로드 실패', 'error');
        } finally {
            setIsLoading(false);
        }
    }, [setNodes, setEdges, isDirty, showToast]);

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
