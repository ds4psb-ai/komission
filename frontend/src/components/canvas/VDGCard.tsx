"use client";

import { memo } from "react";
import {
    Zap, Eye, Music, Brain, Heart, Laugh,
    AlertTriangle, ArrowRight, Wrench, MapPin, Users
} from "lucide-react";
import { cn } from "@/lib/utils";

// ==================== TYPES ====================
interface DopamineRadar {
    visual_spectacle: number;
    audio_stimulation: number;
    narrative_intrigue: number;
    emotional_resonance: number;
    comedy_shock: number;
}

interface IronyAnalysis {
    setup: string;
    twist: string;
    gap_type: string;
}

interface ProductionConstraints {
    min_actors: number;
    locations: string[];
    props: string[];
    difficulty: string;
    primary_challenge: string;
}

interface HookGenome {
    pattern: string;
    delivery: string;
    strength: number;
    hook_summary: string;
}

interface IntentLayer {
    hook_trigger: string;
    irony_analysis: IronyAnalysis;
    dopamine_radar: DopamineRadar;
}

interface CapsuleBrief {
    constraints: ProductionConstraints;
}

export interface VDGData {
    title?: string;
    summary?: string;
    hook_genome?: HookGenome;
    intent_layer?: IntentLayer;
    capsule_brief?: CapsuleBrief;
}

// ==================== SUB-COMPONENTS ====================

const DopamineBar = memo(({
    icon: Icon,
    label,
    value,
    color
}: {
    icon: React.ElementType;
    label: string;
    value: number;
    color: string;
}) => (
    <div className="flex items-center gap-2 text-xs">
        <Icon className={cn("w-3.5 h-3.5", color)} />
        <span className="w-12 text-white/50">{label}</span>
        <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
            <div
                className={cn("h-full rounded-full transition-all", color.replace("text-", "bg-"))}
                style={{ width: `${value * 10}%` }}
            />
        </div>
        <span className="w-4 text-right text-white/60">{value}</span>
    </div>
));
DopamineBar.displayName = "DopamineBar";

const IronyGapSection = memo(({ irony }: { irony: IronyAnalysis }) => (
    <div className="space-y-2 p-3 bg-white/5 rounded-lg border border-white/10">
        <div className="flex items-center gap-2 text-[10px] text-amber-400 uppercase tracking-wider">
            <AlertTriangle className="w-3 h-3" />
            Irony Gap: {irony.gap_type.replace("_", " ")}
        </div>
        <div className="flex items-center gap-2 text-xs">
            <div className="flex-1 p-2 bg-white/5 rounded text-white/70 text-[11px] line-clamp-2">
                <span className="text-white/40">Setup:</span> {irony.setup}
            </div>
            <ArrowRight className="w-4 h-4 text-amber-400 flex-shrink-0" />
            <div className="flex-1 p-2 bg-amber-500/10 rounded text-amber-200 text-[11px] line-clamp-2">
                <span className="text-amber-400/60">Twist:</span> {irony.twist}
            </div>
        </div>
    </div>
));
IronyGapSection.displayName = "IronyGapSection";

const ConstraintsSection = memo(({ constraints }: { constraints: ProductionConstraints }) => (
    <div className="grid grid-cols-2 gap-2 text-[11px]">
        <div className="flex items-center gap-2 text-white/60">
            <Users className="w-3.5 h-3.5 text-cyan-400" />
            <span>{constraints.min_actors}+ actors</span>
        </div>
        <div className="flex items-center gap-2 text-white/60">
            <Zap className="w-3.5 h-3.5 text-yellow-400" />
            <span className={cn(
                constraints.difficulty === "Easy" && "text-green-400",
                constraints.difficulty === "Medium" && "text-yellow-400",
                constraints.difficulty === "Hard" && "text-red-400"
            )}>
                {constraints.difficulty}
            </span>
        </div>
        {constraints.locations.length > 0 && (
            <div className="flex items-center gap-2 text-white/60 col-span-2">
                <MapPin className="w-3.5 h-3.5 text-purple-400" />
                <span>{constraints.locations.join(", ")}</span>
            </div>
        )}
        {constraints.props.length > 0 && (
            <div className="flex items-center gap-2 text-white/60 col-span-2">
                <Wrench className="w-3.5 h-3.5 text-orange-400" />
                <span>{constraints.props.join(", ")}</span>
            </div>
        )}
    </div>
));
ConstraintsSection.displayName = "ConstraintsSection";

// ==================== MAIN COMPONENT ====================

export const VDGCard = memo(({ vdg, className }: { vdg: VDGData; className?: string }) => {
    const hook = vdg.hook_genome;
    const intent = vdg.intent_layer;
    const dopamine = intent?.dopamine_radar;
    const irony = intent?.irony_analysis;
    const constraints = vdg.capsule_brief?.constraints;

    if (!vdg) return null;

    return (
        <div className={cn(
            "glass-panel rounded-xl border border-cyan-500/30 overflow-hidden",
            "bg-gradient-to-br from-slate-900/95 to-slate-950/95 backdrop-blur-xl",
            "shadow-[0_0_40px_rgba(6,182,212,0.1)]",
            className
        )}>
            {/* Header */}
            <div className="px-4 py-3 border-b border-cyan-500/20 bg-gradient-to-r from-cyan-900/30 to-transparent">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Brain className="w-4 h-4 text-cyan-400" />
                        <span className="text-xs font-bold tracking-wider text-white/80 uppercase">
                            VDG Analysis
                        </span>
                    </div>
                    {hook && (
                        <div className="flex items-center gap-2">
                            <span className="text-[10px] text-cyan-400 uppercase">
                                {hook.pattern.replace("_", " ")}
                            </span>
                            <div className="w-12 h-1 bg-white/10 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-cyan-400 rounded-full"
                                    style={{ width: `${(hook.strength || 0) * 100}%` }}
                                />
                            </div>
                        </div>
                    )}
                </div>
                {hook?.hook_summary && (
                    <p className="text-xs text-white/60 mt-2 line-clamp-2">
                        {hook.hook_summary}
                    </p>
                )}
            </div>

            {/* Content */}
            <div className="p-4 space-y-4">
                {/* Dopamine Radar */}
                {dopamine && (
                    <div className="space-y-2">
                        <div className="text-[10px] text-white/40 uppercase tracking-wider">
                            Dopamine Radar
                        </div>
                        <div className="space-y-1.5">
                            <DopamineBar icon={Eye} label="Visual" value={dopamine.visual_spectacle} color="text-purple-400" />
                            <DopamineBar icon={Music} label="Audio" value={dopamine.audio_stimulation} color="text-blue-400" />
                            <DopamineBar icon={Brain} label="Story" value={dopamine.narrative_intrigue} color="text-green-400" />
                            <DopamineBar icon={Heart} label="Emotion" value={dopamine.emotional_resonance} color="text-pink-400" />
                            <DopamineBar icon={Laugh} label="Comedy" value={dopamine.comedy_shock} color="text-yellow-400" />
                        </div>
                    </div>
                )}

                {/* Irony Gap */}
                {irony && irony.gap_type !== "none" && (
                    <IronyGapSection irony={irony} />
                )}

                {/* Production Constraints */}
                {constraints && (
                    <div className="space-y-2">
                        <div className="text-[10px] text-white/40 uppercase tracking-wider">
                            Replication Guide
                        </div>
                        <ConstraintsSection constraints={constraints} />
                        {constraints.primary_challenge && (
                            <div className="text-[10px] text-orange-300/80 mt-2">
                                ⚠️ {constraints.primary_challenge}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
});

VDGCard.displayName = "VDGCard";

export default VDGCard;
