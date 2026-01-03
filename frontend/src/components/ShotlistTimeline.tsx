'use client';

/**
 * ShotlistTimeline - VDG 기반 샷리스트 타임라인
 * 
 * 포팅 원본: mobile/src/components/ShotlistTimeline.tsx (219 lines)
 * 
 * 기능:
 * - 현재 샷 표시 (shotlist_sequence 기반)
 * - 킥 타이밍 pre-alert (kick_timings 기반)
 * - 진행률 타임라인 바
 * 
 * 최적화:
 * - useMemo: 샷 계산 최적화
 * - ARIA: 접근성 속성 추가
 */

import React, { useMemo } from 'react';
import { VdgCoachingData } from '@/hooks/useCoachingWebSocket';

// Types (from VdgCoachingData)
interface ShotGuide {
    index: number;
    t_window: [number, number];
    guide: string;
}

interface KickTiming {
    t_sec: number;
    type: 'punch' | 'end';
    cue: string;
    message: string;
    pre_alert_sec: number;
}

interface ShotlistTimelineProps {
    vdgData: VdgCoachingData | null;
    currentTime: number;  // seconds
    totalDuration: number;  // seconds
    visible?: boolean;
}

export function ShotlistTimeline({
    vdgData,
    currentTime,
    totalDuration,
    visible = true,
}: ShotlistTimelineProps) {
    // useMemo: 현재 샷 계산 최적화
    const currentShot = useMemo(() => {
        if (!vdgData?.shotlist_sequence) return null;
        return vdgData.shotlist_sequence.find(
            (s) => currentTime >= s.t_window[0] && currentTime < s.t_window[1]
        ) || null;
    }, [currentTime, vdgData?.shotlist_sequence]);

    // useMemo: 다가오는 킥 계산 최적화
    const upcomingKick = useMemo(() => {
        if (!vdgData?.kick_timings) return null;
        return vdgData.kick_timings.find(
            (k) => k.t_sec > currentTime && k.t_sec - currentTime <= k.pre_alert_sec
        ) || null;
    }, [currentTime, vdgData?.kick_timings]);

    // useMemo: 다음 샷 미리보기 계산
    const nextShotPreview = useMemo(() => {
        if (!currentShot || !vdgData?.shotlist_sequence) return null;
        const nextShot = vdgData.shotlist_sequence.find(s => s.index === currentShot.index + 1);
        if (!nextShot) return null;
        const timeToNextShot = nextShot.t_window[0] - currentTime;
        if (timeToNextShot <= 3 && timeToNextShot > 0) {
            return { shot: nextShot, timeRemaining: timeToNextShot };
        }
        return null;
    }, [currentShot, currentTime, vdgData?.shotlist_sequence]);

    if (!visible || !vdgData) return null;

    const progress = totalDuration > 0 ? (currentTime / totalDuration) * 100 : 0;
    const totalShots = vdgData.shotlist_sequence?.length || 0;

    return (
        <div
            className="shotlist-timeline absolute top-16 left-4 right-4 z-30"
            role="region"
            aria-label="촬영 가이드 타임라인"
        >
            {/* Progress Bar with Kick Markers */}
            <div className="mb-3">
                <div
                    className="relative h-1 bg-white/20 rounded-full overflow-visible"
                    role="progressbar"
                    aria-valuenow={Math.round(progress)}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-label={`촬영 진행률 ${Math.round(progress)}%`}
                >
                    {/* Progress Fill */}
                    <div
                        className="absolute h-full bg-gradient-to-r from-violet-500 to-purple-500 rounded-full transition-all duration-200"
                        style={{ width: `${progress}%` }}
                    />

                    {/* Kick Markers */}
                    {vdgData.kick_timings?.map((kick, i) => {
                        const kickPos = (kick.t_sec / totalDuration) * 100;
                        return (
                            <div
                                key={i}
                                className={`absolute -top-1 w-2 h-2 rounded-full transform -translate-x-1/2 ${kick.type === 'end' ? 'bg-red-500' : 'bg-amber-500'
                                    }`}
                                style={{ left: `${kickPos}%` }}
                                title={kick.message}
                                role="img"
                                aria-label={`${kick.type === 'end' ? '종료' : '킥'} 포인트: ${kick.message}`}
                            />
                        );
                    })}

                    {/* Shot Segment Dividers */}
                    {vdgData.shotlist_sequence?.map((shot, i) => {
                        if (i === 0) return null;
                        const dividerPos = (shot.t_window[0] / totalDuration) * 100;
                        return (
                            <div
                                key={`divider-${i}`}
                                className="absolute top-0 bottom-0 w-px bg-white/30"
                                style={{ left: `${dividerPos}%` }}
                                aria-hidden="true"
                            />
                        );
                    })}
                </div>

                {/* Shot Counter */}
                <div className="flex justify-between mt-1 text-xs text-white/50">
                    <span aria-live="polite">
                        {currentShot ? `Shot ${currentShot.index + 1}/${totalShots}` : 'Ready'}
                    </span>
                    <span>{Math.floor(currentTime)}s / {Math.floor(totalDuration)}s</span>
                </div>
            </div>

            {/* Current Shot Guide */}
            {currentShot && (
                <div
                    className="bg-black/60 backdrop-blur-sm rounded-xl p-3 mb-2 border border-white/10"
                    role="status"
                    aria-live="polite"
                    aria-label={`현재 샷 ${currentShot.index + 1}`}
                >
                    <div className="flex items-center gap-2 mb-1">
                        <span className="text-violet-400 text-xs font-semibold">
                            📍 Shot {currentShot.index + 1}
                        </span>
                        <span className="text-white/40 text-xs">
                            {Math.floor(currentShot.t_window[0])}s - {Math.floor(currentShot.t_window[1])}s
                        </span>
                    </div>
                    <p className="text-white text-sm leading-relaxed">{currentShot.guide}</p>
                </div>
            )}

            {/* Upcoming Kick Alert */}
            {upcomingKick && (
                <div
                    className={`rounded-xl p-3 flex items-center gap-3 ${upcomingKick.type === 'end' ? 'bg-red-500/90' : 'bg-amber-500/90'
                        } animate-pulse`}
                    role="alert"
                    aria-live="assertive"
                    aria-label={`${Math.ceil(upcomingKick.t_sec - currentTime)}초 후 ${upcomingKick.message}`}
                >
                    <span className="text-2xl" aria-hidden="true">{upcomingKick.cue}</span>
                    <div className="flex-1">
                        <p className="text-white text-sm font-semibold">
                            {upcomingKick.message}
                        </p>
                    </div>
                    <span className="text-white/80 text-sm font-mono">
                        {Math.ceil(upcomingKick.t_sec - currentTime)}초
                    </span>
                </div>
            )}

            {/* Next Shot Preview */}
            {nextShotPreview && (
                <div
                    className="mt-2 bg-white/10 backdrop-blur-sm rounded-lg p-2 border border-violet-500/30"
                    aria-label={`다음 샷: ${nextShotPreview.shot.guide}`}
                >
                    <div className="flex items-center gap-2">
                        <span className="text-violet-300 text-xs">
                            ⏭️ 다음 ({Math.ceil(nextShotPreview.timeRemaining)}초 후)
                        </span>
                        <span className="text-white/70 text-xs truncate flex-1">
                            {nextShotPreview.shot.guide.slice(0, 30)}...
                        </span>
                    </div>
                </div>
            )}
        </div>
    );
}

export default ShotlistTimeline;

