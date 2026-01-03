'use client';

/**
 * Hook Library Page - 훅 패턴 학습 센터
 * 
 * 바이럴 영상의 첫 3초를 결정하는 핵심 오프닝 패턴들을 학습합니다.
 * - 질문형, 충격형, 몰입형 등 검증된 Hook 패턴
 * - 실제 바이럴 영상 예시와 함께 학습
 * - 캔버스에서 바로 적용 가능
 */

import { useTranslations } from 'next-intl';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap, Eye, Volume2, Clock, ArrowRight, Play, Star, TrendingUp, Sparkles, ChevronRight, ExternalLink } from 'lucide-react';
import Link from 'next/link';

// ===== Rich Mock Data =====
interface HookPattern {
    id: string;
    name: string;
    nameKo: string;
    category: 'hook' | 'visual' | 'audio' | 'timing';
    confidence: number;
    sampleCount: number;
    avgRetention: number;
    description: string;
    examples: {
        thumbnail: string;
        platform: 'tiktok' | 'instagram' | 'youtube';
        views: string;
        creator: string;
    }[];
    tips: string[];
    bestFor: string[];
}

const MOCK_PATTERNS: HookPattern[] = [
    {
        id: 'question_hook',
        name: 'Question Hook',
        nameKo: '질문형 훅',
        category: 'hook',
        confidence: 94,
        sampleCount: 1247,
        avgRetention: 72,
        description: '영상 시작 3초 이내에 시청자에게 직접 질문을 던지는 패턴. 호기심을 자극해 스크롤을 멈추게 합니다.',
        examples: [
            { thumbnail: '🤔', platform: 'tiktok', views: '2.3M', creator: '@beautyhacks' },
            { thumbnail: '❓', platform: 'instagram', views: '890K', creator: '@skincare_tips' },
        ],
        tips: [
            '"이거 진짜일까요?" - 진위 의문형',
            '"당신도 이런 경험 있나요?" - 공감 유도형',
            '"왜 아무도 이걸 안 알려줬을까?" - 비밀 공개형',
        ],
        bestFor: ['뷰티', '라이프핵', '정보성 콘텐츠'],
    },
    {
        id: 'shock_reveal',
        name: 'Shock Reveal',
        nameKo: '충격 반전 훅',
        category: 'visual',
        confidence: 91,
        sampleCount: 856,
        avgRetention: 78,
        description: '예상치 못한 시각적 반전으로 시작. Before/After, 숨겨진 것 공개 등으로 첫 프레임부터 시선을 사로잡습니다.',
        examples: [
            { thumbnail: '😱', platform: 'tiktok', views: '5.1M', creator: '@transformation' },
            { thumbnail: '🔥', platform: 'youtube', views: '1.2M', creator: '@makeupdaily' },
        ],
        tips: [
            '결과물을 먼저 보여주고 → 과정은 나중에',
            '극적인 대비를 위해 조명/각도 활용',
            '반전 효과음 + 텍스트 오버레이 필수',
        ],
        bestFor: ['메이크업', '다이어트', '리모델링', 'DIY'],
    },
    {
        id: 'pov_immersion',
        name: 'POV Immersion',
        nameKo: '1인칭 몰입형',
        category: 'visual',
        confidence: 88,
        sampleCount: 623,
        avgRetention: 68,
        description: '1인칭 시점(POV)으로 시청자를 영상 속 상황에 직접 배치. "POV: 당신은..." 형식으로 공감과 몰입도를 극대화합니다.',
        examples: [
            { thumbnail: '👁️', platform: 'tiktok', views: '3.8M', creator: '@dailypov' },
            { thumbnail: '🎭', platform: 'instagram', views: '720K', creator: '@actorlife' },
        ],
        tips: [
            'POV 텍스트를 1초 이내 등장',
            '시청자가 "나"로 느낄 수 있는 상황 설정',
            '감정 공감 (분노, 기쁨, 당황) 극대화',
        ],
        bestFor: ['일상 브이로그', '드라마/연기', '공감 콘텐츠'],
    },
    {
        id: 'asmr_trigger',
        name: 'ASMR Trigger',
        nameKo: 'ASMR 청각 훅',
        category: 'audio',
        confidence: 85,
        sampleCount: 1089,
        avgRetention: 64,
        description: '음식, 제품 등의 ASMR 사운드로 청각적 자극. 무음 버전 대비 평균 1.4배 높은 시청 시간을 기록합니다.',
        examples: [
            { thumbnail: '🍗', platform: 'tiktok', views: '8.2M', creator: '@mukbangking' },
            { thumbnail: '📦', platform: 'youtube', views: '2.1M', creator: '@unboxing_asmr' },
        ],
        tips: [
            '마이크 가까이에서 선명한 소리 수집',
            '바삭/쫀득/뽀드득 등 의태어 텍스트 추가',
            '음향 없이 시작 → 갑자기 ASMR 터트리기',
        ],
        bestFor: ['먹방', '언박싱', '스킨케어', 'GRWM'],
    },
    {
        id: 'countdown_tension',
        name: 'Countdown Tension',
        nameKo: '카운트다운 긴장감',
        category: 'timing',
        confidence: 82,
        sampleCount: 445,
        avgRetention: 71,
        description: '카운트다운 또는 타이머를 활용한 긴장감 조성. "3초 안에 찾으세요", "10초 뒤 공개" 형식으로 이탈을 방지합니다.',
        examples: [
            { thumbnail: '⏱️', platform: 'tiktok', views: '1.5M', creator: '@puzzlegames' },
            { thumbnail: '🔢', platform: 'instagram', views: '560K', creator: '@quickchallenge' },
        ],
        tips: [
            '짧은 카운트다운 (3-5초)이 가장 효과적',
            '시각적 타이머 + 긴장감 있는 BGM',
            '실패 시 리워치 유도 → 조회수 증가',
        ],
        bestFor: ['퀴즈', '챌린지', '숨은그림찾기', '게임'],
    },
    {
        id: 'text_overlay_bait',
        name: 'Text Overlay Bait',
        nameKo: '텍스트 클릭베이트',
        category: 'hook',
        confidence: 79,
        sampleCount: 1523,
        avgRetention: 58,
        description: '화면 상단에 임팩트 있는 텍스트 오버레이. "절대 따라하지 마세요", "마지막이 충격" 등 호기심을 자극합니다.',
        examples: [
            { thumbnail: '⚠️', platform: 'tiktok', views: '4.7M', creator: '@viralclips' },
            { thumbnail: '💀', platform: 'instagram', views: '1.8M', creator: '@shocking_facts' },
        ],
        tips: [
            '글자 크기는 화면의 20% 이상',
            '노란색/빨간색 계열이 주목도 높음',
            '과장은 OK, 거짓은 NG (신뢰도 하락)',
        ],
        bestFor: ['정보성', '반전 콘텐츠', '리스트형'],
    },
];

const CATEGORY_CONFIG: Record<string, { icon: typeof Zap; label: string; labelEn: string; color: string; bg: string }> = {
    hook: { icon: Zap, label: '훅', labelEn: 'Hook', color: 'text-pink-400', bg: 'bg-pink-500/10 border-pink-500/20' },
    visual: { icon: Eye, label: '시각', labelEn: 'Visual', color: 'text-violet-400', bg: 'bg-violet-500/10 border-violet-500/20' },
    audio: { icon: Volume2, label: '오디오', labelEn: 'Audio', color: 'text-cyan-400', bg: 'bg-cyan-500/10 border-cyan-500/20' },
    timing: { icon: Clock, label: '타이밍', labelEn: 'Timing', color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/20' },
};

export default function HookLibraryPage() {
    const t = useTranslations('pages.knowledge');
    const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
    const [expandedPattern, setExpandedPattern] = useState<string | null>(null);

    const filteredPatterns = MOCK_PATTERNS.filter(p =>
        !selectedCategory || p.category === selectedCategory
    );

    const categories = ['hook', 'visual', 'audio', 'timing'];

    return (
        <div className="p-6 lg:p-8">
            <div className="max-w-7xl mx-auto space-y-8">
                {/* Hero Header */}
                <header className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-pink-500/10 via-violet-500/10 to-cyan-500/10 border border-white/10 p-8 lg:p-10">
                    <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-5" />
                    <div className="relative z-10">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="p-3 rounded-2xl bg-pink-500/20 border border-pink-500/30">
                                <Zap className="w-6 h-6 text-pink-400" />
                            </div>
                            <span className="px-3 py-1 text-xs font-bold uppercase tracking-wider bg-[#c1ff00]/10 text-[#c1ff00] rounded-full border border-[#c1ff00]/20">
                                학습 센터
                            </span>
                        </div>
                        <h1 className="text-3xl lg:text-4xl font-black text-white mb-3">
                            훅 패턴 라이브러리
                        </h1>
                        <p className="text-white/60 max-w-2xl text-lg leading-relaxed">
                            바이럴 영상의 첫 3초를 결정하는 검증된 오프닝 패턴들.
                            <br className="hidden lg:block" />
                            <span className="text-white/80">1,000개+ 바이럴 영상</span>에서 추출한 핵심 훅 전략을 학습하세요.
                        </p>
                    </div>

                    {/* Stats Bar */}
                    <div className="relative z-10 mt-8 flex flex-wrap gap-6 text-sm">
                        <div className="flex items-center gap-2">
                            <Star className="w-4 h-4 text-amber-400" />
                            <span className="text-white/40">평균 신뢰도</span>
                            <span className="font-bold text-white">86%</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <TrendingUp className="w-4 h-4 text-emerald-400" />
                            <span className="text-white/40">평균 리텐션</span>
                            <span className="font-bold text-white">68%</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <Sparkles className="w-4 h-4 text-violet-400" />
                            <span className="text-white/40">총 패턴</span>
                            <span className="font-bold text-white">{MOCK_PATTERNS.length}개</span>
                        </div>
                    </div>
                </header>

                {/* Category Filters */}
                <div className="flex gap-3 overflow-x-auto pb-2">
                    <button
                        onClick={() => setSelectedCategory(null)}
                        className={`px-5 py-2.5 rounded-xl text-sm font-bold transition-all whitespace-nowrap flex items-center gap-2
                            ${!selectedCategory
                                ? 'bg-white text-black shadow-lg shadow-white/20'
                                : 'bg-white/5 hover:bg-white/10 text-white border border-white/10'}`}
                    >
                        전체
                        <span className="text-xs opacity-60">{MOCK_PATTERNS.length}</span>
                    </button>
                    {categories.map(cat => {
                        const config = CATEGORY_CONFIG[cat];
                        const Icon = config.icon;
                        const count = MOCK_PATTERNS.filter(p => p.category === cat).length;
                        return (
                            <button
                                key={cat}
                                onClick={() => setSelectedCategory(cat)}
                                className={`px-5 py-2.5 rounded-xl text-sm font-bold transition-all whitespace-nowrap flex items-center gap-2
                                    ${selectedCategory === cat
                                        ? 'bg-white text-black shadow-lg shadow-white/20'
                                        : `bg-white/5 hover:bg-white/10 text-white border border-white/10`}`}
                            >
                                <Icon className={`w-4 h-4 ${selectedCategory === cat ? 'text-black' : config.color}`} />
                                {config.label}
                                <span className="text-xs opacity-60">{count}</span>
                            </button>
                        );
                    })}
                </div>

                {/* Pattern Cards */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                    <AnimatePresence mode="popLayout">
                        {filteredPatterns.map((pattern, idx) => (
                            <PatternCard
                                key={pattern.id}
                                pattern={pattern}
                                index={idx}
                                isExpanded={expandedPattern === pattern.id}
                                onToggle={() => setExpandedPattern(
                                    expandedPattern === pattern.id ? null : pattern.id
                                )}
                            />
                        ))}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
}

function PatternCard({
    pattern,
    index,
    isExpanded,
    onToggle,
}: {
    pattern: HookPattern;
    index: number;
    isExpanded: boolean;
    onToggle: () => void;
}) {
    const config = CATEGORY_CONFIG[pattern.category];
    const Icon = config.icon;

    const confidenceColor = pattern.confidence >= 90 ? 'text-emerald-400' :
        pattern.confidence >= 80 ? 'text-cyan-400' : 'text-amber-400';

    return (
        <motion.div
            layout
            className={`bg-white/5 border border-white/10 rounded-2xl overflow-hidden transition-all hover:border-white/20 ${isExpanded ? 'lg:col-span-2' : ''}`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ delay: index * 0.05 }}
        >
            {/* Header */}
            <div
                className="p-5 cursor-pointer"
                onClick={onToggle}
            >
                <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                        {/* Category & Confidence */}
                        <div className="flex items-center gap-3 mb-3">
                            <span className={`${config.bg} ${config.color} px-3 py-1 rounded-lg text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 border`}>
                                <Icon className="w-3 h-3" />
                                {config.label}
                            </span>
                            <div className="flex items-center gap-1.5">
                                <span className={`text-lg font-black ${confidenceColor}`}>
                                    {pattern.confidence}%
                                </span>
                                <span className="text-white/30 text-xs">신뢰도</span>
                            </div>
                        </div>

                        {/* Title */}
                        <h3 className="text-xl font-bold text-white mb-1 group-hover:text-pink-300 transition-colors">
                            {pattern.nameKo}
                        </h3>
                        <p className="text-xs text-white/40 font-mono">{pattern.name}</p>
                    </div>

                    {/* Expand Indicator */}
                    <motion.div
                        animate={{ rotate: isExpanded ? 90 : 0 }}
                        className="p-2 rounded-lg bg-white/5"
                    >
                        <ChevronRight className="w-5 h-5 text-white/40" />
                    </motion.div>
                </div>

                {/* Description */}
                <p className="text-sm text-gray-400 mt-3 leading-relaxed">
                    {pattern.description}
                </p>

                {/* Quick Stats */}
                <div className="flex items-center gap-5 mt-4 text-xs">
                    <div className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-blue-500" />
                        <span className="text-white/50">샘플</span>
                        <span className="text-white font-bold">{pattern.sampleCount.toLocaleString()}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-purple-500" />
                        <span className="text-white/50">평균 리텐션</span>
                        <span className="text-white font-bold">{pattern.avgRetention}%</span>
                    </div>
                </div>
            </div>

            {/* Expanded Content */}
            <AnimatePresence>
                {isExpanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                    >
                        <div className="px-5 pb-5 space-y-5 border-t border-white/10 pt-5">
                            {/* Examples */}
                            <div>
                                <h4 className="text-xs font-bold text-white/40 uppercase tracking-wider mb-3">
                                    바이럴 예시
                                </h4>
                                <div className="flex gap-3">
                                    {pattern.examples.map((ex, i) => (
                                        <div key={i} className="flex-1 bg-black/40 border border-white/10 rounded-xl p-4 flex items-center gap-3">
                                            <div className="w-12 h-12 rounded-lg bg-white/5 flex items-center justify-center text-2xl">
                                                {ex.thumbnail}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="text-sm font-medium text-white truncate">{ex.creator}</div>
                                                <div className="flex items-center gap-2 text-xs text-white/40">
                                                    <span>{ex.platform}</span>
                                                    <span>•</span>
                                                    <span className="text-emerald-400 font-bold">{ex.views}</span>
                                                </div>
                                            </div>
                                            <Play className="w-4 h-4 text-white/20" />
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Tips */}
                            <div>
                                <h4 className="text-xs font-bold text-white/40 uppercase tracking-wider mb-3">
                                    적용 팁
                                </h4>
                                <div className="space-y-2">
                                    {pattern.tips.map((tip, i) => (
                                        <div key={i} className="flex items-start gap-2 text-sm text-white/70">
                                            <span className="text-[#c1ff00]">•</span>
                                            {tip}
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Best For */}
                            <div>
                                <h4 className="text-xs font-bold text-white/40 uppercase tracking-wider mb-3">
                                    추천 카테고리
                                </h4>
                                <div className="flex flex-wrap gap-2">
                                    {pattern.bestFor.map((cat, i) => (
                                        <span key={i} className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg text-xs text-white/60">
                                            {cat}
                                        </span>
                                    ))}
                                </div>
                            </div>

                            {/* Action */}
                            <Link
                                href={`/canvas?hook=${pattern.id}`}
                                className="block w-full py-3 bg-gradient-to-r from-pink-500/20 to-violet-500/20 hover:from-pink-500/30 hover:to-violet-500/30 border border-pink-500/20 rounded-xl text-center text-sm font-bold text-white transition-all flex items-center justify-center gap-2"
                            >
                                <Sparkles className="w-4 h-4" />
                                캔버스에서 적용하기
                                <ArrowRight className="w-4 h-4" />
                            </Link>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
}
