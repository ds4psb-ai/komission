'use client';

/**
 * TemporalPhaseGuide - 오마쥬 비율 가이드
 * 
 * Temporal Variation Theory 기반:
 * - T0 (0-7일): 100% 복제 권장
 * - T1 (8-14일): 95% 복제 + 5% 창의성
 * - T2 (15-28일): 90% 복제 + 10% 창의성
 * - T3 (29일+): 85% 복제 + 15% 창의성
 * 
 * 시간이 지날수록 동일 콘텐츠는 노출 감소
 * → 창의성 비율을 점진적으로 높여야 지속적 바이럴 가능
 */

import React, { useMemo } from 'react';
import { Clock, Sparkles, Lock } from 'lucide-react';
import {
    TEMPORAL_PHASES,
    getPhaseFromAgeDays,
    type TemporalPhase,
} from '@/lib/coaching-constants';

// Types
interface TemporalPhaseGuideProps {
    patternAge?: number;  // 패턴 등장 후 경과 일수
    patternFirstSeen?: string;  // ISO 날짜
    visible?: boolean;
}

export function TemporalPhaseGuide({
    patternAge,
    patternFirstSeen,
    visible = true,
}: TemporalPhaseGuideProps) {
    // 경과 일수 계산
    const ageDays = useMemo(() => {
        if (patternAge !== undefined) return patternAge;
        if (patternFirstSeen) {
            const firstSeen = new Date(patternFirstSeen);
            const now = new Date();
            const diffMs = now.getTime() - firstSeen.getTime();
            return Math.floor(diffMs / (1000 * 60 * 60 * 24));
        }
        return 0;  // 기본값: T0
    }, [patternAge, patternFirstSeen]);

    const currentPhase = useMemo(() => getPhaseFromAgeDays(ageDays), [ageDays]);
    const phaseInfo = TEMPORAL_PHASES[currentPhase];

    if (!visible) return null;

    return (
        <div
            className="temporal-phase-guide bg-black/80 backdrop-blur-sm rounded-xl p-4 border border-white/10"
            role="region"
            aria-label="오마쥬 비율 가이드"
        >
            {/* 헤더 */}
            <div className="flex items-center gap-2 mb-3">
                <div className={`w-8 h-8 rounded-full ${phaseInfo.color} flex items-center justify-center`}>
                    <Clock className="w-4 h-4 text-white" />
                </div>
                <div>
                    <h3 className="text-white text-sm font-bold">{phaseInfo.label}</h3>
                    <p className="text-white/50 text-xs">패턴 등장 {ageDays}일 경과</p>
                </div>
            </div>

            {/* 오마쥬:창의성 비율 바 */}
            <div className="mb-3">
                <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-white/60">🔒 복제</span>
                    <span className="text-xs text-white/60">✨ 창의</span>
                </div>
                <div className="h-2 bg-white/10 rounded-full overflow-hidden flex">
                    <div
                        className={`${phaseInfo.color} transition-all duration-500`}
                        style={{ width: `${phaseInfo.homage}%` }}
                    />
                    <div
                        className="bg-white/30"
                        style={{ width: `${phaseInfo.creativity}%` }}
                    />
                </div>
                <div className="flex items-center justify-between mt-1">
                    <span className={`text-xs font-bold ${phaseInfo.textColor}`}>
                        {phaseInfo.homage}%
                    </span>
                    <span className="text-xs font-bold text-white/40">
                        {phaseInfo.creativity}%
                    </span>
                </div>
            </div>

            {/* 팁 */}
            <div className="bg-white/5 rounded-lg p-2">
                <div className="flex items-start gap-2">
                    <Sparkles className={`w-4 h-4 ${phaseInfo.textColor} flex-shrink-0 mt-0.5`} />
                    <p className="text-white/70 text-xs leading-relaxed">
                        {phaseInfo.tip}
                    </p>
                </div>
            </div>

            {/* 불변/가변 요소 요약 */}
            <div className="mt-3 flex gap-2">
                <div className="flex-1 bg-red-500/10 border border-red-500/30 rounded-lg p-2">
                    <div className="flex items-center gap-1 mb-1">
                        <Lock className="w-3 h-3 text-red-400" />
                        <span className="text-red-400 text-[10px] font-bold">불변</span>
                    </div>
                    <p className="text-white/60 text-[10px]">
                        훅 · 페이싱 · 페이오프
                    </p>
                </div>
                <div className="flex-1 bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-2">
                    <div className="flex items-center gap-1 mb-1">
                        <Sparkles className="w-3 h-3 text-emerald-400" />
                        <span className="text-emerald-400 text-[10px] font-bold">가변</span>
                    </div>
                    <p className="text-white/60 text-[10px]">
                        소재 · 인물 · 반전
                    </p>
                </div>
            </div>
        </div>
    );
}

export default TemporalPhaseGuide;
