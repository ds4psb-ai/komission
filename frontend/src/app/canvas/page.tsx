"use client";

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
import { PatternGuidePanel } from '@/components/canvas/PatternGuidePanel';
import { AppHeader } from '@/components/AppHeader';
import { SessionHUD } from '@/components/canvas/SessionHUD';
import { api, Pipeline } from '@/lib/api';
import { useUndoRedo } from '@/hooks/useUndoRedo';
import { useAuth } from '@/lib/auth';
import { useAuthGate, AUTH_ACTIONS } from '@/lib/useAuthGate';
import { OutlierSelector, type OutlierItem } from '@/components/canvas/OutlierSelector';
import { Video, Lock, Dna, Brain, BarChart3, Scale, Clapperboard, MapPin, FileText } from 'lucide-react';

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

// Generate unique ID using UUID
const generateNodeId = () => `node_${crypto.randomUUID().slice(0, 8)}`;

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

    // Auth gate for protected actions
    const { requireAuth } = useAuthGate();

    const showToast = useCallback((message: string, type: 'success' | 'error' | 'info' = 'info') => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 3000);
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
                setIsLoading(true);
                try {
                    const pipeline = await api.loadPipeline(templateId);
                    const { nodes: loadedNodes, edges: loadedEdges } = pipeline.graph_data as any;
                    setNodes(loadedNodes || []);
                    setEdges(loadedEdges || []);
                    setPipelineTitle(`${pipeline.title} (Copy)`);
                    // Do NOT set pipelineId, so it saves as new
                    showToast(`템플릿 "${pipeline.title}" 로드 완료! 저장하면 복사본이 생성됩니다.`, 'success');
                } catch (e) {
                    console.error(e);
                    showToast('템플릿 로드 실패', 'error');
                } finally {
                    setIsLoading(false);
                }
            };
            loadTemplate();
        }
    }, [templateId, setNodes, setEdges, showToast]);

    // AI Onboarding: Auto-setup from sourceUrl
    useEffect(() => {
        if (sourceUrl && !templateId) {
            const autoSetup = async () => {
                setIsLoading(true);
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

                    setNodes(newNodes);
                    setEdges(newEdges);

                    // 4. Auto-trigger Gemini analysis
                    showToast('⚡ Gemini 분석을 시작합니다...', 'info');
                    try {
                        await api.analyzeNode(remixNode.node_id);
                        showToast('✅ AI 분석 완료! 결과를 확인하세요.', 'success');
                    } catch (analysisError) {
                        showToast('분석 완료 대기 중... Process 노드를 클릭하세요.', 'info');
                    }

                    // Clear URL from browser history to prevent re-trigger
                    router.replace('/canvas', { scroll: false });

                } catch (e) {
                    console.error(e);
                    showToast('URL 처리 실패. 수동으로 시도해주세요.', 'error');
                } finally {
                    setIsLoading(false);
                }
            };

            autoSetup();
        }
    }, [sourceUrl, templateId, setNodes, setEdges, showToast, router]);

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
            setCreatedNodeId(node.node_id);
            showToast(`소스 등록 완료: ${node.node_id}`, 'success');

            // Update nodes with the created node ID
            setNodes((nds) =>
                nds.map((n) =>
                    n.type === 'process' || n.type === 'output'
                        ? { ...n, data: { ...n.data, nodeId: node.node_id } }
                        : n
                )
            );
        } catch (e) {
            showToast(e instanceof Error ? e.message : '노드 생성 실패', 'error');
            throw e;
        }
    }, [setNodes, showToast]);

    const handleAnalyze = useCallback(async (nodeId: string) => {
        try {
            const result = await api.analyzeNode(nodeId);
            showToast(`${nodeId} 분석 완료`, 'success');
            return result;
        } catch (e) {
            showToast(e instanceof Error ? e.message : '분석 실패', 'error');
            throw e;
        }
    }, [showToast]);

    // Persistence Handlers
    const handleSave = useCallback(async () => {
        // Require auth for saving
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

        // Only ask about public status on first save or if explicitly changing
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
    }, [nodes, pipelineId, pipelineTitle, isPublic, reactFlowInstance, showToast]);

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

    const handleLoad = useCallback(async (id: string) => {
        // Confirm if canvas has unsaved changes
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
                        setTimeout(() => {
                            setEdges((eds) => addEdge({
                                id: `e_${newNode.id}-${guideId}`,
                                source: newNode.id,
                                target: guideId,
                                animated: true,
                                style: { stroke: '#06b6d4', strokeWidth: 2 }
                            } as any, eds));
                            showToast('✨ Guide Node가 자동 생성되었습니다.', 'success');
                        }, 100);
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
                        setNodes(nds => nds.map(n => {
                            if (n.id === newNode.id) {
                                return {
                                    ...n,
                                    data: { ...n.data, status: 'generating' }
                                };
                            }
                            return n;
                        }));

                        // Step 2: Call Opal API via template-seeds/generate
                        try {
                            const response = await api.generateTemplateSeed({
                                parent_id: createdNodeId || undefined,
                                template_type: 'guide',
                            });

                            if (response.success && response.seed) {
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
                                showToast('✅ Opal: 실험 계획 생성 완료!', 'success');
                            } else {
                                throw new Error(response.error || 'Generation failed');
                            }
                        } catch (error) {
                            console.error('Opal generation failed:', error);
                            // Fallback to mock data on error
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
    }, [setNodes, handleSourceSubmit, handleAnalyze, handleExport, createdNodeId, nodes, edges, takeSnapshot, showToast]);

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
            showToast('노드 삭제됨', 'info');
        } catch (err) {
            console.error('Error in handleDeleteNode:', err);
            showToast('노드 삭제 실패', 'error');
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
                <aside className="w-72 flex flex-col z-20 glass-panel border-y-0 border-l-0 border-r border-white/10 p-5 backdrop-blur-2xl bg-black/40">
                    <div className="mb-8">
                        <div className="text-xs font-bold text-violet-400 uppercase tracking-widest mb-1">캔버스 모드</div>
                        <h2 className="text-xl font-bold text-white flex items-center gap-2">
                            <span className="text-2xl">⚡</span>
                            파이프라인
                        </h2>
                        {pipelineTitle && (
                            <p className="text-xs text-emerald-400 mt-2 truncate border border-emerald-500/30 rounded px-2 py-1 bg-emerald-500/10">📝 {pipelineTitle}</p>
                        )}

                        {/* Mode Toggle - Simple/Pro */}
                        <div className="mt-4 flex items-center gap-2 p-2 bg-white/5 rounded-lg border border-white/10">
                            <button
                                onClick={() => {
                                    setCanvasMode('simple');
                                    showToast('🎯 Simple 모드: 핵심 노드만 표시', 'info');
                                }}
                                className={`flex-1 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${canvasMode === 'simple'
                                    ? 'bg-emerald-500 text-white'
                                    : 'text-white/60 hover:text-white hover:bg-white/10'
                                    }`}
                            >
                                🎯 Simple
                            </button>
                            <button
                                onClick={() => {
                                    setCanvasMode('pro');
                                    showToast('⚙️ Pro 모드: 모든 노드 사용 가능', 'info');
                                }}
                                className={`flex-1 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${canvasMode === 'pro'
                                    ? 'bg-violet-500 text-white'
                                    : 'text-white/60 hover:text-white hover:bg-white/10'
                                    }`}
                            >
                                ⚙️ Pro
                            </button>
                        </div>
                        <p className="text-[10px] text-white/40 mt-2">
                            {canvasMode === 'simple' ? '가이드 중심 모드 - 핵심 노드만 표시' : 'Pro 모드 - 모든 노드 및 상세 제어'}
                        </p>
                    </div>

                    {/* P0: Pattern Guide Panel - displays when ?pattern= is in URL */}
                    {patternId && showPatternGuide && (
                        <div className="mb-4">
                            <PatternGuidePanel
                                patternId={patternId}
                                onClose={() => setShowPatternGuide(false)}
                            />
                        </div>
                    )}

                    <div className="space-y-6">
                        {/* Nodes Section */}
                        <div>
                            <h3 className="text-xs font-bold text-white/40 uppercase mb-3 tracking-wider">입력 소스</h3>

                            {/* Restricted Media Source (Admin Only) */}
                            {isAdmin ? (
                                <div
                                    className="p-3 bg-white/5 border border-white/10 rounded-xl cursor-pointer hover:bg-white/10 hover:border-emerald-500/50 transition-all mb-2 flex items-center gap-3"
                                    onDragStart={(event) => event.dataTransfer.setData('application/reactflow', 'source')}
                                    onClick={() => addNode('source')}
                                    draggable
                                >
                                    <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center text-emerald-400"><Video className="w-4 h-4" /></div>
                                    <span className="text-sm font-bold">미디어 소스</span>
                                </div>
                            ) : (
                                <div className="p-3 bg-white/5 border border-white/5 rounded-xl mb-2 flex items-center gap-3 opacity-50 cursor-not-allowed" title="관리자 전용">
                                    <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center text-white/30"><Lock className="w-4 h-4" /></div>
                                    <span className="text-sm font-bold text-white/30">새 미디어 (관리자)</span>
                                </div>
                            )}

                            {/* Outlier Node (Public) */}
                            <div
                                className="p-3 bg-gradient-to-r from-violet-500/10 to-pink-500/10 border border-violet-500/20 rounded-xl cursor-pointer hover:border-violet-500/50 transition-all mb-2 flex items-center gap-3"
                                onClick={() => setShowOutlierSelector(true)}
                                draggable={false}
                            >
                                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500/20 to-pink-500/20 flex items-center justify-center text-white"><Dna className="w-4 h-4" /></div>
                                <div>
                                    <span className="text-sm font-bold text-white">아웃라이어 노드</span>
                                    <div className="text-[10px] text-violet-300">바이럴 히트에서 시작</div>
                                </div>
                            </div>
                        </div>

                        {/* Core Tools - Always Visible */}
                        <div>
                            <h3 className="text-xs font-bold text-white/40 uppercase mb-3 tracking-wider">핵심 도구</h3>
                            <div
                                className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl cursor-pointer hover:border-rose-500/50 transition-all mb-2 flex items-center gap-3"
                                onDragStart={(event) => event.dataTransfer.setData('application/reactflow', 'capsule')}
                                onClick={() => addNode('capsule')}
                                draggable
                            >
                                <div className="w-8 h-8 rounded-lg bg-rose-500/20 flex items-center justify-center text-rose-400"><Lock className="w-4 h-4" /></div>
                                <div>
                                    <span className="text-sm font-bold">Capsule Node</span>
                                    <div className="text-[10px] text-rose-300">가이드 생성 (AI)</div>
                                </div>
                            </div>
                        </div>

                        {/* Pro Mode Only: AI 프로세서 */}
                        {canvasMode === 'pro' && (
                            <div>
                                <h3 className="text-xs font-bold text-white/40 uppercase mb-3 tracking-wider">프로세서</h3>
                                <div
                                    className="p-3 bg-white/5 border border-white/10 rounded-xl cursor-pointer hover:bg-white/10 hover:border-violet-500/50 transition-all mb-2 flex items-center gap-3"
                                    onDragStart={(event) => event.dataTransfer.setData('application/reactflow', 'process')}
                                    onClick={() => addNode('process')}
                                    draggable
                                >
                                    <div className="w-8 h-8 rounded-lg bg-violet-500/20 flex items-center justify-center text-violet-400"><Brain className="w-4 h-4" /></div>
                                    <span className="text-sm font-bold">AI 리믹스 엔진</span>
                                </div>
                            </div>
                        )}

                        {/* Pro Mode Only: 에비던스 루프 */}
                        {canvasMode === 'pro' && (
                            <div>
                                <h3 className="text-xs font-bold text-white/40 uppercase mb-3 tracking-wider">에비던스 루프</h3>

                                <div
                                    className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl cursor-pointer hover:border-blue-500/50 transition-all mb-2 flex items-center gap-3"
                                    onDragStart={(event) => event.dataTransfer.setData('application/reactflow', 'evidence')}
                                    onClick={() => addNode('evidence', undefined, {
                                        nodeId: createdNodeId || undefined,
                                    })}
                                    draggable
                                >
                                    <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center text-blue-400"><BarChart3 className="w-4 h-4" /></div>
                                    <div>
                                        <span className="text-sm font-bold">Evidence Node</span>
                                        <div className="text-[10px] text-blue-300">VDG 성과 테이블 (API 연동)</div>
                                    </div>
                                </div>

                                <div
                                    className="p-3 bg-sky-500/10 border border-sky-500/20 rounded-xl cursor-pointer hover:border-sky-500/50 transition-all mb-2 flex items-center gap-3"
                                    onDragStart={(event) => event.dataTransfer.setData('application/reactflow', 'notebook')}
                                    onClick={() => addNode('notebook')}
                                    draggable
                                >
                                    <div className="w-8 h-8 rounded-lg bg-sky-500/20 flex items-center justify-center text-sky-400"><FileText className="w-4 h-4" /></div>
                                    <div>
                                        <span className="text-sm font-bold">Notebook Library</span>
                                        <div className="text-[10px] text-sky-300">요약/클러스터</div>
                                    </div>
                                </div>

                                <div
                                    className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl cursor-pointer hover:border-amber-500/50 transition-all mb-2 flex items-center gap-3"
                                    onDragStart={(event) => event.dataTransfer.setData('application/reactflow', 'decision')}
                                    onClick={() => addNode('decision')}
                                    draggable
                                >
                                    <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center text-amber-400"><Scale className="w-4 h-4" /></div>
                                    <div>
                                        <span className="text-sm font-bold">Decision Node</span>
                                        <div className="text-[10px] text-amber-300">Opal 결정/실험 계획</div>
                                    </div>
                                </div>

                                <div
                                    className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl cursor-pointer hover:border-emerald-500/50 transition-all mb-2 flex items-center gap-3 border-dashed"
                                    onDragStart={(event) => event.dataTransfer.setData('application/reactflow', 'templateSeed')}
                                    onClick={() => addNode('templateSeed', undefined, {
                                        seed: {
                                            seed_id: `seed_${Date.now()}`,
                                            template_type: 'guide',
                                            hook: 'Opal이 생성할 훅...',
                                            shotlist: [],
                                            parent_id: createdNodeId || undefined,
                                        }
                                    })}
                                    draggable
                                >
                                    <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center text-emerald-400">💊</div>
                                    <div>
                                        <span className="text-sm font-bold">Template Seed</span>
                                        <div className="text-[10px] text-emerald-300">Opal 시드 템플릿</div>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div>
                            <h3 className="text-xs font-bold text-white/40 uppercase mb-3 tracking-wider">출력</h3>
                            <div
                                className="p-3 bg-white/5 border border-white/10 rounded-xl cursor-pointer hover:bg-white/10 hover:border-cyan-500/50 transition-all mb-2 flex items-center gap-3"
                                onDragStart={(event) => event.dataTransfer.setData('application/reactflow', 'output')}
                                onClick={() => addNode('output')}
                                draggable
                            >
                                <div className="w-8 h-8 rounded-lg bg-cyan-500/20 flex items-center justify-center text-cyan-400"><Clapperboard className="w-4 h-4" /></div>
                                <span className="text-sm font-bold">템플릿 내보내기</span>
                            </div>
                        </div>

                        {/* O2O Campaigns Section */}
                        <div>
                            <h3 className="text-xs font-bold text-white/40 uppercase mb-3 tracking-wider flex items-center gap-2">
                                <MapPin className="w-3 h-3" /> O2O 캠페인
                            </h3>
                            <div className="space-y-2 max-h-40 overflow-y-auto">
                                <div
                                    className="p-2 bg-gradient-to-r from-orange-500/10 to-pink-500/10 border border-orange-500/20 rounded-lg cursor-pointer hover:border-orange-500/40 transition-all"
                                    onClick={() => {
                                        showToast('📍 O2O 캠페인 노드가 추가됩니다', 'info');
                                        addNode('source');
                                    }}
                                    draggable
                                    onDragStart={(event) => event.dataTransfer.setData('application/reactflow', 'source')}
                                >
                                    <div className="text-xs font-bold text-orange-400 truncate">강남 팝업스토어</div>
                                    <div className="text-[10px] text-white/40">📞 위치 인증 필요</div>
                                    <div className="text-[10px] text-emerald-400 font-bold">🎁 500 K-Points</div>
                                </div>
                                <div
                                    className="p-2 bg-gradient-to-r from-pink-500/10 to-violet-500/10 border border-pink-500/20 rounded-lg cursor-pointer hover:border-pink-500/40 transition-all"
                                    onClick={() => {
                                        showToast('📍 O2O 캠페인 노드가 추가됩니다', 'info');
                                        addNode('source');
                                    }}
                                    draggable
                                    onDragStart={(event) => event.dataTransfer.setData('application/reactflow', 'source')}
                                >
                                    <div className="text-xs font-bold text-pink-400 truncate">홍대 맛집 챌린지</div>
                                    <div className="text-[10px] text-white/40">📸 영상 촬영 필요</div>
                                    <div className="text-[10px] text-emerald-400 font-bold">🎁 300 K-Points</div>
                                </div>
                            </div>
                            <a href="/o2o" className="block mt-2 text-[10px] text-center text-white/40 hover:text-white/60 transition-colors">
                                → O2O 캠페인으로 이동
                            </a>
                        </div>
                    </div>

                    <div className="mt-auto pt-6 border-t border-white/10 space-y-2">
                        {/* Persistence Controls */}
                        <div className="grid grid-cols-2 gap-2 mb-2">
                            <button
                                onClick={handleSave}
                                disabled={isSaving}
                                className="py-2 bg-gradient-to-r from-emerald-500/20 to-emerald-600/20 border border-emerald-500/30 hover:border-emerald-500/50 rounded-lg text-xs font-bold text-emerald-400 hover:text-emerald-300 transition-all flex items-center justify-center gap-1 disabled:opacity-50"
                            >
                                {isSaving ? '⏳' : '💾'} {isSaving ? '저장 중...' : '저장'}
                            </button>
                            <button
                                onClick={handleLoadList}
                                disabled={isLoading}
                                className="py-2 bg-white/5 border border-white/10 hover:border-white/30 rounded-lg text-xs font-bold text-white/70 hover:text-white transition-all flex items-center justify-center gap-1 disabled:opacity-50"
                            >
                                {isLoading ? '⏳' : '📂'} 불러오기
                            </button>
                        </div>

                        {/* Public Toggle (if already saved) */}
                        {pipelineId && (
                            <button
                                onClick={() => {
                                    setIsPublic(!isPublic);
                                    showToast(`저장 후 파이프라인이 ${!isPublic ? '공개' : '비공개'}로 설정됩니다`, 'info');
                                }}
                                className={`w-full py-2 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1 ${isPublic
                                    ? 'bg-violet-500/20 border border-violet-500/30 text-violet-400'
                                    : 'bg-white/5 border border-white/10 text-white/50'
                                    }`}
                            >
                                {isPublic ? '🌐 공개' : '🔒 비공개'}
                            </button>
                        )}

                        {/* Undo/Redo Controls */}
                        <div className="flex gap-2 mb-4">
                            <button
                                onClick={onUndo}
                                disabled={!canUndo}
                                className="flex-1 py-2 bg-white/5 hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed rounded-lg border border-white/10 text-xs font-bold transition-all flex items-center justify-center gap-1"
                                title="실행 취소 (Cmd+Z)"
                            >
                                <span>↩</span> 실행 취소
                            </button>
                            <button
                                onClick={onRedo}
                                disabled={!canRedo}
                                className="flex-1 py-2 bg-white/5 hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed rounded-lg border border-white/10 text-xs font-bold transition-all flex items-center justify-center gap-1"
                                title="다시 실행 (Cmd+Shift+Z)"
                            >
                                다시 실행 <span>↪</span>
                            </button>
                        </div>

                        {createdNodeId && (
                            <div className="text-xs p-2 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400">
                                ✓ 활성: {createdNodeId}
                            </div>
                        )}

                        <Link href="/" className="w-full py-3 flex items-center justify-center gap-2 bg-white/5 hover:bg-white/10 rounded-xl transition-colors text-sm text-white/60 hover:text-white">
                            ← 대시보드로 나가기
                        </Link>
                    </div>
                </aside>

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
