'use client';

import { useTranslations } from 'next-intl';

/**
 * Pattern Library Page (PEGL v1.0)
 * 
 * NotebookLM Pattern Engine의 출력물인 PatternLibrary를 조회/탐색
 * - invariant_rules: 불변 규칙
 * - mutation_strategy: 변주 포인트
 * - citations: 출처
 */

import { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { api, PatternLibraryItem, PatternLibraryResponse } from '@/lib/api';
import { BookOpen, Clock, ArrowRight, Lightbulb, Repeat } from 'lucide-react';
import Link from 'next/link';

// Mock data for fallback
const MOCK_PATTERNS: PatternLibraryItem[] = [
    {
        id: 'mock-1',
        pattern_id: 'tiktok_beauty_hook2s_v1',
        cluster_id: 'hook-2s',
        temporal_phase: 'T1',
        platform: 'tiktok',
        category: 'beauty',
        invariant_rules: {
            "첫 2초 시선 고정": "얼굴/제품 클로즈업으로 시작",
            "음악 싱크": "비트 드롭에 핵심 장면 배치",
            "텍스트 오버레이": "상단 1/3에 후킹 텍스트"
        },
        mutation_strategy: {
            "배경 변경": { risk: "low", impact: "+5~15%" },
            "컬러 그레이딩": { risk: "medium", impact: "+10~25%" },
            "트랜지션 스타일": { risk: "low", impact: "+3~8%" }
        },
        citations: ["video_001", "video_002", "video_003"],
        revision: 1,
        created_at: new Date().toISOString(),
    },
    {
        id: 'mock-2',
        pattern_id: 'youtube_shorts_unboxing_v2',
        cluster_id: 'unboxing-reveal',
        temporal_phase: 'T2',
        platform: 'youtube',
        category: 'tech',
        invariant_rules: {
            "박스 클로즈업": "개봉 전 박스 전체 샷",
            "손 동작": "천천히 개봉하는 손 ASMR",
            "반응샷": "제품 공개 직후 표정 반응"
        },
        mutation_strategy: {
            "개봉 속도": { risk: "high", impact: "+20~40%" },
            "조명 설정": { risk: "low", impact: "+5~10%" }
        },
        citations: ["video_101", "video_102"],
        revision: 2,
        created_at: new Date(Date.now() - 86400000).toISOString(),
    },
];

const MOCK_LIBRARY: PatternLibraryResponse = {
    total: 2,
    patterns: MOCK_PATTERNS,
};

export default function PatternLibraryPage() {
    const t = useTranslations('pages.knowledge.patterns');
    const [library, setLibrary] = useState<PatternLibraryResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);
    const isMountedRef = useRef(true);

    useEffect(() => {
        loadPatterns();
    }, []);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    const loadPatterns = async () => {
        try {
            const data = await api.getPatternLibrary({ limit: 50 });
            // Use real data if available, otherwise fallback to mock
            const hasData = data.patterns?.length > 0;
            if (!isMountedRef.current) return;
            setLibrary(hasData ? data : MOCK_LIBRARY);
        } catch (e) {
            console.warn("Pattern Library API failed, using mock:", e);
            if (!isMountedRef.current) return;
            setLibrary(MOCK_LIBRARY);
        } finally {
            if (isMountedRef.current) {
                setLoading(false);
            }
        }
    };

    const filteredPatterns = library?.patterns.filter(p =>
        !selectedPlatform || p.platform === selectedPlatform
    ) || [];

    const platforms = [...new Set(library?.patterns.map(p => p.platform) || [])];

    return (
        <div className="p-8">
            <div className="max-w-7xl mx-auto space-y-6">
                {/* Header */}
                <header>
                    <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                        <BookOpen className="w-8 h-8 text-violet-400" />
                        {t('title')}
                    </h1>
                    <p className="text-white/50 mt-2 max-w-2xl whitespace-pre-line">
                        {t('subtitle')}
                    </p>
                </header>

                {/* Filters */}
                {platforms.length > 0 && (
                    <div className="flex gap-2 overflow-x-auto pb-2">
                        <button
                            onClick={() => setSelectedPlatform(null)}
                            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors whitespace-nowrap
                                ${!selectedPlatform ? 'bg-white text-black' : 'bg-white/10 hover:bg-white/20 text-white'}`}
                        >
                            {t('all')}
                        </button>
                        {platforms.map(platform => (
                            <button
                                key={platform}
                                onClick={() => setSelectedPlatform(platform)}
                                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors whitespace-nowrap
                                    ${selectedPlatform === platform ? 'bg-white text-black' : 'bg-white/10 hover:bg-white/20 text-white'}`}
                            >
                                {platform === 'tiktok' ? '🎵 TikTok' :
                                    platform === 'youtube' ? '▶️ YouTube' :
                                        platform === 'instagram' ? '📷 Instagram' : platform}
                            </button>
                        ))}
                    </div>
                )}

                {/* Stats */}
                <div className="flex gap-4 text-sm text-white/40">
                    <span>{library?.total || 0}{t('stats.patterns')}</span>
                    <span>•</span>
                    <span>{platforms.length}{t('stats.platforms')}</span>
                </div>

                {/* Grid */}
                {loading ? (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 animate-pulse">
                        {[1, 2, 3, 4].map(i => (
                            <div key={i} className="h-72 bg-white/5 rounded-xl border border-white/10" />
                        ))}
                    </div>
                ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                        {filteredPatterns.map((pattern, idx) => (
                            <PatternCard key={pattern.id} pattern={pattern} index={idx} />
                        ))}
                    </div>
                )}

                {filteredPatterns.length === 0 && !loading && (
                    <div className="text-center py-12 text-white/40">
                        <BookOpen className="w-12 h-12 mx-auto mb-4 opacity-50" />
                        <p>{t('emptyState')}</p>
                        <p className="text-sm mt-2">{t('emptyStateHint')}</p>
                    </div>
                )}
            </div>
        </div>
    );
}

function PatternCard({ pattern, index }: { pattern: PatternLibraryItem; index: number }) {
    const t = useTranslations('pages.knowledge.patterns');
    const invariantCount = Object.keys(pattern.invariant_rules || {}).length;
    const mutationCount = Object.keys(pattern.mutation_strategy || {}).length;

    return (
        <motion.div
            className="bg-white/5 border border-white/10 rounded-xl overflow-hidden hover:border-violet-500/50 transition-all group"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
        >
            {/* Header */}
            <div className="px-5 py-4 border-b border-[#c1ff00]/20 bg-black/40 backdrop-blur-md">
                <div className="flex items-start justify-between">
                    <div>
                        <h3 className="text-lg font-bold text-white group-hover:text-violet-300 transition-colors">
                            {pattern.pattern_id.replace(/_/g, ' ')}
                        </h3>
                        <div className="flex items-center gap-2 mt-1 text-xs text-white/40">
                            <span className="px-2 py-0.5 bg-white/5 rounded">{pattern.platform}</span>
                            <span>•</span>
                            <span>{pattern.category}</span>
                            <span>•</span>
                            <span>{pattern.temporal_phase}</span>
                        </div>
                    </div>
                    <div className="text-right">
                        <div className="text-xs text-white/40">v{pattern.revision}</div>
                        <div className="text-[10px] text-white/30">{pattern.cluster_id}</div>
                    </div>
                </div>
            </div>

            {/* Body */}
            <div className="px-5 py-4 space-y-4">
                {/* Invariant Rules */}
                <div>
                    <div className="flex items-center gap-2 text-xs text-violet-400 font-bold mb-2">
                        <Lightbulb className="w-3.5 h-3.5" />
                        {t('invariantRules')} ({invariantCount})
                    </div>
                    <div className="space-y-1.5">
                        {Object.entries(pattern.invariant_rules || {}).slice(0, 3).map(([key, value]) => (
                            <div key={key} className="flex text-xs">
                                <span className="text-white/60 w-1/3 truncate">{key}</span>
                                <span className="text-white/40 flex-1 truncate">{String(value)}</span>
                            </div>
                        ))}
                        {invariantCount > 3 && (
                            <div className="text-xs text-white/30">+{invariantCount - 3}{t('more')}</div>
                        )}
                    </div>
                </div>

                {/* Mutation Strategy */}
                <div>
                    <div className="flex items-center gap-2 text-xs text-pink-400 font-bold mb-2">
                        <Repeat className="w-3.5 h-3.5" />
                        {t('mutationStrategy')} ({mutationCount})
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                        {Object.entries(pattern.mutation_strategy || {}).slice(0, 4).map(([key, val]) => {
                            const value = val as { risk?: string; impact?: string } | string;
                            const risk = typeof value === 'object' ? value.risk : 'unknown';
                            const riskColor = risk === 'low' ? 'border-emerald-500/30 text-emerald-400' :
                                risk === 'medium' ? 'border-amber-500/30 text-amber-400' :
                                    'border-red-500/30 text-red-400';
                            return (
                                <span
                                    key={key}
                                    className={`px-2 py-1 rounded text-[10px] border bg-white/5 ${riskColor}`}
                                >
                                    {key}
                                </span>
                            );
                        })}
                    </div>
                </div>
            </div>

            {/* Footer */}
            <div className="px-5 py-3 border-t border-white/5 flex items-center justify-between text-xs text-white/40">
                <div className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(pattern.created_at).toLocaleDateString('ko-KR')}
                </div>
                <Link
                    href={`/canvas?pattern=${pattern.pattern_id}`}
                    className="flex items-center gap-1 text-violet-400 hover:text-violet-300 transition-colors"
                >
                    {t('applyInCanvas')}
                    <ArrowRight className="w-3 h-3" />
                </Link>
            </div>
        </motion.div>
    );
}
