"use client";

/**
 * CanvasSidebar - Canvas Page Sidebar Component
 * 
 * Extracted from canvas/page.tsx for code organization
 * Contains: Mode toggle, Node palette, Pipeline controls
 */

import React from 'react';
import Link from 'next/link';
import { PatternGuidePanel } from './PatternGuidePanel';
import { Video, Lock, Dna, Brain, BarChart3, Scale, Clapperboard, MapPin, FileText } from 'lucide-react';

export interface CanvasSidebarProps {
    // Mode
    canvasMode: 'simple' | 'pro';
    setCanvasMode: (mode: 'simple' | 'pro') => void;

    // Pipeline state
    pipelineTitle: string;
    pipelineId: string | null;
    isPublic: boolean;
    setIsPublic: (v: boolean) => void;
    isDirty: boolean;

    // Loading states
    isSaving: boolean;
    isLoading: boolean;

    // Pattern
    patternId: string | null;
    showPatternGuide: boolean;
    setShowPatternGuide: (v: boolean) => void;

    // Node creation
    isAdmin: boolean;
    createdNodeId: string | null;

    // Undo/Redo
    canUndo: boolean;
    canRedo: boolean;
    onUndo: () => void;
    onRedo: () => void;

    // Handlers
    addNode: (type: string, position?: { x: number; y: number }, data?: any) => void;
    setShowOutlierSelector: (v: boolean) => void;
    handleSave: () => void;
    handleLoadList: () => void;
    showToast: (message: string, type: 'success' | 'error' | 'info') => void;
}

export function CanvasSidebar({
    canvasMode,
    setCanvasMode,
    pipelineTitle,
    pipelineId,
    isPublic,
    setIsPublic,
    isSaving,
    isLoading,
    patternId,
    showPatternGuide,
    setShowPatternGuide,
    isAdmin,
    createdNodeId,
    canUndo,
    canRedo,
    onUndo,
    onRedo,
    addNode,
    setShowOutlierSelector,
    handleSave,
    handleLoadList,
    showToast,
}: CanvasSidebarProps) {
    return (
        <aside className="w-72 flex flex-col z-20 glass-panel border-y-0 border-l-0 border-r border-white/10 p-5 backdrop-blur-2xl bg-black/40">
            {/* Header */}
            <div className="mb-8">
                <div className="text-xs font-bold text-violet-400 uppercase tracking-widest mb-1">캔버스 모드</div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <span className="text-2xl">⚡</span>
                    파이프라인
                </h2>
                {pipelineTitle && (
                    <p className="text-xs text-emerald-400 mt-2 truncate border border-emerald-500/30 rounded px-2 py-1 bg-emerald-500/10">📝 {pipelineTitle}</p>
                )}

                {/* Mode Toggle */}
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

            {/* Pattern Guide Panel */}
            {patternId && showPatternGuide && (
                <div className="mb-4">
                    <PatternGuidePanel
                        patternId={patternId}
                        onClose={() => setShowPatternGuide(false)}
                    />
                </div>
            )}

            {/* Node Palette */}
            <div className="space-y-6 flex-1 overflow-y-auto">
                {/* Input Sources */}
                <div>
                    <h3 className="text-xs font-bold text-white/40 uppercase mb-3 tracking-wider">입력 소스</h3>

                    {/* Admin Only: Media Source */}
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

                    {/* Viral Hit */}
                    <div
                        className="p-3 bg-gradient-to-r from-violet-500/10 to-pink-500/10 border border-violet-500/20 rounded-xl cursor-pointer hover:border-violet-500/50 transition-all mb-2 flex items-center gap-3"
                        onClick={() => setShowOutlierSelector(true)}
                        draggable={false}
                    >
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500/20 to-pink-500/20 flex items-center justify-center text-white"><Dna className="w-4 h-4" /></div>
                        <div>
                            <span className="text-sm font-bold text-white">바이럴 히트 추가</span>
                            <div className="text-[10px] text-violet-300">인기 영상에서 패턴 학습</div>
                        </div>
                    </div>
                </div>

                {/* Simple Mode Helper */}
                {canvasMode === 'simple' && (
                    <div className="p-3 bg-blue-500/5 border border-blue-500/20 rounded-lg">
                        <div className="text-xs text-blue-300 font-medium mb-1">💡 Simple 모드</div>
                        <div className="text-[10px] text-white/50">
                            바이럴 히트를 선택하면 자동으로 촬영 가이드가 생성됩니다.
                            더 많은 도구는 Pro 모드를 활성화하세요.
                        </div>
                    </div>
                )}

                {/* Pro Mode: Tools */}
                {canvasMode === 'pro' && (
                    <>
                        {/* Capsule */}
                        <div>
                            <h3 className="text-xs font-bold text-white/40 uppercase mb-3 tracking-wider">핵심 도구</h3>
                            <NodeButton
                                type="capsule"
                                icon={<Lock className="w-4 h-4" />}
                                label="Capsule Node"
                                sublabel="가이드 생성 (AI)"
                                color="rose"
                                addNode={addNode}
                            />
                        </div>

                        {/* Processors */}
                        <div>
                            <h3 className="text-xs font-bold text-white/40 uppercase mb-3 tracking-wider">프로세서</h3>
                            <NodeButton
                                type="process"
                                icon={<Brain className="w-4 h-4" />}
                                label="AI 리믹스 엔진"
                                color="violet"
                                addNode={addNode}
                            />
                        </div>

                        {/* Evidence Loop */}
                        <div>
                            <h3 className="text-xs font-bold text-white/40 uppercase mb-3 tracking-wider">에비던스 루프</h3>
                            <NodeButton
                                type="evidence"
                                icon={<BarChart3 className="w-4 h-4" />}
                                label="Evidence Node"
                                sublabel="VDG 성과 테이블"
                                color="blue"
                                addNode={addNode}
                                data={{ nodeId: createdNodeId || undefined }}
                            />
                            <NodeButton
                                type="notebook"
                                icon={<FileText className="w-4 h-4" />}
                                label="Notebook Library"
                                sublabel="요약/클러스터"
                                color="sky"
                                addNode={addNode}
                            />
                            <NodeButton
                                type="decision"
                                icon={<Scale className="w-4 h-4" />}
                                label="Decision Node"
                                sublabel="Opal 결정/실험 계획"
                                color="amber"
                                addNode={addNode}
                            />
                            <NodeButton
                                type="templateSeed"
                                icon={<span>💊</span>}
                                label="Template Seed"
                                sublabel="Opal 시드 템플릿"
                                color="emerald"
                                addNode={addNode}
                                dashed
                                data={{
                                    seed: {
                                        seed_id: `seed_${Date.now()}`,
                                        template_type: 'guide',
                                        hook: 'Opal이 생성할 훅...',
                                        shotlist: [],
                                        parent_id: createdNodeId || undefined,
                                    }
                                }}
                            />
                        </div>
                    </>
                )}

                {/* Output */}
                <div>
                    <h3 className="text-xs font-bold text-white/40 uppercase mb-3 tracking-wider">출력</h3>
                    <NodeButton
                        type="output"
                        icon={<Clapperboard className="w-4 h-4" />}
                        label="템플릿 내보내기"
                        color="cyan"
                        addNode={addNode}
                    />
                </div>

                {/* O2O Campaigns */}
                <div>
                    <h3 className="text-xs font-bold text-white/40 uppercase mb-3 tracking-wider flex items-center gap-2">
                        <MapPin className="w-3 h-3" /> O2O 캠페인
                    </h3>
                    <div className="space-y-2 max-h-40 overflow-y-auto">
                        <O2OCampaignItem
                            title="강남 팝업스토어"
                            description="📞 위치 인증 필요"
                            points={500}
                            gradient="from-orange-500/10 to-pink-500/10"
                            borderColor="orange"
                            onClick={() => {
                                showToast('📍 O2O 캠페인 노드가 추가됩니다', 'info');
                                addNode('source');
                            }}
                        />
                        <O2OCampaignItem
                            title="홍대 맛집 챌린지"
                            description="📸 영상 촬영 필요"
                            points={300}
                            gradient="from-pink-500/10 to-violet-500/10"
                            borderColor="pink"
                            onClick={() => {
                                showToast('📍 O2O 캠페인 노드가 추가됩니다', 'info');
                                addNode('source');
                            }}
                        />
                    </div>
                    <a href="/o2o" className="block mt-2 text-[10px] text-center text-white/40 hover:text-white/60 transition-colors">
                        → O2O 캠페인으로 이동
                    </a>
                </div>
            </div>

            {/* Bottom Controls */}
            <div className="mt-auto pt-6 border-t border-white/10 space-y-2">
                {/* Save/Load */}
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

                {/* Public Toggle */}
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

                {/* Undo/Redo */}
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
    );
}

// ===================
// Helper Components
// ===================

interface NodeButtonProps {
    type: string;
    icon: React.ReactNode;
    label: string;
    sublabel?: string;
    color: string;
    addNode: (type: string, position?: { x: number; y: number }, data?: any) => void;
    dashed?: boolean;
    data?: any;
}

function NodeButton({ type, icon, label, sublabel, color, addNode, dashed, data }: NodeButtonProps) {
    const colorClasses: Record<string, string> = {
        rose: 'bg-rose-500/10 border-rose-500/20 hover:border-rose-500/50 text-rose-400',
        violet: 'bg-violet-500/10 border-violet-500/20 hover:border-violet-500/50 text-violet-400',
        blue: 'bg-blue-500/10 border-blue-500/20 hover:border-blue-500/50 text-blue-400',
        sky: 'bg-sky-500/10 border-sky-500/20 hover:border-sky-500/50 text-sky-400',
        amber: 'bg-amber-500/10 border-amber-500/20 hover:border-amber-500/50 text-amber-400',
        emerald: 'bg-emerald-500/10 border-emerald-500/20 hover:border-emerald-500/50 text-emerald-400',
        cyan: 'bg-cyan-500/10 border-cyan-500/20 hover:border-cyan-500/50 text-cyan-400',
    };

    const iconBgClasses: Record<string, string> = {
        rose: 'bg-rose-500/20 text-rose-400',
        violet: 'bg-violet-500/20 text-violet-400',
        blue: 'bg-blue-500/20 text-blue-400',
        sky: 'bg-sky-500/20 text-sky-400',
        amber: 'bg-amber-500/20 text-amber-400',
        emerald: 'bg-emerald-500/20 text-emerald-400',
        cyan: 'bg-cyan-500/20 text-cyan-400',
    };

    const sublabelClasses: Record<string, string> = {
        rose: 'text-rose-300',
        violet: 'text-violet-300',
        blue: 'text-blue-300',
        sky: 'text-sky-300',
        amber: 'text-amber-300',
        emerald: 'text-emerald-300',
        cyan: 'text-cyan-300',
    };

    return (
        <div
            className={`p-3 ${colorClasses[color]} border rounded-xl cursor-pointer transition-all mb-2 flex items-center gap-3 ${dashed ? 'border-dashed' : ''}`}
            onDragStart={(event) => event.dataTransfer.setData('application/reactflow', type)}
            onClick={() => addNode(type, undefined, data)}
            draggable
        >
            <div className={`w-8 h-8 rounded-lg ${iconBgClasses[color]} flex items-center justify-center`}>{icon}</div>
            <div>
                <span className="text-sm font-bold">{label}</span>
                {sublabel && <div className={`text-[10px] ${sublabelClasses[color]}`}>{sublabel}</div>}
            </div>
        </div>
    );
}

interface O2OCampaignItemProps {
    title: string;
    description: string;
    points: number;
    gradient: string;
    borderColor: string;
    onClick: () => void;
}

function O2OCampaignItem({ title, description, points, gradient, borderColor, onClick }: O2OCampaignItemProps) {
    return (
        <div
            className={`p-2 bg-gradient-to-r ${gradient} border border-${borderColor}-500/20 rounded-lg cursor-pointer hover:border-${borderColor}-500/40 transition-all`}
            onClick={onClick}
            draggable
            onDragStart={(event) => event.dataTransfer.setData('application/reactflow', 'source')}
        >
            <div className={`text-xs font-bold text-${borderColor}-400 truncate`}>{title}</div>
            <div className="text-[10px] text-white/40">{description}</div>
            <div className="text-[10px] text-emerald-400 font-bold">🎁 {points} K-Points</div>
        </div>
    );
}
