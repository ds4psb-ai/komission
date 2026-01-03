"use client";

import { useTranslations } from 'next-intl';

import React, { useCallback, useRef, useState, useEffect, Suspense } from 'react';
import {
    ReactFlow,
    Controls,
    Background,
    useNodesState,
    useEdgesState,
    addEdge,
    Connection,
    Edge,
    ReactFlowProvider,
    Node,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { SourceNode, ProcessNode, OutputNode, NotebookNode, TemplateSeedNode, CrawlerOutlierNode, GuideNode } from '@/components/canvas/CustomNodes';
import { EvidenceNode, DecisionNode } from '@/components/canvas/EvidenceNodes';
import { CapsuleNode, type CapsuleDefinition } from '@/components/canvas/CapsuleNode';
import { Inspector } from '@/components/canvas/Inspector';
import { StoryboardPreview } from '@/components/canvas/StoryboardPreview';
import { CanvasSidebar } from '@/components/canvas/CanvasSidebar';
import { AppHeader } from '@/components/AppHeader';
import { SessionHUD } from '@/components/canvas/SessionHUD';
import { api, Pipeline } from '@/lib/api';
import { useUndoRedo } from '@/hooks/useUndoRedo';
import { useAuth } from '@/lib/auth';
import { useAuthGate, AUTH_ACTIONS } from '@/lib/useAuthGate';
import { OutlierSelector, type OutlierItem } from '@/components/canvas/OutlierSelector';

// Custom Node Types
const nodeTypes = {
    source: SourceNode,
    process: ProcessNode,
    output: OutputNode,
    evidence: EvidenceNode,
    decision: DecisionNode,
    capsule: CapsuleNode,
    notebook: NotebookNode,
    templateSeed: TemplateSeedNode,
    crawlerOutlier: CrawlerOutlierNode,
    guide: GuideNode,
};

// Initial Data (Empty canvas)
const initialNodes: Node[] = [];
const initialEdges: Edge[] = [];

const defaultCapsuleDefinition: CapsuleDefinition = {
    id: "capsule.evidence.v1",
    title: "Evidence Synthesizer",
    summary: "Outlier 깊이 데이터를 요약하고 실험 결론을 생성합니다.",
    provider: "Opal + NotebookLM",
    inputs: ["Parent/Outlier set", "기간", "카테고리"],
    outputs: ["EvidenceRef", "DecisionSummary"],
    params: [
        { key: "window", label: "기간", type: "select", options: ["4w", "12w", "1y"], value: "4w" },
        { key: "category", label: "카테고리", type: "select", options: ["Beauty", "Meme", "Food", "Lifestyle"], value: "Beauty" },
        { key: "risk", label: "리스크 허용", type: "select", options: ["Low", "Medium", "High"], value: "Medium" },
        { key: "syncSheets", label: "Sheets 동기화", type: "toggle", value: true },
    ],
    status: "idle",
};

const createCapsuleDefinition = (): CapsuleDefinition => ({
    ...defaultCapsuleDefinition,
    params: defaultCapsuleDefinition.params?.map((param) => ({ ...param })),
});

// Generate unique ID using UUID (fallback for older browsers)
const generateNodeId = () => {
    if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
        return `node_${crypto.randomUUID().slice(0, 8)}`;
    }
    return `node_${Math.random().toString(36).slice(2, 10)}`;
};

function CanvasFlow() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const templateId = searchParams.get('templateId');
    const sourceUrl = searchParams.get('sourceUrl');  // AI Onboarding: auto-setup from URL
    const patternId = searchParams.get('pattern');    // P0: Pattern Library injection

    const reactFlowWrapper = useRef<HTMLDivElement>(null);
    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
    const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);
    const [createdNodeId, setCreatedNodeId] = useState<string | null>(null);

    // Pipeline state
    const [pipelineId, setPipelineId] = useState<string | null>(null);
    const [pipelineTitle, setPipelineTitle] = useState<string>('');
    const [isPublic, setIsPublic] = useState<boolean>(false);
    const [isDirty, setIsDirty] = useState<boolean>(false);

    // Modal state
    const [showLoadModal, setShowLoadModal] = useState(false);
    const [savedPipelines, setSavedPipelines] = useState<Pipeline[]>([]);
    const [showOutlierSelector, setShowOutlierSelector] = useState(false);

    // Loading states
    const [isSaving, setIsSaving] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    // Inspector state
    const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
    const [showInspector, setShowInspector] = useState(true);

    // Storyboard Preview state
    const [showStoryboard, setShowStoryboard] = useState(false);

    // Canvas Mode: Simple (guide-focused) / Pro (detailed control)
    // FR-006: 모드 분리 - Simple은 가이드 중심, Pro는 상세 제어
    const [canvasMode, setCanvasMode] = useState<'simple' | 'pro'>('simple');

    // P0: Pattern Library injection state
    const [showPatternGuide, setShowPatternGuide] = useState(!!patternId);

    const selectedNode = selectedNodeId
        ? nodes.find((node) => node.id === selectedNodeId) || null
        : null;

    // Auth state for access control
    const { user } = useAuth();
    // Simple admin check - in real app, check user.role === 'admin' or specific IDs
    const isAdmin = user?.role === 'admin' || user?.email?.includes('@komission.com');

    // Toast state (simple inline implementation)
    const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);
    const toastTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const edgeTimeoutsRef = useRef<Array<ReturnType<typeof setTimeout>>>([]);
    const isMountedRef = useRef(true);

    // Auth gate for protected actions
    const { requireAuth } = useAuthGate();

    const showToast = useCallback((message: string, type: 'success' | 'error' | 'info' = 'info') => {
        if (!isMountedRef.current) return;
        setToast({ message, type });
        if (toastTimeoutRef.current) {
            clearTimeout(toastTimeoutRef.current);
        }
        toastTimeoutRef.current = setTimeout(() => setToast(null), 3000);
    }, [isMountedRef]);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
            if (toastTimeoutRef.current) {
                clearTimeout(toastTimeoutRef.current);
                toastTimeoutRef.current = null;
            }
            if (edgeTimeoutsRef.current.length > 0) {
                edgeTimeoutsRef.current.forEach(clearTimeout);
                edgeTimeoutsRef.current = [];
            }
        };
    }, []);

    // Track dirty state
    useEffect(() => {
        if (nodes.length > 0 || edges.length > 0) {
            setIsDirty(true);
        }
    }, [nodes, edges]);

    // Load Template Effect
    useEffect(() => {
        if (templateId) {
            const loadTemplate = async () => {
                if (isMountedRef.current) {
                    setIsLoading(true);
                }
                try {
                    const pipeline = await api.loadPipeline(templateId);
                    if (!isMountedRef.current) return;
                    const { nodes: loadedNodes, edges: loadedEdges } = pipeline.graph_data as any;
                    setNodes(loadedNodes || []);
                    setEdges(loadedEdges || []);
                    setPipelineTitle(`${pipeline.title} (Copy)`);
                    // Do NOT set pipelineId, so it saves as new
                    showToast(`템플릿 "${pipeline.title}" 로드 완료! 저장하면 복사본이 생성됩니다.`, 'success');
                } catch (e) {
                    console.error(e);
                    showToast('Template load failed', 'error');
                } finally {
                    if (isMountedRef.current) {
                        setIsLoading(false);
                    }
                }
            };
            loadTemplate();
        }
    }, [templateId, setNodes, setEdges, showToast, isMountedRef]);

    // AI Onboarding: Auto-setup from sourceUrl
    useEffect(() => {
        if (sourceUrl && !templateId) {
            const autoSetup = async () => {
                if (isMountedRef.current) {
                    setIsLoading(true);
                }
                showToast('🔍 AI가 영상을 분석중입니다...', 'info');

                try {
                    // Detect platform from URL
                    const platform = sourceUrl.includes('tiktok') ? 'tiktok'
                        : sourceUrl.includes('instagram') ? 'instagram'
                            : 'youtube';

                    // 1. Create Source Node in UI
                    const sourceNodeId = generateNodeId();
                    const processNodeId = generateNodeId();
                    const outputNodeId = generateNodeId();

                    // 2. Register with backend API
                    const remixNode = await api.createRemixNode({
                        title: 'AI 분석 중...',
                        source_video_url: sourceUrl,
                        platform
                    });

                    if (!isMountedRef.current) return;
                    setCreatedNodeId(remixNode.node_id);

                    // 3. Create the complete pipeline visually
                    const newNodes: Node[] = [
                        {
                            id: sourceNodeId,
                            type: 'source',
                            position: { x: 100, y: 200 },
                            data: {
                                prefillUrl: sourceUrl,
                                registered: true,
                                nodeId: remixNode.node_id
                            },
                        },
                        {
                            id: processNodeId,
                            type: 'process',
                            position: { x: 400, y: 200 },
                            data: {
                                nodeId: remixNode.node_id,
                                autoTrigger: true  // Will auto-start analysis
                            },
                        },
                        {
                            id: outputNodeId,
                            type: 'output',
                            position: { x: 700, y: 200 },
                            data: { nodeId: remixNode.node_id },
                        },
                    ];

                    const newEdges: Edge[] = [
                        {
                            id: `e-${sourceNodeId}-${processNodeId}`,
                            source: sourceNodeId,
                            target: processNodeId,
                            animated: true,
                            style: { stroke: '#a855f7', strokeWidth: 2 }
                        },
                        {
                            id: `e-${processNodeId}-${outputNodeId}`,
                            source: processNodeId,
                            target: outputNodeId,
                            animated: true,
                            style: { stroke: '#06b6d4', strokeWidth: 2 }
                        },
                    ];

                    if (isMountedRef.current) {
                        setNodes(newNodes);
                        setEdges(newEdges);
                    }

                    // 4. Auto-trigger Gemini analysis
                    showToast('⚡ Gemini 분석을 시작합니다...', 'info');
                    try {
                        await api.analyzeNode(remixNode.node_id);
                        showToast('✅ AI 분석 완료! 결과를 확인하세요.', 'success');
                    } catch (analysisError) {
                        showToast('Waiting for analysis... Click Process node.', 'info');
                    }

                    // Clear URL from browser history to prevent re-trigger
                    if (isMountedRef.current) {
                        router.replace('/canvas', { scroll: false });
                    }

                } catch (e) {
                    console.error(e);
                    showToast('URL 처리 실패. 수동으로 시도해주세요.', 'error');
                } finally {
                    if (isMountedRef.current) {
                        setIsLoading(false);
                    }
                }
            };

            autoSetup();
        }
    }, [sourceUrl, templateId, setNodes, setEdges, showToast, router, isMountedRef]);

    // History Hook
    const { takeSnapshot, undo, redo, canUndo, canRedo } = useUndoRedo();

    // Undo/Redo Handlers
    const onUndo = useCallback(() => {
        const previous = undo(nodes, edges);
        if (previous) {
            setNodes(previous.nodes);
            setEdges(previous.edges);
        }
    }, [undo, nodes, edges, setNodes, setEdges]);

    const onRedo = useCallback(() => {
        const next = redo(nodes, edges);
        if (next) {
            setNodes(next.nodes);
            setEdges(next.edges);
        }
    }, [redo, nodes, edges, setNodes, setEdges]);

    // Keyboard Shortcuts
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            // Undo/Redo
            if ((e.metaKey || e.ctrlKey) && e.key === 'z') {
                e.preventDefault();
                if (e.shiftKey) {
                    onRedo();
                } else {
                    onUndo();
                }
            }
            // ESC to close modal
            if (e.key === 'Escape' && showLoadModal) {
                setShowLoadModal(false);
            }
            // ESC to close Outlier selector
            if (e.key === 'Escape' && showOutlierSelector) {
                setShowOutlierSelector(false);
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [onUndo, onRedo, showLoadModal, showOutlierSelector]);

    // API Handlers passed to nodes
    const handleSourceSubmit = useCallback(async (url: string, title: string) => {
        try {
            const node = await api.createRemixNode({
                title,
                source_video_url: url,
                platform: url.includes('tiktok') ? 'tiktok' : url.includes('instagram') ? 'instagram' : 'youtube'
            });
            if (!isMountedRef.current) return;
            setCreatedNodeId(node.node_id);
            showToast(`소스 등록 완료: ${node.node_id}`, 'success');

            // Update nodes with the created node ID
            if (isMountedRef.current) {
                setNodes((nds) =>
                    nds.map((n) =>
                        n.type === 'process' || n.type === 'output'
                            ? { ...n, data: { ...n.data, nodeId: node.node_id } }
                            : n
                    )
                );
            }
        } catch (e) {
            showToast(e instanceof Error ? e.message : 'Node creation failed', 'error');
            throw e;
        }
    }, [setNodes, showToast, isMountedRef]);

    const handleAnalyze = useCallback(async (nodeId: string) => {
        try {
            const result = await api.analyzeNode(nodeId);
            showToast(`${nodeId} 분석 완료`, 'success');
            return result;
        } catch (e) {
            showToast(e instanceof Error ? e.message : 'Analysis failed', 'error');
            throw e;
        }
    }, [showToast]);

    // Persistence Handlers
    const handleSave = useCallback(async () => {
        // Require auth for saving
        if (!requireAuth(AUTH_ACTIONS.SAVE)) return;

        if (!nodes.length) {
            showToast('Canvas is empty!', 'error');
            return;
        }

        let title = pipelineTitle || 'Untitled Pipeline';
        if (!pipelineId) {
            const input = window.prompt('Enter pipeline name:', title);
            if (!input) return;
            title = input;
            setPipelineTitle(title);
        }

        // Only ask about public status on first save or if explicitly changing
        let publicStatus = isPublic;
        if (!pipelineId) {
            publicStatus = window.confirm('Make this pipeline public to the community?');
            setIsPublic(publicStatus);
        }

        if (isMountedRef.current) {
            setIsSaving(true);
        }
        try {
            const graphData = reactFlowInstance?.toObject();

            if (pipelineId) {
                await api.updatePipeline(pipelineId, {
                    graph_data: graphData,
                    is_public: publicStatus
                });
                showToast('Pipeline updated!', 'success');
            } else {
                const newPipeline = await api.savePipeline({
                    title,
                    graph_data: graphData,
                    is_public: publicStatus
                });
                if (!isMountedRef.current) return;
                setPipelineId(newPipeline.id);
                showToast('Pipeline saved!', 'success');
            }
            if (isMountedRef.current) {
                setIsDirty(false);
            }
        } catch (e) {
            showToast('Pipeline save failed', 'error');
            console.error(e);
        } finally {
            if (isMountedRef.current) {
                setIsSaving(false);
            }
        }
    }, [nodes, pipelineId, pipelineTitle, isPublic, reactFlowInstance, showToast, requireAuth, isMountedRef]);

    const handleLoadList = useCallback(async () => {
        if (isMountedRef.current) {
            setIsLoading(true);
        }
        try {
            const list = await api.listPipelines();
            if (!isMountedRef.current) return;
            setSavedPipelines(list);
            setShowLoadModal(true);
        } catch (e) {
            showToast('Pipeline list load failed', 'error');
        } finally {
            if (isMountedRef.current) {
                setIsLoading(false);
            }
        }
    }, [showToast, isMountedRef]);

    const handleLoad = useCallback(async (id: string) => {
        // Confirm if canvas has unsaved changes
        if (isDirty && !window.confirm('You have unsaved changes. Load anyway?')) {
            return;
        }

        if (isMountedRef.current) {
            setIsLoading(true);
        }
        try {
            const pipeline = await api.loadPipeline(id);
            if (!isMountedRef.current) return;
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
            showToast('Pipeline load failed', 'error');
        } finally {
            if (isMountedRef.current) {
                setIsLoading(false);
            }
        }
    }, [setNodes, setEdges, isDirty, showToast, isMountedRef]);

    const handleExport = useCallback((nodeId: string) => {
        router.push(`/remix/${nodeId}`);
    }, [router]);

    const onConnect = useCallback(
        (params: Connection) => {
            takeSnapshot(nodes, edges);
            setEdges((eds) => addEdge({ ...params, animated: true, style: { stroke: '#fff', strokeWidth: 2 } }, eds));
        },
        [setEdges, takeSnapshot, nodes, edges],
    );

    const onDragOver = useCallback((event: React.DragEvent) => {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
    }, []);

    // Add node - with Outlier support
    const addNode = useCallback((type: string, position?: { x: number; y: number }, data?: any) => {
        // Require auth for adding nodes
        if (!requireAuth(AUTH_ACTIONS.ADD_NODE)) return;

        takeSnapshot(nodes, edges);

        const finalPosition = position || { x: 300 + nodes.length * 50, y: 150 + nodes.length * 50 };

        const newNode: Node = {
            id: data?.forceId || generateNodeId(),
            type: type === 'outlier' ? 'source' : type === 'crawlerOutlier' ? 'crawlerOutlier' : type,
            position: finalPosition,
            data: {
                ...(type === 'source' && { onSubmit: handleSourceSubmit }), // Normal URL input
                ...(type === 'outlier' && {
                    outlier: data,
                    // Expert Recommendation: Governance Lock for Master nodes
                    isLocked: data?.layer === 'master',
                    viralBadge: data?.performance_delta || undefined,
                }), // Pre-filled outlier data
                ...(type === 'process' && { onAnalyze: handleAnalyze, nodeId: createdNodeId }),
                ...(type === 'output' && { onExport: handleExport, nodeId: createdNodeId, onPreview: () => setShowStoryboard(true) }),
                ...(type === 'evidence' && {
                    nodeId: createdNodeId || undefined,  // Pass real nodeId for API calls
                    evidence: data?.evidence,
                }),
                ...(type === 'capsule' && {
                    capsule: createCapsuleDefinition(),
                    onComplete: (guideData: any) => {
                        const guideId = generateNodeId();
                        const guidePos = { x: finalPosition.x + 400, y: finalPosition.y };
                        addNode('guide', guidePos, { ...guideData, forceId: guideId });

                        // Connect Capsule -> Guide
                        const timeoutId = setTimeout(() => {
                            setEdges((eds) => addEdge({
                                id: `e_${newNode.id}-${guideId}`,
                                source: newNode.id,
                                target: guideId,
                                animated: true,
                                style: { stroke: '#06b6d4', strokeWidth: 2 }
                            } as any, eds));
                            showToast('✨ Guide Node가 자동 생성되었습니다.', 'success');
                            edgeTimeoutsRef.current = edgeTimeoutsRef.current.filter(id => id !== timeoutId);
                        }, 100);
                        edgeTimeoutsRef.current.push(timeoutId);
                    }
                }),
                ...(type === 'guide' && {
                    ...data
                }),
                ...(type === 'notebook' && {
                    summary: data?.summary || '훅/씬/오디오 패턴 요약을 여기에 표시합니다.',
                    clusterId: data?.clusterId || 'Hook-2s-TextPunch',
                    sourceUrl: data?.sourceUrl,
                }),
                ...(type === 'decision' && {
                    status: 'pending' as const,
                    onGenerateDecision: async () => {
                        // Step 1: Set to generating state
                        if (isMountedRef.current) {
                            setNodes(nds => nds.map(n => {
                                if (n.id === newNode.id) {
                                    return {
                                        ...n,
                                        data: { ...n.data, status: 'generating' }
                                    };
                                }
                                return n;
                            }));
                        }

                        // Step 2: Call Opal API via template-seeds/generate
                        try {
                            const response = await api.generateTemplateSeed({
                                parent_id: createdNodeId || undefined,
                                template_type: 'guide',
                            });

                            if (response.success && response.seed) {
                                if (isMountedRef.current) {
                                    setNodes(nds => nds.map(n => {
                                        if (n.id === newNode.id) {
                                            return {
                                                ...n,
                                                data: {
                                                    ...n.data,
                                                    status: 'decided',
                                                    decision: {
                                                        conclusion: `${response.seed?.seed_params?.hook || 'AI 생성'} 기반 실험 제안`,
                                                        rationale: [
                                                            "Top performing hook pattern identified",
                                                            "Aligned with retention metrics (+15%)",
                                                            "Category benchmark surpassed in initial tests"
                                                        ],
                                                        experiment: {
                                                            id: response.seed?.seed_id || `exp_${Date.now()}`,
                                                            target_metric: "CTR",
                                                            variants: [
                                                                { name: "Control", mutation: "Original (변경 없음)" },
                                                                { name: "Test A", mutation: response.seed?.seed_params?.shotlist?.[0] || "AI 제안" },
                                                                { name: "Test B", mutation: response.seed?.seed_params?.shotlist?.[1] || "AI 변형" }
                                                            ]
                                                        },
                                                        confidence: 0.85,
                                                        seed: response.seed
                                                    }
                                                }
                                            };
                                        }
                                        return n;
                                    }));
                                }
                                showToast('✅ Opal: 실험 계획 생성 완료!', 'success');
                            } else {
                                throw new Error(response.error || 'Generation failed');
                            }
                        } catch (error) {
                            console.error('Opal generation failed:', error);
                            // Fallback to mock data on error
                            if (isMountedRef.current) {
                                setNodes(nds => nds.map(n => {
                                    if (n.id === newNode.id) {
                                        return {
                                            ...n,
                                            data: {
                                                ...n.data,
                                                status: 'decided',
                                                decision: {
                                                    conclusion: "API 오류로 기본 실험 계획을 표시합니다.",
                                                    rationale: [
                                                        "Service temporarily unavailable",
                                                        "Fallback to safe-mode experiment templates",
                                                        "Manual review recommended"
                                                    ],
                                                    experiment: {
                                                        id: `exp_${Date.now()}`,
                                                        target_metric: "CTR",
                                                        variants: [
                                                            { name: "Control", mutation: "Original (변경 없음)" },
                                                            { name: "Test A", mutation: "Hook 강화 (0-3초)" },
                                                        ]
                                                    },
                                                    confidence: 0.5
                                                }
                                            }
                                        };
                                    }
                                    return n;
                                }));
                            }
                            showToast('⚠️ API 오류: 기본 계획으로 대체', 'error');
                        }
                    }
                }),
            },
        };

        setNodes((nds) => nds.concat(newNode));

        if (type === 'outlier') {
            setCreatedNodeId(data.id || data.node_id);
            showToast(`선택된 노드: ${data.title}`, 'success');
        }
    }, [setNodes, handleSourceSubmit, handleAnalyze, handleExport, createdNodeId, nodes, edges, takeSnapshot, showToast, isMountedRef]);

    const onDrop = useCallback(
        (event: React.DragEvent) => {
            event.preventDefault();

            const type = event.dataTransfer.getData('application/reactflow');
            if (!type) return;

            const position = reactFlowInstance?.screenToFlowPosition({
                x: event.clientX,
                y: event.clientY,
            });

            if (type === 'outlier') {
                // If dropping 'outlier', we shouldn't have gotten here mainly because standard drag source
                // just opens the modal. But if we implemented drag from sidebar, it would go here.
                // For now, let's just ignore or handle safely.
                return;
            }

            addNode(type, position);
        },
        [reactFlowInstance, addNode],
    );

    const onNodeDragStart = useCallback(() => {
        takeSnapshot(nodes, edges);
    }, [takeSnapshot, nodes, edges]);

    const handleOutlierSelect = (item: OutlierItem) => {
        // Unified handler: add outlier node with all data
        addNode('outlier', undefined, {
            id: item.id,
            title: item.title,
            platform: item.platform,
            video_url: item.video_url,
            thumbnail_url: item.thumbnail_url,
            view_count: item.view_count,
            tier: item.tier,
            vdg_analysis: item.vdg_analysis,
        });
        setShowOutlierSelector(false);
    };

    // Modal backdrop click handler
    const handleModalBackdropClick = useCallback((e: React.MouseEvent) => {
        if (e.target === e.currentTarget) {
            setShowLoadModal(false);
        }
    }, []);

    // Delete node handler
    const handleDeleteNode = useCallback((nodeId: string) => {
        console.log('handleDeleteNode called for:', nodeId);
        try {
            takeSnapshot(nodes, edges);
            console.log('Snapshot taken');
            setNodes((nds) => {
                const filtered = nds.filter((node) => node.id !== nodeId);
                console.log('Nodes after filter:', filtered.length);
                return filtered;
            });
            setEdges((eds) => {
                const filtered = eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId);
                console.log('Edges after filter:', filtered.length);
                return filtered;
            });
            setSelectedNodeId(null);
            showToast('Node deleted', 'info');
        } catch (err) {
            console.error('Error in handleDeleteNode:', err);
            showToast('Node deletion failed', 'error');
        }
    }, [setNodes, setEdges, takeSnapshot, nodes, edges, showToast]);

    const handleUpdateNodeData = useCallback((nodeId: string, patch: Record<string, unknown>) => {
        setNodes((nds) =>
            nds.map((node) =>
                node.id === nodeId
                    ? { ...node, data: { ...(node.data || {}), ...patch } }
                    : node
            )
        );
    }, [setNodes]);

    return (
        <div className="flex flex-col h-screen bg-[#050505] selection:bg-violet-500/30 selection:text-violet-200 overflow-hidden relative">
            {/* Aurora Background removed - Phase 5: Production tools should prioritize information density */}

            {/* Global Header */}
            <AppHeader />

            {/* Session HUD - Progress Tracker */}
            <SessionHUD nodes={nodes} canvasMode={canvasMode} />

            <div className="flex flex-1 overflow-hidden relative">
                {/* Toast Notification */}
                {toast && (
                    <div className={`fixed bottom-6 right-6 z-[9999] px-4 py-3 rounded-xl shadow-2xl flex items-center gap-3 animate-pulse ${toast.type === 'success' ? 'bg-emerald-500/90 text-white' :
                        toast.type === 'error' ? 'bg-red-500/90 text-white' :
                            'bg-blue-500/90 text-white'
                        }`}>
                        <span className="text-lg">
                            {toast.type === 'success' ? '✓' : toast.type === 'error' ? '✕' : 'ℹ'}
                        </span>
                        <span className="font-medium text-sm">{toast.message}</span>
                    </div>
                )}

                {/* Sidebar (Left Panel) */}
                <CanvasSidebar
                    canvasMode={canvasMode}
                    setCanvasMode={setCanvasMode}
                    pipelineTitle={pipelineTitle}
                    pipelineId={pipelineId}
                    isPublic={isPublic}
                    setIsPublic={setIsPublic}
                    isDirty={isDirty}
                    isSaving={isSaving}
                    isLoading={isLoading}
                    patternId={patternId}
                    showPatternGuide={showPatternGuide}
                    setShowPatternGuide={setShowPatternGuide}
                    isAdmin={isAdmin ?? false}
                    createdNodeId={createdNodeId}
                    canUndo={canUndo}
                    canRedo={canRedo}
                    onUndo={onUndo}
                    onRedo={onRedo}
                    addNode={addNode}
                    setShowOutlierSelector={setShowOutlierSelector}
                    handleSave={handleSave}
                    handleLoadList={handleLoadList}
                    showToast={showToast}
                />

                {/* Main Canvas */}
                <div className="flex-1 h-full relative" ref={reactFlowWrapper}>
                    <ReactFlow
                        nodes={nodes}
                        edges={edges}
                        onNodesChange={onNodesChange}
                        onEdgesChange={onEdgesChange}
                        onConnect={onConnect}
                        onInit={(instance) => setReactFlowInstance(instance)}
                        onDrop={onDrop}
                        onDragOver={onDragOver}
                        onNodeDragStart={onNodeDragStart}
                        onNodeClick={(_, node) => setSelectedNodeId(node.id)}
                        onPaneClick={() => setSelectedNodeId(null)}
                        nodeTypes={nodeTypes}
                        fitView
                        fitViewOptions={{ maxZoom: 0.8, padding: 0.2 }}
                        minZoom={0.3}
                        maxZoom={2}
                        defaultViewport={{ x: 0, y: 0, zoom: 0.75 }}
                        className="bg-transparent"
                        colorMode="dark"
                    >
                        <Background color="rgba(255, 255, 255, 0.1)" gap={20} size={1} />
                        <Controls className="bg-white/10 border border-white/10 rounded-lg !fill-white" />
                    </ReactFlow>
                </div>

                {/* Inspector Panel (Right) */}
                {showInspector && (
                    <Inspector
                        selectedNode={selectedNode}
                        onClose={() => setShowInspector(false)}
                        onDeleteNode={handleDeleteNode}
                        onUpdateNodeData={handleUpdateNodeData}
                        viralData={(() => {
                            const outlier = (selectedNode?.data as Record<string, unknown>)?.outlier as Record<string, unknown> | undefined;
                            if (!outlier) return undefined;
                            return {
                                performanceDelta: (outlier.performance_delta as string) || ((selectedNode?.data as Record<string, unknown>)?.viralBadge as string) || undefined,
                                parentViews: (outlier.view_count as number) || 0,
                                genealogyDepth: (outlier.genealogy_depth as number) ?? 0,
                                forkCount: (outlier.fork_count as number) || 0
                            };
                        })()}
                    />
                )}
            </div>

            {/* Storyboard Preview Modal */}
            <StoryboardPreview
                nodeId={createdNodeId || undefined}
                isOpen={showStoryboard}
                onClose={() => setShowStoryboard(false)}
            />

            {/* Outlier Selector Modal */}
            {showOutlierSelector && (
                <OutlierSelector
                    onSelect={handleOutlierSelect}
                    onClose={() => setShowOutlierSelector(false)}
                />
            )}

            {/* Load Pipeline Modal */}
            {showLoadModal && (
                <div
                    className="absolute inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
                    onClick={handleModalBackdropClick}
                >
                    <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6 w-[400px] max-h-[80vh] flex flex-col shadow-2xl">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-lg font-bold text-white">내 파이프라인</h2>
                            <button
                                onClick={() => setShowLoadModal(false)}
                                className="text-white/40 hover:text-white text-xl"
                                title="닫기 (ESC)"
                            >
                                ✕
                            </button>
                        </div>

                        <div className="flex-1 overflow-y-auto space-y-2 mb-4">
                            {savedPipelines.length === 0 ? (
                                <p className="text-white/30 text-center py-8">저장된 파이프라인이 없습니다.</p>
                            ) : (
                                savedPipelines.map((p) => (
                                    <div
                                        key={p.id}
                                        onClick={() => handleLoad(p.id)}
                                        className="p-3 bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/20 rounded-lg cursor-pointer transition-all group"
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="text-sm font-bold text-white group-hover:text-emerald-400">{p.title}</div>
                                            {p.is_public && <span className="text-xs text-violet-400">🌐</span>}
                                        </div>
                                        <div className="text-xs text-white/30">{new Date(p.updated_at).toLocaleString()}</div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default function CanvasPage() {
    return (
        <ReactFlowProvider>
            <Suspense fallback={
                <div className="flex h-screen items-center justify-center bg-black text-white/50">
                    <div className="text-center">
                        <div className="text-4xl mb-4 animate-pulse">⚡</div>
                        <p>Loading Canvas...</p>
                    </div>
                </div>
            }>
                <CanvasFlow />
            </Suspense>
        </ReactFlowProvider>
    );
}
