'use client';

import { useEffect, useState, useRef } from 'react';
import { api, EvidenceGuide } from '@/lib/api';
import { motion } from 'framer-motion';
import { BookOpen, Target, TrendingUp, ArrowRight, Play } from 'lucide-react';
import Link from 'next/link';

// Mock data matching API type
const MOCK_GUIDES: EvidenceGuide[] = [
    {
        id: "guide-1",
        parent_title: "질문형 Hook 실행 가이드",
        platform: "tiktok",
        category: "hook",
        confidence: 92,
        top_mutation_type: "hook",
        top_mutation_pattern: "question_hook",
        success_rate: "85%",
        recommendation: "3초 안에 시청자의 관심을 끄는 질문형 Hook 제작법. 데이터 기반으로 검증된 패턴을 따라 제작하세요.",
        sample_count: 234,
    },
    {
        id: "guide-2",
        parent_title: "Before/After Reveal 가이드",
        platform: "instagram",
        category: "visual",
        confidence: 88,
        top_mutation_type: "visual",
        top_mutation_pattern: "reveal_before_after",
        success_rate: "78%",
        recommendation: "시각적 변화를 활용한 Reveal 패턴. 뷰티, 인테리어, 다이어트 카테고리에서 특히 효과적.",
        sample_count: 156,
    },
    {
        id: "guide-3",
        parent_title: "ASMR 청각 자극 가이드",
        platform: "youtube",
        category: "audio",
        confidence: 79,
        top_mutation_type: "audio",
        top_mutation_pattern: "asmr_crunch",
        success_rate: "71%",
        recommendation: "오디오 경험을 극대화하는 ASMR 패턴. 음식, 제품 리뷰에서 시청 시간을 1.4배 늘릴 수 있습니다.",
        sample_count: 189,
    },
];

export default function EvidenceGuidesPage() {
    const [guides, setGuides] = useState<EvidenceGuide[]>([]);
    const [loading, setLoading] = useState(true);
    const isMountedRef = useRef(true);

    useEffect(() => {
        loadGuides();
    }, []);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    const loadGuides = async () => {
        try {
            const data = await api.getEvidenceGuides();
            if (!isMountedRef.current) return;
            setGuides(data.guides?.length > 0 ? data.guides : MOCK_GUIDES);
        } catch (e) {
            console.warn("Guides API failed, using mock:", e);
            if (isMountedRef.current) {
                setGuides(MOCK_GUIDES);
            }
        } finally {
            if (isMountedRef.current) {
                setLoading(false);
            }
        }
    };

    return (
        <div className="p-8">
            <div className="max-w-6xl mx-auto space-y-6">
                {/* Header */}
                <header>
                    <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                        <BookOpen className="w-8 h-8 text-emerald-400" />
                        실행 가이드
                    </h1>
                    <p className="text-white/50 mt-2 max-w-2xl">
                        검증된 패턴 기반의 콘텐츠 제작 가이드. 단계별로 따라하면 5분 안에 촬영을 시작할 수 있습니다.
                    </p>
                </header>

                {/* Grid */}
                {loading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-pulse">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="h-64 bg-white/5 rounded-xl border border-white/10" />
                        ))}
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {guides.map((guide, idx) => (
                            <GuideCard key={guide.id} guide={guide} index={idx} />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

function GuideCard({ guide, index }: { guide: EvidenceGuide; index: number }) {
    const platformColors: Record<string, string> = {
        tiktok: "bg-pink-500/20 text-pink-300 border-pink-500/30",
        instagram: "bg-purple-500/20 text-purple-300 border-purple-500/30",
        youtube: "bg-red-500/20 text-red-300 border-red-500/30",
    };
    const platformClass = platformColors[guide.platform] || "bg-white/10 text-white/70";

    return (
        <motion.div
            className="bg-white/5 border border-white/10 rounded-xl overflow-hidden hover:border-emerald-500/50 transition-all"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
        >
            {/* Header */}
            <div className="p-5 border-b border-white/10">
                <div className="flex items-start justify-between mb-3">
                    <span className={`px-2 py-1 rounded text-xs font-bold border ${platformClass}`}>
                        {guide.platform.toUpperCase()}
                    </span>
                    <div className="flex items-center gap-1 text-emerald-400">
                        <Target className="w-4 h-4" />
                        <span className="text-sm font-bold">{guide.confidence}%</span>
                    </div>
                </div>
                <h3 className="text-lg font-bold text-white mb-2">{guide.parent_title}</h3>
                <p className="text-sm text-white/40 line-clamp-2">{guide.recommendation}</p>
            </div>

            {/* Stats */}
            <div className="px-5 py-3 bg-black/20 flex items-center gap-6 text-sm">
                <div className="flex items-center gap-1.5">
                    <TrendingUp className="w-4 h-4 text-cyan-400" />
                    <span className="text-white/60">성공률:</span>
                    <span className="text-white font-medium">{guide.success_rate || 'N/A'}</span>
                </div>
                <div className="text-white/40">
                    샘플 {guide.sample_count}개
                </div>
            </div>

            {/* Pattern Info */}
            <div className="p-5">
                {guide.top_mutation_pattern && (
                    <div className="mb-4">
                        <div className="text-xs text-white/40 uppercase font-bold mb-2">탑 패턴</div>
                        <span className="px-2 py-1 bg-violet-500/10 text-violet-300 rounded text-xs border border-violet-500/20">
                            {guide.top_mutation_pattern.replace(/_/g, ' ')}
                        </span>
                    </div>
                )}

                <Link
                    href={`/remix/new?guide=${guide.id}`}
                    className="w-full py-2.5 bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/30 rounded-lg text-emerald-300 text-sm font-medium transition-all flex items-center justify-center gap-2"
                >
                    <Play className="w-4 h-4" />
                    촬영 시작하기
                    <ArrowRight className="w-3.5 h-3.5" />
                </Link>
            </div>
        </motion.div>
    );
}
