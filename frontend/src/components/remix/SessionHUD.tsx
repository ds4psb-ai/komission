// frontend/src/components/remix/SessionHUD.tsx
"use client";

import { useSessionStore } from "@/stores/useSessionStore";
import { SESSION_PHASES } from "@/lib/types/session";
import { SessionStepper } from "./SessionStepper";
import { Badge } from "@/components/ui/Badge";
import { Zap, Settings2 } from "lucide-react";

interface SessionHUDProps {
    nodeId: string;
}

export function SessionHUD({ nodeId }: SessionHUDProps) {
    const phase = useSessionStore((s) => s.phase);
    const mode = useSessionStore((s) => s.mode);
    const setMode = useSessionStore((s) => s.setMode);
    const outlier = useSessionStore((s) => s.outlier);
    const quest = useSessionStore((s) => s.quest);
    const run = useSessionStore((s) => s.run);

    // Next action based on current phase
    const getNextAction = (): { label: string; description: string } | null => {
        switch (phase) {
            case "discover":
                return { label: "레시피 설정", description: "아웃라이어를 선택하고 변수를 커스터마이즈하세요" };
            case "setup":
                return { label: "촬영 시작", description: "준비가 완료되면 촬영을 시작하세요" };
            case "shoot":
                return { label: "영상 제출", description: "촬영이 완료되면 제출하세요" };
            case "submit":
                return { label: "성과 추적", description: "제출 완료! 성과를 확인하세요" };
            case "track":
                return null;
            default:
                return null;
        }
    };

    const nextAction = getNextAction();

    return (
        <div className="border-b border-white/5 bg-black sticky top-16 z-40">
            <div className="container mx-auto px-4 py-3">
                <div className="flex items-center justify-between gap-4">

                    {/* Left: Phase Progress */}
                    <div>
                        <SessionStepper />
                    </div>

                    {/* Center: Context Info (Hidden on mobile) */}
                    <div className="hidden lg:flex items-center gap-2 flex-1 justify-center">
                        {outlier && (
                            <Badge variant="soft" intent="success" className="max-w-[150px] truncate">
                                📍 {outlier.title}
                            </Badge>
                        )}
                        {quest && (
                            <Badge variant="soft" intent="warning">
                                🎯 +{quest.rewardPoints}P
                            </Badge>
                        )}
                        {run && (
                            <Badge variant="soft" intent="error">
                                🎬 {run.status}
                            </Badge>
                        )}
                    </div>

                    {/* Right: Controls */}
                    <div className="flex items-center gap-3">
                        {/* Mode Toggle */}
                        <div className="flex items-center gap-1 bg-white/5 rounded-lg p-0.5 border border-white/5">
                            <button
                                onClick={() => setMode("simple")}
                                className={`flex items-center gap-1 px-2.5 py-1.5 rounded-md text-[10px] font-bold transition-all ${mode === "simple"
                                    ? "bg-[rgb(var(--color-violet))] text-white shadow-sm"
                                    : "text-white/50 hover:text-white hover:bg-white/5"
                                    }`}
                            >
                                <Zap className="w-3 h-3" />
                                <span>간편</span>
                            </button>
                            <button
                                onClick={() => setMode("pro")}
                                className={`flex items-center gap-1 px-2.5 py-1.5 rounded-md text-[10px] font-bold transition-all ${mode === "pro"
                                    ? "bg-[rgb(var(--color-pink))] text-white shadow-sm"
                                    : "text-white/50 hover:text-white hover:bg-white/5"
                                    }`}
                            >
                                <Settings2 className="w-3 h-3" />
                                <span>Pro</span>
                            </button>
                        </div>

                        {/* Next Action Hint (Desktop only) */}
                        {nextAction && (
                            <div className="hidden xl:flex items-center gap-2 px-3 py-1.5 bg-[rgba(var(--color-violet),0.1)] border border-[rgba(var(--color-violet),0.2)] rounded-lg">
                                <span className="text-[rgb(var(--color-violet))] text-xs">→</span>
                                <span className="text-[11px] font-bold text-[rgb(var(--color-violet))]">
                                    {nextAction.label}
                                </span>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
