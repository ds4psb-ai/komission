'use client';

import { motion, stagger } from 'framer-motion';
import { Sparkles, Zap, Music, Camera } from 'lucide-react';

export interface SpokeOptionData {
    id: string;
    type: 'hook' | 'audio' | 'visual' | 'trend';
    label: string;
    description: string;
    confidence: number;
}

interface SpokeOptionsProps {
    options: SpokeOptionData[];
    parentLayoutId: string;
    onSelect: (option: SpokeOptionData) => void;
    selectedId?: string;
}

const SPOKE_ICONS: Record<SpokeOptionData['type'], React.ElementType> = {
    hook: Sparkles,
    audio: Music,
    visual: Camera,
    trend: Zap,
};

const SPOKE_COLORS: Record<SpokeOptionData['type'], string> = {
    hook: 'from-violet-500 to-purple-600',
    audio: 'from-cyan-500 to-blue-600',
    visual: 'from-pink-500 to-rose-600',
    trend: 'from-amber-500 to-orange-600',
};

/**
 * SpokeOptions - 변주 옵션 카드 그룹
 * 
 * Motion 12 stagger 애니메이션으로 순차적으로 등장합니다.
 * Hub 카드 아래에 수평 스크롤로 배치됩니다.
 */
export function SpokeOptions({ options, parentLayoutId, onSelect, selectedId }: SpokeOptionsProps) {
    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: {
                delayChildren: stagger(0.12, { from: 'first' }),
            },
        },
    };

    const itemVariants = {
        hidden: {
            opacity: 0,
            y: 20,  // 09 전략: 간결한 슬라이드
        },
        visible: {
            opacity: 1,
            y: 0,
            transition: {
                duration: 0.2,  // 09 전략: 150-250ms
                ease: 'easeOut' as const,
            },
        },
    };

    return (
        <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="flex gap-3 overflow-x-auto pb-4 px-4 -mx-4 hide-scrollbar"
        >
            {options.map((option) => {
                const Icon = SPOKE_ICONS[option.type];
                const gradient = SPOKE_COLORS[option.type];
                const isSelected = selectedId === option.id;

                return (
                    <motion.button
                        key={option.id}
                        layoutId={`${parentLayoutId}-spoke-${option.id}`}
                        variants={itemVariants}
                        onClick={() => onSelect(option)}
                        className={`
              relative flex-shrink-0 w-[140px] p-4 rounded-2xl
              border transition-all duration-200
              ${isSelected
                                ? 'bg-white/15 border-[#c1ff00]/50 ring-2 ring-[#c1ff00]/30'
                                : 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20'
                            }
            `}
                        whileHover={{ scale: 1.03 }}
                        whileTap={{ scale: 0.97 }}
                    >
                        {/* 아이콘 */}
                        <div className={`
              w-10 h-10 rounded-xl flex items-center justify-center mb-3
              bg-gradient-to-br ${gradient}
            `}>
                            <Icon className="w-5 h-5 text-white" />
                        </div>

                        {/* 라벨 */}
                        <h4 className="text-sm font-bold text-white mb-1">
                            {option.label}
                        </h4>

                        {/* 설명 */}
                        <p className="text-xs text-white/50 line-clamp-2">
                            {option.description}
                        </p>

                        {/* 신뢰도 인디케이터 */}
                        <div className="flex items-center gap-1.5 mt-3">
                            <div className="flex-1 h-1 rounded-full bg-white/10 overflow-hidden">
                                <motion.div
                                    className={`h-full rounded-full bg-gradient-to-r ${gradient}`}
                                    initial={{ width: 0 }}
                                    animate={{ width: `${option.confidence}%` }}
                                    transition={{ delay: 0.3, duration: 0.2, ease: 'easeOut' }}
                                />
                            </div>
                            <span className="text-[10px] text-white/40">
                                {option.confidence}%
                            </span>
                        </div>

                        {/* 선택 체크 */}
                        {isSelected && (
                            <motion.div
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                className="absolute top-2 right-2 w-5 h-5 rounded-full bg-[#c1ff00] flex items-center justify-center"
                            >
                                <svg className="w-3 h-3 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                </svg>
                            </motion.div>
                        )}
                    </motion.button>
                );
            })}
        </motion.div>
    );
}

export default SpokeOptions;
