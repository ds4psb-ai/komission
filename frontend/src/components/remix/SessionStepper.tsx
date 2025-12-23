"use client";

import { useSessionStore } from "@/stores/useSessionStore";
import { SESSION_PHASES, SessionPhase } from "@/lib/types/session";
import { Check, CircleDot } from "lucide-react";

export function SessionStepper() {
    const currentPhase = useSessionStore((s) => s.phase);

    // Helper to get phase index
    const getPhaseIndex = (phase: SessionPhase) =>
        SESSION_PHASES.findIndex((p) => p.phase === phase);

    const currentIndex = getPhaseIndex(currentPhase);

    return (
        <div className="flex items-center gap-2">
            {/* Mobile: Simple Progress Text */}
            <div className="md:hidden text-xs font-bold text-white/70">
                <span className="text-[rgb(var(--color-violet))]">Step {currentIndex + 1}</span>
                <span className="mx-1">/</span>
                <span>{SESSION_PHASES.length}</span>
            </div>

            {/* Desktop: Visual Stepper */}
            <div className="hidden md:flex items-center">
                {SESSION_PHASES.map((phase, idx) => {
                    const isCompleted = idx < currentIndex;
                    const isActive = idx === currentIndex;

                    return (
                        <div key={phase.phase} className="flex items-center group">
                            {/* Connector Line */}
                            {idx > 0 && (
                                <div
                                    className={`w-8 h-0.5 mx-1 transition-colors duration-300 ${idx <= currentIndex
                                            ? "bg-[rgb(var(--color-violet))]"
                                            : "bg-white/10"
                                        }`}
                                />
                            )}

                            {/* Step Circle */}
                            <div
                                className={`relative flex items-center justify-center w-8 h-8 rounded-full transition-all duration-300 ${isActive
                                        ? "bg-[rgb(var(--color-violet))] ring-4 ring-[rgba(var(--color-violet),0.2)] shadow-[0_0_15px_rgba(var(--color-violet),0.5)]"
                                        : isCompleted
                                            ? "bg-[rgba(var(--color-violet),0.2)] border border-[rgba(var(--color-violet),0.5)] text-[rgb(var(--color-violet))]"
                                            : "bg-white/5 border border-white/10 text-white/20"
                                    }`}
                                title={phase.label}
                            >
                                {isCompleted ? (
                                    <Check className="w-4 h-4" />
                                ) : isActive ? (
                                    <CircleDot className="w-4 h-4 text-white animate-pulse" />
                                ) : (
                                    <span className="text-xs">{idx + 1}</span>
                                )}

                                {/* Tooltip Label */}
                                <span className={`absolute top-full mt-2 text-[10px] font-medium whitespace-nowrap transition-opacity duration-300 ${isActive ? "opacity-100 text-white" : "opacity-0 group-hover:opacity-100 text-white/50"
                                    }`}>
                                    {phase.label}
                                </span>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
