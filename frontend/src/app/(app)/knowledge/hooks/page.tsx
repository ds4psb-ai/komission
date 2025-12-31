'use client';

import { useEffect, useState, useRef } from 'react';
import { api, HookLibraryResponse, HookPattern } from '@/lib/api';
import { motion } from 'framer-motion';
import { Zap, Eye, Volume2, Clock, ArrowRight } from 'lucide-react';
import Link from 'next/link';

// Mock data for demo
const MOCK_HOOKS: HookPattern[] = [
    { pattern_code: "question_hook", pattern_type: "hook", confidence_score: 92, sample_count: 847, avg_retention: 68, description: "영상 시작 3초 이내 시청자에게 직접 질문을 던지는 패턴. '이거 진짜일까요?', '당신도 이런 경험 있나요?' 형태가 효과적." },
    { pattern_code: "shock_reveal", pattern_type: "visual", confidence_score: 88, sample_count: 523, avg_retention: 72, description: "예상치 못한 시각적 반전으로 시작. Before/After, 숨겨진 것 공개 등. 첫 프레임부터 호기심 유발." },
    { pattern_code: "countdown_tension", pattern_type: "timing", confidence_score: 85, sample_count: 312, avg_retention: 61, description: "카운트다운 또는 타이머를 활용한 긴장감 조성. '3초 안에 찾으세요', '10초 뒤에 공개' 등." },
    { pattern_code: "pov_immersion", pattern_type: "visual", confidence_score: 82, sample_count: 428, avg_retention: 65, description: "1인칭 시점(POV)으로 시청자를 영상 속 상황에 직접 배치. 공감 및 몰입도 극대화." },
    { pattern_code: "asmr_sound", pattern_type: "audio", confidence_score: 79, sample_count: 651, avg_retention: 58, description: "음식, 제품 등의 ASMR 사운드로 청각적 자극. 무음 버전 대비 평균 1.4배 시청 시간." },
    { pattern_code: "text_overlay_hook", pattern_type: "hook", confidence_score: 76, sample_count: 892, avg_retention: 55, description: "화면 상단에 임팩트 있는 텍스트 오버레이. '절대 따라하지 마세요', '마지막이 충격' 등 클릭베이트 스타일." },
];

const MOCK_LIBRARY: HookLibraryResponse = {
    total_patterns: 6,
    top_hooks: MOCK_HOOKS,
    categories: ["hook", "visual", "audio", "timing"],
    last_updated: new Date().toISOString(),
};

const CATEGORY_CONFIG: Record<string, { icon: typeof Zap; label: string; color: string }> = {
    hook: { icon: Zap, label: "훅", color: "text-pink-400" },
    visual: { icon: Eye, label: "시각", color: "text-violet-400" },
    audio: { icon: Volume2, label: "오디오", color: "text-cyan-400" },
    timing: { icon: Clock, label: "타이밍", color: "text-amber-400" },
};

export default function HookLibraryPage() {
    const [library, setLibrary] = useState<HookLibraryResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
    const isMountedRef = useRef(true);

    useEffect(() => {
        loadHooks();
    }, []);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    const loadHooks = async () => {
        try {
            const data = await api.getHookLibrary({ limit: 50 });
            const hasQualityData = data.top_hooks?.length > 0 &&
                data.top_hooks.some(h => h.confidence_score > 50);
            if (!isMountedRef.current) return;
            setLibrary(hasQualityData ? data : MOCK_LIBRARY);
        } catch (e) {
            console.warn("Hook API failed, using mock:", e);
            if (isMountedRef.current) {
                setLibrary(MOCK_LIBRARY);
            }
        } finally {
            if (isMountedRef.current) {
                setLoading(false);
            }
        }
    };

    const filteredHooks = library?.top_hooks.filter(h =>
        !selectedCategory || h.pattern_type === selectedCategory
    ) || [];

    return (
        <div className="p-8">
            <div className="max-w-7xl mx-auto space-y-6">
                {/* Header */}
                <header>
                    <h1 className="text-3xl font-bold text-white">
                        훅 라이브러리
                    </h1>
                    <p className="text-white/50 mt-2 max-w-2xl">
                        바이럴 영상에서 추출한 고성과 오프닝 패턴 컬렉션. 신뢰도가 높은 패턴을 참고해 콘텐츠를 제작하세요.
                    </p>
                </header>

                {/* Filters */}
                {library?.categories && (
                    <div className="flex gap-2 overflow-x-auto pb-2">
                        <button
                            onClick={() => setSelectedCategory(null)}
                            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors whitespace-nowrap
                                ${!selectedCategory ? 'bg-white text-black' : 'bg-white/10 hover:bg-white/20 text-white'}`}
                        >
                            전체
                        </button>
                        {library.categories.map(cat => {
                            const config = CATEGORY_CONFIG[cat] || { icon: Zap, label: cat, color: "text-white" };
                            const Icon = config.icon;
                            return (
                                <button
                                    key={cat}
                                    onClick={() => setSelectedCategory(cat)}
                                    className={`px-4 py-2 rounded-full text-sm font-medium transition-colors whitespace-nowrap flex items-center gap-1.5
                                        ${selectedCategory === cat ? 'bg-white text-black' : 'bg-white/10 hover:bg-white/20 text-white'}`}
                                >
                                    <Icon className="w-3.5 h-3.5" />
                                    {config.label}
                                </button>
                            );
                        })}
                    </div>
                )}

                {/* Grid */}
                {loading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 animate-pulse">
                        {[1, 2, 3, 4, 5, 6].map(i => (
                            <div key={i} className="h-56 bg-white/5 rounded-xl border border-white/10" />
                        ))}
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                        {filteredHooks.map((hook, idx) => (
                            <HookCard key={hook.pattern_code} hook={hook} index={idx} />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

function HookCard({ hook, index }: { hook: HookPattern; index: number }) {
    const scoreColor = hook.confidence_score > 85 ? 'text-green-400' :
        hook.confidence_score > 70 ? 'text-cyan-400' : 'text-yellow-400';

    const config = CATEGORY_CONFIG[hook.pattern_type] || { icon: Zap, label: hook.pattern_type, color: "text-white" };

    return (
        <motion.div
            className="bg-white/5 border border-white/10 p-5 rounded-xl hover:border-violet-500/50 transition-all group relative"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.05 }}
        >
            {/* Rank number */}
            <div className="absolute top-3 right-3 text-4xl font-black text-white/5">
                {index + 1}
            </div>

            {/* Category & Confidence */}
            <div className="flex justify-between items-start mb-3 relative z-10">
                <span className={`${config.color} bg-white/5 px-2 py-1 rounded text-xs uppercase tracking-wider font-bold flex items-center gap-1`}>
                    <config.icon className="w-3 h-3" />
                    {config.label}
                </span>
                <div className="text-right">
                    <span className={`text-xl font-black ${scoreColor}`}>
                        {Math.round(hook.confidence_score)}%
                    </span>
                    <div className="text-[10px] text-white/40 uppercase">신뢰도</div>
                </div>
            </div>

            {/* Title */}
            <h3 className="text-lg font-bold mb-2 text-white group-hover:text-pink-300 transition-colors">
                {hook.pattern_code.replace(/_/g, ' ')}
            </h3>

            {/* Description */}
            <p className="text-sm text-gray-400 mb-4 line-clamp-2">
                {hook.description || "설명 없음"}
            </p>

            {/* Stats */}
            <div className="flex items-center gap-4 text-xs font-mono text-gray-500 border-t border-white/10 pt-3">
                <div className="flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                    샘플: {hook.sample_count}개
                </div>
                {hook.avg_retention && (
                    <div className="flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-purple-500" />
                        유지율: {hook.avg_retention}%
                    </div>
                )}
            </div>

            {/* Action */}
            <Link
                href={`/canvas?pattern=${hook.pattern_code}`}
                className="mt-4 w-full py-2 bg-white/5 hover:bg-violet-500/20 rounded border border-white/10 hover:border-violet-500/30 text-sm font-medium transition-all flex items-center justify-center gap-2 text-white/70 hover:text-white"
            >
                캔버스에서 적용하기
                <ArrowRight className="w-3.5 h-3.5" />
            </Link>
        </motion.div>
    );
}
