import React, { useEffect, useState, useRef } from 'react';
import { api, MutationStrategyResponse } from '@/lib/api';

interface MutationStrategyCardProps {
    nodeId: string;
}

export function MutationStrategyCard({ nodeId }: MutationStrategyCardProps) {
    const [strategies, setStrategies] = useState<MutationStrategyResponse[] | null>(null);
    const [loading, setLoading] = useState(true);
    const isMountedRef = useRef(true);

    useEffect(() => {
        const fetchStrategy = async () => {
            try {
                const res = await api.getMutationStrategy(nodeId);
                if (!isMountedRef.current) return;
                setStrategies(res);
            } catch (err) {
                console.error("Failed to fetch mutation strategy:", err);
            } finally {
                if (isMountedRef.current) {
                    setLoading(false);
                }
            }
        };

        if (nodeId) {
            fetchStrategy();
        }
    }, [nodeId]);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    if (loading) return <div className="glass-panel p-6 rounded-2xl animate-pulse h-48"></div>;
    if (!strategies || strategies.length === 0) return null;

    // Show top strategy
    const topStrategy = strategies[0];

    return (
        <div className="glass-panel p-6 rounded-2xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                <svg className="w-24 h-24 text-emerald-400" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zm0 9l2.5-1.25L12 8.5l-2.5 1.25L12 11zm0 2.5l-5-2.5-5 2.5L12 22l10-8.5-5-2.5-5 2.5z" /></svg>
            </div>

            <div className="relative z-10">
                <div className="flex justify-between items-start mb-4">
                    <div>
                        <h3 className="text-sm font-bold text-emerald-400 uppercase tracking-widest mb-1">
                            추천 변주 전략 (Mutation Strategy)
                        </h3>
                        <p className="text-xs text-white/50">{topStrategy.rationale}</p>
                    </div>
                    <div className="bg-emerald-500/20 text-emerald-300 px-3 py-1 rounded-lg border border-emerald-500/30 font-bold text-sm">
                        {topStrategy.expected_boost} 예상
                    </div>
                </div>

                <div className="space-y-3 mt-4">
                    {/* Render mutation details safely */}
                    {Object.entries(topStrategy.mutation_strategy).map(([key, value]) => {
                        if (!value) return null;
                        return (
                            <div key={key} className="flex items-start gap-3 bg-white/5 p-3 rounded-lg border border-white/5">
                                <span className="text-xs font-bold text-white/40 uppercase w-16 pt-0.5">{key}</span>
                                <div className="text-sm text-slate-200">
                                    {/* Just render the value string representation for now */}
                                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                </div>
                            </div>
                        );
                    })}
                </div>

                <div className="mt-6 flex justify-between items-center border-t border-white/10 pt-4">
                    <div className="flex items-center gap-2">
                        <span className="text-xs text-white/40">신뢰도</span>
                        <div className="h-1.5 w-20 bg-slate-700 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-emerald-500"
                                style={{ width: `${topStrategy.confidence * 100}%` }}
                            ></div>
                        </div>
                        <span className="text-xs font-mono text-emerald-400">
                            {Math.round(topStrategy.confidence * 100)}%
                        </span>
                    </div>

                    <button className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold px-4 py-2 rounded-lg transition-colors flex items-center gap-2">
                        <span>이 전략으로 변주하기</span>
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
                    </button>
                </div>
            </div>
        </div>
    );
}
