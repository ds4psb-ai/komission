// frontend/src/app/remix/[nodeId]/earn/page.tsx
"use client";

import { useSessionStore } from "@/stores/useSessionStore";
import { useParams } from "next/navigation";

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
                <h1 className="text-2xl font-black">💰 수익 기회</h1>
                {quest && (
                    <span className="px-4 py-2 bg-emerald-500/20 text-emerald-400 rounded-full text-sm font-bold border border-emerald-500/30">
                        ✅ 퀘스트 적용됨
                    </span>
                )}
            </div>

            {/* Active Quest */}
            {quest && (
                <div className="p-[2px] rounded-2xl bg-gradient-to-r from-emerald-500 to-cyan-500">
                    <div className="bg-[#0a0a0a] rounded-[14px] p-6">
                        <div className="flex items-center justify-between mb-4">
                            <span className="text-sm font-bold text-emerald-400">현재 진행 중</span>
                            <span className="text-2xl font-black text-white">+{quest.rewardPoints}P</span>
                        </div>
                        <h3 className="text-lg font-bold text-white mb-2">{quest.title}</h3>
                        <div className="text-sm text-white/60">촬영 완료 후 자동으로 보상이 지급됩니다</div>
                    </div>
                </div>
            )}

            {/* Available Quests */}
            <div className="space-y-4">
                <h2 className="text-lg font-bold text-white/80">추천 퀘스트</h2>
                {availableQuests.map((q) => (
                    <div
                        key={q.campaignId}
                        className="glass-panel p-6 rounded-2xl border border-white/10 hover:border-orange-500/30 transition-all group"
                    >
                        <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-3">
                                <span className="text-2xl">🎯</span>
                                <div>
                                    <h3 className="font-bold text-white group-hover:text-orange-300 transition-colors">
                                        {q.title}
                                    </h3>
                                    <div className="text-xs text-white/50">{q.brand}</div>
                                </div>
                            </div>
                            <div className="text-xl font-black text-orange-400">+{q.rewardPoints}P</div>
                        </div>
                        <p className="text-sm text-white/60 mb-4">{q.description}</p>
                        <button
                            onClick={() => acceptQuest(q)}
                            disabled={!!quest}
                            className="w-full py-3 rounded-xl bg-orange-500/20 border border-orange-500/30 text-orange-300 font-bold hover:bg-orange-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                        >
                            {quest?.campaignId === q.campaignId ? "✅ 적용됨" : "퀘스트 수락"}
                        </button>
                    </div>
                ))}
            </div>

            {/* O2O Section */}
            <div className="glass-panel p-6 rounded-2xl border border-pink-500/20">
                <div className="flex items-center gap-3 mb-4">
                    <span className="text-2xl">🛍️</span>
                    <div>
                        <h2 className="font-bold text-white">O2O 체험단</h2>
                        <p className="text-xs text-white/50">오프라인 제품 체험 기회</p>
                    </div>
                </div>
                <div className="text-center py-8 text-white/40">
                    새로운 체험단 모집을 준비 중입니다...
                </div>
            </div>
        </div>
    );
}
