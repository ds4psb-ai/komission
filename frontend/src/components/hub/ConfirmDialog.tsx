'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Check, X } from 'lucide-react';

interface ConfirmDialogProps {
    isOpen: boolean;
    message?: string;
    confirmLabel?: string;
    cancelLabel?: string;
    onConfirm: () => void;
    onCancel: () => void;
}

/**
 * ConfirmDialog - "이대로 찾으시겠습니까?" 확인 다이얼로그
 * 
 * Human-in-the-Loop 패턴의 핵심 UI 컴포넌트입니다.
 * Hub-Spokes 트랜지션 전에 사용자 확정을 받습니다.
 */
export function ConfirmDialog({
    isOpen,
    message = '이대로 찾으시겠습니까?',
    confirmLabel = '네, 찾아주세요',
    cancelLabel = '다시 고를게요',
    onConfirm,
    onCancel,
}: ConfirmDialogProps) {
    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 z-50 flex items-center justify-center px-4"
                >
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
                        onClick={onCancel}
                    />

                    {/* Dialog */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                        className="relative w-full max-w-sm bg-[#0a0a0c] border border-white/10 rounded-3xl p-6 shadow-2xl"
                    >
                        {/* 아이콘 */}
                        <div className="flex justify-center mb-4">
                            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-[#c1ff00]/20 to-[#c1ff00]/5 flex items-center justify-center">
                                <span className="text-3xl">🎯</span>
                            </div>
                        </div>

                        {/* 메시지 */}
                        <h2 className="text-xl font-bold text-center text-white mb-2">
                            {message}
                        </h2>
                        <p className="text-sm text-white/50 text-center mb-6">
                            선택하신 패턴으로 추천을 시작합니다
                        </p>

                        {/* 버튼 */}
                        <div className="flex flex-col gap-3">
                            <motion.button
                                onClick={onConfirm}
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                                className="flex items-center justify-center gap-2 w-full py-4 rounded-2xl bg-[#c1ff00] text-black font-bold text-lg shadow-[0_0_20px_rgba(193,255,0,0.3)]"
                            >
                                <Check className="w-5 h-5 stroke-[3]" />
                                {confirmLabel}
                            </motion.button>

                            <motion.button
                                onClick={onCancel}
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                                className="flex items-center justify-center gap-2 w-full py-4 rounded-2xl bg-white/5 border border-white/10 text-white/70 font-medium"
                            >
                                <X className="w-5 h-5" />
                                {cancelLabel}
                            </motion.button>
                        </div>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}

export default ConfirmDialog;
