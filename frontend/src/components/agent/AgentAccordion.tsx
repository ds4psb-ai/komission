'use client';

import { useState, ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronUp, ChevronDown, Send } from 'lucide-react';
import { KomiAvatar } from './KomiAvatar';

interface AgentAccordionProps {
    children: ReactNode;
    isOpen?: boolean;
    onToggle?: (isOpen: boolean) => void;
    unreadCount?: number;
    agentName?: string;
}

/**
 * AgentAccordion (New Design)
 * 
 * 기존 Full-width 대신 중앙 정렬된 Floating Widget 스타일로 변경.
 * "Komi" 페르소나 아바타와 브랜드 컬러(#c1ff00)를 적극 활용.
 */
export function AgentAccordion({
    children,
    isOpen: controlledIsOpen,
    onToggle,
    unreadCount = 0,
    agentName = 'Komi',
}: AgentAccordionProps) {
    const [internalIsOpen, setInternalIsOpen] = useState(false);
    const isOpen = controlledIsOpen ?? internalIsOpen;

    const handleToggle = () => {
        const newState = !isOpen;
        setInternalIsOpen(newState);
        onToggle?.(newState);
    };

    return (
        <div className="fixed bottom-0 left-0 right-0 z-50 pointer-events-none flex justify-center pb-4">
            <motion.div
                layout
                initial={false}
                animate={{
                    width: isOpen ? '92%' : 'auto',
                    maxWidth: isOpen ? '600px' : '300px',
                }}
                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                className={`
          pointer-events-auto
          relative flex flex-col
          bg-[#0a0a0c]/80 backdrop-blur-xl
          border border-white/10
          shadow-[0_8px_32px_rgba(0,0,0,0.4)]
          overflow-hidden
          ${isOpen ? 'rounded-3xl' : 'rounded-full'}
        `}
            >
                {/* Header (Status Bar style when collapsed) */}
                <motion.button
                    layout="position"
                    onClick={handleToggle}
                    className={`
            relative z-10 w-full flex items-center justify-between
            ${isOpen ? 'p-4 border-b border-white/5' : 'pl-2 pr-6 py-2'}
            bg-gradient-to-r from-white/5 to-transparent
          `}
                >
                    <div className="flex items-center gap-3">
                        {/* Avatar */}
                        <motion.div layout id="komi-avatar-container">
                            <KomiAvatar size={isOpen ? 'md' : 'sm'} />
                        </motion.div>

                        {/* Title / Status Text */}
                        <div className="text-left flex flex-col justify-center">
                            <motion.div layout className="flex items-center gap-2">
                                <span className={`font-bold text-white ${isOpen ? 'text-lg' : 'text-sm'}`}>
                                    {agentName}
                                </span>
                                {unreadCount > 0 && (
                                    <span className="flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full bg-[#c1ff00] text-black text-[10px] font-bold">
                                        {unreadCount}
                                    </span>
                                )}
                                {!isOpen && (
                                    <span className="text-[10px] text-[#c1ff00] font-medium tracking-wide px-1.5 py-0.5 rounded-full bg-[#c1ff00]/10 border border-[#c1ff00]/20">
                                        ONLINE
                                    </span>
                                )}
                            </motion.div>

                            {isOpen && (
                                <motion.span
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="text-xs text-white/50"
                                >
                                    Viral Intelligence Agent
                                </motion.span>
                            )}
                        </div>
                    </div>

                    {/* Toggle Action */}
                    <div className="flex items-center gap-3">
                        {!isOpen && (
                            <span className="text-xs text-white/40 mr-1">
                                탭하여 대화하기
                            </span>
                        )}
                        <motion.div
                            animate={{ rotate: isOpen ? 180 : 0 }}
                            className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center border border-white/5"
                        >
                            <ChevronUp className="w-4 h-4 text-white/70" />
                        </motion.div>
                    </div>
                </motion.button>

                {/* Content Area */}
                <AnimatePresence>
                    {isOpen && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.3 }}
                            className="relative flex flex-col"
                        >
                            {/* Chat Content */}
                            <div className="h-[400px] max-h-[50vh] overflow-y-auto px-4 py-4 hide-scrollbar">
                                {children}
                            </div>

                            {/* Input Area (Mock) */}
                            <div className="p-3 bg-white/5 border-t border-white/5">
                                <div className="flex items-center gap-2 bg-[#0a0a0c] rounded-2xl px-4 py-3 border border-white/10 focus-within:border-[#c1ff00]/50 transition-colors">
                                    <input
                                        type="text"
                                        placeholder="코미에게 물어보세요..."
                                        className="flex-1 bg-transparent text-sm text-white placeholder-white/30 outline-none"
                                    />
                                    <button className="flex items-center justify-center w-8 h-8 rounded-xl bg-[#c1ff00] text-black hover:bg-[#c1ff00]/90 transition-colors">
                                        <Send className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.div>
        </div>
    );
}

export default AgentAccordion;
