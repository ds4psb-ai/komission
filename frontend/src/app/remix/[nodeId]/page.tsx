"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, RemixNodeDetail, QuestRecommendation } from "@/lib/api";
import { GenealogyWidget } from "@/components/GenealogyWidget";
import { AppHeader } from "@/components/AppHeader";
import { FilmingGuide } from "@/components/FilmingGuide";
import { CelebrationModal } from "@/components/CelebrationModal";
import { MutationStrategyCard } from "@/components/MutationStrategyCard";
import { PatternConfidenceChart } from "@/components/PatternConfidenceChart";
import { useWorkContext } from "@/contexts/WorkContext";

export default function RemixDetailPage() {
    const params = useParams();
    const router = useRouter();
    const nodeId = params.nodeId as string;

    // WorkContext for ContextBar persistence
    const workContext = useWorkContext();

    const [node, setNode] = useState<RemixNodeDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [analyzing, setAnalyzing] = useState(false);
    const [forking, setForking] = useState(false);
    const [showVideoModal, setShowVideoModal] = useState(false);
    const [showFilmingGuide, setShowFilmingGuide] = useState(false);

    // Expert Recommendations: Quest & Invisible Forking State
    const [questAccepted, setQuestAccepted] = useState(false);
    const [forkedNodeId, setForkedNodeId] = useState<string | null>(null);
    const [isInvisibleForking, setIsInvisibleForking] = useState(false);

    // Expert Recommendation: Celebration Modal
    const [showCelebration, setShowCelebration] = useState(false);

    // Expert Recommendation: Quest Matching
    const [recommendedQuests, setRecommendedQuests] = useState<QuestRecommendation[]>([]);
    const [questsLoading, setQuestsLoading] = useState(false);

    // Phase 2: View Mode Toggle (Simple = 빠른 촬영, Studio = 전체 분석)
    const [viewMode, setViewMode] = useState<'simple' | 'studio'>('simple');

    useEffect(() => {
        if (nodeId) fetchNode();
    }, [nodeId]);

    async function fetchNode() {
        try {
            const data = await api.getRemixNode(nodeId);
            setNode(data);

            // Update WorkContext when node loads
            workContext.setRecipe({
                nodeId: data.node_id,
                title: data.title,
            });
            workContext.setOutlier({
                id: data.node_id,
                title: data.title,
                performanceDelta: data.performance_delta || undefined,
            });
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    }

    // Expert Recommendation: Load Quest Matching on node load
    async function fetchQuestMatching() {
        if (!nodeId) return;
        setQuestsLoading(true);
        try {
            const response = await api.getQuestMatching(nodeId);
            setRecommendedQuests(response.recommended_quests);
        } catch (err) {
            console.error('Quest matching failed:', err);
        } finally {
            setQuestsLoading(false);
        }
    }

    useEffect(() => {
        if (node) fetchQuestMatching();
    }, [node]);

    async function handleAnalyze() {
        if (!node) return;
        setAnalyzing(true);
        try {
            await api.analyzeNode(node.node_id);
            await fetchNode();
        } catch (err) {
            alert("Analysis failed. See console.");
            console.error(err);
        } finally {
            setAnalyzing(false);
        }
    }

    async function handleFork() {
        if (!node) return;
        if (!confirm("이 노드를 Fork하시겠습니까? 새로운 Mutation이 생성됩니다.")) return;

        setForking(true);
        try {
            const forkedNode = await api.forkRemixNode(node.node_id);
            alert("✅ Fork 성공! 새 노드로 이동합니다.");
            router.push(`/remix/${forkedNode.node_id}`);
        } catch (err) {
            alert(err instanceof Error ? err.message : "Fork 실패");
            console.error(err);
        } finally {
            setForking(false);
        }
    }

    // Expert Recommendation: Invisible Forking on Shoot Start
    async function handleStartFilming() {
        if (!node) return;

        setIsInvisibleForking(true);
        try {
            // Background fork to track "attempt" data
            const forkedNode = await api.forkRemixNode(node.node_id);
            setForkedNodeId(forkedNode.node_id);
            console.log('[Invisible Fork] Created attempt node:', forkedNode.node_id);

            // Update WorkContext with Run info
            workContext.setRun({
                attemptNumber: (workContext.run?.attemptNumber || 0) + 1,
                forkedNodeId: forkedNode.node_id,
                startedAt: new Date(),
            });
        } catch (err) {
            // Silent fail - don't block user from filming
            console.warn('[Invisible Fork] Failed:', err);
            // Still track the attempt locally
            workContext.setRun({
                attemptNumber: (workContext.run?.attemptNumber || 0) + 1,
                startedAt: new Date(),
            });
        } finally {
            setIsInvisibleForking(false);
            setShowFilmingGuide(true);
        }
    }

    // Expert Recommendation: Quest Accept Handler
    function handleQuestAccept() {
        setQuestAccepted(true);

        // Update WorkContext with Quest info from first recommended quest
        if (recommendedQuests.length > 0) {
            const firstQuest = recommendedQuests[0];
            workContext.setQuest({
                questId: firstQuest.id,
                brand: firstQuest.brand || undefined,
                rewardPoints: firstQuest.reward_points,
                accepted: true,
            });
        }

        // TODO: Call API to register quest participation
        // api.acceptQuest(node.node_id, questId);
    }

    function handleDownload(type: 'audio' | 'prompt') {
        if (!node) return;

        // For now, we show what would be downloaded - in production, these would be presigned S3 URLs
        const path = type === 'audio' ? node.audio_guide_path : undefined;

        if (path) {
            // In production: window.open(presignedUrl, '_blank');
            alert(`다운로드 준비 중: ${path}`);
        } else {
            alert("이 리소스는 아직 준비되지 않았습니다.");
        }
    }

    if (loading) return <div className="min-h-screen bg-black flex items-center justify-center"><div className="animate-spin rounded-full h-12 w-12 border-t-2 border-violet-500"></div></div>;
    if (!node) return <div className="min-h-screen bg-black text-white flex items-center justify-center">노드를 찾을 수 없습니다</div>;

    const geminiAnalysis = node.gemini_analysis as any;
    const claudeBrief = node.claude_brief as any;

    return (
        <div className="min-h-screen bg-black text-white pb-20 selection:bg-violet-500/30">
            {/* Video Modal */}
            {showVideoModal && node.source_video_url && (
                <div
                    className="fixed inset-0 z-[100] bg-black/95 backdrop-blur-xl flex items-center justify-center p-4"
                    onClick={() => setShowVideoModal(false)}
                >
                    <div className="max-w-4xl w-full" onClick={(e) => e.stopPropagation()}>
                        <div className="flex justify-end mb-4">
                            <button
                                onClick={() => setShowVideoModal(false)}
                                className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center hover:bg-white/20 transition-colors"
                            >
                                ✕
                            </button>
                        </div>
                        {node.source_video_url.includes('tiktok') || node.source_video_url.includes('instagram') ? (
                            <div className="glass-panel rounded-2xl p-8 text-center">
                                <div className="text-6xl mb-4">🔗</div>
                                <p className="text-white/60 mb-6">외부 플랫폼 영상입니다. 새 탭에서 열립니다.</p>
                                <a
                                    href={node.source_video_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-block px-8 py-4 bg-violet-600 hover:bg-violet-500 rounded-xl font-bold transition-colors"
                                >
                                    {node.platform === 'tiktok' ? '🎵 TikTok에서 보기' : '📷 Instagram에서 보기'}
                                </a>
                            </div>
                        ) : (
                            <video
                                src={node.source_video_url}
                                controls
                                autoPlay
                                className="w-full rounded-2xl shadow-2xl"
                            />
                        )}
                    </div>
                </div>
            )}

            {/* Shared Header */}
            <AppHeader />

            {/* Node Info Bar + Mode Toggle */}
            <div className="border-b border-white/5 bg-black/50">
                <div className="container mx-auto px-6 py-3 flex justify-between items-center">
                    <span className="font-mono text-xs text-white/40">
                        ID: {node.node_id}
                    </span>

                    {/* Mode Toggle (Phase 2) */}
                    <div className="flex items-center gap-2 mx-auto">
                        <button
                            onClick={() => setViewMode('simple')}
                            className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${viewMode === 'simple'
                                ? 'bg-violet-500 text-white shadow-[0_0_15px_rgba(139,92,246,0.4)]'
                                : 'bg-white/5 text-white/50 hover:text-white hover:bg-white/10'
                                }`}
                        >
                            ⚡ 간편
                        </button>
                        <button
                            onClick={() => setViewMode('studio')}
                            className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${viewMode === 'studio'
                                ? 'bg-pink-500 text-white shadow-[0_0_15px_rgba(236,72,153,0.4)]'
                                : 'bg-white/5 text-white/50 hover:text-white hover:bg-white/10'
                                }`}
                        >
                            🎛️ 스튜디오
                        </button>
                    </div>

                    <div className="flex gap-3">
                        {node.layer !== 'master' && (
                            <span className="px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-bold border border-emerald-500/20">
                                MUTATION
                            </span>
                        )}
                        <span className="px-3 py-1 rounded-full bg-violet-500/10 text-violet-400 text-xs font-bold border border-violet-500/20">
                            {node.layer.toUpperCase()}
                        </span>
                    </div>
                    {/* Breadcrumb / Back Link */}
                    <Link href="/" className="absolute left-6 top-1/2 -translate-y-1/2 text-xs font-bold text-white/40 hover:text-white transition-colors flex items-center gap-1">
                        ← BACK TO LIST
                    </Link>
                </div>
            </div>

            <main className="container mx-auto px-6 py-10 max-w-7xl">

                {/* Dashboard Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

                    {/* Left Column: Media & Context (7 cols) */}
                    <div className="lg:col-span-7 space-y-8">

                        {/* Title Block */}
                        <div>
                            <h1 className="text-4xl md:text-5xl font-black mb-4 tracking-tight leading-tight text-transparent bg-clip-text bg-gradient-to-r from-white via-white to-white/50">
                                {node.title}
                            </h1>
                            <div className="flex gap-6 text-sm text-white/60 font-medium">
                                <span className="flex items-center gap-2">
                                    👁️ {node.view_count.toLocaleString()} 조회수
                                </span>
                                <span className="flex items-center gap-2 text-violet-400">
                                    🚀 바이럴 검증됨
                                </span>
                                <span>
                                    {new Date(node.created_at).toLocaleDateString()}
                                </span>
                            </div>
                        </div>

                        {/* ⚡ Hero CTA - Phase 3: Primary Action Area */}
                        <div className="p-[2px] rounded-3xl bg-gradient-to-r from-violet-500 via-pink-500 to-orange-500 shadow-[0_0_50px_rgba(139,92,246,0.3)]">
                            <div className="bg-[#050505] rounded-[22px] p-6">
                                <div className="flex flex-col md:flex-row items-center gap-6">
                                    {/* Left: Quick Summary */}
                                    <div className="flex-1 text-center md:text-left">
                                        <div className="text-sm text-white/50 mb-1">예상 조회수</div>
                                        <div className="text-3xl font-black text-white mb-2">50K ~ 100K</div>
                                        {questAccepted && (
                                            <span className="inline-flex items-center gap-1 px-3 py-1 bg-emerald-500/20 text-emerald-400 text-xs font-bold rounded-full border border-emerald-500/30">
                                                ✅ +500P 퀘스트 적용됨
                                            </span>
                                        )}
                                    </div>

                                    {/* Right: CTA Buttons */}
                                    <div className="flex flex-col gap-3 w-full md:w-auto">
                                        <button
                                            onClick={handleStartFilming}
                                            disabled={isInvisibleForking}
                                            className="px-8 py-4 rounded-2xl bg-gradient-to-r from-violet-500 to-pink-500 text-white font-black text-lg hover:from-violet-400 hover:to-pink-400 disabled:opacity-70 transition-all shadow-[0_0_30px_rgba(139,92,246,0.5)] flex items-center justify-center gap-3 min-w-[200px]"
                                        >
                                            {isInvisibleForking ? (
                                                <>
                                                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                                    <span>준비 중...</span>
                                                </>
                                            ) : (
                                                <>
                                                    <span className="text-2xl">🎬</span>
                                                    <span>지금 촬영 시작</span>
                                                </>
                                            )}
                                        </button>

                                        {!questAccepted && recommendedQuests.length > 0 && (
                                            <button
                                                onClick={handleQuestAccept}
                                                className="px-6 py-2 rounded-xl bg-orange-500/20 border border-orange-500/40 text-orange-300 font-bold text-sm hover:bg-orange-500/30 transition-all flex items-center justify-center gap-2"
                                            >
                                                ⚔️ 퀘스트 수락하고 +500P
                                            </button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                        {/* 💰 Revenue Prediction Card - Expert Recommendation */}
                        <div className="p-[1px] rounded-3xl bg-gradient-to-r from-yellow-500 via-orange-500 to-pink-500 shadow-[0_0_40px_rgba(234,179,8,0.2)]">
                            <div className="bg-[#0a0a0a] rounded-[23px] p-6">
                                <div className="flex items-center gap-3 mb-4">
                                    <span className="text-3xl">💰</span>
                                    <div>
                                        <h3 className="font-bold text-white">이 리믹스를 따라하면...</h3>
                                        <p className="text-xs text-white/50">유사 Fork 평균 성장률 기반 예측</p>
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4 mb-4">
                                    <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                                        <div className="text-xs text-white/40 mb-1">예상 조회수</div>
                                        <div className="text-2xl font-black text-white">50K ~ 100K</div>
                                    </div>
                                    <div className="p-4 bg-yellow-500/10 rounded-xl border border-yellow-500/20">
                                        <div className="text-xs text-yellow-400/60 mb-1">예상 수익</div>
                                        <div className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-br from-yellow-300 via-yellow-400 to-orange-500 drop-shadow-[0_2px_10px_rgba(234,179,8,0.3)]">$10 ~ $30</div>
                                    </div>
                                </div>
                                <div className="text-center p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
                                    <span className="text-xs text-emerald-400 font-bold">⚡ 지금 도전하면 50% 로열티 적용!</span>
                                </div>
                            </div>
                        </div>

                        {/* 🆕 Recommended Quests - Expert Recommendation */}
                        {recommendedQuests.length > 0 && (
                            <div className="glass-panel p-6 rounded-3xl border border-pink-500/20 bg-[#0a0a0a]">
                                <div className="flex items-center gap-3 mb-4">
                                    <span className="text-2xl">🎯</span>
                                    <div>
                                        <h3 className="font-bold text-white">추천 퀘스트</h3>
                                        <p className="text-xs text-white/50">이 리믹스에 맞는 O2O 체험단이에요!</p>
                                    </div>
                                </div>
                                <div className="space-y-3">
                                    {recommendedQuests.slice(0, 3).map((quest) => (
                                        <div
                                            key={quest.id}
                                            className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/10 hover:border-pink-500/50 hover:bg-white/10 transition-all duration-300 cursor-pointer group hover:scale-[1.02] hover:shadow-[0_0_20px_rgba(236,72,153,0.15)]"
                                            onClick={() => {
                                                setQuestAccepted(true);
                                            }}
                                        >
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-lg bg-pink-500/20 flex items-center justify-center text-lg">
                                                    {quest.category === 'fashion' ? '👗' : quest.category === 'beauty' ? '💄' : quest.category === 'food' ? '🍽️' : '🎁'}
                                                </div>
                                                <div>
                                                    <div className="font-bold text-white text-sm">{quest.brand || quest.campaign_title}</div>
                                                    <div className="text-xs text-white/40">{quest.place_name}</div>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <div className="text-pink-400 font-bold">+{quest.reward_points}P</div>
                                                {quest.reward_product && (
                                                    <div className="text-[10px] text-white/40">{quest.reward_product}</div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                                {!questAccepted ? (
                                    <button
                                        onClick={() => setQuestAccepted(true)}
                                        className="w-full mt-4 py-3 rounded-xl bg-gradient-to-r from-pink-500 to-violet-500 text-white font-bold text-sm hover:from-pink-400 hover:to-violet-400 transition-all shadow-[0_0_20px_rgba(219,39,119,0.3)] animate-pulse-glow"
                                    >
                                        ⚔️ 퀘스트 수락하고 +500P 받기
                                    </button>
                                ) : (
                                    <div className="w-full mt-4 py-3 rounded-xl bg-emerald-500/20 border border-emerald-500/30 text-center text-emerald-400 font-bold text-sm">
                                        ✅ 퀘스트 수락됨! 촬영 시작하세요
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Premium Video Player Frame */}
                        <div
                            className="aspect-video glass-panel rounded-3xl relative overflow-hidden group cursor-pointer"
                            onClick={() => node.source_video_url && setShowVideoModal(true)}
                        >
                            {/* Ambient Glow */}
                            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[120%] bg-violet-500/20 opacity-0 group-hover:opacity-20 blur-3xl transition-opacity duration-700"></div>

                            <div className="absolute inset-0 flex flex-col items-center justify-center z-10">
                                <button className="w-24 h-24 rounded-full bg-white/10 backdrop-blur-lg border border-white/20 flex items-center justify-center hover:scale-110 hover:bg-white/20 transition-all duration-300 shadow-[0_0_30px_rgba(139,92,246,0.3)] group-hover:shadow-[0_0_50px_rgba(139,92,246,0.6)]">
                                    <span className="text-6xl ml-2 text-white">▶</span>
                                </button>
                                <p className="mt-6 text-white/50 font-light tracking-widest text-sm uppercase">
                                    {node.source_video_url ? '재생하려면 클릭' : '영상 없음'}
                                </p>
                            </div>

                            {/* Video Meta Overlay */}
                            <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-black/80 to-transparent flex justify-between items-end">
                                <div>
                                    <div className="text-xs text-white/40 mb-1">플랫폼 소스</div>
                                    <div className="flex items-center gap-2 text-white font-bold">
                                        {node.platform === 'tiktok' ? '🎵 TikTok' : node.platform === 'instagram' ? '📷 Instagram' : node.platform || 'Unknown'}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Scene Timeline - Cinematic Strip Style (Studio Mode Only) */}
                        {viewMode === 'studio' && (
                            <div className="glass-panel p-8 rounded-3xl border border-white/5 bg-[#0a0a0a] relative overflow-hidden">
                                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-violet-500 via-pink-500 to-orange-500 opacity-50" />

                                <h2 className="text-xl font-black mb-6 flex items-center gap-3 tracking-tight">
                                    <span className="text-2xl">🎬</span> 씨네마틱 타임라인
                                    <span className="text-[10px] font-bold bg-white/10 px-2 py-0.5 rounded text-white/50 ml-auto border border-white/5 uppercase tracking-wider">4 Scenes Detected</span>
                                </h2>

                                <div className="relative">
                                    {/* Connecting Line */}
                                    <div className="absolute top-[2.2rem] left-0 w-full h-0.5 bg-white/10 z-0"></div>

                                    <div className="grid grid-cols-4 gap-4 relative z-10">
                                        {[
                                            { time: '0:00', label: 'HOOK', desc: '시선 끌기', emoji: '🎯', color: 'text-rose-400' },
                                            { time: '0:03', label: 'PROBLEM', desc: '문제 제기', emoji: '❓', color: 'text-amber-400' },
                                            { time: '0:08', label: 'SOLUTION', desc: '해결책', emoji: '💡', color: 'text-emerald-400' },
                                            { time: '0:14', label: 'ACTION', desc: '행동 유도', emoji: '🔥', color: 'text-violet-400' },
                                        ].map((scene, i) => (
                                            <div key={i} className="group cursor-pointer">
                                                <div className="flex flex-col items-center text-center">
                                                    <div className={`w-16 h-16 rounded-2xl bg-[#1a1a1a] border border-white/10 flex items-center justify-center text-3xl mb-3 shadow-lg group-hover:scale-110 group-hover:border-white/30 transition-all duration-300 ${scene.color}`}>
                                                        {scene.emoji}
                                                    </div>
                                                    <div className="px-2 py-0.5 bg-black rounded text-[10px] font-mono text-white/30 mb-1 border border-white/5">{scene.time}</div>
                                                    <div className="font-black text-sm text-white/90 tracking-wide">{scene.label}</div>
                                                    <div className="text-xs text-white/50 mt-0.5">{scene.desc}</div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Mise-en-scène Guide - Magazine Style (Studio Mode Only) */}
                        {viewMode === 'studio' && (
                            <div className="glass-panel p-8 rounded-3xl border border-white/5 bg-[#0a0a0a]">
                                <h2 className="text-xl font-black mb-6 flex items-center gap-3 tracking-tight">
                                    <span className="text-2xl">🎥</span> 미장센 디렉팅 가이드
                                </h2>
                                <div className="space-y-4">
                                    <div className="flex gap-5 p-4 bg-white/[0.03] rounded-2xl border border-white/5 hover:bg-white/[0.06] transition-colors">
                                        <div className="flex-shrink-0 w-12 h-12 bg-white/5 rounded-full flex items-center justify-center text-xl border border-white/10">1️⃣</div>
                                        <div>
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className="font-bold text-white text-lg">인트로 클로즈업</span>
                                                <span className="px-2 py-0.5 rounded bg-white/10 text-[10px] font-bold text-white/50 uppercase">Camera</span>
                                            </div>
                                            <p className="text-sm text-white/60 leading-relaxed">
                                                제품을 45도 각도에서 타이트하게 잡으세요. 자연광이 왼쪽에서 들어오게 배치하여 입체감을 살립니다.
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex gap-5 p-4 bg-white/[0.03] rounded-2xl border border-white/5 hover:bg-white/[0.06] transition-colors">
                                        <div className="flex-shrink-0 w-12 h-12 bg-white/5 rounded-full flex items-center justify-center text-xl border border-white/10">2️⃣</div>
                                        <div>
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className="font-bold text-white text-lg">리액션 미디엄샷</span>
                                                <span className="px-2 py-0.5 rounded bg-white/10 text-[10px] font-bold text-white/50 uppercase">Acting</span>
                                            </div>
                                            <p className="text-sm text-white/60 leading-relaxed">
                                                제품 사용 후 놀라는 표정을 담으세요. 카메라를 정면으로 응시하며 아이컨택을 유지하는 것이 중요합니다.
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex gap-5 p-4 bg-white/[0.03] rounded-2xl border border-white/5 hover:bg-white/[0.06] transition-colors">
                                        <div className="flex-shrink-0 w-12 h-12 bg-white/5 rounded-full flex items-center justify-center text-xl border border-white/10">3️⃣</div>
                                        <div>
                                            <div className="font-bold text-white text-lg mb-1">마무리 풀샷 & 텍스트</div>
                                            <p className="text-sm text-white/60 leading-relaxed">
                                                상반신이 나오게 뒤로 물러나고, 머리 위 공간(헤드룸)을 비워 자막이 들어갈 자리를 확보하세요.
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Genealogy Context (Studio Mode Only) */}
                        {viewMode === 'studio' && (
                            <GenealogyWidget
                                nodeId={node.node_id}
                                depth={node.genealogy_depth}
                                layer={node.layer}
                            />
                        )}

                        {/* Mutation Strategy (Studio Mode Only) */}
                        {viewMode === 'studio' && node.layer !== 'master' && (
                            <MutationStrategyCard nodeId={node.node_id} />
                        )}

                    </div>

                    {/* Right Column: Intelligence & Resources (5 cols) */}
                    <div className="lg:col-span-5 space-y-6">

                        {/* ... (Action Card) ... */}

                        {/* Simplified Action Card - Studio Mode Only (Fork & Canvas) */}
                        {viewMode === 'studio' && (
                            <div className="glass-panel p-5 rounded-2xl border border-white/10">
                                <h3 className="text-sm font-bold text-white/60 mb-4 uppercase tracking-wider">고급 옵션</h3>
                                <div className="space-y-3">
                                    {/* Fork Button */}
                                    <button
                                        onClick={handleFork}
                                        disabled={forking}
                                        className="w-full py-3 rounded-xl bg-white/5 border border-white/10 text-white font-bold text-sm hover:bg-white/10 transition-colors flex items-center justify-center gap-2"
                                    >
                                        {forking ? (
                                            <>
                                                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                                <span>포크 중...</span>
                                            </>
                                        ) : (
                                            <span>🔀 노드 포크하기</span>
                                        )}
                                    </button>

                                    {/* Canvas Edit Button */}
                                    <Link
                                        href={`/canvas?sourceUrl=${encodeURIComponent(node.source_video_url || '')}`}
                                        className="w-full py-3 rounded-xl bg-violet-500/10 border border-violet-500/20 text-violet-300 font-bold text-sm hover:bg-violet-500/20 transition-colors flex items-center justify-center gap-2"
                                    >
                                        🕸️ 캔버스에서 고급 편집
                                    </Link>
                                </div>
                            </div>
                        )}

                        {/* Product Experience Group Card - Premium */}
                        <div className="group relative p-[1px] rounded-3xl bg-gradient-to-br from-orange-500 via-pink-500 to-violet-600 shadow-[0_10px_40px_-10px_rgba(244,114,182,0.3)] hover:shadow-[0_20px_50px_-10px_rgba(244,114,182,0.5)] transition-all duration-500">
                            <div className="bg-[#0a0a0a] rounded-[23px] p-7 h-full relative overflow-hidden">
                                {/* Sparkle Effect */}
                                <div className="absolute -top-10 -right-10 w-32 h-32 bg-orange-500/20 rounded-full blur-3xl group-hover:bg-orange-500/30 transition-colors"></div>

                                <div className="relative z-10">
                                    <div className="flex justify-between items-start mb-6">
                                        <div>
                                            <h2 className="text-xl font-black text-white mb-1 flex items-center gap-2">
                                                🛒 O2O 체험단 매칭
                                            </h2>
                                            <p className="text-white/40 text-xs font-medium">이 콘텐츠로 수익을 창출하세요</p>
                                        </div>
                                        <span className="px-3 py-1 rounded-full bg-orange-500 text-black text-xs font-black uppercase tracking-wider animate-pulse shadow-[0_0_15px_rgba(249,115,22,0.5)]">
                                            LIVE
                                        </span>
                                    </div>

                                    <div className="space-y-4">
                                        {/* Active Campaign Card */}
                                        <div className="p-4 bg-white/[0.08] rounded-2xl border border-white/10 hover:border-orange-500/50 hover:bg-white/[0.12] transition-all cursor-pointer group/card relative overflow-hidden">
                                            <div className="absolute inset-0 bg-gradient-to-r from-orange-500/10 to-transparent opacity-0 group-hover/card:opacity-100 transition-opacity" />

                                            <div className="relative z-10">
                                                <div className="flex justify-between items-start mb-3">
                                                    <div>
                                                        <div className="font-bold text-lg text-white group-hover/card:text-orange-300 transition-colors">삼양 불닭 신제품</div>
                                                        <div className="text-xs text-orange-400 font-bold mt-0.5">🔥 핫 챌린지 선정됨</div>
                                                    </div>
                                                    <div className="text-right">
                                                        <div className="text-emerald-400 font-black text-lg">+500P</div>
                                                        <div className="text-[10px] text-white/30">예상 수익</div>
                                                    </div>
                                                </div>

                                                <div className="flex items-center gap-3 text-xs text-white/40 mb-4 bg-black/40 p-2 rounded-lg">
                                                    <span>📦 택배 수령</span>
                                                    <span className="w-px h-3 bg-white/10"></span>
                                                    <span>📅 12/25 마감</span>
                                                    <span className="w-px h-3 bg-white/10"></span>
                                                    <span>👥 12/100명 신청</span>
                                                </div>

                                                <button
                                                    onClick={handleQuestAccept}
                                                    disabled={questAccepted}
                                                    className={`w-full py-3 rounded-xl text-sm font-bold text-white shadow-lg transition-all ${questAccepted
                                                        ? 'bg-emerald-600 cursor-default'
                                                        : 'bg-gradient-to-r from-orange-500 to-pink-600 hover:shadow-orange-500/25 hover:scale-[1.02] active:scale-[0.98]'
                                                        }`}
                                                >
                                                    {questAccepted ? (
                                                        <span>✅ 퀴스트 수락됨! 촬영하면 +500P</span>
                                                    ) : (
                                                        <span>⚔️ 퀴스트 수락하고 +500P 받기</span>
                                                    )}
                                                </button>
                                            </div>
                                        </div>

                                        {/* Expired Campaign */}
                                        <div className="p-4 bg-white/5 rounded-2xl border border-white/5 opacity-50 hover:opacity-70 transition-opacity cursor-not-allowed">
                                            <div className="flex justify-between items-start mb-2">
                                                <div className="font-bold text-white/70">오네드리 팝업 방문</div>
                                                <span className="px-2 py-0.5 rounded bg-white/10 text-[10px] font-bold">마감됨</span>
                                            </div>
                                            <div className="text-xs text-white/30">📍 강남구 역삼동 • 방문형</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* AI DNA Analysis (Studio Mode Only) */}
                        {viewMode === 'studio' && (
                            <div className="glass-panel p-6 rounded-3xl">
                                <div className="flex justify-between items-center mb-6">
                                    <h2 className="text-lg font-bold flex items-center gap-2">
                                        🧬 AI 비디오 DNA
                                        {!geminiAnalysis && (
                                            <button onClick={handleAnalyze} disabled={analyzing} className="text-xs bg-violet-600 px-3 py-1 rounded-full ml-auto hover:bg-violet-500 disabled:bg-violet-800 transition-colors">
                                                {analyzing ? "스캔 중..." : "스캐너 실행"}
                                            </button>
                                        )}
                                    </h2>
                                    {geminiAnalysis && <span className="text-xs text-green-400">● Live</span>}
                                </div>

                                {/* Pattern Confidence Chart (New) */}
                                <div className="mb-8">
                                    <PatternConfidenceChart />
                                </div>

                                {geminiAnalysis ? (
                                    <div className="space-y-6">
                                        {/* BPM Gauge */}
                                        <div>
                                            <div className="flex justify-between text-sm mb-2 text-white/60">
                                                <span>Energy / BPM</span>
                                                <span className="text-white font-mono">{geminiAnalysis.metadata?.bpm || 128} BPM</span>
                                            </div>
                                            <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                                                <div className="h-full bg-gradient-to-r from-cyan-400 to-violet-500 w-[70%]"></div>
                                            </div>
                                        </div>

                                        {/* Mood Tags */}
                                        <div>
                                            <div className="text-sm text-white/60 mb-2">감지된 무드</div>
                                            <div className="flex flex-wrap gap-2">
                                                {geminiAnalysis.metadata?.mood ? (
                                                    <span className="px-3 py-1 rounded-lg bg-white/5 border border-white/10 text-sm">
                                                        {geminiAnalysis.metadata.mood}
                                                    </span>
                                                ) : (
                                                    ['Energetic', 'Urban', 'Fast-paced'].map(tag => (
                                                        <span key={tag} className="px-3 py-1 rounded-lg bg-white/5 border border-white/10 text-sm">{tag}</span>
                                                    ))
                                                )}
                                            </div>
                                        </div>

                                        {/* Key Elements */}
                                        <div className="p-4 bg-white/5 rounded-xl border border-white/5">
                                            <div className="text-xs text-white/40 mb-2 uppercase tracking-wide">시각적 요소</div>
                                            <p className="text-sm text-white/80 leading-relaxed">
                                                {geminiAnalysis.visual_dna?.setting_description || "분석 대기 클래식..."}
                                            </p>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="py-10 text-center text-white/30 border-2 border-dashed border-white/5 rounded-xl">
                                        분석 데이터 없음
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Claude Strategy (Studio Mode Only) */}
                        {viewMode === 'studio' && geminiAnalysis && (
                            <div className="glass-panel p-6 rounded-3xl border-violet-500/20">
                                <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                                    🧠 전략 브리프
                                    <span className="text-xs bg-violet-500 px-2 py-0.5 rounded text-white ml-2">Claude 3.5</span>
                                </h2>
                                <div className="space-y-4">
                                    <div className="p-4 rounded-xl bg-violet-500/10 border border-violet-500/20">
                                        <h3 className="text-violet-300 font-bold mb-1 text-sm">타겟 오디언스</h3>
                                        <p className="text-sm text-white/80">{geminiAnalysis.commerce_context?.primary_category || '트렌딩'}에 관심있는 Z세대</p>
                                    </div>

                                    {claudeBrief ? (
                                        <div className="space-y-3">
                                            {claudeBrief.title_kr && (
                                                <div>
                                                    <div className="text-xs text-white/40">추천 제목</div>
                                                    <div className="font-bold">{claudeBrief.title_kr}</div>
                                                </div>
                                            )}

                                            <div>
                                                <div className="text-xs text-white/40 mb-1">Hashtags</div>
                                                <div className="text-sm text-cyan-400">
                                                    {claudeBrief.hashtags?.join(' ')}
                                                </div>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="text-sm text-white/50 italic">전략 생성 중...</div>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Resource Downloads (Studio Mode Only) */}
                        {viewMode === 'studio' && (
                            <div className="glass-panel p-6 rounded-3xl">
                                <h2 className="text-lg font-bold mb-4">📂 크리에이터 리소스</h2>
                                <div className="space-y-3">
                                    <button
                                        onClick={() => handleDownload('audio')}
                                        className="w-full flex items-center justify-between p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors group"
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-lg bg-cyan-500/20 flex items-center justify-center text-cyan-400">🎵</div>
                                            <div className="text-left">
                                                <div className="text-sm font-bold">오디오 소스</div>
                                                <div className="text-xs text-white/40">{node.audio_guide_path ? '사용 가능' : '준비 중'}</div>
                                            </div>
                                        </div>
                                        <span className="text-white/20 group-hover:text-white transition-colors">↓</span>
                                    </button>
                                    <button
                                        onClick={() => handleDownload('prompt')}
                                        className="w-full flex items-center justify-between p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors group"
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-lg bg-pink-500/20 flex items-center justify-center text-pink-400">📝</div>
                                            <div className="text-left">
                                                <div className="text-sm font-bold">프롬프트 가이드</div>
                                                <div className="text-xs text-white/40">{node.storyboard_images ? '사용 가능' : '준비 중'}</div>
                                            </div>
                                        </div>
                                        <span className="text-white/20 group-hover:text-white transition-colors">↓</span>
                                    </button>
                                </div>
                            </div>
                        )}

                    </div>
                </div>
            </main>

            {/* 🎬 Filming Guide Modal */}
            <FilmingGuide
                isOpen={showFilmingGuide}
                onClose={() => setShowFilmingGuide(false)}
                guideVideoUrl={node.source_video_url || undefined}
                bpm={geminiAnalysis?.metadata?.bpm || 120}
                duration={15}
                onRecordingComplete={(blob, syncOffset) => {
                    console.log('Recording complete!', { blob, syncOffset });
                    setShowFilmingGuide(false);
                    setShowCelebration(true); // Show celebration modal!
                }}
            />

            {/* 🎉 Celebration Modal - Expert Recommendation */}
            <CelebrationModal
                isOpen={showCelebration}
                onClose={() => setShowCelebration(false)}
                nodeTitle={node.title}
                estimatedViews={{ min: 50000, max: 100000 }}
                estimatedRevenue={{ min: 10, max: 30 }}
                earnedPoints={350}
                questBonus={questAccepted ? 500 : 0}
            />
        </div>
    );
}

