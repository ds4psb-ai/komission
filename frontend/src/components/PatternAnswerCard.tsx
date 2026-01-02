"use client";

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Zap, Timer, Music, ChevronDown, Camera, LucideIcon } from 'lucide-react';

export interface PatternAnswerCardProps {
    pattern_id: string;
    cluster_id: string;
    pattern_summary: string;
    signature: {
        hook: string;
        timing: string;
        audio: string;
    };
    fit_score: number;
    evidence_strength: number;
    tier: 'S' | 'A' | 'B';
    platform: 'tiktok' | 'youtube' | 'instagram';
    recurrence?: {
        status: 'confirmed' | 'candidate' | 'unmatched';
        ancestor_cluster_id?: string;
        recurrence_score?: number;
        origin_year?: number;
    };
    // 신뢰 시그널 (NEW)
    trust_signals?: {
        analyzed_videos?: number;      // 분석된 영상 수
        avg_views?: number;            // 평균 조회수
        top_percentile?: number;       // 상위 N%
        expected_filming_mins?: number; // 예상 촬영 시간
    };
    onViewEvidence?: () => void;
    onShoot?: () => void;
    isEvidenceExpanded?: boolean;
    children?: React.ReactNode;
}

export default function PatternAnswerCard({
    cluster_id,
    pattern_summary,
    signature,
    fit_score,
    evidence_strength,
    tier,
    platform,
    recurrence,
    trust_signals,
    onViewEvidence,
    onShoot,
    isEvidenceExpanded = false,
    children
}: PatternAnswerCardProps) {
    // Determine colors based on tier
    const getTierGradient = () => {
        switch (tier) {
            case 'S': return 'from-amber-300 via-yellow-400 to-orange-500';
            case 'A': return 'from-violet-400 to-purple-600';
            case 'B': return 'from-blue-400 to-indigo-600';
            default: return 'from-gray-400 to-gray-600';
        }
    };

    const getGlowColor = () => {
        switch (tier) {
            case 'S': return 'rgba(251, 191, 36, 0.2)';
            case 'A': return 'rgba(139, 92, 246, 0.2)';
            case 'B': return 'rgba(59, 130, 246, 0.2)';
        }
    };

    const platformLabelMap: Record<typeof platform, string> = {
        tiktok: '틱톡',
        youtube: '유튜브 쇼츠',
        instagram: '인스타 릴스',
    };
    const platformLabel = platformLabelMap[platform] || platform;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="relative w-full"
        >
            {/* Main Card Container */}
            <div
                className={`
                    relative overflow-hidden rounded-3xl border 
                    bg-[#0A0A0C]/80 backdrop-blur-3xl
                    transition-all duration-300
                    ${tier === 'S' ? 'border-amber-500/30' : 'border-white/10'}
                `}
                style={{
                    boxShadow: `0 0 40px -10px ${getGlowColor()}`
                }}
            >
                {/* S-Tier Ambient Effect */}
                {tier === 'S' && (
                    <div className="absolute -top-20 -right-20 w-40 h-40 bg-amber-500/20 blur-[60px] rounded-full pointer-events-none" />
                )}

                {/* Header Section */}
                <div className="p-6 pb-4">
                    <div className="flex items-start justify-between mb-4">
                        {/* Tier Badge */}
                        <div className="relative group">
                            <div className={`
                                absolute inset-0 rounded-xl blur-sm opacity-50 
                                bg-gradient-to-r ${getTierGradient()}
                            `} />
                            <div className={`
                                relative flex items-center gap-1.5 px-3 py-1.5 rounded-xl 
                                bg-gradient-to-b from-[#1a1a1c] to-[#0A0A0C] border border-white/10
                            `}>
                                <span className={`font-black text-lg bg-gradient-to-br ${getTierGradient()} bg-clip-text text-transparent`}>
                                    {tier}티어
                                </span>
                                {tier === 'S' && (
                                    <Sparkles className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
                                )}
                            </div>
                        </div>

                        {/* Recurrence Badge */}
                        {recurrence?.status === 'confirmed' && (
                            <motion.div
                                initial={{ opacity: 0, x: 10 }}
                                animate={{ opacity: 1, x: 0 }}
                                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400"
                            >
                                <RotateCw className="w-3.5 h-3.5" />
                                <span className="text-xs font-bold">재등장</span>
                            </motion.div>
                        )}
                    </div>

                    {/* Title */}
                    <div className="mb-6">
                        <div className="text-xs font-mono text-white/40 mb-1 flex items-center gap-2">
                            <span>#{cluster_id}</span>
                            <span className="w-1 h-1 rounded-full bg-white/20" />
                            <span>{platformLabel}</span>
                        </div>
                        <h2 className="text-2xl font-bold text-white leading-tight text-balance">
                            {pattern_summary}
                        </h2>
                    </div>

                    {/* Signature Pills - Detailed Specs */}
                    <div className="grid grid-cols-1 gap-2.5">
                        <SignatureRow
                            icon={Zap}
                            label="훅"
                            value={signature.hook}
                            color="text-yellow-300"
                            bg="bg-yellow-500/10"
                        />
                        <SignatureRow
                            icon={Timer}
                            label="타이밍"
                            value={signature.timing}
                            color="text-cyan-300"
                            bg="bg-cyan-500/10"
                        />
                        <SignatureRow
                            icon={Music}
                            label="오디오"
                            value={signature.audio}
                            color="text-pink-300"
                            bg="bg-pink-500/10"
                        />
                    </div>

                    {/* 신뢰 시그널 배너 */}
                    {trust_signals && (trust_signals.analyzed_videos || trust_signals.avg_views) && (
                        <div className="mt-4 p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/20">
                            <div className="flex items-center gap-2 text-emerald-400 text-xs font-medium mb-2">
                                <span>📊</span>
                                <span>AI 데이터 기반 분석</span>
                            </div>
                            <div className="grid grid-cols-2 gap-3 text-xs">
                                {trust_signals.analyzed_videos && (
                                    <div>
                                        <span className="text-white/50">분석 영상 </span>
                                        <span className="text-white font-bold">{trust_signals.analyzed_videos.toLocaleString()}개</span>
                                    </div>
                                )}
                                {trust_signals.avg_views && (
                                    <div>
                                        <span className="text-white/50">평균 조회수 </span>
                                        <span className="text-white font-bold">{(trust_signals.avg_views / 10000).toFixed(0)}만</span>
                                    </div>
                                )}
                                {trust_signals.top_percentile && (
                                    <div>
                                        <span className="text-white/50">성과 상위 </span>
                                        <span className="text-emerald-400 font-bold">{trust_signals.top_percentile}%</span>
                                    </div>
                                )}
                                {trust_signals.expected_filming_mins && (
                                    <div>
                                        <span className="text-white/50">예상 촬영 </span>
                                        <span className="text-white font-bold">~{trust_signals.expected_filming_mins}분</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>

                {/* Stats Bar */}
                <div className="px-6 py-4 border-t border-white/5 bg-white/[0.02] flex items-center justify-between">
                    <div className="flex items-center gap-6">
                        <div className="text-center">
                            <div className="text-[10px] text-white/40 font-medium uppercase tracking-wider mb-0.5">적합도</div>
                            <div className="text-lg font-bold text-white">
                                {Math.round(fit_score * 100)}%
                            </div>
                        </div>
                        <div className="w-px h-8 bg-white/10" />
                        <div className="text-center">
                            <div className="text-[10px] text-white/40 font-medium uppercase tracking-wider mb-0.5">증거</div>
                            <div className="text-lg font-bold text-white flex items-center gap-1">
                                {evidence_strength}
                                <span className="text-xs font-normal text-white/50">건</span>
                            </div>
                        </div>
                    </div>

                    <motion.button
                        whileTap={{ scale: 0.95 }}
                        onClick={onViewEvidence}
                        className={`
                            p-2 rounded-full transition-colors
                            ${isEvidenceExpanded ? 'bg-white/10 text-white' : 'hover:bg-white/10 text-white/50'}
                        `}
                    >
                        <ChevronDown className={`w-5 h-5 transition-transform duration-300 ${isEvidenceExpanded ? 'rotate-180' : ''}`} />
                    </motion.button>
                </div>

                {/* Expanded Logic (Evidence) */}
                <AnimatePresence>
                    {isEvidenceExpanded && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.3 }}
                            className="overflow-hidden bg-[#050505]/50 border-t border-white/5"
                        >
                            <div className="p-6">
                                {children}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Primary CTA */}
                <div className="p-4 border-t border-white/5">
                    <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={onShoot}
                        className={`
                            w-full py-4 rounded-2xl font-bold text-lg flex items-center justify-center gap-2 shadow-lg
                            bg-gradient-to-r ${getTierGradient()} text-white
                        `}
                        style={{
                            textShadow: '0 1px 2px rgba(0,0,0,0.2)'
                        }}
                    >
                        <Camera className="w-5 h-5" />
                        촬영 가이드 시작
                    </motion.button>
                </div>
            </div>
        </motion.div>
    );
}

// Sub-component for neat rows
interface SignatureRowProps {
    icon: LucideIcon;
    label: string;
    value: string;
    color: string;
    bg: string;
}

function SignatureRow({ icon: Icon, label, value, color, bg }: SignatureRowProps) {
    return (
        <div className="flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-white/5">
            <div className={`p-2 rounded-lg ${bg} ${color}`}>
                <Icon className="w-4 h-4" />
            </div>
            <div className="flex-1">
                <div className="text-[10px] text-white/40 font-medium uppercase">{label}</div>
                <div className="text-sm font-medium text-white/90">{value}</div>
            </div>
        </div>
    );
}

// Helper icon
function RotateCw({ className }: { className?: string }) {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
        >
            <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8" />
            <path d="M21 3v5h-5" />
        </svg>
    );
}
