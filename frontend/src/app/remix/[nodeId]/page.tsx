// frontend/src/app/remix/[nodeId]/page.tsx
// Unified page with query-based tab navigation (PEGL v1.0)
"use client";

import { useTranslations } from 'next-intl';

import Link from "next/link";
import { useSearchParams, useParams } from "next/navigation";
import { useSessionStore } from "@/stores/useSessionStore";
import { useState, useEffect, useRef } from "react";
import { api, type QuestRecommendation } from "@/lib/api";
import dynamic from "next/dynamic";

// Components
import { QuickGuide } from "@/components/remix/QuickGuide";
import { VariableSlotEditor } from "@/components/remix/VariableSlotEditor";
import { QuestChip } from "@/components/remix/QuestChip";
import { HeroSection } from "@/components/remix/HeroSection";
import { CelebrationModal } from "@/components/CelebrationModal";
import { StoryboardPanel } from "@/components/video/StoryboardPanel";
import { VDGCard } from "@/components/canvas/VDGCard";
import { CoachingSession } from "@/components/CoachingSession";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { PipelineProgress, type PipelineStep } from "@/components/PipelineProgress";
import { SessionHUD } from "@/components/SessionHUD";
import { Target, Clapperboard, Check, ShoppingBag, Upload, MessageCircle } from "lucide-react";

// Dynamic imports for PRO tab content
const PatternConfidenceChart = dynamic(
    () => import("@/components/PatternConfidenceChart").then((m) => ({ default: m.PatternConfidenceChart })),
    { ssr: false, loading: () => <div className="h-64 bg-white/5 rounded-xl animate-pulse" /> }
);

const GenealogyWidget = dynamic(
    () => import("@/components/GenealogyWidget").then((m) => ({ default: m.GenealogyWidget })),
    { ssr: false, loading: () => <div className="h-64 bg-white/5 rounded-xl animate-pulse" /> }
);

// ==== Tab Content Components ====

function ShootTabContent({ nodeId }: { nodeId: string }) {
    const outlier = useSessionStore((s) => s.outlier);
    const quest = useSessionStore((s) => s.quest);
    const slots = useSessionStore((s) => s.slots);
    const run = useSessionStore((s) => s.run);
    const setRunCreated = useSessionStore((s) => s.setRunCreated);
    const setRunStatus = useSessionStore((s) => s.setRunStatus);

    const [isStarting, setIsStarting] = useState(false);
    const [showCelebration, setShowCelebration] = useState(false);
    const [showCoaching, setShowCoaching] = useState(false);
    const [isMobile, setIsMobile] = useState(false);
    const isMountedRef = useRef(true);

    useEffect(() => {
        if (typeof window === "undefined") return;
        const media = window.matchMedia("(max-width: 768px)");
        const update = () => setIsMobile(media.matches);
        update();
        if (media.addEventListener) {
            media.addEventListener("change", update);
            return () => media.removeEventListener("change", update);
        }
        media.addListener(update);
        return () => media.removeListener(update);
    }, []);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    const handleStartFilming = async () => {
        if (isMountedRef.current) {
            setIsStarting(true);
        }
        try {
            const forkedNode = await api.forkRemixNode(nodeId);
            if (!isMountedRef.current) return;
            setRunCreated({ runId: forkedNode.node_id, forkNodeId: forkedNode.node_id });
            setRunStatus("shooting");
            // Open AI coaching session after fork success
            setShowCoaching(true);
        } catch (error) {
            console.warn("[ShootTab] Fork failed:", error);
            const message = error instanceof Error ? error.message : "촬영 시작에 실패했습니다.";
            alert(message);
        } finally {
            if (isMountedRef.current) {
                setIsStarting(false);
            }
        }
    };

    const handleCompleteFilming = () => {
        setRunStatus("submitted");
        setShowCelebration(true);
    };

    const handleCloseCelebration = () => {
        setShowCelebration(false);
    };

    const canShoot = isMobile;
    const startLabel = canShoot ? "촬영 가이드 시작" : "모바일에서만 촬영 가능";
    const completeLabel = canShoot ? "촬영 완료" : "모바일에서 촬영 완료";

    // Get VDG analysis data from outlier if available
    const vdgAnalysis = outlier?.vdg_analysis;
    const hookGenome = vdgAnalysis?.hook_genome;

    return (
        <div className="space-y-6">
            {/* 🆕 Hero Section - Video + Hook Highlight */}
            <HeroSection
                title={outlier?.title || "리믹스 촬영"}
                sourceUrl={outlier?.sourceUrl || ""}
                thumbnailUrl={outlier?.thumbnailUrl}
                platform={outlier?.platform}
                hookGenome={hookGenome}
            />

            {/* CTA Section */}
            <Card variant="neon" padding="md">
                <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                    <div>
                        {quest && (
                            <Badge variant="soft" intent="success" className="gap-1.5">
                                <Target className="w-3.5 h-3.5" />
                                +{quest.rewardPoints}P 퀘스트 적용됨
                            </Badge>
                        )}
                    </div>
                    <div className="flex items-center gap-3">
                        {run?.status === "shooting" ? (
                            <Button
                                variant="primary"
                                size="lg"
                                onClick={canShoot ? handleCompleteFilming : undefined}
                                disabled={!canShoot}
                                leftIcon={<Upload className="w-5 h-5" />}
                                className="bg-gradient-to-r from-emerald-500 to-cyan-500"
                            >
                                {completeLabel}
                            </Button>
                        ) : (
                            <Button
                                variant="primary"
                                size="lg"
                                onClick={canShoot ? handleStartFilming : undefined}
                                isLoading={isStarting}
                                disabled={isStarting || !canShoot}
                                leftIcon={<Clapperboard className="w-5 h-5" />}
                            >
                                {startLabel}
                            </Button>
                        )}
                    </div>
                </div>
                <p className="text-xs text-white/40 text-center mt-3">
                    촬영은 모바일에서 진행하고 웹은 가이드/제출을 담당합니다
                </p>
            </Card>

            {/* 🆕 Storyboard - Scene-by-scene guide */}
            {vdgAnalysis && (
                <StoryboardPanel rawVdg={vdgAnalysis as any} defaultExpanded={true} />
            )}

            {/* Quick Guide */}
            <QuickGuide />

            {/* Variable Slots */}
            {slots.length > 0 && <VariableSlotEditor />}

            {/* Quest Info */}
            <QuestChip />

            {/* Celebration Modal */}
            <CelebrationModal
                isOpen={showCelebration}
                onClose={handleCloseCelebration}
                nodeTitle={outlier?.title || "리믹스"}
                earnedPoints={350}
                questBonus={quest?.rewardPoints || 0}
            />

            {/* AI Coaching Session - Real-time audio coaching */}
            <CoachingSession
                isOpen={showCoaching}
                onClose={() => setShowCoaching(false)}
                videoId={nodeId}
                packId={nodeId}
                mode="variation"
                onComplete={(sessionId) => {
                    console.log("✅ Coaching session completed:", sessionId);
                    setShowCoaching(false);
                }}
            />
        </div>
    );
}

function EarnTabContent({ nodeId }: { nodeId: string }) {
    const quest = useSessionStore((s) => s.quest);
    const acceptQuest = useSessionStore((s) => s.acceptQuest);
    const [quests, setQuests] = useState<QuestRecommendation[]>([]);
    const [loading, setLoading] = useState(true);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    useEffect(() => {
        let active = true;

        const fetchQuests = async () => {
            try {
                const data = await api.getQuestMatching(nodeId);
                if (active) {
                    setQuests(data.recommended_quests || []);
                    setLoading(false);
                }
            } catch (error) {
                if (active) {
                    setErrorMessage(error instanceof Error ? error.message : "추천 퀘스트를 불러오지 못했습니다.");
                    setLoading(false);
                }
            }
        };

        fetchQuests();

        return () => {
            active = false;
        };
    }, [nodeId]);

    const formatDeadline = (deadline: string) => {
        const date = new Date(deadline);
        if (Number.isNaN(date.getTime())) return "마감 정보 없음";
        return date.toLocaleDateString("ko-KR", { month: "2-digit", day: "2-digit" });
    };

    const normalizeCampaignType = (campaignType?: string | null) => {
        const value = (campaignType || "").toLowerCase();
        if (value.includes("ship")) return "shipment";
        if (value.includes("instant") || value.includes("digital")) return "instant";
        if (value.includes("visit") || value.includes("trial") || value.includes("onsite")) return "onsite";
        return "onsite";
    };

    const getTypeConfig = (type: string) => {
        switch (type) {
            case "instant":
                return { color: "cyan" as const, label: "🔵 즉시", desc: "바로 촬영 가능" };
            case "shipment":
                return { color: "violet" as const, label: "🟣 배송", desc: "제품 수령 후 촬영" };
            default:
                return { color: "orange" as const, label: "🟠 방문", desc: "위치 인증 필요" };
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-black text-white">💰 수익 기회</h1>
                {quest && (
                    <Badge variant="default" intent="success" className="gap-1.5">
                        <Check className="w-4 h-4" /> 퀘스트 적용됨
                    </Badge>
                )}
            </div>

            <Card variant="default">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="font-bold text-white">캠페인 유형 안내</h2>
                    <Badge variant="outline" intent="warning">현재: 방문형</Badge>
                </div>
                <div className="grid gap-3 md:grid-cols-3 text-xs text-white/60">
                    <div className="rounded-xl border border-white/10 bg-white/5 p-3">
                        <div className="font-bold text-white/80 mb-1">🔵 즉시형</div>
                        <div>브랜드 가이드에 맞춰 바로 촬영</div>
                        <div className="mt-2 text-[10px] text-white/30">준비중</div>
                    </div>
                    <div className="rounded-xl border border-orange-500/20 bg-orange-500/5 p-3">
                        <div className="font-bold text-white/80 mb-1">🟠 방문형</div>
                        <div>위치 인증 후 촬영 진행</div>
                        <div className="mt-2 text-[10px] text-orange-400">사용 가능</div>
                    </div>
                    <div className="rounded-xl border border-violet-500/20 bg-violet-500/5 p-3">
                        <div className="font-bold text-white/80 mb-1">🟣 배송형</div>
                        <div>지원 → 선정 → 배송 → 촬영</div>
                        <div className="mt-2 text-[10px] text-white/30">준비중</div>
                    </div>
                </div>
            </Card>

            {quest && (
                <Card variant="default" className="border-l-4 border-l-emerald-500">
                    <div className="flex items-center justify-between">
                        <div>
                            <span className="text-sm font-bold text-emerald-400">현재 진행 중</span>
                            <h3 className="text-lg font-bold text-white">{quest.title}</h3>
                        </div>
                        <span className="text-2xl font-black text-white">+{quest.rewardPoints}P</span>
                    </div>
                </Card>
            )}

            <div className="space-y-4">
                <h2 className="text-lg font-bold text-white/80">추천 퀘스트</h2>
                {loading && (
                    <Card variant="default" className="text-center py-6 text-white/40">
                        추천 퀘스트를 불러오는 중...
                    </Card>
                )}
                {!loading && errorMessage && (
                    <Card variant="default" className="text-center py-6 text-white/40">
                        {errorMessage}
                    </Card>
                )}
                {!loading && !errorMessage && quests.length === 0 && (
                    <Card variant="default" className="text-center py-6 text-white/40">
                        현재 추천 가능한 퀘스트가 없습니다.
                    </Card>
                )}
                {!loading && !errorMessage && quests.map((q) => {
                    const normalizedType = normalizeCampaignType(q.campaign_type);
                    const typeConfig = getTypeConfig(normalizedType);
                    const steps =
                        q.fulfillment_steps && q.fulfillment_steps.length > 0
                            ? q.fulfillment_steps
                            : ["신청", "선정", "배송", "촬영"];

                    return (
                        <Card key={q.id} variant="hover">
                            <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-lg bg-orange-500/20 flex items-center justify-center text-orange-400">
                                        <Target className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <h3 className="font-bold text-white">{q.campaign_title}</h3>
                                            <Badge variant="outline" intent={typeConfig.color === 'cyan' ? 'cyan' : typeConfig.color === 'violet' ? 'brand' : 'warning'}>{typeConfig.label}</Badge>
                                        </div>
                                        <div className="text-xs text-white/50">
                                            {q.brand || "브랜드"}
                                            {q.place_name ? ` · ${q.place_name}` : ` · ${typeConfig.desc}`}
                                        </div>
                                    </div>
                                </div>
                                <div className="text-xl font-black text-orange-400">+{q.reward_points}P</div>
                            </div>

                            {q.address && (
                                <div className="text-sm text-white/60 mb-3">{q.address}</div>
                            )}
                            {q.reward_product && (
                                <div className="text-xs text-white/40 mb-3">제공 제품: {q.reward_product}</div>
                            )}
                            <div className="flex items-center justify-between text-xs text-white/40 mb-4">
                                <span>마감 {formatDeadline(q.deadline)}</span>
                                {normalizedType === "onsite" && (
                                    <Link href="/o2o" className="text-orange-300 hover:text-orange-200">
                                        위치 인증 안내
                                    </Link>
                                )}
                            </div>

                            {normalizedType === "shipment" && (
                                <div className="mb-4 p-3 bg-violet-500/10 rounded-lg border border-violet-500/20">
                                    <div className="flex items-center justify-between text-xs text-white/60 mb-2">
                                        <span>배송 진행 단계</span>
                                        <span>1 / {steps.length}</span>
                                    </div>
                                    <div className="flex gap-1">
                                        {steps.map((step, idx) => (
                                            <div key={step} className="flex-1 flex flex-col items-center gap-1">
                                                <div className={`w-full h-1.5 rounded-full ${idx < 1 ? "bg-violet-500" : "bg-white/10"}`} />
                                                <span className={`text-[10px] ${idx < 1 ? "text-violet-400" : "text-white/30"}`}>{step}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <Button
                                variant="ghost"
                                onClick={() =>
                                    acceptQuest({
                                        campaignId: q.id,
                                        title: q.campaign_title,
                                        rewardPoints: q.reward_points,
                                        status: "accepted",
                                        campaignType: normalizedType === "onsite" ? "onsite" : normalizedType,
                                        placeName: q.place_name ?? undefined,
                                        address: q.address ?? undefined,
                                        deadline: q.deadline,
                                        rewardProduct: q.reward_product,
                                    })
                                }
                                disabled={!!quest}
                                className="w-full border border-white/10"
                            >
                                퀘스트 수락
                            </Button>
                        </Card>
                    );
                })}
            </div>

            <Card variant="default">
                <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg bg-pink-500/20 flex items-center justify-center text-pink-400">
                        <ShoppingBag className="w-5 h-5" />
                    </div>
                    <div>
                        <h2 className="font-bold text-white">O2O 체험단</h2>
                        <p className="text-xs text-white/50">오프라인 제품 체험 기회</p>
                    </div>
                </div>
                <div className="text-center py-6 text-white/40 bg-black/20 rounded-lg">
                    새로운 체험단 모집을 준비 중입니다...
                </div>
            </Card>
        </div>
    );
}

function AnalyzeTabContent({ nodeId }: { nodeId: string }) {
    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-black flex items-center gap-3">
                🧬 AI 비디오 DNA
                <Badge variant="default" intent="brand">PRO</Badge>
            </h1>

            <Card>
                <h2 className="text-lg font-bold mb-4">📊 패턴 신뢰도</h2>
                <PatternConfidenceChart />
            </Card>

            <Card>
                <h3 className="text-sm font-bold text-white/60 uppercase tracking-wider mb-4">추천 해시태그</h3>
                <div className="flex flex-wrap gap-2">
                    {["#챌린지", "#viral", "#fyp", "#리믹스", "#틱톡"].map((tag) => (
                        <span key={tag} className="px-3 py-1 bg-cyan-500/20 text-cyan-300 text-sm rounded-full border border-cyan-500/30">
                            {tag}
                        </span>
                    ))}
                </div>
            </Card>
        </div>
    );
}

function GenealogyTabContent({ nodeId }: { nodeId: string }) {
    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-black flex items-center gap-3">
                🌳 Genealogy
                <Badge variant="default" intent="brand">PRO</Badge>
            </h1>
            <Card className="min-h-[400px]">
                <GenealogyWidget nodeId={nodeId} />
            </Card>
        </div>
    );
}

function StudioTabContent({ nodeId }: { nodeId: string }) {
    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-black flex items-center gap-3">
                🎛️ Studio
                <Badge variant="default" intent="brand">PRO</Badge>
            </h1>
            <Card className="text-center py-12">
                <p className="text-white/60 mb-4">고급 편집 기능은 캔버스에서 사용 가능합니다.</p>
                <Button variant="primary" onClick={() => (window.location.href = "/canvas")}>
                    캔버스로 이동
                </Button>
            </Card>
        </div>
    );
}

// ==== Main Page Component ====

function RemixPageContent({ nodeId }: { nodeId: string }) {
    const searchParams = useSearchParams();
    const tab = searchParams.get("tab") || "shoot";

    const renderTabContent = () => {
        switch (tab) {
            case "shoot":
                return <ShootTabContent nodeId={nodeId} />;
            case "earn":
                return <EarnTabContent nodeId={nodeId} />;
            case "analyze":
                return <AnalyzeTabContent nodeId={nodeId} />;
            case "genealogy":
                return <GenealogyTabContent nodeId={nodeId} />;
            case "studio":
                return <StudioTabContent nodeId={nodeId} />;
            default:
                return <ShootTabContent nodeId={nodeId} />;
        }
    };

    // Map tab to pipeline step
    const tabToPipeline: Record<string, PipelineStep> = {
        shoot: 'guide',
        earn: 'experiment',
        analyze: 'graph',
        genealogy: 'graph',
        studio: 'guide',
    };
    const currentPipelineStep = tabToPipeline[tab] || 'guide';

    return (
        <div className="max-w-4xl mx-auto">
            {/* PEGL v1.0: Pipeline Progress Header */}
            <div className="mb-6 py-3 border-b border-white/5">
                <PipelineProgress
                    currentStep={currentPipelineStep}
                    completedSteps={['outlier']}
                />
            </div>

            {renderTabContent()}

            {/* Session HUD */}
            <SessionHUD />
        </div>
    );
}

export default function RemixPage() {
    const params = useParams<{ nodeId: string }>();
    const nodeIdParam = params?.nodeId;
    const nodeId = Array.isArray(nodeIdParam) ? nodeIdParam[0] : nodeIdParam;

    if (!nodeId) {
        return <div className="max-w-4xl mx-auto py-8 text-center text-white/50">Loading...</div>;
    }

    return <RemixPageContent nodeId={nodeId} />;
}
