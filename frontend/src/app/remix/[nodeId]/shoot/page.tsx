// frontend/src/app/remix/[nodeId]/shoot/page.tsx
"use client";

import { useSessionStore } from "@/stores/useSessionStore";
import { useParams } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import { QuickGuide } from "@/components/remix/QuickGuide";
import { VariableSlotEditor } from "@/components/remix/VariableSlotEditor";
import { QuestChip } from "@/components/remix/QuestChip";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Target, Clapperboard } from "lucide-react";

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
            // Create invisible fork for tracking (uses client API with auth token)
            const forkedNode = await api.forkRemixNode(nodeId);
            setRunCreated({
                runId: forkedNode.node_id,
                forkNodeId: forkedNode.node_id,
            });
            setRunStatus("shooting");
            console.log("[ShootPage] Invisible fork created:", forkedNode.node_id);
        } catch (error) {
            // Silent fail - don't block user from filming
            console.warn("[ShootPage] Invisible fork failed (continuing anyway):", error);
            // Still track the attempt locally even if fork fails
            setRunCreated({
                runId: `local-${Date.now()}`,
            });
            setRunStatus("shooting");
        } finally {
            setIsStarting(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            {/* Hero CTA */}
            <div className="p-[2px] rounded-3xl bg-gradient-to-r from-[rgb(var(--color-violet))] via-[rgb(var(--color-pink))] to-[rgb(var(--color-orange))] shadow-[0_0_50px_rgba(var(--color-violet),0.3)]">
                <div className="bg-[#050505] rounded-[22px] p-8">
                    <div className="flex flex-col md:flex-row items-center gap-8">
                        {/* Left: Summary */}
                        <div className="flex-1 text-center md:text-left">
                            <h1 className="text-2xl font-black text-white mb-2 ml-1">
                                {outlier?.title || "리믹스 촬영"}
                            </h1>
                            <div className="text-sm text-white/50 mb-4 ml-1">
                                예상 조회수 <span className="text-white font-bold">50K ~ 100K</span>
                            </div>
                            {quest && (
                                <Badge variant="subtle" color="emerald" className="gap-1.5 py-1 px-3">
                                    <Target className="w-3.5 h-3.5" />
                                    +{quest.rewardPoints}P 퀘스트 적용됨
                                </Badge>
                            )}
                        </div>

                        {/* Right: CTA */}
                        <div className="flex flex-col gap-4 w-full md:w-auto">
                            <Button
                                variant="primary"
                                size="lg"
                                onClick={handleStartFilming}
                                isLoading={isStarting}
                                disabled={isStarting}
                                className="w-full md:w-auto text-xl py-6 px-10 shadow-[0_0_40px_rgba(var(--color-violet),0.5)] bg-gradient-to-r from-[rgb(var(--color-violet))] to-[rgb(var(--color-pink))]"
                                leftIcon={<Clapperboard className="w-8 h-8 mr-2" />}
                            >
                                촬영 시작
                            </Button>
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

