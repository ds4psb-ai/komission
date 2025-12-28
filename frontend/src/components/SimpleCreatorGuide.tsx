'use client';

/**
 * SimpleCreatorGuide - Minimal Creator View (PEGL v1.0)
 * 
 * Per docs/17_TEMPORAL_VARIATION_THEORY.md Section 5.2:
 * - 3-line summary
 * - Slots only (invariant + variable)
 * - Single CTA
 * - No heavy graphs
 * 
 * Non-negotiables (15_FINAL_ARCHITECTURE.md):
 * - Canvas = I/O only
 * - PatternLibrary data from DB (SoR)
 */

import { useState, useEffect } from 'react';
import { api, PatternLibraryItem } from '@/lib/api';
import { Lock, Sparkles, ArrowRight, Loader2 } from 'lucide-react';

interface SimpleCreatorGuideProps {
    patternId: string;
    onApply?: () => void;
}

export function SimpleCreatorGuide({ patternId, onApply }: SimpleCreatorGuideProps) {
    const [pattern, setPattern] = useState<PatternLibraryItem | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const load = async () => {
            try {
                setLoading(true);
                const data = await api.getPatternDetail(patternId);
                setPattern(data);
            } catch (e) {
                console.error('Failed to load pattern:', e);
            } finally {
                setLoading(false);
            }
        };
        load();
    }, [patternId]);

    if (loading) {
        return (
            <div className="flex items-center justify-center p-8">
                <Loader2 className="w-6 h-6 animate-spin text-violet-400" />
            </div>
        );
    }

    if (!pattern) {
        return (
            <div className="p-4 text-center text-white/50 text-sm">
                패턴을 찾을 수 없습니다
            </div>
        );
    }

    // Extract slots from pattern
    const invariantRules = pattern.invariant_rules || {};
    const mutationStrategy = pattern.mutation_strategy || {};

    // Get top 3 invariant rules (slots)
    const invariantSlots = Object.entries(invariantRules).slice(0, 3);

    // Get top 3 variable slots (exclude internal fields like _creator_feedback)
    const variableSlots = Object.entries(mutationStrategy)
        .filter(([key]) => !key.startsWith('_'))
        .slice(0, 3);

    // 3-line summary
    const summary = `${pattern.platform} ${pattern.category} 패턴 • ${pattern.temporal_phase} • 변주 ${variableSlots.length}개`;

    return (
        <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl p-5 max-w-sm mx-auto shadow-2xl border border-white/10">
            {/* 3-line Summary */}
            <div className="text-center mb-4">
                <div className="text-xs text-violet-400 font-medium uppercase tracking-wider mb-1">
                    Creator Guide
                </div>
                <div className="text-white/60 text-xs">
                    {summary}
                </div>
            </div>

            {/* 🔒 Invariant Slots */}
            <div className="mb-4">
                <div className="flex items-center gap-1.5 text-xs font-bold text-amber-400 mb-2">
                    <Lock className="w-3.5 h-3.5" />
                    이건 꼭 지켜주세요
                </div>
                <div className="space-y-1.5">
                    {invariantSlots.map(([key, value]) => (
                        <div
                            key={key}
                            className="flex items-start gap-2 text-xs text-white/80 bg-amber-500/5 rounded-lg px-3 py-2 border border-amber-500/20"
                        >
                            <span className="text-amber-400">•</span>
                            <span>{typeof value === 'string' ? value : key}</span>
                        </div>
                    ))}
                    {invariantSlots.length === 0 && (
                        <div className="text-xs text-white/40">규칙 없음</div>
                    )}
                </div>
            </div>

            {/* ✨ Variable Slots */}
            <div className="mb-5">
                <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-400 mb-2">
                    <Sparkles className="w-3.5 h-3.5" />
                    여기서 창의력 발휘!
                </div>
                <div className="space-y-1.5">
                    {variableSlots.map(([key, value]) => {
                        const displayValue = typeof value === 'object' && value !== null
                            ? (value as any).impact || (value as any).description || key
                            : key;
                        return (
                            <div
                                key={key}
                                className="flex items-start gap-2 text-xs text-white/80 bg-emerald-500/5 rounded-lg px-3 py-2 border border-emerald-500/20"
                            >
                                <span className="text-emerald-400">•</span>
                                <span>{displayValue}</span>
                            </div>
                        );
                    })}
                    {variableSlots.length === 0 && (
                        <div className="text-xs text-white/40">변주 포인트 없음</div>
                    )}
                </div>
            </div>

            {/* Single CTA */}
            <button
                onClick={onApply}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-violet-600 to-pink-600 hover:from-violet-500 hover:to-pink-500 rounded-xl text-white text-sm font-bold transition-all shadow-lg shadow-violet-500/25"
            >
                촬영 시작하기
                <ArrowRight className="w-4 h-4" />
            </button>
        </div>
    );
}
