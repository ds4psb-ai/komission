'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { api, OutlierItem } from '@/lib/api';
import { HubCard, HubCardData, SpokeOptionData, HubSpokesTransition } from '@/components/hub';
import { AgentAccordion, KomiAvatar } from '@/components/agent';
import { ArrowLeft, Sparkles, RefreshCw, AlertCircle } from 'lucide-react';
import Link from 'next/link';

/**
 * For You 페이지 - 추천 바이럴 레퍼런스
 */
export default function ForYouPage() {
    const [outliers, setOutliers] = useState<OutlierItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedOutlier, setSelectedOutlier] = useState<OutlierItem | null>(null);
    const [showTransition, setShowTransition] = useState(false);
    const [agentOpen, setAgentOpen] = useState(false);

    // Mock 데이터
    const MOCK_OUTLIERS: OutlierItem[] = [
        {
            id: 'mock-1',
            external_id: 'abc123',
            video_url: 'https://tiktok.com/@user/video/123',
            platform: 'tiktok',
            category: 'lifestyle',
            title: '이거 진짜 대박... 3일만에 100만뷰 🔥',
            thumbnail_url: 'https://picsum.photos/seed/hub1/400/700',
            view_count: 1250000,
            like_count: 45000,
            share_count: 8200,
            outlier_score: 0.92,
            outlier_tier: 'S',
            creator_avg_views: 25000,
            creator_username: 'viral_master',
            engagement_rate: 0.045,
            crawled_at: new Date().toISOString(),
            status: 'selected',
            analysis_status: 'completed',
            promoted_to_node_id: null,
            best_comments_count: 15,
            vdg_analysis: {
                title: '3일만에 100만뷰 달성',
                hook_genome: { pattern: 'Curiosity Gap', strength: 0.95 },
            },
        },
        {
            id: 'mock-2',
            external_id: 'def456',
            video_url: 'https://youtube.com/shorts/xyz',
            platform: 'youtube',
            category: 'food',
            title: '편의점 꿀조합 레시피 (진짜 맛있음)',
            thumbnail_url: 'https://picsum.photos/seed/hub2/400/700',
            view_count: 890000,
            like_count: 32000,
            share_count: 5400,
            outlier_score: 0.87,
            outlier_tier: 'A',
            creator_avg_views: 18000,
            creator_username: 'food_explorer',
            engagement_rate: 0.038,
            crawled_at: new Date().toISOString(),
            status: 'selected',
            analysis_status: 'completed',
            promoted_to_node_id: null,
            best_comments_count: 12,
            vdg_analysis: {
                title: '편의점 꿀조합',
                hook_genome: { pattern: 'How-To Reveal', strength: 0.88 },
            },
        },
        {
            id: 'mock-3',
            external_id: 'ghi789',
            video_url: 'https://tiktok.com/@creator/video/789',
            platform: 'tiktok',
            category: 'beauty',
            title: '이 립 진짜 미쳤어... 완판 전에 사세요',
            thumbnail_url: 'https://picsum.photos/seed/hub3/400/700',
            view_count: 2100000,
            like_count: 78000,
            share_count: 15000,
            outlier_score: 0.95,
            outlier_tier: 'S',
            creator_avg_views: 45000,
            creator_username: 'beauty_queen',
            engagement_rate: 0.052,
            crawled_at: new Date().toISOString(),
            status: 'selected',
            analysis_status: 'completed',
            promoted_to_node_id: null,
            best_comments_count: 22,
            vdg_analysis: {
                title: '완판 립 리뷰',
                hook_genome: { pattern: 'FOMO Urgency', strength: 0.91 },
            },
        },
        {
            id: 'mock-4',
            external_id: 'jkl012',
            video_url: 'https://instagram.com/reels/abc',
            platform: 'instagram',
            category: 'fitness',
            title: '2주만에 복근 만드는 운동 (진짜임)',
            thumbnail_url: 'https://picsum.photos/seed/hub4/400/700',
            view_count: 650000,
            like_count: 28000,
            share_count: 4200,
            outlier_score: 0.82,
            outlier_tier: 'A',
            creator_avg_views: 15000,
            creator_username: 'fit_coach',
            engagement_rate: 0.041,
            crawled_at: new Date().toISOString(),
            status: 'selected',
            analysis_status: 'completed',
            promoted_to_node_id: null,
            best_comments_count: 8,
            vdg_analysis: {
                title: '2주 복근 챌린지',
                hook_genome: { pattern: 'Transformation Promise', strength: 0.85 },
            },
        },
    ];

    useEffect(() => {
        loadOutliers();
    }, []);

    const loadOutliers = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await api.listOutliers({
                limit: 10,
                status: 'selected',
                sortBy: 'outlier_score'
            });
            setOutliers(response.items.length > 0 ? response.items : MOCK_OUTLIERS);
        } catch {
            setOutliers(MOCK_OUTLIERS);
        } finally {
            setLoading(false);
        }
    };

    const toHubCardData = (outlier: OutlierItem): HubCardData => ({
        id: outlier.id,
        videoId: outlier.external_id,
        thumbnailUrl: outlier.thumbnail_url || '/placeholder-thumb.jpg',
        title: outlier.title || outlier.vdg_analysis?.title || '제목 없음',
        patternName: outlier.vdg_analysis?.hook_genome?.pattern || `Tier ${outlier.outlier_tier}`,
        views: outlier.view_count,
        score: Math.round(outlier.outlier_score * 100),
    });

    const generateSpokeOptions = (outlier: OutlierItem): SpokeOptionData[] => {
        const hookPattern = outlier.vdg_analysis?.hook_genome?.pattern || 'hook';
        return [
            { id: 'spoke-hook', type: 'hook', label: '훅 변주', description: `"${hookPattern}" 패턴을 내 스타일로 재해석`, confidence: 85 },
            { id: 'spoke-audio', type: 'audio', label: '오디오 변주', description: '같은 구조, 새로운 음악/보이스', confidence: 72 },
            { id: 'spoke-visual', type: 'visual', label: '비주얼 변주', description: '샷 구성과 색감만 참고', confidence: 68 },
            { id: 'spoke-trend', type: 'trend', label: '트렌드 믹스', description: '최신 트렌드와 결합', confidence: 58 },
        ];
    };

    const handleCardClick = (outlier: OutlierItem) => {
        setSelectedOutlier(outlier);
        setShowTransition(true);
    };

    const handleTransitionComplete = (spoke: SpokeOptionData) => {
        console.log('Selected spoke:', spoke);
        setShowTransition(false);
        setSelectedOutlier(null);
    };

    const handleTransitionCancel = () => {
        setShowTransition(false);
        setSelectedOutlier(null);
    };

    return (
        <div className="min-h-screen bg-[#0a0a0c] text-white pb-24">
            {/* Header */}
            <header className="sticky top-0 z-20 bg-[#0a0a0c]/90 backdrop-blur-sm border-b border-white/5 px-4 py-3">
                <div className="flex items-center justify-between max-w-lg mx-auto">
                    <Link href="/" className="flex items-center gap-2 text-white/60 hover:text-white transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                        <span className="text-sm">홈</span>
                    </Link>
                    <h1 className="font-bold">For You</h1>
                    <button onClick={loadOutliers} className="p-2 rounded-full hover:bg-white/10 transition-colors" disabled={loading}>
                        <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                </div>
            </header>

            {/* Banner */}
            <div className="px-4 py-3 bg-[#c1ff00]/10 border-b border-[#c1ff00]/20">
                <div className="max-w-lg mx-auto flex items-center gap-3">
                    <Sparkles className="w-5 h-5 text-[#c1ff00] flex-shrink-0" />
                    <p className="text-sm text-white/80">당신을 위한 바이럴 레퍼런스를 추천해드려요</p>
                </div>
            </div>

            {/* Content */}
            <main className="px-4 py-6 max-w-lg mx-auto">
                {error && (
                    <div className="flex items-center gap-3 p-4 rounded-2xl bg-red-500/10 border border-red-500/20 mb-6">
                        <AlertCircle className="w-5 h-5 text-red-400" />
                        <div>
                            <p className="text-sm text-red-400">{error}</p>
                            <button onClick={loadOutliers} className="text-xs text-red-300 underline mt-1">다시 시도</button>
                        </div>
                    </div>
                )}

                {loading && (
                    <div className="flex flex-col items-center justify-center py-20">
                        <RefreshCw className="w-8 h-8 text-[#c1ff00] animate-spin mb-4" />
                        <p className="text-white/50 text-sm">추천 콘텐츠 로딩 중...</p>
                    </div>
                )}

                {!loading && !error && (
                    <div className="grid grid-cols-2 gap-3">
                        {outliers.map((outlier, index) => (
                            <motion.div
                                key={outlier.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.08, duration: 0.2 }}
                            >
                                <HubCard
                                    data={toHubCardData(outlier)}
                                    layoutId={`hub-card-${outlier.id}`}
                                    onClick={() => handleCardClick(outlier)}
                                />
                            </motion.div>
                        ))}
                    </div>
                )}

                {!loading && !error && outliers.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-20">
                        <AlertCircle className="w-12 h-12 text-white/20 mb-4" />
                        <p className="text-white/50 text-sm mb-2">추천할 콘텐츠가 없습니다</p>
                    </div>
                )}
            </main>

            {/* Hub-Spokes Transition */}
            {selectedOutlier && (
                <HubSpokesTransition
                    parentCard={toHubCardData(selectedOutlier)}
                    spokeOptions={generateSpokeOptions(selectedOutlier)}
                    isActive={showTransition}
                    onComplete={handleTransitionComplete}
                    onCancel={handleTransitionCancel}
                />
            )}

            {/* Komi Agent */}
            <AgentAccordion isOpen={agentOpen} onToggle={setAgentOpen} agentName="Komi" unreadCount={agentOpen ? 0 : 1}>
                <div className="flex flex-col gap-4">
                    <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 mt-1"><KomiAvatar size="sm" isSpeaking /></div>
                        <div className="bg-[#c1ff00]/10 border border-[#c1ff00]/20 rounded-2xl rounded-tl-none p-3 max-w-[85%]">
                            <p className="text-sm text-[#c1ff00] font-medium mb-1">Hub-Spokes 추천 완료</p>
                            <p className="text-sm text-white/90 leading-relaxed">
                                현재 선택하신 아웃라이어는 <span className="text-[#c1ff00]">"Curiosity Gap"</span> 패턴이 강력합니다.
                                훅 변주를 적용하시면 조회수 성과를 그대로 가져가면서 차별화할 수 있어요.
                            </p>
                        </div>
                    </div>
                    <div className="flex items-end justify-end gap-2">
                        <div className="bg-white/10 rounded-2xl rounded-tr-none p-3 max-w-[80%]">
                            <p className="text-sm text-white/90">오디오 변주는 어때?</p>
                        </div>
                    </div>
                    <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 mt-1"><KomiAvatar size="sm" /></div>
                        <div className="bg-white/5 border border-white/10 rounded-2xl rounded-tl-none p-3 max-w-[85%]">
                            <p className="text-sm text-white/80 leading-relaxed">
                                오디오 변주는 리스크가 조금 있습니다(72%).
                                원본의 나레이션 톤이 성과에 큰 영향을 미치고 있어서, 완전히 다른 오디오를 쓰면 이탈률이 15% 증가할 것으로 예측됩니다.
                            </p>
                        </div>
                    </div>
                </div>
            </AgentAccordion>
        </div>
    );
}
