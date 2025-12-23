// frontend/src/app/remix/[nodeId]/page.tsx
// Unified page with query-based tab navigation
"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { useSessionStore } from "@/stores/useSessionStore";
import { useState, useEffect, Suspense } from "react";
import { api } from "@/lib/api";
import dynamic from "next/dynamic";

// Components
import { QuickGuide } from "@/components/remix/QuickGuide";
import { VariableSlotEditor } from "@/components/remix/VariableSlotEditor";
import { QuestChip } from "@/components/remix/QuestChip";
import { CelebrationModal } from "@/components/CelebrationModal";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Target, Clapperboard, Check, ShoppingBag, Upload } from "lucide-react";

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

    const handleStartFilming = async () => {
        setIsStarting(true);
        try {
            const forkedNode = await api.forkRemixNode(nodeId);
            setRunCreated({ runId: forkedNode.node_id, forkNodeId: forkedNode.node_id });
            setRunStatus("shooting");
        } catch (error) {
            console.warn("[ShootTab] Fork failed:", error);
            setRunCreated({ runId: `local-${Date.now()}` });
            setRunStatus("shooting");
        } finally {
            setIsStarting(false);
        }
    };

    const handleCompleteFilming = () => {
        setRunStatus("submitted");
        setShowCelebration(true);
    };

    const handleCloseCelebration = () => {
        setShowCelebration(false);
    };

    return (
        <div className="space-y-6">
            {/* Hero CTA */}
            <Card variant="neon" padding="lg">
                <div className="flex flex-col md:flex-row items-center gap-6">
                    <div className="flex-1 text-center md:text-left">
                        <h1 className="text-2xl font-black text-white mb-2">
                            {outlier?.title || "리믹스 촬영"}
                        </h1>
                        <div className="text-sm text-white/50 mb-3">
                            예상 조회수 <span className="text-white font-bold">50K ~ 100K</span>
                        </div>
                        {quest && (
                            <Badge variant="subtle" color="emerald" className="gap-1.5">
                                <Target className="w-3.5 h-3.5" />
                                +{quest.rewardPoints}P 퀘스트 적용됨
                            </Badge>
                        )}
                    </div>

                    {run?.status === "shooting" ? (
                        <Button
                            variant="primary"
                            size="lg"
                            onClick={handleCompleteFilming}
                            leftIcon={<Upload className="w-6 h-6" />}
                            className="text-lg px-8 py-5 bg-gradient-to-r from-emerald-500 to-cyan-500"
                        >
                            촬영 완료
                        </Button>
                    ) : (
                        <Button
                            variant="primary"
                            size="lg"
                            onClick={handleStartFilming}
                            isLoading={isStarting}
                            disabled={isStarting}
                            leftIcon={<Clapperboard className="w-6 h-6" />}
                            className="text-lg px-8 py-5"
                        >
                            촬영 시작
                        </Button>
                    )}
                </div>
            </Card>

            <QuickGuide />
            {slots.length > 0 && <VariableSlotEditor />}
            <QuestChip />

            {/* Celebration Modal */}
            <CelebrationModal
                isOpen={showCelebration}
                onClose={handleCloseCelebration}
                nodeTitle={outlier?.title || "리믹스"}
                earnedPoints={350}
                questBonus={quest?.rewardPoints || 0}
            />
        </div>
    );
}

function EarnTabContent({ nodeId }: { nodeId: string }) {
    const quest = useSessionStore((s) => s.quest);
    const acceptQuest = useSessionStore((s) => s.acceptQuest);

    // Campaign types: instant (즉시), onsite (방문), shipment (배송)
    const availableQuests = [
        { campaignId: "quest-1", title: "삼양 불닭볶음면 챌린지", rewardPoints: 500, brand: "삼양식품", description: "불닭볶음면을 활용한 리믹스 제작", type: "instant" as const },
        { campaignId: "quest-2", title: "올리브영 뷰티 리뷰", rewardPoints: 300, brand: "올리브영", description: "최신 뷰티 제품 리뷰 콘텐츠", type: "onsite" as const },
        { campaignId: "quest-3", title: "쿠팡 신상 언박싱", rewardPoints: 800, brand: "쿠팡", description: "배송 제품 언박싱 및 첫인상 리뷰", type: "shipment" as const, shipmentStatus: 1 },
    ];

    const getTypeConfig = (type: string) => {
        switch (type) {
            case "instant": return { color: "cyan" as const, label: "🔵 즉시", desc: "바로 촬영 가능" };
            case "onsite": return { color: "orange" as const, label: "🟠 방문", desc: "위치 인증 필요" };
            case "shipment": return { color: "violet" as const, label: "🟣 배송", desc: "제품 수령 후 촬영" };
            default: return { color: "default" as const, label: "기본", desc: "" };
        }
    };

    const shipmentSteps = ["신청", "선정", "배송", "촬영"];

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-black text-white">💰 수익 기회</h1>
                {quest && (
                    <Badge variant="solid" color="emerald" className="gap-1.5">
                        <Check className="w-4 h-4" /> 퀘스트 적용됨
                    </Badge>
                )}
            </div>

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
                {availableQuests.map((q) => {
                    const typeConfig = getTypeConfig(q.type);
                    return (
                        <Card key={q.campaignId} variant="hover">
                            <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-lg bg-orange-500/20 flex items-center justify-center text-orange-400">
                                        <Target className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <h3 className="font-bold text-white">{q.title}</h3>
                                            <Badge variant="outline" color={typeConfig.color}>
                                                {typeConfig.label}
                                            </Badge>
                                        </div>
                                        <div className="text-xs text-white/50">{q.brand} · {typeConfig.desc}</div>
                                    </div>
                                </div>
                                <div className="text-xl font-black text-orange-400">+{q.rewardPoints}P</div>
                            </div>

                            {/* Shipment Progress Stepper */}
                            {q.type === "shipment" && q.shipmentStatus && (
                                <div className="mb-4 p-3 bg-violet-500/10 rounded-lg border border-violet-500/20">
                                    <div className="flex items-center justify-between text-xs text-white/60 mb-2">
                                        <span>배송 진행 상태</span>
                                        <span>{q.shipmentStatus} / {shipmentSteps.length}</span>
                                    </div>
                                    <div className="flex gap-1">
                                        {shipmentSteps.map((step, idx) => (
                                            <div key={step} className="flex-1 flex flex-col items-center gap-1">
                                                <div className={`w-full h-1.5 rounded-full ${idx < q.shipmentStatus ? "bg-violet-500" : "bg-white/10"}`} />
                                                <span className={`text-[10px] ${idx < q.shipmentStatus ? "text-violet-400" : "text-white/30"}`}>{step}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <p className="text-sm text-white/60 mb-4">{q.description}</p>
                            <Button
                                variant="ghost"
                                onClick={() => acceptQuest({ ...q, status: "suggested" })}
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
                <Badge variant="solid" color="violet">PRO</Badge>
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
                <Badge variant="solid" color="violet">PRO</Badge>
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
                <Badge variant="solid" color="violet">PRO</Badge>
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

    return <div className="max-w-4xl mx-auto">{renderTabContent()}</div>;
}

interface PageProps {
    params: Promise<{ nodeId: string }>;
}

export default function RemixPage({ params }: PageProps) {
    const [nodeId, setNodeId] = useState<string>("");

    useEffect(() => {
        params.then((p) => setNodeId(p.nodeId));
    }, [params]);

    if (!nodeId) {
        return <div className="max-w-4xl mx-auto py-8 text-center text-white/50">Loading...</div>;
    }

    return (
        <Suspense fallback={<div className="max-w-4xl mx-auto py-8 text-center text-white/50">Loading...</div>}>
            <RemixPageContent nodeId={nodeId} />
        </Suspense>
    );
}
