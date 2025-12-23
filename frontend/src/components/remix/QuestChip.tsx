// frontend/src/components/remix/QuestChip.tsx
"use client";

import { useSessionStore } from "@/stores/useSessionStore";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { X, Target } from "lucide-react";

export function QuestChip() {
    const quest = useSessionStore((s) => s.quest);
    const clearQuest = useSessionStore((s) => s.clearQuest);

    if (!quest) {
        return null;
    }

    return (
        <Card variant="neon" className="border border-[rgb(var(--color-orange),0.2)] bg-gradient-to-br from-[rgb(var(--color-orange),0.05)] to-transparent">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-[rgb(var(--color-orange),0.2)] flex items-center justify-center text-[rgb(var(--color-orange))]">
                        <Target className="w-6 h-6" />
                    </div>
                    <div>
                        <div className="font-bold text-white">{quest.title}</div>
                        <div className="text-sm text-white/50">
                            {quest.status === "accepted" ? "진행 중" : "추천됨"}
                        </div>
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
                        촬영 완료 후 자동으로 보상이 지급됩니다
                    </div>
                </div>
            )}
        </Card>
    );
}
