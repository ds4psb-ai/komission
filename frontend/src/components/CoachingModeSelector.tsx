"use client";

/**
 * CoachingModeSelector - 코칭 모드 선택 컴포넌트
 * 
 * Basic (규칙 TTS) vs Pro (Gemini Live)
 */
import { Sparkles, Zap, Crown, Check } from "lucide-react";

export type CoachingTier = "basic" | "pro";

interface CoachingModeSelectorProps {
    tier: CoachingTier;
    onChange: (tier: CoachingTier) => void;
    credits: number;
    disabled?: boolean;
}

const TIERS = {
    basic: {
        name: "Basic",
        description: "규칙 기반 코칭",
        cost: 1,
        features: [
            "시간별 체크포인트 피드백",
            "DirectorPack DNA 규칙",
            "자연스러운 TTS 음성",
        ],
        icon: Zap,
        color: "violet",
        recommended: false,
    },
    pro: {
        name: "Pro",
        description: "AI 대화형 코칭",
        cost: 3,
        features: [
            "Basic 모든 기능 포함",
            "실시간 대화형 피드백",
            "감정/에너지 인식",
            "스마트 끼어들기 감지",
        ],
        icon: Crown,
        color: "amber",
        recommended: true,
    },
};

export function CoachingModeSelector({
    tier,
    onChange,
    credits,
    disabled = false,
}: CoachingModeSelectorProps) {
    const canAffordPro = credits >= TIERS.pro.cost;

    return (
        <div className="space-y-3">
            <div className="text-sm text-white/60 flex items-center justify-between">
                <span>코칭 모드 선택</span>
                <span className="flex items-center gap-1">
                    <Sparkles className="w-4 h-4 text-violet-400" />
                    <span className="font-bold text-white">{credits}</span> 크레딧
                </span>
            </div>

            <div className="grid grid-cols-2 gap-3">
                {(Object.keys(TIERS) as CoachingTier[]).map((tierKey) => {
                    const tierInfo = TIERS[tierKey];
                    const TierIcon = tierInfo.icon;
                    const isSelected = tier === tierKey;
                    const isDisabled = disabled || (tierKey === "pro" && !canAffordPro);
                    const colorClass = tierInfo.color === "amber"
                        ? "from-amber-500 to-orange-500 border-amber-500/30"
                        : "from-violet-500 to-purple-500 border-violet-500/30";

                    return (
                        <button
                            key={tierKey}
                            onClick={() => !isDisabled && onChange(tierKey)}
                            disabled={isDisabled}
                            className={`
                                relative p-4 rounded-xl border-2 transition-all text-left
                                ${isSelected
                                    ? `bg-gradient-to-br ${colorClass} border-opacity-100`
                                    : "bg-white/5 border-white/10 hover:border-white/20"}
                                ${isDisabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
                            `}
                        >
                            {isSelected && (
                                <div className="absolute top-2 right-2">
                                    <Check className="w-4 h-4 text-white" />
                                </div>
                            )}

                            <div className="flex items-center gap-2 mb-2">
                                <TierIcon className={`w-5 h-5 ${isSelected ? "text-white" :
                                    tierInfo.color === "amber" ? "text-amber-400" : "text-violet-400"
                                    }`} />
                                <span className="font-bold">{tierInfo.name}</span>
                            </div>

                            <p className="text-xs text-white/60 mb-2">{tierInfo.description}</p>

                            <div className="text-sm font-bold">
                                {tierInfo.cost} 크레딧<span className="font-normal text-white/50">/분</span>
                            </div>

                            {tierKey === "pro" && !canAffordPro && (
                                <div className="mt-2 text-xs text-red-400">
                                    크레딧 부족 ({credits}/{tierInfo.cost})
                                </div>
                            )}
                        </button>
                    );
                })}
            </div>

            {tier === "pro" && (
                <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                    <div className="flex items-start gap-2">
                        <Crown className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                        <div className="text-xs text-amber-200/80">
                            <strong>Pro 모드</strong>: Gemini Live로 실시간 대화형 코칭을 받아요.
                            촬영 중 질문도 할 수 있어요!
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default CoachingModeSelector;
