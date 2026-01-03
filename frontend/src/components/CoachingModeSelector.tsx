"use client";
import { useTranslations } from 'next-intl';

/**
 * CoachingModeSelector - 코칭 설정 통합 컴포넌트
 * 
 * Phase 1 하드닝:
 * - Tier: Basic vs Pro
 * - OutputMode: graphic(디폴트) | text | audio | graphic_audio
 * - Persona: strict_pd | close_friend | calm_mentor | energetic
 */
import { Sparkles, Zap, Crown, Check, Eye, MessageSquare, Volume2, MonitorPlay, User } from "lucide-react";

export type CoachingTier = "basic" | "pro";
export type CoachingOutputMode = "graphic" | "text" | "audio" | "graphic_audio";
export type CoachingPersona = "drill_sergeant" | "bestie" | "chill_guide" | "hype_coach";

export interface CoachingSettings {
    tier: CoachingTier;
    outputMode: CoachingOutputMode;
    persona: CoachingPersona;
}

interface CoachingModeSelectorProps {
    settings: CoachingSettings;
    onChange: (settings: CoachingSettings) => void;
    credits: number;
    disabled?: boolean;
    /** 촬영자 ≠ 피사체 (오디오 허용) */
    separateShooter?: boolean;
}

const TIERS = {
    basic: {
        name: "Basic",
        description: "규칙 기반 코칭",
        cost: 1,
        icon: Zap,
        color: "violet",
    },
    pro: {
        name: "Pro",
        description: "AI 대화형 코칭",
        cost: 3,
        icon: Crown,
        color: "amber",
        recommended: true,
    },
};

const OUTPUT_MODES = {
    graphic: {
        name: "그래픽",
        description: "화면 오버레이 (잡음 X)",
        icon: Eye,
        default: true,
    },
    text: {
        name: "텍스트",
        description: "조용한 자막",
        icon: MessageSquare,
    },
    audio: {
        name: "음성",
        description: "TTS 코칭",
        icon: Volume2,
    },
    graphic_audio: {
        name: "그래픽+음성",
        description: "오버레이 + TTS",
        icon: MonitorPlay,
    },
};

const PERSONAS = {
    drill_sergeant: {
        name: "빡센 디렉터",
        description: "날카로운 촬영 감독",
        emoji: "🎬",
    },
    bestie: {
        name: "찐친",
        description: "옆자리 친구 바이브",
        emoji: "✨",
    },
    chill_guide: {
        name: "릴렉스 가이드",
        description: "ASMR 급 차분함",
        emoji: "🧘",
        default: true,
    },
    hype_coach: {
        name: "하이퍼 부스터",
        description: "텐션 200%",
        emoji: "⚡",
    },
};

export function CoachingModeSelector({
    settings,
    onChange,
    credits,
    disabled = false,
    separateShooter = false,
}: CoachingModeSelectorProps) {
    const t = useTranslations('coachingSelector');
    const canAffordPro = credits >= TIERS.pro.cost;

    const updateSettings = (partial: Partial<CoachingSettings>) => {
        onChange({ ...settings, ...partial });
    };

    return (
        <div className="space-y-4">
            {/* 크레딧 표시 */}
            <div className="text-sm text-white/60 flex items-center justify-between">
                <span>{t('title')}</span>
                <span className="flex items-center gap-1">
                    <Sparkles className="w-4 h-4 text-violet-400" />
                    <span className="font-bold text-white">{credits}</span> {t('credits')}
                </span>
            </div>

            {/* Tier 선택 */}
            <div className="grid grid-cols-2 gap-2">
                {(Object.keys(TIERS) as CoachingTier[]).map((tierKey) => {
                    const tierInfo = TIERS[tierKey];
                    const TierIcon = tierInfo.icon;
                    const isSelected = settings.tier === tierKey;
                    const isDisabled = disabled || (tierKey === "pro" && !canAffordPro);

                    return (
                        <button
                            key={tierKey}
                            onClick={() => !isDisabled && updateSettings({ tier: tierKey })}
                            disabled={isDisabled}
                            className={`
                                relative p-3 rounded-lg border transition-all text-left
                                ${isSelected
                                    ? "bg-gradient-to-br from-violet-500/20 to-purple-500/20 border-violet-500/50"
                                    : "bg-white/5 border-white/10 hover:border-white/20"}
                                ${isDisabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
                            `}
                        >
                            {isSelected && <Check className="absolute top-2 right-2 w-3 h-3 text-violet-400" />}
                            <div className="flex items-center gap-2">
                                <TierIcon className={`w-4 h-4 ${isSelected ? "text-violet-400" : "text-white/60"}`} />
                                <span className="font-medium text-sm">{t(`tiers.${tierKey}.name`)}</span>
                                <span className="text-xs text-white/40">{tierInfo.cost}{t('creditsPerMin')}</span>
                            </div>
                        </button>
                    );
                })}
            </div>

            {/* 출력 모드 선택 */}
            <div>
                <div className="text-xs text-white/50 mb-2">{t('outputMode')}</div>
                <div className="grid grid-cols-4 gap-1">
                    {(Object.keys(OUTPUT_MODES) as CoachingOutputMode[]).map((modeKey) => {
                        const mode = OUTPUT_MODES[modeKey];
                        const ModeIcon = mode.icon;
                        const isSelected = settings.outputMode === modeKey;
                        // 오디오 모드는 촬영자 분리 시에만 권장
                        const needsWarning = (modeKey === "audio" || modeKey === "graphic_audio") && !separateShooter;

                        return (
                            <button
                                key={modeKey}
                                onClick={() => updateSettings({ outputMode: modeKey })}
                                disabled={disabled}
                                title={`${t(`outputModes.${modeKey}.description`)}${needsWarning ? ` (${t('audioWarningFull')})` : ""}`}
                                className={`
                                    p-2 rounded-lg border text-center transition-all
                                    ${isSelected
                                        ? "bg-violet-500/20 border-violet-500/50"
                                        : "bg-white/5 border-white/10 hover:border-white/20"}
                                    ${disabled ? "opacity-50" : "cursor-pointer"}
                                `}
                            >
                                <ModeIcon className={`w-4 h-4 mx-auto ${isSelected ? "text-violet-400" : "text-white/60"}`} />
                                <div className="text-[10px] mt-1 text-white/60">{t(`outputModes.${modeKey}.name`)}</div>
                                {needsWarning && isSelected && (
                                    <div className="text-[8px] text-amber-400 mt-0.5">⚠️{t('audioWarning')}</div>
                                )}
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* 페르소나 선택 */}
            <div>
                <div className="text-xs text-white/50 mb-2">{t('coachingStyle')}</div>
                <div className="grid grid-cols-4 gap-1">
                    {(Object.keys(PERSONAS) as CoachingPersona[]).map((personaKey) => {
                        const persona = PERSONAS[personaKey];
                        const isSelected = settings.persona === personaKey;

                        return (
                            <button
                                key={personaKey}
                                onClick={() => updateSettings({ persona: personaKey })}
                                disabled={disabled}
                                title={t(`personas.${personaKey}.description`)}
                                className={`
                                    p-2 rounded-lg border text-center transition-all
                                    ${isSelected
                                        ? "bg-violet-500/20 border-violet-500/50"
                                        : "bg-white/5 border-white/10 hover:border-white/20"}
                                    ${disabled ? "opacity-50" : "cursor-pointer"}
                                `}
                            >
                                <span className="text-lg">{persona.emoji}</span>
                                <div className="text-[10px] mt-1 text-white/60 leading-tight">{t(`personas.${personaKey}.name`)}</div>
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* 설정 요약 */}
            <div className="p-2 bg-white/5 rounded-lg text-xs text-white/60 flex items-center justify-between">
                <span>
                    {t(`tiers.${settings.tier}.name`)} · {t(`outputModes.${settings.outputMode}.name`)} · {PERSONAS[settings.persona].emoji}
                </span>
                <span className="text-violet-400">
                    {TIERS[settings.tier].cost}{t('creditsPerMin')}
                </span>
            </div>
        </div>
    );
}

/** 디폴트 설정 */
export const DEFAULT_COACHING_SETTINGS: CoachingSettings = {
    tier: "pro",
    outputMode: "graphic",  // 디폴트: 그래픽 (잡음 방지)
    persona: "chill_guide",  // 힙한 네이밍: 릴렉스 가이드
};

export default CoachingModeSelector;

