"use client";

import { useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Node } from '@xyflow/react';
import { ChevronRight, Play, Sparkles, Target } from 'lucide-react';

interface SessionHUDProps {
    nodes: Node[];
    canvasMode: 'simple' | 'pro';
}

interface SessionStep {
    id: string;
    label: string;
    completed: boolean;
}

/**
 * SessionHUD - Shows current progress and next action based on canvas state
 * Per 10_UI_UX_STRATEGY.md: "헤더 + 세션 HUD + 본문(탭) 구조"
 */
export function SessionHUD({ nodes, canvasMode }: SessionHUDProps) {
    const router = useRouter();

    // Derive session state from nodes on canvas
    const { steps, currentStep, nextAction } = useMemo(() => {
        const hasSource = nodes.some(n => n.type === 'source' || n.type === 'crawlerOutlier');
        const hasCapsule = nodes.some(n => n.type === 'capsule');
        const hasGuide = nodes.some(n => n.type === 'guide');
        const hasDecision = nodes.some(n => n.type === 'decision');

        const steps: SessionStep[] = [
            { id: 'source', label: '소스 선택', completed: hasSource },
            { id: 'capsule', label: '캡슐 설정', completed: hasCapsule },
            { id: 'guide', label: '가이드 생성', completed: hasGuide },
            { id: 'shoot', label: 'Shoot', completed: false },
        ];

        // Find current step (first incomplete)
        const currentStepIdx = steps.findIndex(s => !s.completed);
        const currentStep = currentStepIdx >= 0 ? steps[currentStepIdx] : steps[steps.length - 1];

        // Determine next action
        let nextAction = { label: '시작하기', target: '', enabled: true };
        if (!hasSource) {
            nextAction = { label: '아웃라이어 선택', target: 'sidebar', enabled: true };
        } else if (!hasCapsule) {
            nextAction = { label: 'Capsule 추가', target: 'sidebar', enabled: true };
        } else if (!hasGuide) {
            nextAction = { label: 'Guide 생성', target: 'capsule', enabled: true };
        } else {
            nextAction = { label: '🎬 Shoot 시작', target: '/wizard', enabled: true };
        }

        return { steps, currentStep, nextAction };
    }, [nodes]);

    const completedCount = steps.filter(s => s.completed).length;
    const progress = (completedCount / steps.length) * 100;

    return (
        <div className="w-full bg-gradient-to-r from-black/60 via-black/40 to-black/60 backdrop-blur-md border-b border-white/10 px-6 py-3">
            <div className="flex items-center justify-between max-w-screen-2xl mx-auto">
                {/* Left: Progress Steps */}
                <div className="flex items-center gap-2">
                    {steps.map((step, i) => (
                        <div key={step.id} className="flex items-center">
                            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${step.completed
                                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                    : step.id === currentStep.id
                                        ? 'bg-violet-500/20 text-violet-400 border border-violet-500/30'
                                        : 'bg-white/5 text-white/40 border border-white/10'
                                }`}>
                                {step.completed ? '✓' : (i + 1)}
                                <span className="hidden sm:inline">{step.label}</span>
                            </div>
                            {i < steps.length - 1 && (
                                <ChevronRight className="w-4 h-4 text-white/20 mx-1" />
                            )}
                        </div>
                    ))}
                </div>

                {/* Center: Progress Bar (subtle) */}
                <div className="hidden md:flex items-center gap-3 px-4">
                    <div className="w-32 h-1.5 bg-white/10 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-gradient-to-r from-violet-500 to-emerald-500 rounded-full transition-all duration-500"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                    <span className="text-xs text-white/50">{completedCount}/{steps.length}</span>
                </div>

                {/* Right: Next Action CTA */}
                <button
                    onClick={() => {
                        if (nextAction.target.startsWith('/')) {
                            router.push(nextAction.target);
                        }
                        // For sidebar/capsule targets, we could scroll to element or highlight
                    }}
                    className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-violet-500 to-cyan-500 hover:from-violet-400 hover:to-cyan-400 text-white text-sm font-bold rounded-xl transition-all shadow-lg hover:shadow-xl"
                >
                    {nextAction.target.startsWith('/') ? (
                        <Play className="w-4 h-4" />
                    ) : (
                        <Target className="w-4 h-4" />
                    )}
                    {nextAction.label}
                </button>
            </div>
        </div>
    );
}

SessionHUD.displayName = 'SessionHUD';
