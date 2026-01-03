/**
 * 코칭 시스템 공통 상수 및 타입
 * 
 * 모든 코칭 컴포넌트에서 공유하는 상수와 타입 정의
 * - 불변 요소 (Invariant Elements)
 * - 킥 타입 (Kick Types)
 * - 역할 스타일 (Role Styles)
 * - Temporal Phase (시간축)
 */

import React from 'react';
import { Target, Timer, Layers, Music, Lock } from 'lucide-react';

// ==========================================
// 불변 요소 (Invariant Elements)
// ==========================================

export type InvariantElement = 'hook' | 'pacing' | 'composition' | 'payoff' | 'audio';

export interface InvariantBadgeInfo {
    emoji: string;
    label: string;
    color: string;
    description: string;  // 사용자 가치: 설명 추가
    icon?: React.ReactNode;
}

/**
 * 불변 요소별 뱃지 정보
 * 
 * 바이럴 패턴을 모르는 사용자를 위한 설명 포함
 */
export const INVARIANT_BADGES: Record<InvariantElement, InvariantBadgeInfo> = {
    'hook': {
        emoji: '🎣',
        label: '훅',
        color: 'bg-red-500',
        description: '첫 2초 안에 시청자 시선을 사로잡는 요소',
        icon: React.createElement(Target, { className: 'w-3 h-3' }),
    },
    'pacing': {
        emoji: '⏱️',
        label: '페이싱',
        color: 'bg-blue-500',
        description: '컷 편집 타이밍과 영상의 리듬감',
        icon: React.createElement(Timer, { className: 'w-3 h-3' }),
    },
    'composition': {
        emoji: '📐',
        label: '구도',
        color: 'bg-purple-500',
        description: '카메라 앵글과 프레이밍 배치',
        icon: React.createElement(Layers, { className: 'w-3 h-3' }),
    },
    'payoff': {
        emoji: '🎯',
        label: '페이오프',
        color: 'bg-emerald-500',
        description: '영상 끝에 시청자에게 주는 만족감',
        icon: React.createElement(Target, { className: 'w-3 h-3' }),
    },
    'audio': {
        emoji: '🎵',
        label: '오디오',
        color: 'bg-amber-500',
        description: 'BGM 드롭과 효과음 타이밍',
        icon: React.createElement(Music, { className: 'w-3 h-3' }),
    },
};

// ==========================================
// 킥 타입 (Kick Types)
// ==========================================

export type KickType = 'punch' | 'end';

export interface KickTypeInfo {
    label: string;
    color: string;
    bgColor: string;
    description: string;
}

export const KICK_TYPE_STYLES: Record<KickType, KickTypeInfo> = {
    'punch': {
        label: '펀치',
        color: 'text-amber-400',
        bgColor: 'bg-amber-500/90',
        description: '시청자를 사로잡는 핵심 순간',
    },
    'end': {
        label: '마무리',
        color: 'text-violet-400',
        bgColor: 'bg-violet-500/90',
        description: '영상을 완성하는 마지막 터치',
    },
};

// ==========================================
// 역할 스타일 (Role Styles)
// ==========================================

export type KeyframeRole = 'START' | 'PEAK' | 'END';

export interface RoleStyleInfo {
    emoji: string;
    label: string;
    description: string;
}

export const ROLE_STYLES: Record<KeyframeRole, RoleStyleInfo> = {
    'START': {
        emoji: '🎬',
        label: '시작',
        description: '킥 구간의 시작 지점',
    },
    'PEAK': {
        emoji: '⚡',
        label: '클라이맥스',
        description: '킥의 핵심 순간 (가장 중요)',
    },
    'END': {
        emoji: '🎯',
        label: '마무리',
        description: '킥 구간의 종료 지점',
    },
};

// ==========================================
// Temporal Phase (시간축)
// ==========================================

export type TemporalPhase = 'T0' | 'T1' | 'T2' | 'T3';

export interface TemporalPhaseInfo {
    label: string;
    homage: number;
    creativity: number;
    desc: string;
    color: string;
    textColor: string;
    tip: string;
}

/**
 * Temporal Variation Theory 기반 시간축 정의
 * 
 * 시간이 지날수록 오마쥬 비율 감소, 창의성 비율 증가
 */
export const TEMPORAL_PHASES: Record<TemporalPhase, TemporalPhaseInfo> = {
    T0: {
        label: 'T0 (0-7일)',
        homage: 100,
        creativity: 0,
        desc: '100% 복제 권장',
        color: 'bg-emerald-500',
        textColor: 'text-emerald-400',
        tip: '원본을 그대로 따라하세요. 신선도가 가장 높은 구간입니다.',
    },
    T1: {
        label: 'T1 (8-14일)',
        homage: 95,
        creativity: 5,
        desc: '95% 복제 + 5% 창의',
        color: 'bg-blue-500',
        textColor: 'text-blue-400',
        tip: '소재만 살짝 변경해보세요. (예: 음식→뷰티)',
    },
    T2: {
        label: 'T2 (15-28일)',
        homage: 90,
        creativity: 10,
        desc: '90% 복제 + 10% 창의',
        color: 'bg-amber-500',
        textColor: 'text-amber-400',
        tip: '인물 변경 + 미세 반전을 시도해보세요.',
    },
    T3: {
        label: 'T3 (29일+)',
        homage: 85,
        creativity: 15,
        desc: '85% 복제 + 15% 창의',
        color: 'bg-violet-500',
        textColor: 'text-violet-400',
        tip: '중간 킥 추가 + 로컬라이징으로 신선함을 더하세요.',
    },
};

/**
 * 경과 일수로 Temporal Phase 결정
 */
export function getPhaseFromAgeDays(ageDays: number): TemporalPhase {
    if (ageDays <= 7) return 'T0';
    if (ageDays <= 14) return 'T1';
    if (ageDays <= 28) return 'T2';
    return 'T3';
}

// ==========================================
// 미장센 요소 (Mise-en-Scene)
// ==========================================

export type MiseEnSceneElement = 'outfit_color' | 'background' | 'lighting' | 'camera_angle' | 'prop';

export interface MiseEnSceneElementInfo {
    label: string;
    description: string;
}

export const MISE_EN_SCENE_ELEMENTS: Record<MiseEnSceneElement, MiseEnSceneElementInfo> = {
    'outfit_color': {
        label: '의상',
        description: '착용 의상 색상과 스타일',
    },
    'background': {
        label: '배경',
        description: '촬영 장소와 배경 구성',
    },
    'lighting': {
        label: '조명',
        description: '조명 방향과 밝기',
    },
    'camera_angle': {
        label: '카메라',
        description: '카메라 앵글과 거리',
    },
    'prop': {
        label: '소품',
        description: '영상에 등장하는 물건들',
    },
};
