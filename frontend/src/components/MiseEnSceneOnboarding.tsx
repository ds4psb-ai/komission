'use client';
import { useTranslations } from 'next-intl';

/**
 * MiseEnSceneOnboarding - 촬영 전 준비 체크리스트
 * 
 * VDG mise_en_scene_guides 기반 온보딩 UI
 * 
 * 기능:
 * - 의상/배경/소품 등 촬영 준비 가이드
 * - 체크리스트 형태로 표시
 * - 모든 high priority 항목 확인 후 촬영 시작
 */

import React, { useState, useEffect } from 'react';
import {
    CheckCircle, Circle, AlertTriangle,
    Shirt, Camera, Lightbulb, MapPin, Sparkles,
    ChevronRight
} from 'lucide-react';
import { MISE_EN_SCENE_ELEMENTS, type MiseEnSceneElement } from '@/lib/coaching-constants';

// Types
interface MiseEnSceneGuide {
    element: string;
    value: string;
    guide: string;
    priority: 'high' | 'medium';
    evidence?: string;
}

interface MiseEnSceneOnboardingProps {
    guides: MiseEnSceneGuide[];
    onReady: () => void;
    onSkip?: () => void;
    visible?: boolean;
}

// Element 아이콘 매핑
const ELEMENT_ICONS: Record<string, React.ReactNode> = {
    'outfit_color': <Shirt className="w-5 h-5" />,
    'background': <MapPin className="w-5 h-5" />,
    'lighting': <Lightbulb className="w-5 h-5" />,
    'camera_angle': <Camera className="w-5 h-5" />,
    'prop': <Sparkles className="w-5 h-5" />,
};

// Element 라벨 (coaching-constants 활용)
const getElementLabel = (element: string): string => {
    const info = MISE_EN_SCENE_ELEMENTS[element as MiseEnSceneElement];
    return info?.label || element;
};

export function MiseEnSceneOnboarding({
    guides,
    onReady,
    onSkip,
    visible = true,
}: MiseEnSceneOnboardingProps) {
    const [checkedItems, setCheckedItems] = useState<Set<number>>(new Set());

    // High priority 항목만 필터링
    const highPriorityGuides = guides.filter(g => g.priority === 'high');
    const mediumPriorityGuides = guides.filter(g => g.priority === 'medium');

    // 모든 high priority 체크 여부
    const allHighPriorityChecked = highPriorityGuides.every((_, i) =>
        checkedItems.has(i)
    );

    const toggleCheck = (index: number) => {
        setCheckedItems(prev => {
            const next = new Set(prev);
            if (next.has(index)) {
                next.delete(index);
            } else {
                next.add(index);
            }
            return next;
        });
    };

    if (!visible || guides.length === 0) return null;

    return (
        <div
            className="fixed inset-0 z-50 bg-black/90 backdrop-blur-sm flex items-center justify-center p-4"
            role="dialog"
            aria-modal="true"
            aria-labelledby="onboarding-title"
            aria-describedby="onboarding-description"
        >
            <div className="w-full max-w-md bg-gradient-to-b from-zinc-900 to-black rounded-2xl border border-white/10 overflow-hidden">
                {/* Header */}
                <div className="p-6 border-b border-white/10">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
                            <Sparkles className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <h2 id="onboarding-title" className="text-lg font-bold text-white">촬영 준비</h2>
                            <p className="text-sm text-white/50">미장센 체크리스트</p>
                        </div>
                    </div>
                    <p id="onboarding-description" className="text-sm text-white/60 mt-3">
                        원본 영상의 성공 요인을 참고하여 준비해주세요
                    </p>
                </div>

                {/* Checklist */}
                <div className="p-4 max-h-[50vh] overflow-y-auto">
                    {/* High Priority Items */}
                    {highPriorityGuides.length > 0 && (
                        <div className="mb-4">
                            <div className="flex items-center gap-2 mb-3">
                                <AlertTriangle className="w-4 h-4 text-amber-400" />
                                <span className="text-xs font-semibold text-amber-400 uppercase tracking-wide">
                                    필수 확인
                                </span>
                            </div>
                            <div className="space-y-2" role="group" aria-label="필수 확인 항목">
                                {highPriorityGuides.map((guide, i) => (
                                    <ChecklistItem
                                        key={`high-${i}`}
                                        guide={guide}
                                        checked={checkedItems.has(i)}
                                        onToggle={() => toggleCheck(i)}
                                        isHighPriority
                                    />
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Medium Priority Items */}
                    {mediumPriorityGuides.length > 0 && (
                        <div>
                            <div className="flex items-center gap-2 mb-3">
                                <span className="text-xs font-semibold text-white/40 uppercase tracking-wide">
                                    권장 사항
                                </span>
                            </div>
                            <div className="space-y-2" role="group" aria-label="권장 사항 항목">
                                {mediumPriorityGuides.map((guide, i) => (
                                    <ChecklistItem
                                        key={`med-${i}`}
                                        guide={guide}
                                        checked={checkedItems.has(highPriorityGuides.length + i)}
                                        onToggle={() => toggleCheck(highPriorityGuides.length + i)}
                                        isHighPriority={false}
                                    />
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer Actions */}
                <div className="p-4 border-t border-white/10 bg-black/50">
                    <div className="flex gap-3">
                        {onSkip && (
                            <button
                                onClick={onSkip}
                                className="flex-1 py-3 px-4 rounded-xl bg-white/5 text-white/60 font-medium text-sm hover:bg-white/10 transition-colors"
                                aria-label="미장센 체크 건너뛰기"
                            >
                                건너뛰기
                            </button>
                        )}
                        <button
                            onClick={onReady}
                            disabled={!allHighPriorityChecked && highPriorityGuides.length > 0}
                            aria-disabled={!allHighPriorityChecked && highPriorityGuides.length > 0}
                            className={`flex-1 py-3 px-4 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all ${allHighPriorityChecked || highPriorityGuides.length === 0
                                ? 'bg-gradient-to-r from-violet-500 to-purple-600 text-white hover:opacity-90'
                                : 'bg-white/10 text-white/30 cursor-not-allowed'
                                }`}
                        >
                            촬영 시작
                            <ChevronRight className="w-4 h-4" />
                        </button>
                    </div>
                    {!allHighPriorityChecked && highPriorityGuides.length > 0 && (
                        <p className="text-xs text-amber-400/80 text-center mt-2">
                            필수 항목을 모두 확인해주세요
                        </p>
                    )}
                </div>
            </div>
        </div>
    );
}

// Checklist Item Component
function ChecklistItem({
    guide,
    checked,
    onToggle,
    isHighPriority,
}: {
    guide: MiseEnSceneGuide;
    checked: boolean;
    onToggle: () => void;
    isHighPriority: boolean;
}) {
    const icon = ELEMENT_ICONS[guide.element] || <Sparkles className="w-5 h-5" />;
    const label = getElementLabel(guide.element);

    return (
        <button
            onClick={onToggle}
            role="checkbox"
            aria-checked={checked}
            aria-label={`${label}: ${guide.value}${isHighPriority ? ' (필수)' : ''}`}
            className={`w-full p-3 rounded-xl flex items-start gap-3 text-left transition-all ${checked
                ? 'bg-emerald-500/10 border border-emerald-500/30'
                : isHighPriority
                    ? 'bg-white/5 border border-amber-500/30 hover:bg-white/10'
                    : 'bg-white/5 border border-white/10 hover:bg-white/10'
                }`}
        >
            {/* Check Icon */}
            <div className={`flex-shrink-0 mt-0.5 ${checked ? 'text-emerald-400' : 'text-white/30'
                }`}>
                {checked ? (
                    <CheckCircle className="w-5 h-5" />
                ) : (
                    <Circle className="w-5 h-5" />
                )}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                    <span className={`${checked ? 'text-emerald-400' : 'text-violet-400'}`}>
                        {icon}
                    </span>
                    <span className="text-xs font-semibold text-white/60 uppercase">
                        {label}
                    </span>
                    {isHighPriority && !checked && (
                        <span className="px-1.5 py-0.5 text-[10px] font-bold bg-amber-500/20 text-amber-400 rounded">
                            필수
                        </span>
                    )}
                </div>
                <p className="text-sm text-white font-medium leading-relaxed">
                    {guide.value}
                </p>
                <p className="text-xs text-white/50 mt-1">
                    {guide.guide}
                </p>
            </div>
        </button>
    );
}

export default MiseEnSceneOnboarding;
