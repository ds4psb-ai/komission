/**
 * STPF Components
 * 
 * STPF v3.1 시각 컴포넌트:
 * - STPFBadge: Go/No-Go 신호 배지
 * - STPFPanel: 전체 분석 패널
 * - STPFMeter: 점수 미터
 */
'use client';
import { useTranslations } from 'next-intl';

import React, { useState } from 'react';
import {
    TrendingUp, TrendingDown, Minus,
    CheckCircle, XCircle, AlertTriangle, HelpCircle,
    Zap, Target, Shield, DollarSign,
    ChevronDown, ChevronUp, Sparkles
} from 'lucide-react';

// ==================
// Types
// ==================

interface STPFGrade {
    grade: string;
    label: string;
    description: string;
    action: string;
    kelly_hint: string;
    color: string;
}

interface STPFBadgeProps {
    score: number;
    signal: 'GO' | 'CONSIDER' | 'NO-GO' | 'MODERATE' | 'CAUTION' | 'NO_GO';
    grade?: STPFGrade;
    size?: 'sm' | 'md' | 'lg';
    showScore?: boolean;
    onClick?: () => void;
}

// ==================
// Constants
// ==================

const SIGNAL_CONFIG = {
    'GO': {
        label: 'GO',
        icon: CheckCircle,
        bgColor: 'bg-emerald-500',
        textColor: 'text-white',
        borderColor: 'border-emerald-400',
        glowColor: 'shadow-emerald-500/50',
    },
    'CONSIDER': {
        label: 'CONSIDER',
        icon: AlertTriangle,
        bgColor: 'bg-yellow-500',
        textColor: 'text-black',
        borderColor: 'border-yellow-400',
        glowColor: 'shadow-yellow-500/50',
    },
    'MODERATE': {
        label: 'MODERATE',
        icon: Minus,
        bgColor: 'bg-blue-500',
        textColor: 'text-white',
        borderColor: 'border-blue-400',
        glowColor: 'shadow-blue-500/50',
    },
    'CAUTION': {
        label: 'CAUTION',
        icon: AlertTriangle,
        bgColor: 'bg-orange-500',
        textColor: 'text-white',
        borderColor: 'border-orange-400',
        glowColor: 'shadow-orange-500/50',
    },
    'NO-GO': {
        label: 'NO-GO',
        icon: XCircle,
        bgColor: 'bg-red-500',
        textColor: 'text-white',
        borderColor: 'border-red-400',
        glowColor: 'shadow-red-500/50',
    },
    'NO_GO': {
        label: 'NO-GO',
        icon: XCircle,
        bgColor: 'bg-red-500',
        textColor: 'text-white',
        borderColor: 'border-red-400',
        glowColor: 'shadow-red-500/50',
    },
};

const GRADE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
    'S': { bg: 'bg-[#c1ff00]/20', text: 'text-[#c1ff00]', border: 'border-[#c1ff00]/50' },
    'A': { bg: 'bg-purple-500/20', text: 'text-purple-300', border: 'border-purple-500/50' },
    'B': { bg: 'bg-blue-500/20', text: 'text-blue-300', border: 'border-blue-500/50' },
    'C': { bg: 'bg-zinc-500/20', text: 'text-zinc-400', border: 'border-zinc-500/50' },
};

const SIZE_CONFIG = {
    sm: { badge: 'px-2 py-1 text-xs', icon: 'w-3 h-3', score: 'text-xs' },
    md: { badge: 'px-3 py-1.5 text-sm', icon: 'w-4 h-4', score: 'text-sm' },
    lg: { badge: 'px-4 py-2 text-base', icon: 'w-5 h-5', score: 'text-base' },
};

// ==================
// STPFBadge Component
// ==================

export function STPFBadge({
    score,
    signal,
    grade,
    size = 'md',
    showScore = true,
    onClick,
}: STPFBadgeProps) {
    const config = SIGNAL_CONFIG[signal] || SIGNAL_CONFIG['CONSIDER'];
    const sizeConfig = SIZE_CONFIG[size];
    const Icon = config.icon;

    const gradeColor = grade ? GRADE_COLORS[grade.grade] || GRADE_COLORS['C'] : null;

    return (
        <div
            className={`
                inline-flex items-center gap-2 rounded-full font-bold
                ${config.bgColor} ${config.textColor}
                ${sizeConfig.badge}
                shadow-lg ${config.glowColor}
                ${onClick ? 'cursor-pointer hover:scale-105 transition-transform' : ''}
            `}
            onClick={onClick}
        >
            <Icon className={sizeConfig.icon} />
            <span>{config.label}</span>
            {showScore && (
                <span className={`opacity-90 ${sizeConfig.score}`}>
                    {score}
                </span>
            )}
            {grade && (
                <span className={`
                    ml-1 px-1.5 py-0.5 rounded text-xs font-bold
                    ${gradeColor?.bg} ${gradeColor?.text}
                `}>
                    {grade.grade}
                </span>
            )}
        </div>
    );
}

// ==================
// STPFMeter Component
// ==================

interface STPFMeterProps {
    score: number;
    showLabel?: boolean;
    height?: number;
}

export function STPFMeter({ score, showLabel = true, height = 8 }: STPFMeterProps) {
    // Calculate percentage and color
    const percentage = Math.min(100, Math.max(0, score / 10));

    const getColor = (s: number) => {
        if (s >= 700) return 'bg-emerald-500';
        if (s >= 500) return 'bg-yellow-500';
        if (s >= 300) return 'bg-orange-500';
        return 'bg-red-500';
    };

    return (
        <div className="w-full">
            {showLabel && (
                <div className="flex justify-between mb-1 text-xs text-gray-400">
                    <span>STPF Score</span>
                    <span className="font-bold">{score} / 1000</span>
                </div>
            )}
            <div
                className="w-full bg-gray-700 rounded-full overflow-hidden"
                style={{ height }}
            >
                <div
                    className={`h-full ${getColor(score)} transition-all duration-500 ease-out`}
                    style={{ width: `${percentage}%` }}
                />
            </div>
        </div>
    );
}

// ==================
// STPFPanel Component
// ==================

interface STPFPanelProps {
    score: number;
    signal: 'GO' | 'CONSIDER' | 'NO-GO' | 'MODERATE' | 'CAUTION' | 'NO_GO';
    grade?: STPFGrade;
    why?: string;
    how?: string[];
    kellyPercent?: number;
    expanded?: boolean;
    onToggle?: () => void;
}

export function STPFPanel({
    score,
    signal,
    grade,
    why,
    how,
    kellyPercent,
    expanded = false,
    onToggle,
}: STPFPanelProps) {
    const [isExpanded, setIsExpanded] = useState(expanded);

    const toggleExpand = () => {
        setIsExpanded(!isExpanded);
        onToggle?.();
    };

    const gradeColor = grade ? GRADE_COLORS[grade.grade] || GRADE_COLORS['C'] : null;

    return (
        <div className="bg-gray-800/80 backdrop-blur rounded-xl border border-gray-700 overflow-hidden">
            {/* Header */}
            <div
                className="p-4 flex items-center justify-between cursor-pointer hover:bg-white/5 transition-colors"
                onClick={toggleExpand}
            >
                <div className="flex items-center gap-3">
                    <Sparkles className="w-5 h-5 text-[#c1ff00]" />
                    <span className="font-bold text-white uppercase tracking-wider">STPF ANALYSIS</span>
                </div>
                <div className="flex items-center gap-3">
                    <STPFBadge score={score} signal={signal} grade={grade} size="sm" />
                    {isExpanded ? (
                        <ChevronUp className="w-5 h-5 text-gray-400" />
                    ) : (
                        <ChevronDown className="w-5 h-5 text-gray-400" />
                    )}
                </div>
            </div>

            {/* Expanded Content */}
            {isExpanded && (
                <div className="px-4 pb-4 space-y-4 border-t border-gray-700 pt-4">
                    {/* Score Meter */}
                    <STPFMeter score={score} />

                    {/* Grade Info */}
                    {grade && (
                        <div className={`p-3 rounded-lg ${gradeColor?.bg} ${gradeColor?.text}`}>
                            <div className="flex items-center justify-between mb-2">
                                <span className="font-bold text-lg">{grade.grade}</span>
                                <span className="text-sm opacity-90">{grade.label}</span>
                            </div>
                            <p className="text-sm opacity-80">{grade.description}</p>
                            <div className="mt-2 pt-2 border-t border-white/20">
                                <p className="text-sm font-medium">📌 {grade.action}</p>
                            </div>
                        </div>
                    )}

                    {/* Kelly Recommendation */}
                    {kellyPercent !== undefined && (
                        <div className="flex items-center gap-3 p-3 bg-gray-700/50 rounded-lg">
                            <Target className="w-5 h-5 text-blue-400" />
                            <div>
                                <div className="text-sm text-gray-400">권장 투자 비율</div>
                                <div className="text-xl font-bold text-white">
                                    {kellyPercent.toFixed(1)}%
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Why */}
                    {why && (
                        <div className="p-3 bg-gray-700/50 rounded-lg">
                            <div className="flex items-center gap-2 mb-2">
                                <HelpCircle className="w-4 h-4 text-yellow-400" />
                                <span className="text-sm font-bold text-white">Why</span>
                            </div>
                            <p className="text-sm text-gray-300">{why}</p>
                        </div>
                    )}

                    {/* How */}
                    {how && how.length > 0 && (
                        <div className="p-3 bg-gray-700/50 rounded-lg">
                            <div className="flex items-center gap-2 mb-2">
                                <Zap className="w-4 h-4 text-emerald-400" />
                                <span className="text-sm font-bold text-white">How (개선 방안)</span>
                            </div>
                            <ul className="space-y-1">
                                {how.slice(0, 3).map((item, idx) => (
                                    <li key={idx} className="text-sm text-gray-300 flex items-start gap-2">
                                        <span className="text-emerald-400">•</span>
                                        {item}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

// ==================
// STPFQuickView Component (Compact)
// ==================

interface STPFQuickViewProps {
    score: number;
    signal: 'GO' | 'CONSIDER' | 'NO-GO';
    grade?: string;
    loading?: boolean;
}

export function STPFQuickView({ score, signal, grade, loading }: STPFQuickViewProps) {
    if (loading) {
        return (
            <div className="flex items-center gap-2 px-3 py-2 bg-gray-800/60 rounded-lg animate-pulse">
                <div className="w-4 h-4 bg-gray-600 rounded-full" />
                <div className="w-16 h-4 bg-gray-600 rounded" />
            </div>
        );
    }

    const config = SIGNAL_CONFIG[signal] || SIGNAL_CONFIG['CONSIDER'];
    const Icon = config.icon;

    return (
        <div className={`
            inline-flex items-center gap-2 px-3 py-1.5 rounded-lg
            border ${config.borderColor} bg-gray-800/60
        `}>
            <Icon className={`w-4 h-4 ${config.bgColor.replace('bg-', 'text-')}`} />
            <span className="text-sm font-bold text-white">{score}</span>
            {grade && (
                <span className={`
                    text-xs font-bold px-1.5 py-0.5 rounded
                    ${GRADE_COLORS[grade]?.bg || 'bg-gray-600'} 
                    ${GRADE_COLORS[grade]?.text || 'text-white'}
                `}>
                    {grade}
                </span>
            )}
        </div>
    );
}

export default STPFBadge;
