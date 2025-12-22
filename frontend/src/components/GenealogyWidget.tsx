import React from 'react';

interface GenealogyWidgetProps {
    depth: number;
    layer: string;
    parentId?: string;
    performanceDelta?: string; // e.g. "+350%"
}

export function GenealogyWidget({ depth, layer, parentId, performanceDelta }: GenealogyWidgetProps) {
    const steps = [];

    // Construct a mock history based on depth
    // In a real app, this would fetch the full graph path from Neo4j
    for (let i = 0; i <= depth; i++) {
        steps.push(i);
    }

    return (
        <div className="glass-panel p-6 rounded-2xl mb-6">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-sm font-bold text-white/40 uppercase tracking-widest">바이럴 계보</h3>
                <span className="text-xs bg-violet-500/20 text-violet-300 px-3 py-1 rounded-full border border-violet-500/30">
                    깊이: {depth}
                </span>
            </div>

            <div className="relative flex flex-col gap-8 pl-4 border-l-2 border-dashed border-white/10 ml-3">
                {/* Render Ancestors */}
                {depth > 0 && (
                    <div className="relative group">
                        {/* Node Dot */}
                        <div className="absolute -left-[21px] top-3 w-4 h-4 rounded-full bg-slate-700 border-2 border-slate-500 z-10 group-hover:scale-125 transition-transform"></div>

                        <div className="bg-white/5 border border-white/5 p-3 rounded-xl hover:bg-white/10 transition-colors cursor-pointer flex gap-4 items-center">
                            <div className="w-12 h-12 bg-slate-800 rounded-lg flex-shrink-0 flex items-center justify-center text-xs text-white/30">
                                부모
                            </div>
                            <div>
                                <div className="text-xs text-white/40 mb-1">원본 노드</div>
                                <div className="text-sm font-medium text-slate-300">오리지널 컨셉</div>
                            </div>
                        </div>

                        {/* Connection Label */}
                        <div className="absolute -left-[14px] top-14 h-8 border-l border-violet-500/50"></div>
                        <div className="absolute left-6 -bottom-6 text-xs text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                            변이: {performanceDelta || "+??%"} 🚀
                        </div>
                    </div>
                )}

                {/* Current Node */}
                <div className="relative">
                    <div className="absolute -left-[23px] top-6 w-5 h-5 rounded-full bg-violet-500 border-4 border-black shadow-[0_0_15px_rgba(139,92,246,0.6)] z-20 animate-pulse"></div>

                    <div className="glass-panel p-4 rounded-xl border-violet-500/30 bg-violet-500/5 relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-2 opacity-30">
                            <svg className="w-16 h-16 text-violet-500" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zm0 9l2.5-1.25L12 8.5l-2.5 1.25L12 11zm0 2.5l-5-2.5-5 2.5L12 22l10-8.5-5-2.5-5 2.5z" /></svg>
                        </div>

                        <div className="relative z-10">
                            <div className="text-xs text-violet-400 font-bold mb-1 uppercase">현재 노드</div>
                            <div className="text-lg font-bold text-white">
                                {layer === 'master' ? '마스터 오리진' : '진화된 변이'}
                            </div>
                            <div className="text-xs text-white/50 mt-2">
                                이 노드는 현재 {layer === 'master' ? '유기적' : '가속화된'} 성장을 추적중입니다.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
