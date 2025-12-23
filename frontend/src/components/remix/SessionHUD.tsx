// frontend/src/components/remix/SessionHUD.tsx
"use client";

import { useSessionStore } from "@/stores/useSessionStore";
import { SESSION_PHASES, type SessionPhase } from "@/lib/types/session";

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

    const currentPhaseInfo = SESSION_PHASES.find((p) => p.phase === phase);
    const currentPhaseIndex = SESSION_PHASES.findIndex((p) => p.phase === phase);

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
        <div className="border-b border-white/5 bg-gradient-to-r from-violet-900/10 to-pink-900/10">
            <div className="container mx-auto px-6 py-3">
                <div className="flex items-center justify-between gap-4">
                    {/* Left: Phase Progress */}
                    <div className="flex items-center gap-4">
                        {/* Phase Steps */}
                        <div className="flex items-center gap-1">
                            {SESSION_PHASES.map((p, idx) => (
                                <div
                                    key={p.phase}
                                    className={`flex items-center ${idx < SESSION_PHASES.length - 1 ? "pr-1" : ""
                                        }`}
                                >
                                    <div
                                        className={`w-6 h-6 rounded-full flex items-center justify-center text-xs transition-all ${idx < currentPhaseIndex
                                                ? "bg-emerald-500 text-white"
                                                : idx === currentPhaseIndex
                                                    ? "bg-violet-500 text-white shadow-[0_0_10px_rgba(139,92,246,0.5)]"
                                                    : "bg-white/10 text-white/40"
                                            }`}
                                        title={`${p.label}: ${p.description}`}
                                    >
                                        {idx < currentPhaseIndex ? "✓" : p.icon}
                                    </div>
                                    {idx < SESSION_PHASES.length - 1 && (
                                        <div
                                            className={`w-4 h-0.5 mx-0.5 ${idx < currentPhaseIndex ? "bg-emerald-500" : "bg-white/10"
                                                }`}
                                        />
                                    )}
                                </div>
                            ))}
                        </div>

                        {/* Current Phase Label */}
                        <div className="hidden md:block">
                            <span className="text-xs text-white/50">현재 단계:</span>
                            <span className="ml-2 text-xs font-bold text-violet-300">
                                {currentPhaseInfo?.label}
                            </span>
                        </div>
                    </div>

                    {/* Center: Context Chips */}
                    <div className="flex items-center gap-2 flex-1 justify-center">
                        {outlier && (
                            <span className="px-2 py-1 bg-emerald-500/20 border border-emerald-500/30 rounded-full text-[10px] font-bold text-emerald-300 truncate max-w-[120px]">
                                📍 {outlier.title}
                            </span>
                        )}
                        {quest && (
                            <span className="px-2 py-1 bg-orange-500/20 border border-orange-500/30 rounded-full text-[10px] font-bold text-orange-300">
                                🎯 +{quest.rewardPoints}P
                            </span>
                        )}
                        {run && (
                            <span className="px-2 py-1 bg-pink-500/20 border border-pink-500/30 rounded-full text-[10px] font-bold text-pink-300">
                                🎬 {run.status}
                            </span>
                        )}
                    </div>

                    {/* Right: Mode Toggle + Next Action */}
                    <div className="flex items-center gap-3">
                        {/* Mode Toggle */}
                        <div className="flex items-center gap-1 bg-white/5 rounded-lg p-0.5">
                            <button
                                onClick={() => setMode("simple")}
                                className={`px-3 py-1 rounded-md text-[10px] font-bold transition-all ${mode === "simple"
                                        ? "bg-violet-500 text-white"
                                        : "text-white/50 hover:text-white"
                                    }`}
                            >
                                ⚡ 간편
                            </button>
                            <button
                                onClick={() => setMode("pro")}
                                className={`px-3 py-1 rounded-md text-[10px] font-bold transition-all ${mode === "pro"
                                        ? "bg-pink-500 text-white"
                                        : "text-white/50 hover:text-white"
                                    }`}
                            >
                                🎛️ Pro
                            </button>
                        </div>

                        {/* Next Action */}
                        {nextAction && (
                            <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 bg-violet-500/20 border border-violet-500/30 rounded-lg">
                                <span className="text-violet-300 text-xs">→</span>
                                <span className="text-[10px] font-bold text-violet-200">
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
