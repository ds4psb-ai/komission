// frontend/src/app/remix/[nodeId]/shoot/page.tsx
"use client";

import { useSessionStore } from "@/stores/useSessionStore";
import { useParams } from "next/navigation";
import { useState } from "react";
import { forkNodeAction } from "../actions";
import { QuickGuide } from "@/components/remix/QuickGuide";
import { VariableSlotEditor } from "@/components/remix/VariableSlotEditor";
import { QuestChip } from "@/components/remix/QuestChip";

export default function ShootPage() {
    const params = useParams();
    const nodeId = params.nodeId as string;

    const outlier = useSessionStore((s) => s.outlier);
    const quest = useSessionStore((s) => s.quest);
    const slots = useSessionStore((s) => s.slots);
    const setRunCreated = useSessionStore((s) => s.setRunCreated);
    const setRunStatus = useSessionStore((s) => s.setRunStatus);

    const [isStarting, setIsStarting] = useState(false);

    const handleStartFilming = async () => {
        setIsStarting(true);
        try {
            // Create invisible fork for tracking
            const result = await forkNodeAction(nodeId);
            if (result.success && result.forkedNodeId) {
                setRunCreated({
                    runId: result.forkedNodeId,
                    forkNodeId: result.forkedNodeId,
                });
                setRunStatus("shooting");
            }
        } catch (error) {
            console.error("[ShootPage] Start filming error:", error);
        } finally {
            setIsStarting(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            {/* Hero CTA */}
            <div className="p-[2px] rounded-3xl bg-gradient-to-r from-violet-500 via-pink-500 to-orange-500 shadow-[0_0_50px_rgba(139,92,246,0.3)]">
                <div className="bg-[#050505] rounded-[22px] p-8">
                    <div className="flex flex-col md:flex-row items-center gap-8">
                        {/* Left: Summary */}
                        <div className="flex-1 text-center md:text-left">
                            <h1 className="text-2xl font-black text-white mb-2">
                                {outlier?.title || "리믹스 촬영"}
                            </h1>
                            <div className="text-sm text-white/50 mb-4">
                                예상 조회수 <span className="text-white font-bold">50K ~ 100K</span>
                            </div>
                            {quest && (
                                <span className="inline-flex items-center gap-1 px-3 py-1.5 bg-emerald-500/20 text-emerald-400 text-sm font-bold rounded-full border border-emerald-500/30">
                                    🎯 +{quest.rewardPoints}P 퀘스트 적용됨
                                </span>
                            )}
                        </div>

                        {/* Right: CTA */}
                        <div className="flex flex-col gap-4 w-full md:w-auto">
                            <button
                                onClick={handleStartFilming}
                                disabled={isStarting}
                                className="px-10 py-5 rounded-2xl bg-gradient-to-r from-violet-500 to-pink-500 text-white font-black text-xl hover:from-violet-400 hover:to-pink-400 disabled:opacity-70 transition-all shadow-[0_0_40px_rgba(139,92,246,0.5)] flex items-center justify-center gap-3"
                            >
                                {isStarting ? (
                                    <>
                                        <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                        <span>준비 중...</span>
                                    </>
                                ) : (
                                    <>
                                        <span className="text-3xl">🎬</span>
                                        <span>촬영 시작</span>
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Quick Guide (Simple Mode Only) */}
            <QuickGuide />

            {/* Variable Slots */}
            {slots.length > 0 && <VariableSlotEditor />}

            {/* Quest Info */}
            <QuestChip />
        </div>
    );
}

