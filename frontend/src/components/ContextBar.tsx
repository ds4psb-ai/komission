"use client";

import Link from 'next/link';
import { useWorkContextSafe } from '@/contexts/WorkContext';

/**
 * ContextBar: 작업 컨텍스트 표시 바
 * - 모든 핵심 페이지 상단에 고정
 * - 현재 작업 중인 Outlier/Recipe/Run/Quest 표시
 */

export function ContextBar() {
    const context = useWorkContextSafe();

    // Provider 외부이거나 컨텍스트가 비어있으면 표시 안함
    if (!context) return null;

    const { outlier, recipe, run, quest } = context;

    // 모든 컨텍스트가 비어있으면 표시 안함
    if (!outlier && !recipe && !run && !quest) return null;

    return (
        <div className="bg-black/60 backdrop-blur-xl border-b border-white/5 sticky top-[60px] z-40">
            <div className="container mx-auto px-6 py-2 flex items-center gap-4 text-xs overflow-x-auto no-scrollbar">

                {/* Outlier Chip */}
                {outlier && (
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-300 flex-shrink-0">
                        <span className="text-sm">🧬</span>
                        <span className="font-medium truncate max-w-[150px]">{outlier.title}</span>
                        {outlier.performanceDelta && (
                            <span className="text-emerald-400 font-bold">{outlier.performanceDelta}</span>
                        )}
                    </div>
                )}

                {/* Divider */}
                {outlier && (recipe || run || quest) && (
                    <span className="text-white/20">→</span>
                )}

                {/* Recipe Chip */}
                {recipe && (
                    <Link
                        href={`/remix/${recipe.nodeId}`}
                        className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-pink-500/10 border border-pink-500/20 text-pink-300 hover:border-pink-500/40 transition-colors flex-shrink-0"
                    >
                        <span className="text-sm">📋</span>
                        <span className="font-mono">{recipe.nodeId.slice(0, 8)}...</span>
                        {recipe.version && (
                            <span className="text-white/40">v{recipe.version}</span>
                        )}
                    </Link>
                )}

                {/* Divider */}
                {recipe && (run || quest) && (
                    <span className="text-white/20">→</span>
                )}

                {/* Run/Attempt Chip */}
                {run && (
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 flex-shrink-0">
                        <span className="text-sm">🎬</span>
                        <span className="font-medium">시도 #{run.attemptNumber}</span>
                        {run.startedAt && (
                            <span className="text-white/40">
                                {run.startedAt.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
                            </span>
                        )}
                    </div>
                )}

                {/* Quest Chip */}
                {quest && (
                    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full flex-shrink-0 ${quest.accepted
                            ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-300'
                            : 'bg-orange-500/10 border border-orange-500/20 text-orange-300'
                        }`}>
                        <span className="text-sm">{quest.accepted ? '✅' : '🎯'}</span>
                        <span className="font-medium truncate max-w-[100px]">{quest.brand || 'Quest'}</span>
                        <span className="font-bold">+{quest.rewardPoints}P</span>
                    </div>
                )}

                {/* Clear Button */}
                <button
                    onClick={() => context.clearAll()}
                    className="ml-auto px-2 py-1 text-white/20 hover:text-white/60 transition-colors flex-shrink-0"
                    title="컨텍스트 초기화"
                >
                    ✕
                </button>
            </div>
        </div>
    );
}
