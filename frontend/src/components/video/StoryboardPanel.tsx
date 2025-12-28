"use client";

/**
 * Storyboard Panel - VDG 분석 데이터를 씬별 스토리보드 카드로 시각화
 * 
 * Features:
 * - 씬별 카드 UI (펼치기/접기)
 * - 한글 레이블 (백엔드에서 번역)
 * - 타임라인 시각화
 * - 카메라/조명/오디오 태그 표시
 */

import React, { useState } from 'react';
import {
    ChevronDown, ChevronRight, Camera, MapPin,
    Music, MessageSquare, Film, Clock, Sparkles,
    Volume2, Lightbulb, Clapperboard
} from 'lucide-react';

// ==================
// Types
// ==================

interface AudioEvent {
    label: string;
    label_en: string;
    intensity: string;
}

interface CameraInfo {
    shot: string;
    shot_en: string;
    move: string;
    move_en: string;
    angle: string;
    angle_en: string;
}

interface SceneData {
    scene_id: string;
    scene_number: number;
    time_start: number;
    time_end: number;
    duration_sec: number;
    time_label: string;
    role: string;
    role_en: string;
    summary: string;
    summary_ko: string;
    dialogue: string;
    comedic_device: string[];
    camera: CameraInfo;
    location: string;
    lighting: string;
    lighting_en: string;
    edit_pace: string;
    edit_pace_en: string;
    audio_events: AudioEvent[];
    music: string;
    ambient: string;
}

interface RawVDG {
    title: string;
    title_ko: string;
    total_duration: number;
    scene_count: number;
    scenes: SceneData[];
}

interface StoryboardPanelProps {
    rawVdg?: RawVDG | null;
    defaultExpanded?: boolean;
}

// ==================
// Scene Card Component
// ==================

function SceneCard({ scene, isFirst }: { scene: SceneData; isFirst: boolean }) {
    const [expanded, setExpanded] = useState(isFirst);

    // Role color mapping
    const roleColors: Record<string, string> = {
        "훅": "bg-cyan-500/20 text-cyan-300 border-cyan-500/30",
        "Hook": "bg-cyan-500/20 text-cyan-300 border-cyan-500/30",
        "액션": "bg-orange-500/20 text-orange-300 border-orange-500/30",
        "Action": "bg-orange-500/20 text-orange-300 border-orange-500/30",
        "리액션": "bg-violet-500/20 text-violet-300 border-violet-500/30",
        "Reaction": "bg-violet-500/20 text-violet-300 border-violet-500/30",
        "셋업": "bg-blue-500/20 text-blue-300 border-blue-500/30",
        "Setup": "bg-blue-500/20 text-blue-300 border-blue-500/30",
    };

    const roleColor = roleColors[scene.role] || roleColors[scene.role_en] || "bg-zinc-500/20 text-zinc-300 border-zinc-500/30";

    return (
        <div className="bg-zinc-900/50 border border-white/10 rounded-xl overflow-hidden">
            {/* Header - Always visible */}
            <button
                onClick={() => setExpanded(!expanded)}
                className="w-full p-4 flex items-center gap-3 hover:bg-white/5 transition-colors text-left"
            >
                {/* Scene number */}
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500/30 to-pink-500/30 flex items-center justify-center shrink-0">
                    <span className="text-white font-bold text-sm">{scene.scene_number}</span>
                </div>

                {/* Timing */}
                <div className="flex items-center gap-1.5 text-white/50 text-xs font-mono shrink-0">
                    <Clock className="w-3 h-3" />
                    <span>{scene.time_label}</span>
                    <span className="text-white/30">({scene.duration_sec}s)</span>
                </div>

                {/* Role badge */}
                <span className={`px-2 py-0.5 rounded text-xs font-bold border ${roleColor}`}>
                    {scene.role || scene.role_en}
                </span>

                {/* Summary preview */}
                <span className="text-white/70 text-sm truncate flex-1">
                    {!scene.summary_ko && scene.summary && (
                        <span className="text-amber-400/80 text-[10px] font-bold mr-1.5">[EN]</span>
                    )}
                    {scene.summary_ko || scene.summary}
                </span>

                {/* Expand icon */}
                <div className="shrink-0 text-white/40">
                    {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                </div>
            </button>

            {/* Expanded content */}
            {expanded && (
                <div className="px-4 pb-4 space-y-3 border-t border-white/5">
                    {/* Summary - Full */}
                    <div className="pt-3">
                        <p className="text-white/90 text-sm leading-relaxed">
                            {!scene.summary_ko && scene.summary && (
                                <span className="text-amber-400/80 text-[10px] font-bold mr-1.5">[EN]</span>
                            )}
                            {scene.summary_ko || scene.summary}
                        </p>
                    </div>

                    {/* Dialogue */}
                    {scene.dialogue && scene.dialogue !== "n/a" && (
                        <div className="flex items-start gap-2 p-3 bg-white/5 rounded-lg">
                            <MessageSquare className="w-4 h-4 text-yellow-400 shrink-0 mt-0.5" />
                            <div>
                                <span className="text-xs text-yellow-400/70 font-bold">대사</span>
                                <p className="text-white/80 text-sm italic">"{scene.dialogue}"</p>
                            </div>
                        </div>
                    )}

                    {/* Camera, Location, Lighting grid */}
                    <div className="grid grid-cols-2 gap-2">
                        {/* Location */}
                        {scene.location && (
                            <div className="flex items-center gap-2 p-2 bg-white/5 rounded-lg">
                                <MapPin className="w-4 h-4 text-emerald-400" />
                                <div>
                                    <span className="text-[10px] text-white/40 block">장소</span>
                                    <span className="text-xs text-white/80">{scene.location}</span>
                                </div>
                            </div>
                        )}

                        {/* Camera */}
                        {scene.camera?.shot && (
                            <div className="flex items-center gap-2 p-2 bg-white/5 rounded-lg">
                                <Camera className="w-4 h-4 text-pink-400" />
                                <div>
                                    <span className="text-[10px] text-white/40 block">카메라</span>
                                    <span className="text-xs text-white/80">
                                        {scene.camera.shot}
                                        {scene.camera.move && ` → ${scene.camera.move}`}
                                    </span>
                                </div>
                            </div>
                        )}

                        {/* Lighting */}
                        {scene.lighting && (
                            <div className="flex items-center gap-2 p-2 bg-white/5 rounded-lg">
                                <Lightbulb className="w-4 h-4 text-amber-400" />
                                <div>
                                    <span className="text-[10px] text-white/40 block">조명</span>
                                    <span className="text-xs text-white/80">{scene.lighting}</span>
                                </div>
                            </div>
                        )}

                        {/* Edit pace */}
                        {scene.edit_pace && (
                            <div className="flex items-center gap-2 p-2 bg-white/5 rounded-lg">
                                <Film className="w-4 h-4 text-blue-400" />
                                <div>
                                    <span className="text-[10px] text-white/40 block">편집</span>
                                    <span className="text-xs text-white/80">{scene.edit_pace}</span>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Audio events */}
                    {scene.audio_events && scene.audio_events.length > 0 && (
                        <div className="flex items-start gap-2">
                            <Volume2 className="w-4 h-4 text-cyan-400 shrink-0 mt-1" />
                            <div className="flex flex-wrap gap-1.5">
                                {scene.audio_events.map((audio, i) => (
                                    <span
                                        key={i}
                                        className={`px-2 py-0.5 rounded text-xs border ${audio.intensity === 'high'
                                            ? 'bg-red-500/10 border-red-500/30 text-red-300'
                                            : 'bg-cyan-500/10 border-cyan-500/30 text-cyan-300'
                                            }`}
                                    >
                                        {audio.label || audio.label_en}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Comedic devices */}
                    {scene.comedic_device && scene.comedic_device.length > 0 && (
                        <div className="flex items-start gap-2">
                            <Sparkles className="w-4 h-4 text-yellow-400 shrink-0 mt-1" />
                            <div className="flex flex-wrap gap-1.5">
                                {scene.comedic_device.map((device, i) => (
                                    <span
                                        key={i}
                                        className="px-2 py-0.5 bg-yellow-500/10 border border-yellow-500/30 rounded text-xs text-yellow-300"
                                    >
                                        {device}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

// ==================
// Main Component
// ==================

export function StoryboardPanel({ rawVdg, defaultExpanded = true }: StoryboardPanelProps) {
    const [isExpanded, setIsExpanded] = useState(defaultExpanded);

    if (!rawVdg || !rawVdg.scenes || rawVdg.scenes.length === 0) {
        return (
            <div className="p-4 bg-white/5 border border-white/10 rounded-xl text-center">
                <Clapperboard className="w-8 h-8 text-white/20 mx-auto mb-2" />
                <p className="text-white/40 text-sm">스토리보드 데이터가 없습니다</p>
            </div>
        );
    }

    return (
        <div className="space-y-3">
            {/* Header */}
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full flex items-center justify-between p-3 bg-gradient-to-br from-violet-500/10 to-pink-500/10 border border-violet-500/30 rounded-xl hover:border-violet-500/50 transition-colors"
            >
                <div className="flex items-center gap-3">
                    <Clapperboard className="w-5 h-5 text-violet-400" />
                    <span className="text-white font-bold">스토리보드</span>
                    <span className="px-2 py-0.5 bg-white/10 rounded text-xs text-white/60 font-mono">
                        {rawVdg.scene_count}개 씬 • {rawVdg.total_duration.toFixed(1)}초
                    </span>
                </div>
                <div className="text-white/40">
                    {isExpanded ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                </div>
            </button>

            {/* Scene cards */}
            {isExpanded && (
                <div className="space-y-2">
                    {rawVdg.scenes.map((scene, index) => (
                        <SceneCard key={scene.scene_id} scene={scene} isFirst={index === 0} />
                    ))}
                </div>
            )}
        </div>
    );
}

export default StoryboardPanel;
