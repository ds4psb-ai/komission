"use client";

/**
 * For You Page - Answer-First 패턴 추천
 * 
 * API 연동 완료 버전
 * - GET /api/v1/for-you 실제 호출
 * - 카테고리/플랫폼 필터
 * - Session 흐름 연계
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { RefreshCw, Filter, Sparkles, ChevronRight, Play, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import PatternAnswerCard, { PatternAnswerCardProps } from '@/components/PatternAnswerCard';
import EvidenceBar, { BestComment, RecurrenceEvidence, RiskTag } from '@/components/EvidenceBar';
import FeedbackWidget, { FeedbackData } from '@/components/FeedbackWidget';

// API Response Types
interface ApiComment {
    text: string;
    likes: number;
    lang: string;
    translation_en?: string;
}

interface ApiRecommendation {
    id: string;
    outlier_id: string;
    title: string | null;
    video_url: string;
    thumbnail_url: string | null;
    platform: string;
    category: string;
    tier: 'S' | 'A' | 'B' | 'C';
    outlier_score: number | null;
    evidence: {
        best_comments: ApiComment[];
        total_views: number;
        engagement_rate: number | null;
        growth_rate: string | null;
    };
    recurrence: {
        ancestor_cluster_id: string | null;
        recurrence_score: number | null;
        recurrence_count: number;
    } | null;
    cluster_id?: string;
    cluster_name?: string;
}

interface ForYouApiResponse {
    recommendations: ApiRecommendation[];
    total_count: number;
    has_more: boolean;
}

// Filter options
const CATEGORIES = ['all', 'beauty', 'meme', 'food', 'fashion', 'trending'];
const PLATFORMS = ['all', 'tiktok', 'youtube', 'instagram'];

const CATEGORY_LABELS: Record<string, string> = {
    all: '전체',
    beauty: '뷰티',
    meme: '밈',
    food: '푸드',
    fashion: '패션',
    trending: '트렌딩',
    tech: '테크',
    lifestyle: '라이프',
    entertainment: '엔터',
};

const PLATFORM_LABELS: Record<string, string> = {
    all: '전체',
    tiktok: '틱톡',
    youtube: '유튜브 쇼츠',
    instagram: '인스타 릴스',
};

const formatCategoryLabel = (value: string) => CATEGORY_LABELS[value] || value;
const formatPlatformLabel = (value: string) => PLATFORM_LABELS[value] || value;

export default function ForYouPage() {
    const router = useRouter();

    // State
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [recommendations, setRecommendations] = useState<ApiRecommendation[]>([]);
    const [topPattern, setTopPattern] = useState<ApiRecommendation | null>(null);
    const [isEvidenceExpanded, setIsEvidenceExpanded] = useState(false);

    // Filters
    const [showFilters, setShowFilters] = useState(false);
    const [category, setCategory] = useState('all');
    const [platform, setPlatform] = useState('all');

    // Fetch recommendations from API
    const fetchRecommendations = useCallback(async () => {
        setIsLoading(true);
        setError(null);

        try {
            const params = new URLSearchParams();
            if (category !== 'all') params.append('category', category);
            if (platform !== 'all') params.append('platform', platform);
            params.append('limit', '10');

            const res = await fetch(`/api/v1/for-you?${params.toString()}`);

            if (!res.ok) {
                throw new Error(`API error: ${res.status}`);
            }

            const data: ForYouApiResponse = await res.json();
            setRecommendations(data.recommendations);
            setTopPattern(data.recommendations[0] || null);
        } catch (err) {
            console.error('Failed to fetch recommendations:', err);
            setError('추천을 불러오지 못했습니다');
        } finally {
            setIsLoading(false);
        }
    }, [category, platform]);

    useEffect(() => {
        fetchRecommendations();
    }, [fetchRecommendations]);

    // Convert API data to component props
    const mapToCardProps = (rec: ApiRecommendation): PatternAnswerCardProps & {
        best_comments: BestComment[];
        recurrence_evidence?: RecurrenceEvidence;
        risk_tags: RiskTag[];
    } => ({
        pattern_id: rec.id,
        cluster_id: rec.cluster_id || rec.category,
        pattern_summary: rec.title || `${formatPlatformLabel(rec.platform)} ${formatCategoryLabel(rec.category)} 패턴`,
        signature: {
            hook: rec.tier === 'S' ? '강력한 오프닝' : '일반 오프닝',
            timing: rec.evidence.growth_rate || '정보 없음',
            audio: rec.platform === 'tiktok' ? '틱톡 트렌딩 사운드' : '플랫폼 기본 사운드',
        },
        fit_score: (rec.outlier_score || 100) / 1000,
        evidence_strength: rec.evidence.best_comments.length,
        tier: rec.tier === 'C' ? 'B' : rec.tier,  // Map C → B for component compatibility
        platform: rec.platform as 'tiktok' | 'youtube' | 'instagram',
        recurrence: rec.recurrence?.recurrence_score ? {
            status: 'confirmed' as const,
            ancestor_cluster_id: rec.recurrence.ancestor_cluster_id || undefined,
            recurrence_score: rec.recurrence.recurrence_score,
            origin_year: 2024,
        } : undefined,
        best_comments: rec.evidence.best_comments.map((c, i) => ({
            text: c.text,
            likes: c.likes,
            lang: (c.lang === 'ko' || c.lang === 'en' ? c.lang : 'other') as 'ko' | 'en' | 'other',
            tag: i === 0 ? 'hook' as const : undefined,
        })),
        recurrence_evidence: rec.recurrence?.recurrence_score ? {
            ancestor_cluster_id: rec.recurrence.ancestor_cluster_id || '',
            recurrence_score: rec.recurrence.recurrence_score,
            historical_lift: rec.evidence.growth_rate || '정보 없음',
            origin_year: 2024,
        } : undefined,
        risk_tags: [],
    });

    const handleViewEvidence = () => {
        setIsEvidenceExpanded(!isEvidenceExpanded);
    };

    const handleShoot = () => {
        if (!topPattern) return;
        // Navigate to session with pattern
        router.push(`/session/result?pattern=${topPattern.id}`);
    };

    const handleSelectPattern = (pattern: ApiRecommendation) => {
        setTopPattern(pattern);
        setIsEvidenceExpanded(false);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const handleFeedback = (feedback: FeedbackData) => {
        console.log('Feedback submitted:', feedback);
        // TODO: POST to API
    };

    const handleWatchVideo = (url: string) => {
        window.open(url, '_blank');
    };

    return (
        <div className="min-h-screen pb-24">
            {/* Header Actions */}
            <div className="sticky top-16 z-30 flex justify-between items-center px-4 py-2 max-w-lg mx-auto">
                <button
                    onClick={() => setShowFilters(!showFilters)}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-full transition-colors ${showFilters ? 'bg-purple-500/30 text-purple-300' : 'bg-white/10 text-white/60 hover:bg-white/20'
                        }`}
                >
                    <Filter className="w-4 h-4" />
                    <span className="text-sm">필터</span>
                </button>

                <button
                    onClick={fetchRecommendations}
                    disabled={isLoading}
                    className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors backdrop-blur-sm disabled:opacity-50"
                >
                    <RefreshCw className={`w-5 h-5 text-white/60 ${isLoading ? 'animate-spin' : ''}`} />
                </button>
            </div>

            {/* Filter Panel */}
            <AnimatePresence>
                {showFilters && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden max-w-lg mx-auto px-4"
                    >
                        <div className="py-4 space-y-4 border-b border-white/10">
                            {/* Category Filter */}
                            <div>
                                <label className="text-xs text-white/40 mb-2 block">카테고리</label>
                                <div className="flex flex-wrap gap-2">
                                    {CATEGORIES.map((cat) => (
                                        <button
                                            key={cat}
                                            onClick={() => setCategory(cat)}
                                            className={`px-3 py-1 rounded-full text-sm transition-colors ${category === cat
                                                ? 'bg-purple-500 text-white'
                                                : 'bg-white/10 text-white/60 hover:bg-white/20'
                                                }`}
                                        >
                                            {formatCategoryLabel(cat)}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Platform Filter */}
                            <div>
                                <label className="text-xs text-white/40 mb-2 block">플랫폼</label>
                                <div className="flex flex-wrap gap-2">
                                    {PLATFORMS.map((plat) => (
                                        <button
                                            key={plat}
                                            onClick={() => setPlatform(plat)}
                                            className={`px-3 py-1 rounded-full text-sm transition-colors ${platform === plat
                                                ? 'bg-blue-500 text-white'
                                                : 'bg-white/10 text-white/60 hover:bg-white/20'
                                                }`}
                                        >
                                            {formatPlatformLabel(plat)}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            <main className="max-w-lg mx-auto px-4 py-6 space-y-6">
                {/* Error State */}
                {error && (
                    <div className="p-4 rounded-xl bg-red-500/20 border border-red-500/30 text-red-300 text-center">
                        {error}
                        <button
                            onClick={fetchRecommendations}
                            className="block mx-auto mt-2 text-sm underline"
                        >
                            다시 시도
                        </button>
                    </div>
                )}

                {/* Loading State */}
                {isLoading && (
                    <div className="space-y-4">
                        <div className="h-64 rounded-2xl bg-white/5 animate-pulse" />
                        <div className="h-12 rounded-xl bg-white/5 animate-pulse" />
                    </div>
                )}

                {/* Empty State */}
                {!isLoading && !error && recommendations.length === 0 && (
                    <div className="text-center py-16">
                        <Sparkles className="w-12 h-12 text-white/20 mx-auto mb-4" />
                        <p className="text-white/60">아직 분석된 패턴이 없습니다</p>
                        <p className="text-sm text-white/40 mt-2">곧 새로운 추천이 도착합니다!</p>
                    </div>
                )}

                {/* Top Pattern Answer */}
                {!isLoading && topPattern && (
                    <motion.div
                        key={topPattern.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="space-y-4"
                    >
                        {/* Video Preview Button */}
                        <button
                            onClick={() => handleWatchVideo(topPattern.video_url)}
                            className="w-full relative aspect-video rounded-xl overflow-hidden group"
                        >
                            {topPattern.thumbnail_url ? (
                                <img
                                    src={topPattern.thumbnail_url}
                                    alt={topPattern.title || '영상 썸네일'}
                                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                                />
                            ) : (
                                <div className="w-full h-full bg-gradient-to-br from-purple-900/50 to-blue-900/50 flex items-center justify-center">
                                    <Play className="w-16 h-16 text-white/50" />
                                </div>
                            )}
                            <div className="absolute inset-0 bg-black/30 group-hover:bg-black/10 transition-colors flex items-center justify-center">
                                <div className="w-16 h-16 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center">
                                    <Play className="w-8 h-8 text-white ml-1" />
                                </div>
                            </div>
                            {/* Tier Badge */}
                            <div className={`absolute top-3 left-3 px-3 py-1 rounded-full text-sm font-bold ${topPattern.tier === 'S' ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white' :
                                topPattern.tier === 'A' ? 'bg-purple-500/80 text-white' :
                                    'bg-blue-500/80 text-white'
                                }`}>
                                {topPattern.tier}티어
                            </div>
                            {/* Platform Badge */}
                            <div className="absolute top-3 right-3 px-2 py-1 rounded bg-black/50 text-xs text-white/80 backdrop-blur-sm">
                                {formatPlatformLabel(topPattern.platform)}
                            </div>
                        </button>

                        {/* Answer Card with Evidence */}
                        <PatternAnswerCard
                            {...mapToCardProps(topPattern)}
                            onViewEvidence={handleViewEvidence}
                            onShoot={handleShoot}
                            isEvidenceExpanded={isEvidenceExpanded}
                        >
                            <EvidenceBar
                                best_comments={mapToCardProps(topPattern).best_comments}
                                recurrence={mapToCardProps(topPattern).recurrence_evidence}
                                risk_tags={mapToCardProps(topPattern).risk_tags}
                                evidence_count={topPattern.evidence.best_comments.length}
                                confidence_label={topPattern.tier === 'S' ? 'strong' : 'moderate'}
                            />
                        </PatternAnswerCard>

                        {/* Stats Bar */}
                        <div className="flex items-center justify-between px-4 py-3 rounded-xl bg-white/5 border border-white/10">
                            <div className="text-center">
                                <div className="text-lg font-bold text-white">
                                    {(topPattern.evidence.total_views / 1000000).toFixed(1)}M
                                </div>
                                <div className="text-xs text-white/40">조회수</div>
                            </div>
                            <div className="h-8 w-px bg-white/10" />
                            <div className="text-center">
                                <div className="text-lg font-bold text-green-400">
                                    {topPattern.evidence.growth_rate || '정보 없음'}
                                </div>
                                <div className="text-xs text-white/40">성장률</div>
                            </div>
                            <div className="h-8 w-px bg-white/10" />
                            <div className="text-center">
                                <div className="text-lg font-bold text-purple-400">
                                    {topPattern.outlier_score?.toFixed(0) || '정보 없음'}
                                </div>
                                <div className="text-xs text-white/40">점수</div>
                            </div>
                        </div>

                        {/* Feedback Widget */}
                        <div className="px-4 py-2 rounded-xl bg-white/5 border border-white/10">
                            <FeedbackWidget
                                pattern_id={topPattern.id}
                                context="answer_card"
                                onSubmit={handleFeedback}
                            />
                        </div>
                    </motion.div>
                )}

                {/* Other Recommendations */}
                {!isLoading && recommendations.length > 1 && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.2 }}
                        className="space-y-3"
                    >
                        <h2 className="text-sm font-medium text-white/40 px-1">
                            다른 추천 ({recommendations.length - 1})
                        </h2>
                        {recommendations.slice(1).map((pattern) => (
                            <button
                                key={pattern.id}
                                onClick={() => handleSelectPattern(pattern)}
                                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl border transition-all ${topPattern?.id === pattern.id
                                    ? 'bg-purple-500/20 border-purple-500/50'
                                    : 'bg-white/5 border-white/10 hover:bg-white/10'
                                    }`}
                            >
                                {/* Thumbnail */}
                                <div className="w-16 h-16 rounded-lg overflow-hidden flex-shrink-0 bg-white/10">
                                    {pattern.thumbnail_url ? (
                                        <img
                                            src={pattern.thumbnail_url}
                                            alt=""
                                            className="w-full h-full object-cover"
                                        />
                                    ) : (
                                        <div className="w-full h-full flex items-center justify-center">
                                            <Play className="w-6 h-6 text-white/30" />
                                        </div>
                                    )}
                                </div>

                                {/* Info */}
                                <div className="flex-1 text-left">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${pattern.tier === 'S' ? 'bg-gradient-to-r from-amber-500/30 to-orange-500/30 text-amber-300' :
                                            pattern.tier === 'A' ? 'bg-purple-500/30 text-purple-300' :
                                                'bg-blue-500/20 text-blue-300'
                                            }`}>
                                            {pattern.tier}
                                        </span>
                                        <span className="text-xs text-white/40">{pattern.platform}</span>
                                    </div>
                                    <p className="text-sm text-white/80 line-clamp-1">
                                        {pattern.title || `${formatCategoryLabel(pattern.category)} 패턴`}
                                    </p>
                                    <p className="text-xs text-white/40 mt-0.5">
                                        {(pattern.evidence.total_views / 1000000).toFixed(1)}M 조회 • {pattern.evidence.growth_rate || '정보 없음'}
                                    </p>
                                </div>

                                <ChevronRight className="w-5 h-5 text-white/30 flex-shrink-0" />
                            </button>
                        ))}
                    </motion.div>
                )}
            </main>
        </div>
    );
}
