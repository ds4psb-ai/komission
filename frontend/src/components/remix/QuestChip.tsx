// frontend/src/components/remix/QuestChip.tsx
"use client";

import { useSessionStore } from "@/stores/useSessionStore";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { X, Target } from "lucide-react";

export function QuestChip() {
    const quest = useSessionStore((s) => s.quest);
    const clearQuest = useSessionStore((s) => s.clearQuest);

    if (!quest) {
        return null;
    }

    const typeMeta =
        quest.campaignType === "instant"
            ? { label: "즉시", color: "cyan" as const, note: "즉시 촬영 가능" }
            : quest.campaignType === "shipment"
                ? { label: "배송", color: "violet" as const, note: "제품 수령 후 촬영" }
                : quest.campaignType === "onsite"
                    ? { label: "방문", color: "orange" as const, note: "위치 인증 필요" }
                    : null;

    return (
        <Card variant="neon" className="border border-[rgb(var(--color-orange),0.2)] bg-gradient-to-br from-[rgb(var(--color-orange),0.05)] to-transparent">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-[rgb(var(--color-orange),0.2)] flex items-center justify-center text-[rgb(var(--color-orange))]">
                        <Target className="w-6 h-6" />
                    </div>
                    <div>
                        <div className="font-bold text-white">{quest.title}</div>
                        <div className="flex items-center gap-2 text-xs text-white/50">
                            <span>{quest.status === "accepted" ? "진행 중" : "추천됨"}</span>
                            {typeMeta && (
                                <Badge variant="outline" color={typeMeta.color}>
                                    {typeMeta.label}
                                </Badge>
                            )}
                        </div>
                        {quest.placeName && (
                            <div className="text-xs text-white/40 mt-1">
                                {quest.placeName}
                                {quest.address ? ` · ${quest.address}` : ""}
                            </div>
                        )}
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <div className="text-right">
                        <div className="text-2xl font-black text-[rgb(var(--color-orange))]">
                            +{quest.rewardPoints}
                        </div>
                        <div className="text-xs text-white/40">포인트</div>
                    </div>

                    {quest.status === "accepted" && (
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={clearQuest}
                            className="text-white/30 hover:text-white/60"
                            title="퀘스트 취소"
                        >
                            <X className="w-4 h-4" />
                        </Button>
                    )}
                </div>
            </div>

            {quest.status === "accepted" && (
                <div className="mt-4 pt-4 border-t border-[rgb(var(--color-orange),0.1)]">
                    <div className="flex items-center gap-2 text-sm text-[rgb(var(--color-orange))]">
                        <span className="w-2 h-2 rounded-full bg-[rgb(var(--color-orange))] animate-pulse" />
                        {typeMeta?.note || "촬영 완료 후 자동으로 보상이 지급됩니다"}
                    </div>
                    {quest.campaignType === "onsite" && (
                        <Link href="/o2o" className="mt-2 inline-block text-xs text-orange-300 hover:text-orange-200">
                            위치 인증하러 가기 →
                        </Link>
                    )}
                </div>
            )}
        </Card>
    );
}
