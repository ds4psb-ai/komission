'use client';

import { motion } from 'framer-motion';

/**
 * Global Page Transition Template
 * 
 * Next.js의 template.tsx는 라우트 변경 시마다 리마운트되어
 * 페이지 진입 애니메이션을 자동으로 트리거합니다.
 */
export default function Template({ children }: { children: React.ReactNode }) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
                duration: 0.25,
                ease: [0.25, 0.46, 0.45, 0.94] // easeOutQuad
            }}
        >
            {children}
        </motion.div>
    );
}
