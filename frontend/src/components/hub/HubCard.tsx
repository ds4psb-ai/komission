'use client';

import { motion } from 'framer-motion';
import { Play, Eye, TrendingUp } from 'lucide-react';

export interface HubCardData {
    id: string;
    videoId: string;
    thumbnailUrl: string;
    title: string;
    patternName: string;
    views: number;
    score: number;
}

interface HubCardProps {
    data: HubCardData;
    layoutId?: string;
    isExpanded?: boolean;
    onClick?: () => void;
}

/**
 * HubCard - 중앙 부모 패턴 카드
 * 
 * Motion 12 layoutId를 사용하여 카드 → Hub 중앙으로 
 * 부드럽게 모프하는 애니메이션을 지원합니다.
 */
export function HubCard({ data, layoutId, isExpanded = false, onClick }: HubCardProps) {
    const cardLayoutId = layoutId ?? `hub-card-${data.id}`;

    return (
        <motion.div
            layoutId={cardLayoutId}
            onClick={onClick}
            className={`
        relative overflow-hidden rounded-2xl cursor-pointer
        ${isExpanded
                    ? 'w-full max-w-md mx-auto'
                    : 'w-full'
                }
      `}
            transition={{
                type: 'spring',
                stiffness: 300,
                damping: 30
            }}
            whileHover={!isExpanded ? { scale: 1.02 } : undefined}
            whileTap={!isExpanded ? { scale: 0.98 } : undefined}
        >
            {/* 썸네일 배경 */}
            <motion.div
                layoutId={`${cardLayoutId}-thumbnail`}
                className="relative aspect-[9/16] w-full"
            >
                <img
                    src={data.thumbnailUrl}
                    alt={data.title}
                    className="w-full h-full object-cover"
                />

                {/* 그라디언트 오버레이 */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />

                {/* 재생 아이콘 */}
                <motion.div
                    layoutId={`${cardLayoutId}-play`}
                    className="absolute inset-0 flex items-center justify-center"
                >
                    <div className="w-14 h-14 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center">
                        <Play className="w-6 h-6 text-white fill-white ml-1" />
                    </div>
                </motion.div>
            </motion.div>

            {/* 카드 정보 */}
            <motion.div
                layoutId={`${cardLayoutId}-info`}
                className="absolute bottom-0 left-0 right-0 p-4"
            >
                {/* 패턴 이름 태그 */}
                <motion.div
                    layoutId={`${cardLayoutId}-pattern`}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#c1ff00]/20 border border-[#c1ff00]/30 mb-2"
                >
                    <TrendingUp className="w-3.5 h-3.5 text-[#c1ff00]" />
                    <span className="text-xs font-semibold text-[#c1ff00]">
                        {data.patternName}
                    </span>
                </motion.div>

                {/* 제목 */}
                <motion.h3
                    layoutId={`${cardLayoutId}-title`}
                    className={`
            font-bold text-white line-clamp-2
            ${isExpanded ? 'text-lg' : 'text-sm'}
          `}
                >
                    {data.title}
                </motion.h3>

                {/* 통계 */}
                <motion.div
                    layoutId={`${cardLayoutId}-stats`}
                    className="flex items-center gap-3 mt-2 text-white/60 text-xs"
                >
                    <div className="flex items-center gap-1">
                        <Eye className="w-3.5 h-3.5" />
                        <span>{formatViews(data.views)}</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <span className="text-[#c1ff00]">+{data.score}%</span>
                        <span>성과</span>
                    </div>
                </motion.div>
            </motion.div>
        </motion.div>
    );
}

function formatViews(views: number): string {
    if (views >= 1_000_000) {
        return `${(views / 1_000_000).toFixed(1)}M`;
    }
    if (views >= 1_000) {
        return `${(views / 1_000).toFixed(1)}K`;
    }
    return views.toString();
}

export default HubCard;
