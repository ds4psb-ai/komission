'use client';

import { useState, ReactNode } from 'react';
import { motion, AnimatePresence, stagger } from 'framer-motion';
import { HubCard, HubCardData } from './HubCard';
import { SpokeOptions, SpokeOptionData } from './SpokeOptions';
import { ConfirmDialog } from './ConfirmDialog';

type TransitionPhase = 'idle' | 'confirm' | 'dim' | 'morph' | 'spokes' | 'complete';

interface HubSpokesTransitionProps {
    parentCard: HubCardData;
    spokeOptions: SpokeOptionData[];
    isActive: boolean;
    onComplete: (selectedSpoke: SpokeOptionData) => void;
    onCancel: () => void;
    children?: ReactNode;
}

/**
 * HubSpokesTransition - Hub-Spokes 4단계 Morph 트랜지션
 * 
 * Phase 1: Confirm Dialog ("이대로 찾으시겠습니까?")
 * Phase 2: Dim Overlay (100ms)
 * Phase 3: Hub Fly-in + Morph (250ms spring)
 * Phase 4: Spokes Stagger (150ms × N)
 * Phase 5: Complete
 */
export function HubSpokesTransition({
    parentCard,
    spokeOptions,
    isActive,
    onComplete,
    onCancel,
}: HubSpokesTransitionProps) {
    const [phase, setPhase] = useState<TransitionPhase>('idle');
    const [selectedSpoke, setSelectedSpoke] = useState<SpokeOptionData | null>(null);

    const handleConfirm = () => {
        setPhase('dim');
        // Dim → Morph 자동 전환
        setTimeout(() => setPhase('morph'), 100);
    };

    const handleMorphComplete = () => {
        setPhase('spokes');
    };

    const handleSpokeSelect = (spoke: SpokeOptionData) => {
        setSelectedSpoke(spoke);
    };

    const handleFinalConfirm = () => {
        if (selectedSpoke) {
            setPhase('complete');
            onComplete(selectedSpoke);
        }
    };

    const handleCancel = () => {
        setPhase('idle');
        setSelectedSpoke(null);
        onCancel();
    };

    // Activate → Confirm phase 전환
    if (isActive && phase === 'idle') {
        setPhase('confirm');
    }

    return (
        <>
            {/* Confirm Dialog */}
            <ConfirmDialog
                isOpen={phase === 'confirm'}
                onConfirm={handleConfirm}
                onCancel={handleCancel}
            />

            {/* Dim Overlay */}
            <AnimatePresence>
                {(phase === 'dim' || phase === 'morph' || phase === 'spokes') && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.1 }}
                        className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm"
                    />
                )}
            </AnimatePresence>

            {/* Hub + Spokes View */}
            <AnimatePresence>
                {(phase === 'morph' || phase === 'spokes') && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-50 flex flex-col items-center justify-center px-4 py-8"
                    >
                        {/* Hub Card (중앙) */}
                        <motion.div
                            className="w-full max-w-xs mb-6"
                            initial={{ y: 100, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ type: 'spring', stiffness: 300, damping: 30, duration: 0.25 }}
                            onAnimationComplete={handleMorphComplete}
                        >
                            <HubCard
                                data={parentCard}
                                layoutId={`hub-card-${parentCard.id}`}
                                isExpanded
                            />
                        </motion.div>

                        {/* Spokes (하단) */}
                        {phase === 'spokes' && (
                            <motion.div className="w-full max-w-lg">
                                <h3 className="text-center text-white/60 text-sm mb-3">
                                    어떤 변주를 적용할까요?
                                </h3>
                                <SpokeOptions
                                    options={spokeOptions}
                                    parentLayoutId={`hub-card-${parentCard.id}`}
                                    selectedId={selectedSpoke?.id}
                                    onSelect={handleSpokeSelect}
                                />

                                {/* 최종 확인 버튼 */}
                                {selectedSpoke && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        className="mt-6 px-4"
                                    >
                                        <motion.button
                                            onClick={handleFinalConfirm}
                                            whileHover={{ scale: 1.02 }}
                                            whileTap={{ scale: 0.98 }}
                                            className="w-full py-4 rounded-2xl bg-[#c1ff00] text-black font-bold text-lg shadow-[0_0_20px_rgba(193,255,0,0.4)]"
                                        >
                                            {selectedSpoke.label}로 콘텐츠 생성
                                        </motion.button>
                                    </motion.div>
                                )}

                                {/* 취소 버튼 */}
                                <motion.button
                                    onClick={handleCancel}
                                    className="w-full mt-3 py-3 text-white/50 text-sm"
                                    whileTap={{ scale: 0.98 }}
                                >
                                    다시 선택하기
                                </motion.button>
                            </motion.div>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
}

export default HubSpokesTransition;
