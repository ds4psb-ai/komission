"use client";
import { useTranslations } from 'next-intl';

/**
 * ConsentModal - MCP Tool 실행 동의 UI
 * 
 * 명시적 동의가 필요한 작업 (데이터 생성, 비용 발생) 실행 전 표시
 * - generate_source_pack
 * - reanalyze_vdg
 */
import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Sparkles, X, Check, DollarSign, Database, Zap } from 'lucide-react';

export type ConsentType = 'data_creation' | 'cost_incur' | 'external_api';

export interface ConsentAction {
    id: string;
    name: string;
    description: string;
    type: ConsentType;
    estimatedCost?: string;
    details?: string[];
}

interface ConsentModalProps {
    isOpen: boolean;
    action: ConsentAction | null;
    onConfirm: () => void;
    onCancel: () => void;
    isLoading?: boolean;
}

const TYPE_CONFIG: Record<ConsentType, {
    icon: typeof AlertTriangle;
    color: string;
    bgColor: string;
    label: string;
}> = {
    data_creation: {
        icon: Database,
        color: 'text-blue-400',
        bgColor: 'bg-blue-500/20',
        label: '데이터 생성',
    },
    cost_incur: {
        icon: DollarSign,
        color: 'text-amber-400',
        bgColor: 'bg-amber-500/20',
        label: '비용 발생',
    },
    external_api: {
        icon: Zap,
        color: 'text-purple-400',
        bgColor: 'bg-purple-500/20',
        label: '외부 API 호출',
    },
};

export default function ConsentModal({
    isOpen,
    action,
    onConfirm,
    onCancel,
    isLoading = false,
}: ConsentModalProps) {
    if (!action) return null;

    const config = TYPE_CONFIG[action.type];
    const Icon = config.icon;

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
                        onClick={onCancel}
                    />

                    {/* Modal */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                        className="fixed inset-x-4 top-1/2 -translate-y-1/2 mx-auto max-w-md z-50"
                    >
                        <div className="relative bg-gradient-to-b from-slate-800/90 to-slate-900/90 backdrop-blur-xl rounded-2xl border border-white/10 shadow-2xl overflow-hidden">
                            {/* Glow effect */}
                            <div className={`absolute inset-0 ${config.bgColor} opacity-10`} />

                            {/* Header */}
                            <div className="relative px-6 pt-6 pb-4 border-b border-white/10">
                                <button
                                    onClick={onCancel}
                                    className="absolute top-4 right-4 p-2 rounded-full hover:bg-white/10 transition-colors"
                                >
                                    <X className="w-5 h-5 text-white/60" />
                                </button>

                                <div className="flex items-center gap-3">
                                    <div className={`p-3 rounded-xl ${config.bgColor}`}>
                                        <Icon className={`w-6 h-6 ${config.color}`} />
                                    </div>
                                    <div>
                                        <h2 className="text-lg font-semibold text-white">
                                            동의가 필요합니다
                                        </h2>
                                        <p className="text-sm text-white/60">
                                            {config.label} 작업
                                        </p>
                                    </div>
                                </div>
                            </div>

                            {/* Content */}
                            <div className="relative px-6 py-5 space-y-4">
                                <div>
                                    <h3 className="text-base font-medium text-white mb-1">
                                        {action.name}
                                    </h3>
                                    <p className="text-sm text-white/70">
                                        {action.description}
                                    </p>
                                </div>

                                {/* Details */}
                                {action.details && action.details.length > 0 && (
                                    <div className="bg-white/5 rounded-xl p-4 space-y-2">
                                        <p className="text-xs font-medium text-white/40 uppercase tracking-wider">
                                            상세 정보
                                        </p>
                                        <ul className="space-y-1.5">
                                            {action.details.map((detail, i) => (
                                                <li key={i} className="flex items-start gap-2 text-sm text-white/70">
                                                    <span className="text-white/40">•</span>
                                                    {detail}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {/* Cost warning */}
                                {action.estimatedCost && (
                                    <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-amber-500/10 border border-amber-500/20">
                                        <DollarSign className="w-4 h-4 text-amber-400" />
                                        <span className="text-sm text-amber-300">
                                            예상 비용: {action.estimatedCost}
                                        </span>
                                    </div>
                                )}
                            </div>

                            {/* Footer */}
                            <div className="relative px-6 pb-6 pt-2 flex gap-3">
                                <button
                                    onClick={onCancel}
                                    disabled={isLoading}
                                    className="flex-1 py-3 px-4 rounded-xl bg-white/10 hover:bg-white/20 text-white/80 font-medium transition-colors disabled:opacity-50"
                                >
                                    취소
                                </button>
                                <button
                                    onClick={onConfirm}
                                    disabled={isLoading}
                                    className={`
                                        flex-1 py-3 px-4 rounded-xl font-medium transition-all
                                        flex items-center justify-center gap-2
                                        ${isLoading
                                            ? 'bg-gray-500 cursor-wait'
                                            : 'bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white shadow-lg shadow-purple-500/25'
                                        }
                                    `}
                                >
                                    {isLoading ? (
                                        <>
                                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                            진행 중...
                                        </>
                                    ) : (
                                        <>
                                            <Check className="w-4 h-4" />
                                            동의 및 실행
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
