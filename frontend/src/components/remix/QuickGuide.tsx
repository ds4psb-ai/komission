// frontend/src/components/remix/QuickGuide.tsx
"use client";

import { useSessionStore } from "@/stores/useSessionStore";

interface GuideStep {
    step: number;
    title: string;
    description: string;
    color: string;
}

const SIMPLE_GUIDE_STEPS: GuideStep[] = [
    {
        step: 1,
        title: "Hook 시작",
        description: "첫 3초 안에 시선을 사로잡으세요",
        color: "violet",
    },
    {
        step: 2,
        title: "핵심 전달",
        description: "원본의 핵심 패턴을 따라하세요",
        color: "pink",
    },
    {
        step: 3,
        title: "CTA 마무리",
        description: "팔로우, 좋아요, 댓글 유도하세요",
        color: "orange",
    },
];

export function QuickGuide() {
    const mode = useSessionStore((s) => s.mode);

    if (mode !== "simple") {
        return null;
    }

    return (
        <div className="glass-panel p-6 rounded-2xl space-y-4">
            <h2 className="text-lg font-bold flex items-center gap-2">
                ⚡ 빠른 가이드
                <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/30">
                    3단계
                </span>
            </h2>

            <div className="space-y-3">
                {SIMPLE_GUIDE_STEPS.map(({ step, title, description, color }) => (
                    <div key={step} className="flex items-start gap-3 group">
                        <span
                            className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold shrink-0 transition-transform group-hover:scale-110 ${color === "violet"
                                    ? "bg-violet-500 shadow-[0_0_15px_rgba(139,92,246,0.4)]"
                                    : color === "pink"
                                        ? "bg-pink-500 shadow-[0_0_15px_rgba(236,72,153,0.4)]"
                                        : "bg-orange-500 shadow-[0_0_15px_rgba(249,115,22,0.4)]"
                                }`}
                        >
                            {step}
                        </span>
                        <div className="flex-1">
                            <div className="font-bold text-white group-hover:text-violet-300 transition-colors">
                                {title}
                            </div>
                            <div className="text-sm text-white/60">{description}</div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Progress Indicator */}
            <div className="pt-4 border-t border-white/5">
                <div className="flex items-center justify-between text-xs text-white/50 mb-2">
                    <span>진행률</span>
                    <span>0 / 3 완료</span>
                </div>
                <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full w-0 bg-gradient-to-r from-violet-500 via-pink-500 to-orange-500 transition-all" />
                </div>
            </div>
        </div>
    );
}
