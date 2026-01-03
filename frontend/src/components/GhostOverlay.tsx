'use client';

/**
 * GhostOverlay - 오마쥬 모드 불변 요소 복제 가이드
 * 
 * 핵심 철학 (Temporal Variation Theory):
 * "바이럴 변주는 시간 경과에 따라 오마쥬 비율이 감소하며,
 *  핵심 로직(hook/pacing/payoff)은 불변, 창의성은 가변"
 * 
 * Ghost Overlay = 불변 요소를 정밀하게 복제할 수 있게 돕는 핵심 도구
 * 
 * 기능:
 * - VDG viral_kicks 기반 확장 keyframes
 * - 불변 요소 뱃지 (🎣 hook, ⏱️ pacing, 📐 composition, 🎯 payoff, 🎵 audio)
 * - 킥 타이밍 대형 카운트다운
 * - 불변 요소 복제 강조
 * - 투명도/블렌드 모드 조절
 */

import React, { useMemo, useState, useCallback } from 'react';
import { Eye, EyeOff, Blend, Minus, Plus, Lock } from 'lucide-react';
import {
    INVARIANT_BADGES,
    KICK_TYPE_STYLES,
    ROLE_STYLES,
    type InvariantElement,
    type KickType,
    type KeyframeRole,
} from '@/lib/coaching-constants';

// Types
interface Keyframe {
    t_ms: number;
    role: KeyframeRole;
    kick_type: KickType;
    kick_index: number;
    kick_mechanism: string;
    image_url: string;
    what_to_see: string;
    invariant_elements: InvariantElement[];
    coaching_tip?: string;
    confidence: number;
}

interface GhostOverlayProps {
    keyframes: Keyframe[];
    currentTimeMs: number;
    visible?: boolean;
    onVisibilityChange?: (visible: boolean) => void;
}

export function GhostOverlay({
    keyframes,
    currentTimeMs,
    visible = true,
    onVisibilityChange,
}: GhostOverlayProps) {
    const [opacity, setOpacity] = useState(0.35);
    const [blendMode, setBlendMode] = useState<'normal' | 'difference'>('normal');
    const [showControls, setShowControls] = useState(false);

    // useMemo: 현재 키프레임 계산 (가장 최근 킥의 PEAK 우선)
    const currentKeyframe = useMemo(() => {
        if (!keyframes || keyframes.length === 0) return null;

        // 현재 시간 이전 또는 같은 키프레임 중 가장 최근 것
        const validKeyframes = keyframes.filter(k => k.t_ms <= currentTimeMs);
        if (validKeyframes.length === 0) {
            // 아직 첫 키프레임에 도달하지 않음 → 첫 번째 PEAK 표시
            const firstPeak = keyframes.find(k => k.role === 'PEAK');
            return firstPeak || keyframes[0];
        }

        // 가장 가까운 PEAK > END > START 우선순위
        const byPriority = [...validKeyframes].sort((a, b) => {
            const priorityOrder = { 'PEAK': 0, 'END': 1, 'START': 2 };
            const pa = priorityOrder[a.role] ?? 99;
            const pb = priorityOrder[b.role] ?? 99;
            if (pa !== pb) return pa - pb;
            return b.t_ms - a.t_ms; // 같은 우선순위면 더 최근 것
        });

        return byPriority[0];
    }, [keyframes, currentTimeMs]);

    // useMemo: 다가오는 킥 (3초 이내)
    const upcomingKick = useMemo(() => {
        if (!keyframes || keyframes.length === 0) return null;

        // PEAK 기준으로 3초 이내 킥 찾기
        const peaks = keyframes.filter(k => k.role === 'PEAK');
        const upcoming = peaks.find(k => {
            const timeToKick = (k.t_ms - currentTimeMs) / 1000;
            return timeToKick > 0 && timeToKick <= 3;
        });

        return upcoming;
    }, [keyframes, currentTimeMs]);

    // useMemo: 킥까지 남은 시간
    const timeToKick = useMemo(() => {
        if (!upcomingKick) return null;
        return (upcomingKick.t_ms - currentTimeMs) / 1000;
    }, [upcomingKick, currentTimeMs]);

    const handleOpacityChange = useCallback((delta: number) => {
        setOpacity(prev => Math.max(0.1, Math.min(0.7, prev + delta)));
    }, []);

    if (!visible || !currentKeyframe) return null;

    const kickStyle = KICK_TYPE_STYLES[currentKeyframe.kick_type] || KICK_TYPE_STYLES.punch;
    const roleStyle = ROLE_STYLES[currentKeyframe.role] || ROLE_STYLES.PEAK;

    return (
        <div
            className="ghost-overlay absolute inset-0 z-20 pointer-events-none"
            role="img"
            aria-label={`레퍼런스 가이드: ${currentKeyframe.what_to_see}`}
        >
            {/* 레퍼런스 이미지 오버레이 */}
            <img
                src={currentKeyframe.image_url}
                alt={`${currentKeyframe.role} keyframe: ${currentKeyframe.what_to_see}`}
                className="absolute inset-0 w-full h-full object-cover"
                style={{
                    opacity: opacity,
                    mixBlendMode: blendMode,
                }}
                onError={(e) => {
                    // 이미지 로드 실패 시 숨김
                    (e.target as HTMLImageElement).style.display = 'none';
                }}
            />

            {/* ===== 킥 타이밍 대형 카운트다운 ===== */}
            {upcomingKick && timeToKick !== null && timeToKick <= 3 && (
                <div
                    className="absolute inset-0 flex flex-col items-center justify-center z-30"
                    role="alert"
                    aria-live="assertive"
                >
                    {/* 대형 카운트다운 숫자 */}
                    <div className={`text-[120px] md:text-[180px] font-black ${kickStyle.color} animate-pulse drop-shadow-2xl`}>
                        {Math.ceil(timeToKick)}
                    </div>

                    {/* 코칭 팁 */}
                    {upcomingKick.coaching_tip && (
                        <div className={`px-6 py-3 rounded-2xl ${kickStyle.bgColor} shadow-lg`}>
                            <p className="text-white text-lg md:text-xl font-bold text-center">
                                {upcomingKick.coaching_tip}
                            </p>
                        </div>
                    )}

                    {/* 불변 요소 뱃지 */}
                    <div className="flex gap-2 mt-4">
                        {upcomingKick.invariant_elements.map(element => {
                            const badge = INVARIANT_BADGES[element];
                            return badge ? (
                                <div
                                    key={element}
                                    className={`px-3 py-1.5 rounded-full ${badge.color} flex items-center gap-1.5`}
                                >
                                    <Lock className="w-3 h-3 text-white" />
                                    <span className="text-white text-xs font-bold">{badge.label}</span>
                                </div>
                            ) : null;
                        })}
                    </div>
                </div>
            )}

            {/* ===== 상단: 현재 상태 표시 ===== */}
            {(!upcomingKick || timeToKick === null || timeToKick > 3) && (
                <>
                    {/* 역할 + 킥 타입 뱃지 */}
                    <div className="absolute top-4 right-4 pointer-events-auto flex gap-2">
                        <div className={`px-3 py-1.5 rounded-full ${kickStyle.bgColor} flex items-center gap-2 shadow-lg`}>
                            <span>{roleStyle.emoji}</span>
                            <span className="text-white text-xs font-bold">{roleStyle.label}</span>
                        </div>
                    </div>

                    {/* 불변 요소 뱃지 (상단 좌측) - 설명 툴팁 포함 */}
                    <div className="absolute top-4 left-4 pointer-events-auto flex flex-wrap gap-1.5 max-w-[50%]">
                        {currentKeyframe.invariant_elements.map(element => {
                            const badge = INVARIANT_BADGES[element];
                            return badge ? (
                                <div
                                    key={element}
                                    className={`px-2 py-1 rounded-full ${badge.color} flex items-center gap-1 cursor-help`}
                                    title={`${badge.emoji} ${badge.label}: ${badge.description}`}
                                >
                                    <Lock className="w-2.5 h-2.5 text-white" />
                                    <span className="text-white text-[10px] font-bold">{badge.label}</span>
                                </div>
                            ) : null;
                        })}
                    </div>

                    {/* 하단: What to See 가이드 */}
                    <div className="absolute bottom-28 left-4 right-4 pointer-events-auto">
                        <div className="bg-black/80 backdrop-blur-sm rounded-xl p-3 border border-white/10">
                            <div className="flex items-center gap-2 mb-1">
                                <Lock className="w-4 h-4 text-amber-400" />
                                <span className="text-amber-400 text-xs font-semibold">불변 요소 복제</span>
                            </div>
                            <p className="text-white text-sm font-medium leading-relaxed">
                                {currentKeyframe.what_to_see}
                            </p>
                            {currentKeyframe.coaching_tip && (
                                <p className="text-white/60 text-xs mt-1">
                                    💡 {currentKeyframe.coaching_tip}
                                </p>
                            )}
                        </div>
                    </div>
                </>
            )}

            {/* ===== 컨트롤 패널 (접힘식) ===== */}
            <button
                onClick={() => setShowControls(!showControls)}
                className="absolute bottom-4 right-4 p-2.5 rounded-full bg-black/70 pointer-events-auto border border-white/20"
                aria-label={showControls ? "설정 패널 닫기" : "설정 패널 열기"}
            >
                {showControls ? (
                    <EyeOff className="w-4 h-4 text-white/70" />
                ) : (
                    <Eye className="w-4 h-4 text-white/70" />
                )}
            </button>

            {showControls && (
                <div
                    className="absolute bottom-16 right-4 w-64 pointer-events-auto"
                    role="toolbar"
                    aria-label="고스트 오버레이 설정"
                >
                    <div className="bg-black/90 backdrop-blur-sm rounded-xl p-4 border border-white/10">
                        {/* 투명도 조절 */}
                        <div className="mb-4">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-white/60 text-xs">투명도</span>
                                <span className="text-white text-xs font-mono">{Math.round(opacity * 100)}%</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => handleOpacityChange(-0.1)}
                                    className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20"
                                    aria-label="투명도 감소"
                                >
                                    <Minus className="w-3 h-3 text-white" />
                                </button>
                                <input
                                    type="range"
                                    min="10"
                                    max="70"
                                    value={opacity * 100}
                                    onChange={(e) => setOpacity(Number(e.target.value) / 100)}
                                    className="flex-1 h-1 bg-white/20 rounded-full appearance-none cursor-pointer accent-violet-500"
                                    aria-label="투명도 슬라이더"
                                />
                                <button
                                    onClick={() => handleOpacityChange(0.1)}
                                    className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20"
                                    aria-label="투명도 증가"
                                >
                                    <Plus className="w-3 h-3 text-white" />
                                </button>
                            </div>
                        </div>

                        {/* 블렌드 모드 토글 */}
                        <div className="flex items-center justify-between">
                            <span className="text-white/60 text-xs">구도 비교 모드</span>
                            <button
                                onClick={() => setBlendMode(blendMode === 'normal' ? 'difference' : 'normal')}
                                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors ${blendMode === 'difference'
                                    ? 'bg-violet-500 text-white'
                                    : 'bg-white/10 text-white/60 hover:bg-white/20'
                                    }`}
                                aria-pressed={blendMode === 'difference'}
                                aria-label={`구도 비교 모드 ${blendMode === 'difference' ? '켜짐' : '꺼짐'}`}
                            >
                                <Blend className="w-4 h-4" />
                                <span className="text-xs font-medium">{blendMode === 'difference' ? 'ON' : 'OFF'}</span>
                            </button>
                        </div>

                        {/* 표시 토글 */}
                        <button
                            onClick={() => onVisibilityChange?.(false)}
                            className="w-full mt-4 py-2 rounded-lg bg-white/5 text-white/50 text-xs hover:bg-white/10"
                        >
                            레퍼런스 숨기기
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

export default GhostOverlay;
