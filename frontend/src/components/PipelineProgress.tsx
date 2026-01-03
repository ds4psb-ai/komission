'use client';
import { useTranslations } from 'next-intl';

/**
 * PipelineProgress - 파이프라인 진행 단계 표시 (PEGL v1.0)
 * 
 * 문서: 15_FINAL_ARCHITECTURE.md Phase 6
 * Outlier → Graph → Guide → Experiment → Evidence 흐름 시각화
 */
import { Check, Circle, ChevronRight, Sparkles, GitBranch, FileText, FlaskConical, BarChart3 } from 'lucide-react';

export type PipelineStep = 'outlier' | 'graph' | 'guide' | 'experiment' | 'evidence';

interface PipelineProgressProps {
    currentStep: PipelineStep;
    completedSteps?: PipelineStep[];
    className?: string;
    compact?: boolean;
}

const STEPS: { id: PipelineStep; label: string; icon: typeof Circle }[] = [
    { id: 'outlier', label: 'Outlier', icon: Sparkles },
    { id: 'graph', label: 'Graph', icon: GitBranch },
    { id: 'guide', label: 'Guide', icon: FileText },
    { id: 'experiment', label: 'Experiment', icon: FlaskConical },
    { id: 'evidence', label: 'Evidence', icon: BarChart3 },
];

export function PipelineProgress({
    currentStep,
    completedSteps = [],
    className = '',
    compact = false
}: PipelineProgressProps) {
    const currentIndex = STEPS.findIndex(s => s.id === currentStep);

    return (
        <div className={`flex items-center ${compact ? 'gap-1' : 'gap-2'} ${className}`}>
            {STEPS.map((step, index) => {
                const isCompleted = completedSteps.includes(step.id) || index < currentIndex;
                const isCurrent = step.id === currentStep;
                const Icon = step.icon;

                return (
                    <div key={step.id} className="flex items-center">
                        {/* Step */}
                        <div
                            className={`flex items-center gap-1.5 px-2 py-1 rounded-lg transition-all ${isCurrent
                                    ? 'bg-violet-500/20 border border-violet-500/50 text-violet-300'
                                    : isCompleted
                                        ? 'bg-emerald-500/10 text-emerald-400'
                                        : 'bg-white/5 text-white/30'
                                }`}
                        >
                            {isCompleted && !isCurrent ? (
                                <Check className="w-3 h-3" />
                            ) : (
                                <Icon className="w-3 h-3" />
                            )}
                            {!compact && (
                                <span className="text-xs font-medium">{step.label}</span>
                            )}
                        </div>

                        {/* Connector */}
                        {index < STEPS.length - 1 && (
                            <ChevronRight className={`w-3 h-3 mx-1 ${index < currentIndex ? 'text-emerald-400/50' : 'text-white/10'
                                }`} />
                        )}
                    </div>
                );
            })}
        </div>
    );
}

/**
 * SimplePipelineStep - 단일 단계 표시 (더 간단한 버전)
 */
interface SimplePipelineStepProps {
    step: PipelineStep;
    isActive?: boolean;
    isCompleted?: boolean;
}

export function SimplePipelineStep({ step, isActive, isCompleted }: SimplePipelineStepProps) {
    const stepConfig = STEPS.find(s => s.id === step);
    if (!stepConfig) return null;

    const Icon = stepConfig.icon;

    return (
        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${isActive
                ? 'bg-violet-500 text-white'
                : isCompleted
                    ? 'bg-emerald-500/20 text-emerald-400'
                    : 'bg-white/5 text-white/40'
            }`}>
            {isCompleted && !isActive ? <Check className="w-3 h-3" /> : <Icon className="w-3 h-3" />}
            {stepConfig.label}
        </div>
    );
}

export default PipelineProgress;
