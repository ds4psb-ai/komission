/**
 * TemplateSeedNode.tsx
 * 
 * Template Seed Node for Canvas
 * Based on 08_CANVAS_NODE_CONTRACTS.md - Opal 템플릿 시드
 * 
 * 입력: Decision (parent_id, experiment)
 * 출력: Template Seed (hook, shotlist, audio, scene, timing, do_not)
 */
import { memo, useState, useCallback, useEffect, useRef } from "react";
import { Handle, Position } from "@xyflow/react";

interface SeedParams {
    hook?: string;
    shotlist?: string[];
    audio?: string;
    scene?: string;
    timing?: string[];
    do_not?: string[];
}

interface TemplateSeedNodeData {
    parentId?: string;
    clusterId?: string;
    seed?: SeedParams;
    status?: 'idle' | 'generating' | 'done' | 'error';
    errorMessage?: string;
}

export const TemplateSeedNode = memo(({ data }: { data: TemplateSeedNodeData }) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [seed, setSeed] = useState<SeedParams | null>(data.seed || null);
    const status = data.status || (seed ? 'done' : 'idle');
    const isMountedRef = useRef(true);

    useEffect(() => {
        setSeed(data.seed ?? null);
    }, [data.seed]);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    const generateSeed = useCallback(async () => {
        if (!data.parentId) {
            if (isMountedRef.current) {
                setError('Parent ID가 필요합니다');
            }
            return;
        }

        if (isMountedRef.current) {
            setLoading(true);
            setError(null);
        }

        try {
            const response = await fetch('/api/v1/template-seeds/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    parent_id: data.parentId,
                    cluster_id: data.clusterId,
                    template_type: 'capsule',
                }),
            });

            if (!response.ok) throw new Error('시드 생성 실패');

            const result = await response.json();
            if (!isMountedRef.current) return;
            if (result.success && result.seed?.seed_params) {
                setSeed(result.seed.seed_params);
            }
        } catch (e) {
            if (!isMountedRef.current) return;
            setError(e instanceof Error ? e.message : '오류 발생');
        } finally {
            if (isMountedRef.current) {
                setLoading(false);
            }
        }
    }, [data.parentId, data.clusterId]);

    const statusStyles = {
        idle: 'border-purple-500/40',
        generating: 'border-purple-500/60 animate-pulse',
        done: 'border-emerald-500/50',
        error: 'border-red-500/50',
    };

    return (
        <div className={`glass-panel rounded-2xl min-w-[340px] overflow-hidden border ${statusStyles[loading ? 'generating' : seed ? 'done' : status]} transition-all duration-300 shadow-lg`}>
            {/* Header */}
            <div className="px-5 py-3 border-b border-purple-500/20 bg-gradient-to-r from-purple-900/40 via-violet-900/20 to-transparent flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <span className="text-lg">🎬</span>
                    <span className="font-bold text-xs tracking-widest text-white/90 uppercase">Template Seed</span>
                </div>
                <div className="flex items-center gap-2">
                    {loading && <div className="w-2 h-2 rounded-full bg-purple-500 animate-pulse" />}
                    {seed && !loading && <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_5px_#10b981]" />}
                    {error && <div className="w-2 h-2 rounded-full bg-red-500" />}
                </div>
            </div>

            {/* Body */}
            <div className="p-5 bg-black/60 backdrop-blur-xl space-y-4">
                <Handle type="target" position={Position.Left} className="!bg-purple-500 !w-3 !h-3 !border-2 !border-black" />

                {/* Error Message */}
                {error && (
                    <div className="p-2 bg-red-500/10 border border-red-500/20 rounded text-xs text-red-400">
                        ⚠️ {error}
                    </div>
                )}

                {/* Loading State */}
                {loading && (
                    <div className="py-8 flex flex-col items-center gap-3">
                        <div className="relative">
                            <div className="w-12 h-12 border-4 border-purple-500/30 border-t-purple-500 rounded-full animate-spin" />
                            <span className="absolute inset-0 flex items-center justify-center text-lg">✨</span>
                        </div>
                        <div className="text-xs text-purple-400 font-bold">Opal 시드 생성 중...</div>
                    </div>
                )}

                {/* Seed Display */}
                {seed && !loading && (
                    <div className="space-y-3">
                        {/* Hook */}
                        <div className="p-3 bg-purple-500/10 border border-purple-500/20 rounded-xl">
                            <div className="text-[10px] text-purple-300 font-bold mb-1">🎯 HOOK (0-2초)</div>
                            <div className="text-sm text-white/90 font-medium">{seed.hook}</div>
                        </div>

                        {/* Shotlist */}
                        {seed.shotlist && seed.shotlist.length > 0 && (
                            <div className="space-y-1">
                                <div className="text-[10px] text-white/50 uppercase font-bold">📹 Shotlist</div>
                                <div className="flex flex-wrap gap-1">
                                    {seed.shotlist.map((shot, i) => (
                                        <span key={i} className="px-2 py-1 text-[10px] bg-white/5 border border-white/10 rounded text-white/70">
                                            {i + 1}. {shot}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Timing */}
                        {seed.timing && seed.timing.length > 0 && (
                            <div className="flex items-center gap-2">
                                <span className="text-[10px] text-white/40">⏱️</span>
                                <div className="flex gap-1">
                                    {seed.timing.map((t, i) => (
                                        <span key={i} className="px-1.5 py-0.5 text-[9px] font-mono bg-cyan-500/10 text-cyan-400 rounded">
                                            {t}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Audio & Scene */}
                        <div className="grid grid-cols-2 gap-2 text-[10px]">
                            {seed.audio && (
                                <div className="p-2 bg-white/5 rounded">
                                    <div className="text-white/40 mb-0.5">🎵 Audio</div>
                                    <div className="text-white/70">{seed.audio}</div>
                                </div>
                            )}
                            {seed.scene && (
                                <div className="p-2 bg-white/5 rounded">
                                    <div className="text-white/40 mb-0.5">🎬 Scene</div>
                                    <div className="text-white/70">{seed.scene}</div>
                                </div>
                            )}
                        </div>

                        {/* Do Not */}
                        {seed.do_not && seed.do_not.length > 0 && (
                            <div className="p-2 bg-red-500/5 border border-red-500/20 rounded-lg">
                                <div className="text-[9px] text-red-400 font-bold mb-1">⛔ 금지 요소</div>
                                <div className="flex flex-wrap gap-1">
                                    {seed.do_not.map((item, i) => (
                                        <span key={i} className="px-1.5 py-0.5 text-[9px] bg-red-500/10 text-red-300 rounded">
                                            {item}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Generate Button */}
                {!seed && !loading && (
                    <div className="text-center py-6">
                        <button
                            onClick={generateSeed}
                            disabled={!data.parentId}
                            className="px-5 py-2.5 bg-gradient-to-r from-purple-500 to-violet-500 text-white text-xs font-bold rounded-lg shadow-lg hover:from-purple-400 hover:to-violet-400 transition-all transform hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            ✨ 템플릿 시드 생성
                        </button>
                        <div className="mt-3 text-[10px] text-white/30">
                            {data.parentId ? 'Decision 기반 촬영 가이드 생성' : 'Parent ID 필요'}
                        </div>
                    </div>
                )}

                {/* Regenerate Button */}
                {seed && !loading && (
                    <button
                        onClick={generateSeed}
                        className="w-full py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-[10px] text-white/50 transition-all"
                    >
                        🔄 다시 생성
                    </button>
                )}

                <Handle type="source" position={Position.Right} className="!bg-purple-500 !w-3 !h-3 !border-2 !border-black" />
            </div>
        </div>
    );
});

TemplateSeedNode.displayName = 'TemplateSeedNode';

export default TemplateSeedNode;
