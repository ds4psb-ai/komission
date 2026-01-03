'use client';

import { motion } from 'framer-motion';

interface KomiAvatarProps {
    size?: 'sm' | 'md' | 'lg';
    isSpeaking?: boolean;
}

/**
 * KomiAvatar - 코미 에이전트 아이덴티티
 * 
 * 시그니처 형광 라임(#c1ff00)을 사용한 숨쉬는 생명체형 아바타.
 * 2개의 회전하는 링과 중앙의 펄스 코어로 구성됨.
 */
export function KomiAvatar({ size = 'md', isSpeaking = false }: KomiAvatarProps) {
    const sizeClasses = {
        sm: 'w-8 h-8',
        md: 'w-12 h-12',
        lg: 'w-20 h-20',
    };

    return (
        <div className={`relative flex items-center justify-center ${sizeClasses[size]}`}>
            {/* Outer Glow */}
            <motion.div
                animate={{
                    scale: [1, 1.2, 1],
                    opacity: [0.3, 0.6, 0.3],
                }}
                transition={{
                    duration: 3,
                    repeat: Infinity,
                    ease: "easeInOut",
                }}
                className="absolute inset-0 bg-[#c1ff00]/20 blur-xl rounded-full"
            />

            {/* Rotating Ring 1 */}
            <motion.div
                animate={{ rotate: 360 }}
                transition={{
                    duration: 8,
                    repeat: Infinity,
                    ease: "linear",
                }}
                className="absolute inset-0 border border-[#c1ff00]/40 rounded-3xl"
                style={{ borderRadius: '40% 60% 70% 30% / 40% 50% 60% 50%' }}
            />

            {/* Rotating Ring 2 (Reverse) */}
            <motion.div
                animate={{ rotate: -360 }}
                transition={{
                    duration: 12,
                    repeat: Infinity,
                    ease: "linear",
                }}
                className="absolute inset-[2px] border border-[#c1ff00]/60 rounded-full opacity-70"
                style={{ borderRadius: '60% 40% 30% 70% / 60% 30% 70% 40%' }}
            />

            {/* Core */}
            <motion.div
                animate={isSpeaking ? {
                    scale: [0.9, 1.1, 0.9],
                } : {
                    scale: [1, 1.05, 1],
                }}
                transition={{
                    duration: isSpeaking ? 0.4 : 2,
                    repeat: Infinity,
                    ease: "easeInOut",
                }}
                className="relative z-10 w-[40%] h-[40%] bg-[#c1ff00] rounded-full shadow-[0_0_15px_rgba(193,255,0,0.8)]"
            >
                <div className="absolute top-[20%] right-[25%] w-[30%] h-[30%] bg-white rounded-full opacity-60 mix-blend-overlay" />
            </motion.div>
        </div>
    );
}
