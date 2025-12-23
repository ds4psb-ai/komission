"use client";

import React from 'react';
import { Node } from '@xyflow/react';
import type { CapsuleDefinition, CapsuleParam } from '@/components/canvas/CapsuleNode';
import { cn } from '@/lib/utils';
import { Video, Brain, Clapperboard, Lock } from 'lucide-react';

interface InspectorProps {
    selectedNode: Node | null;
    onClose: () => void;
    onDeleteNode?: (nodeId: string) => void;
    onUpdateNodeData?: (nodeId: string, patch: Record<string, unknown>) => void;
    viralData?: {
        performanceDelta?: string;
        parentViews?: number;
        genealogyDepth?: number;
        forkCount?: number;
    };
}

export function Inspector({ selectedNode, onClose, onDeleteNode, onUpdateNodeData, viralData }: InspectorProps) {
    if (!selectedNode) {
        return (
            <aside className="w-80 bg-black/40 backdrop-blur-xl border-l border-white/5 p-6 flex flex-col relative overflow-hidden">
                <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-[0.02] pointer-events-none" />
                <div className="flex justify-between items-center mb-6 relative z-10">
                    <h3 className="font-black text-white/40 uppercase tracking-widest text-xs">인스펙터</h3>
                </div>
                <div className="flex-1 flex items-center justify-center text-center relative z-10">
                    <div className="text-white/20">
                        <div className="text-5xl mb-4 animate-bounce opacity-30">👆</div>
                        <p className="text-xs font-mono uppercase tracking-widest">노드를 선택하여<br />데이터 확인</p>
                    </div>
                </div>
            </aside>
        );
    }

    const nodeType = selectedNode.type || 'unknown';
    const nodeData = selectedNode.data as Record<string, unknown>;
    const capsule = (nodeData.capsule as CapsuleDefinition | undefined)
        || (nodeType === 'capsule' ? (nodeData as unknown as CapsuleDefinition) : undefined);

    const updateCapsuleParam = (param: CapsuleParam, value: string | number | boolean) => {
        if (!capsule || !onUpdateNodeData) return;

        const nextParams = (capsule.params || []).map((item) =>
            item.key === param.key ? { ...item, value } : item
        );

        onUpdateNodeData(selectedNode.id, {
            capsule: { ...capsule, params: nextParams },
        });
    };

    return (
        <aside className="w-80 bg-black/60 backdrop-blur-2xl border-l border-white/5 flex flex-col overflow-y-auto relative h-full shadow-2xl">
            {/* Ambient Background */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-violet-600/10 blur-[100px] pointer-events-none" />

            {/* Header */}
            <div className="p-6 border-b border-white/5 bg-gradient-to-r from-white/5 to-transparent relative z-10">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="font-black text-white text-lg tracking-tight">인스펙터</h3>
                    <button
                        onClick={onClose}
                        className="w-8 h-8 flex items-center justify-center rounded-full bg-white/5 hover:bg-white/10 text-white/50 hover:text-white transition-all"
                    >
                        ✕
                    </button>
                </div>

                {/* Node Type Badge */}
                <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold border backdrop-blur-md ${nodeType === 'source' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.1)]' :
                    nodeType === 'process' ? 'bg-violet-500/10 text-violet-400 border-violet-500/20 shadow-[0_0_15px_rgba(139,92,246,0.1)]' :
                        nodeType === 'capsule' ? 'bg-rose-500/10 text-rose-300 border-rose-500/20 shadow-[0_0_15px_rgba(244,63,94,0.15)]' :
                            'bg-cyan-500/10 text-cyan-400 border-cyan-500/20 shadow-[0_0_15px_rgba(6,182,212,0.1)]'
                    }`}>
                    {nodeType === 'source' && <Video className="w-3 h-3" />}
                    {nodeType === 'process' && <Brain className="w-3 h-3" />}
                    {nodeType === 'output' && <Clapperboard className="w-3 h-3" />}
                    {nodeType === 'capsule' && <Lock className="w-3 h-3" />}
                    <span className="uppercase tracking-wider">{nodeType} Node</span>
                </div>
            </div>

            <div className="p-6 space-y-8 relative z-10">
                {/* Viral Insight Badges - HUD Style */}
                {viralData && (
                    <div className="space-y-4">
                        <h4 className="text-[10px] font-bold text-white/30 uppercase tracking-[0.2em] flex items-center gap-2">
                            <span className="w-1 h-1 rounded-full bg-pink-500"></span>
                            바이럴 DNA
                        </h4>

                        {viralData.performanceDelta && (
                            <div className="p-4 bg-gradient-to-br from-pink-500/10 to-transparent border border-pink-500/20 rounded-xl relative overflow-hidden group">
                                <div className="absolute inset-0 bg-pink-500/5 group-hover:bg-pink-500/10 transition-colors" />
                                <div className="text-[10px] text-pink-300/70 font-bold uppercase tracking-wider mb-1">성과 지표</div>
                                <div className="text-3xl font-black text-white drop-shadow-[0_0_10px_rgba(236,72,153,0.5)]">
                                    {viralData.performanceDelta}
                                </div>
                            </div>
                        )}

                        <div className="grid grid-cols-2 gap-3">
                            {viralData.parentViews !== undefined && (
                                <div className="p-3 bg-white/5 border border-white/5 rounded-xl hover:border-white/20 transition-colors">
                                    <div className="text-[10px] text-white/30 uppercase mb-1">부모 조회수</div>
                                    <div className="text-sm font-bold text-white font-mono tracking-tight">
                                        {viralData.parentViews.toLocaleString()}
                                    </div>
                                </div>
                            )}
                            {viralData.genealogyDepth !== undefined && (
                                <div className="p-3 bg-white/5 border border-white/5 rounded-xl hover:border-white/20 transition-colors">
                                    <div className="text-[10px] text-white/30 uppercase mb-1">생성 세대</div>
                                    <div className="text-sm font-bold text-white font-mono tracking-tight">
                                        Lv.{viralData.genealogyDepth}
                                    </div>
                                </div>
                            )}
                            {viralData.forkCount !== undefined && (
                                <div className="p-3 bg-white/5 border border-white/5 rounded-xl col-span-2 flex justify-between items-center group hover:border-emerald-500/30 transition-colors">
                                    <div className="text-[10px] text-white/30 uppercase">파생 포크</div>
                                    <div className="text-sm font-bold text-emerald-400 font-mono tracking-tight flex items-center gap-2">
                                        <span className="text-emerald-500/50">🌿</span>
                                        {viralData.forkCount}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Node Properties */}
                <div className="space-y-4">
                    <h4 className="text-[10px] font-bold text-white/30 uppercase tracking-[0.2em] flex items-center gap-2">
                        <span className="w-1 h-1 rounded-full bg-cyan-500"></span>
                        속성
                    </h4>

                    <div className="space-y-3">
                        <div className="group">
                            <label className="text-[10px] text-white/30 uppercase mb-1 block">노드 ID</label>
                            <div className="text-[10px] font-mono text-white/50 bg-black/40 px-3 py-2 rounded-lg border border-white/5 group-hover:border-white/20 transition-colors break-all">
                                {selectedNode.id}
                            </div>
                        </div>

                        <div className="group">
                            <label className="text-[10px] text-white/30 uppercase mb-1 block">좌표</label>
                            <div className="text-[10px] font-mono text-cyan-400/70 bg-cyan-900/10 px-3 py-2 rounded-lg border border-cyan-500/10 group-hover:border-cyan-500/30 transition-colors">
                                X: {Math.round(selectedNode.position.x)} <span className="text-white/20 mx-2">|</span> Y: {Math.round(selectedNode.position.y)}
                            </div>
                        </div>

                        {Boolean(nodeData.nodeId) && (
                            <div className="group">
                                <label className="text-[10px] text-white/30 uppercase mb-1 block">리믹스 자산 ID</label>
                                <div className="text-[10px] font-mono text-emerald-400/70 bg-emerald-900/10 px-3 py-2 rounded-lg border border-emerald-500/10 group-hover:border-emerald-500/30 transition-colors flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                                    {String(nodeData.nodeId)}
                                </div>
                            </div>
                        )}

                        {capsule?.id && (
                            <div className="group">
                                <label className="text-[10px] text-white/30 uppercase mb-1 block">Capsule ID</label>
                                <div className="text-[10px] font-mono text-rose-300/80 bg-rose-900/10 px-3 py-2 rounded-lg border border-rose-500/20">
                                    {capsule.id}
                                </div>
                            </div>
                        )}

                        {Boolean(nodeData.isLocked) && (
                            <div className="mt-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl flex items-center gap-3">
                                <span className="text-xl">🔒</span>
                                <div>
                                    <div className="text-xs font-bold text-amber-400">브랜드 보호</div>
                                    <div className="text-[10px] text-amber-400/60">수정 잠금됨</div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {capsule && (
                    <div className="space-y-4">
                        <h4 className="text-[10px] font-bold text-white/30 uppercase tracking-[0.2em] flex items-center gap-2">
                            <span className="w-1 h-1 rounded-full bg-rose-400"></span>
                            Capsule 파라미터
                        </h4>

                        <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-xs text-rose-200/80">
                            내부 체인은 비공개입니다. 노출된 파라미터만 조정할 수 있습니다.
                        </div>

                        <div className="space-y-3">
                            {(capsule.params || []).map((param) => {
                                const disabled = !onUpdateNodeData;

                                if (param.type === 'select') {
                                    return (
                                        <div key={param.key} className="space-y-1">
                                            <label className="text-[10px] text-white/40 uppercase">{param.label}</label>
                                            <select
                                                disabled={disabled}
                                                value={String(param.value ?? '')}
                                                onChange={(e) => updateCapsuleParam(param, e.target.value)}
                                                className={cn(
                                                    "w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs text-white/70 focus:outline-none focus:border-rose-500/40",
                                                    disabled && "opacity-60 cursor-not-allowed"
                                                )}
                                            >
                                                {(param.options || []).map((option) => (
                                                    <option key={option} value={option}>
                                                        {option}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>
                                    );
                                }

                                if (param.type === 'toggle') {
                                    return (
                                        <button
                                            key={param.key}
                                            type="button"
                                            disabled={disabled}
                                            onClick={() => updateCapsuleParam(param, !param.value)}
                                            className={cn(
                                                "w-full flex items-center justify-between px-3 py-2 rounded-lg border text-xs",
                                                param.value
                                                    ? "border-rose-400/40 text-rose-200 bg-rose-500/10"
                                                    : "border-white/10 text-white/50 bg-black/30",
                                                disabled && "opacity-60 cursor-not-allowed"
                                            )}
                                        >
                                            <span>{param.label}</span>
                                            <span>{param.value ? "ON" : "OFF"}</span>
                                        </button>
                                    );
                                }

                                return (
                                    <div key={param.key} className="space-y-1">
                                        <label className="text-[10px] text-white/40 uppercase">{param.label}</label>
                                        <input
                                            type={param.type === 'number' ? 'number' : 'text'}
                                            disabled={disabled}
                                            value={String(param.value ?? '')}
                                            onChange={(e) =>
                                                updateCapsuleParam(
                                                    param,
                                                    param.type === 'number' ? Number(e.target.value) : e.target.value
                                                )
                                            }
                                            className={cn(
                                                "w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs text-white/70 focus:outline-none focus:border-rose-500/40",
                                                disabled && "opacity-60 cursor-not-allowed"
                                            )}
                                        />
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}
            </div>

            {/* Actions */}
            <div className="mt-auto p-6 border-t border-white/5 bg-black/40 backdrop-blur-xl space-y-3 relative z-20">
                {Boolean(nodeData.nodeId) && (
                    <a
                        href={`/remix/${String(nodeData.nodeId)}`}
                        className="w-full py-3 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 rounded-xl text-xs font-bold text-white transition-all flex items-center justify-center gap-2 group"
                    >
                        <span className="group-hover:rotate-45 transition-transform duration-300">↗</span> 상세 페이지
                    </a>
                )}
                <button
                    onClick={() => {
                        if (onDeleteNode) {
                            onDeleteNode(selectedNode.id);
                        }
                    }}
                    className="w-full py-3 bg-red-500/5 hover:bg-red-500/10 border border-red-500/10 hover:border-red-500/30 rounded-xl text-xs font-bold text-red-500/60 hover:text-red-400 transition-colors flex items-center justify-center gap-2"
                >
                    🗑️ 노드 삭제
                </button>
            </div>
        </aside>
    );
}
