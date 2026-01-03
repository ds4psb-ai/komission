'use client';

import { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { api, OutlierItem } from '@/lib/api';
import { HubCard, HubCardData, SpokeOptionData, HubSpokesTransition } from '@/components/hub';
import { AgentAccordion, KomiAvatar } from '@/components/agent';
import { LanguageGateBadge } from '@/components/outlier';
import { ArrowLeft, Sparkles, RefreshCw, AlertCircle, Globe, ChevronDown } from 'lucide-react';
import Link from 'next/link';

type LanguageFilter = 'all' | 'ko' | 'en';

// Extended mock type with language
interface MockOutlier extends OutlierItem {
    lang?: string;
    hasTranslation?: boolean;
}

export default function ForYouPage() {
    const [outliers, setOutliers] = useState<MockOutlier[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedOutlier, setSelectedOutlier] = useState<MockOutlier | null>(null);
    const [showTransition, setShowTransition] = useState(false);
    const [agentOpen, setAgentOpen] = useState(false);
    const [languageFilter, setLanguageFilter] = useState<LanguageFilter>('all');
    const [chatInput, setChatInput] = useState('');
    const [chatMessages, setChatMessages] = useState<Array<{ role: 'user' | 'agent', text: string }>>([]);

    // Mock 데이터 with language fields
    const MOCK_OUTLIERS: MockOutlier[] = [
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
            lang: 'ko',
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
            title: 'Convenience Store Combo Recipe (So Good!)',
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
            lang: 'en',
            hasTranslation: true,
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
            lang: 'ko',
            vdg_analysis: {
                title: '완판 립 리뷰',
                hook_genome: { pattern: 'FOMO Urgency', strength: 0.91 },
            },
        },
        {
            id: 'mock-4',
            external_id: 'jkl012',
            video_url: 'https://tiktok.com/@fitness/video/012',
            platform: 'tiktok',
            category: 'fitness',
            title: 'Get Abs in 2 Weeks (For Real)',
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
            lang: 'en',
            hasTranslation: false,
            vdg_analysis: {
                title: '2주 복근 챌린지',
                hook_genome: { pattern: 'Transformation Promise', strength: 0.85 },
            },
        },
    ];

    // Komi Mock Responses
    const KOMI_RESPONSES = [
        "이 패턴은 \"Curiosity Gap\"으로 분석됩니다. 첫 2초 안에 시청자의 궁금증을 유발하는 것이 핵심이에요.",
        "추천 변주 방식은 '훅 변주'입니다. 오리지널의 성과를 그대로 가져가면서 차별화할 수 있어요.",
        "해당 콘텐츠는 영어이지만 번역이 제공됩니다. 한국 시장에 적용하려면 문화적 맥락 조정이 필요해요.",
        "이 패턴의 평균 조회수는 85만으로, 상위 5% 성과입니다. 재현 가능성이 높아요.",
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

    // Filter outliers by language
    const filteredOutliers = useMemo(() => {
        if (languageFilter === 'all') return outliers;
        return outliers.filter(o => {
            const lang = (o as MockOutlier).lang || 'ko';
            if (languageFilter === 'ko') return lang === 'ko';
            if (languageFilter === 'en') return lang === 'en';
            return true;
        });
    }, [outliers, languageFilter]);

    const toHubCardData = (outlier: MockOutlier): HubCardData => ({
        id: outlier.id,
        videoId: outlier.external_id,
        thumbnailUrl: outlier.thumbnail_url || '/placeholder-thumb.jpg',
        title: outlier.title || outlier.vdg_analysis?.title || '제목 없음',
        patternName: outlier.vdg_analysis?.hook_genome?.pattern || `Tier ${outlier.outlier_tier}`,
        views: outlier.view_count,
        score: Math.round(outlier.outlier_score * 100),
    });

    const generateSpokeOptions = (outlier: MockOutlier): SpokeOptionData[] => {
        const hookPattern = outlier.vdg_analysis?.hook_genome?.pattern || 'hook';
        return [
            { id: 'spoke-hook', type: 'hook', label: '훅 변주', description: `"${hookPattern}" 패턴을 내 스타일로 재해석`, confidence: 85 },
            { id: 'spoke-audio', type: 'audio', label: '오디오 변주', description: '같은 구조, 새로운 음악/보이스', confidence: 72 },
            { id: 'spoke-visual', type: 'visual', label: '비주얼 변주', description: '샷 구성과 색감만 참고', confidence: 68 },
            { id: 'spoke-trend', type: 'trend', label: '트렌드 믹스', description: '최신 트렌드와 결합', confidence: 58 },
        ];
    };

    const handleCardClick = (outlier: MockOutlier) => {
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

    const handleChatSubmit = () => {
        if (!chatInput.trim()) return;

        // Add user message
        setChatMessages(prev => [...prev, { role: 'user', text: chatInput }]);
        setChatInput('');

        // Simulate agent response
        setTimeout(() => {
            const randomResponse = KOMI_RESPONSES[Math.floor(Math.random() * KOMI_RESPONSES.length)];
            setChatMessages(prev => [...prev, { role: 'agent', text: randomResponse }]);
        }, 800);
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

            {/* Banner + Language Filter */}
            <div className="px-4 py-3 bg-[#c1ff00]/10 border-b border-[#c1ff00]/20">
                <div className="max-w-lg mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <Sparkles className="w-5 h-5 text-[#c1ff00] flex-shrink-0" />
                        <p className="text-sm text-white/80">당신을 위한 바이럴 레퍼런스</p>
                    </div>

                    {/* Language Filter Dropdown */}
                    <div className="relative">
                        <select
                            value={languageFilter}
                            onChange={(e) => setLanguageFilter(e.target.value as LanguageFilter)}
                            className="appearance-none bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 pr-8 text-xs text-white/80 cursor-pointer hover:bg-white/10 transition-colors"
                        >
                            <option value="all">🌐 전체</option>
                            <option value="ko">🇰🇷 한국어</option>
                            <option value="en">🇺🇸 영어</option>
                        </select>
                        <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40 pointer-events-none" />
                    </div>
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
                        {filteredOutliers.map((outlier, index) => (
                            <motion.div
                                key={outlier.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.08, duration: 0.2 }}
                                className="relative"
                            >
                                <HubCard
                                    data={toHubCardData(outlier)}
                                    layoutId={`hub-card-${outlier.id}`}
                                    onClick={() => handleCardClick(outlier)}
                                />
                                {/* Language Badge */}
                                {(outlier as MockOutlier).lang && (outlier as MockOutlier).lang !== 'ko' && (
                                    <div className="absolute top-2 left-2">
                                        <LanguageGateBadge
                                            lang={(outlier as MockOutlier).lang!}
                                            hasTranslation={(outlier as MockOutlier).hasTranslation}
                                        />
                                    </div>
                                )}
                            </motion.div>
                        ))}
                    </div>
                )}

                {!loading && !error && filteredOutliers.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-20">
                        <Globe className="w-12 h-12 text-white/20 mb-4" />
                        <p className="text-white/50 text-sm mb-2">해당 언어의 콘텐츠가 없습니다</p>
                        <button
                            onClick={() => setLanguageFilter('all')}
                            className="text-[#c1ff00] text-xs underline"
                        >
                            전체 보기
                        </button>
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

            {/* Komi Agent with Chat */}
            <AgentAccordion
                isOpen={agentOpen}
                onToggle={setAgentOpen}
                agentName="Komi"
                unreadCount={agentOpen ? 0 : 1}
                chatInput={chatInput}
                onChatInputChange={setChatInput}
                onChatSubmit={handleChatSubmit}
            >
                <div className="flex flex-col gap-4">
                    {/* Initial System Message */}
                    <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 mt-1"><KomiAvatar size="sm" isSpeaking /></div>
                        <div className="bg-[#c1ff00]/10 border border-[#c1ff00]/20 rounded-2xl rounded-tl-none p-3 max-w-[85%]">
                            <p className="text-sm text-[#c1ff00] font-medium mb-1">바이럴 분석 준비 완료</p>
                            <p className="text-sm text-white/90 leading-relaxed">
                                카드를 선택하면 패턴 분석과 변주 추천을 해드릴게요. 궁금한 점이 있으시면 물어보세요!
                            </p>
                        </div>
                    </div>

                    {/* Dynamic Chat Messages */}
                    {chatMessages.map((msg, idx) => (
                        msg.role === 'user' ? (
                            <div key={idx} className="flex items-end justify-end gap-2">
                                <div className="bg-white/10 rounded-2xl rounded-tr-none p-3 max-w-[80%]">
                                    <p className="text-sm text-white/90">{msg.text}</p>
                                </div>
                            </div>
                        ) : (
                            <div key={idx} className="flex items-start gap-3">
                                <div className="flex-shrink-0 mt-1"><KomiAvatar size="sm" /></div>
                                <div className="bg-white/5 border border-white/10 rounded-2xl rounded-tl-none p-3 max-w-[85%]">
                                    <p className="text-sm text-white/80 leading-relaxed">{msg.text}</p>
                                </div>
                            </div>
                        )
                    ))}
                </div>
            </AgentAccordion>
        </div>
    );
}
