// frontend/src/components/remix/QuestChip.tsx
"use client";

import { useSessionStore } from "@/stores/useSessionStore";

export function QuestChip() {
    const quest = useSessionStore((s) => s.quest);
    const clearQuest = useSessionStore((s) => s.clearQuest);

    if (!quest) {
        return null;
    }

    return (
        <div className="glass-panel p-6 rounded-2xl border border-orange-500/20 bg-gradient-to-br from-orange-500/5 to-transparent">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-orange-500/20 flex items-center justify-center text-2xl">
                        🎯
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
                        <div className="text-2xl font-black text-orange-400">
                            +{quest.rewardPoints}
                        </div>
                        <div className="text-xs text-white/40">포인트</div>
                    </div>

                    {quest.status === "accepted" && (
                        <button
                            onClick={clearQuest}
                            className="p-2 text-white/30 hover:text-white/60 transition-colors"
                            title="퀘스트 취소"
                        >
                            ✕
                        </button>
                    )}
                </div>
            </div>

            {quest.status === "accepted" && (
                <div className="mt-4 pt-4 border-t border-orange-500/10">
                    <div className="flex items-center gap-2 text-sm text-orange-300">
                        <span className="w-2 h-2 rounded-full bg-orange-400 animate-pulse" />
                        촬영 완료 후 자동으로 보상이 지급됩니다
                    </div>
                </div>
            )}
        </div>
    );
}
