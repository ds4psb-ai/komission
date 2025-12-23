// frontend/src/app/remix/[nodeId]/earn/page.tsx
"use client";

import { useSessionStore } from "@/stores/useSessionStore";
import { useParams } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Target, ShoppingBag, Check } from "lucide-react";

export default function EarnPage() {
    const params = useParams();
    const nodeId = params.nodeId as string;
    const quest = useSessionStore((s) => s.quest);
    const acceptQuest = useSessionStore((s) => s.acceptQuest);

    // Mock quest data - in production this would come from API
    const availableQuests = [
        {
            campaignId: "quest-1",
            title: "삼양 불닭볶음면 챌린지",
            rewardPoints: 500,
            status: "suggested" as const,
            brand: "삼양식품",
            description: "불닭볶음면을 활용한 리믹스 제작",
        },
        {
            campaignId: "quest-2",
            title: "올리브영 뷰티 리뷰",
            rewardPoints: 300,
            status: "suggested" as const,
            brand: "올리브영",
            description: "최신 뷰티 제품 리뷰 콘텐츠",
        },
    ];

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-black text-white">💰 수익 기회</h1>
                {quest && (
                    <Badge variant="solid" color="emerald" className="gap-1.5 py-1.5 px-4 text-sm">
                        <Check className="w-4 h-4" /> 퀘스트 적용됨
                    </Badge>
                )}
            </div>

            {/* Active Quest */}
            {quest && (
                <Card variant="neon" className="border border-[rgb(var(--color-emerald),0.2)] bg-gradient-to-br from-[rgb(var(--color-emerald),0.1)] to-transparent">
                    <div className="flex items-center justify-between mb-4">
                        <span className="text-sm font-bold text-[rgb(var(--color-emerald))] flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-[rgb(var(--color-emerald))] animate-pulse" />
                            현재 진행 중
                        </span>
                        <span className="text-2xl font-black text-white">+{quest.rewardPoints}P</span>
                    </div>
                    <h3 className="text-lg font-bold text-white mb-2 ml-1">{quest.title}</h3>
                    <div className="text-sm text-white/60 ml-1">촬영 완료 후 자동으로 보상이 지급됩니다</div>
                </Card>
            )}

            {/* Available Quests */}
            <div className="space-y-4">
                <h2 className="text-lg font-bold text-white/80">추천 퀘스트</h2>
                {availableQuests.map((q) => (
                    <Card key={q.campaignId} variant="default" className="group border border-white/10 hover:border-[rgb(var(--color-orange),0.3)] transition-all">
                        <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 rounded-xl bg-[rgb(var(--color-orange),0.2)] flex items-center justify-center text-[rgb(var(--color-orange))]">
                                    <Target className="w-6 h-6" />
                                </div>
                                <div>
                                    <h3 className="font-bold text-white group-hover:text-[rgb(var(--color-orange))] transition-colors">
                                        {q.title}
                                    </h3>
                                    <div className="text-xs text-white/50">{q.brand}</div>
                                </div>
                            </div>
                            <div className="text-xl font-black text-[rgb(var(--color-orange))]">+{q.rewardPoints}P</div>
                        </div>
                        <p className="text-sm text-white/60 mb-6 pl-1">{q.description}</p>
                        <Button
                            variant={quest?.campaignId === q.campaignId ? "ghost" : "primary"}
                            onClick={() => acceptQuest(q)}
                            disabled={!!quest}
                            className={`w-full ${quest?.campaignId === q.campaignId
                                ? "bg-[rgb(var(--color-emerald),0.2)] text-[rgb(var(--color-emerald))]"
                                : "bg-[rgba(var(--color-orange),0.2)] text-[rgb(var(--color-orange))] hover:bg-[rgb(var(--color-orange))] hover:text-white border border-[rgb(var(--color-orange),0.3)]"
                                }`}
                        >
                            {quest?.campaignId === q.campaignId ? "✅ 이미 적용됨" : "퀘스트 수락"}
                        </Button>
                    </Card>
                ))}
            </div>

            {/* O2O Section */}
            <Card variant="default" className="border border-[rgb(var(--color-pink),0.2)]">
                <div className="flex items-center gap-4 mb-4">
                    <div className="w-12 h-12 rounded-xl bg-[rgb(var(--color-pink),0.2)] flex items-center justify-center text-[rgb(var(--color-pink))]">
                        <ShoppingBag className="w-6 h-6" />
                    </div>
                    <div>
                        <h2 className="font-bold text-white">O2O 체험단</h2>
                        <p className="text-xs text-white/50">오프라인 제품 체험 기회</p>
                    </div>
                </div>
                <div className="text-center py-8 text-white/40 bg-black/20 rounded-xl border border-white/5">
                    새로운 체험단 모집을 준비 중입니다...
                </div>
            </Card>
        </div>
    );
}
