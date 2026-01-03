'use client';
import { useTranslations } from 'next-intl';

/**
 * OutlierMetrics - Display view/like/share counts and outlier score
 */

import { Eye, Heart, MessageCircle, Share2 } from 'lucide-react';

interface OutlierMetricsProps {
    viewCount: number;
    likeCount?: number;
    shareCount?: number;
    commentCount?: number;
    outlierScore?: number;
    layout?: 'horizontal' | 'grid' | 'compact';
    className?: string;
}

function formatNumber(num: number): string {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(0)}K`;
    return num.toString();
}

export function OutlierMetrics({
    viewCount,
    likeCount,
    shareCount,
    commentCount,
    outlierScore,
    layout = 'horizontal',
    className = '',
}: OutlierMetricsProps) {
    const t = useTranslations('components.metrics');
    if (layout === 'compact') {
        return (
            <div className={`flex items-center gap-2 text-[10px] ${className}`}>
                <span className="px-2 py-0.5 bg-black/60 rounded-full text-white flex items-center gap-1">
                    <Eye className="w-3 h-3" /> {formatNumber(viewCount)}
                </span>
                {typeof outlierScore === 'number' && (
                    <span className="px-2 py-0.5 bg-pink-500/60 rounded-full text-white font-mono">
                        {outlierScore.toFixed(0)}x
                    </span>
                )}
            </div>
        );
    }

    if (layout === 'grid') {
        return (
            <div className={`grid grid-cols-3 gap-4 ${className}`}>
                <div className="p-3 bg-white/5 rounded-xl text-center">
                    <Eye className="w-5 h-5 mx-auto text-cyan-400 mb-1" />
                    <div className="text-lg font-black text-white">{formatNumber(viewCount)}</div>
                    <div className="text-[10px] text-white/40">{t('views')}</div>
                </div>
                <div className="p-3 bg-white/5 rounded-xl text-center">
                    <Heart className="w-5 h-5 mx-auto text-pink-400 mb-1" />
                    <div className="text-lg font-black text-white">{typeof likeCount === 'number' ? formatNumber(likeCount) : '-'}</div>
                    <div className="text-[10px] text-white/40">{t('likes')}</div>
                </div>
                <div className="p-3 bg-white/5 rounded-xl text-center">
                    <MessageCircle className="w-5 h-5 mx-auto text-emerald-400 mb-1" />
                    <div className="text-lg font-black text-white">{commentCount ?? 0}</div>
                    <div className="text-[10px] text-white/40">{t('comments')}</div>
                </div>
            </div>
        );
    }

    // horizontal layout
    return (
        <div className={`flex items-center gap-4 text-xs text-white/60 ${className}`}>
            <span className="flex items-center gap-1">
                <Eye className="w-4 h-4 text-cyan-400" />
                {formatNumber(viewCount)}
            </span>
            {typeof likeCount === 'number' && (
                <span className="flex items-center gap-1">
                    <Heart className="w-4 h-4 text-pink-400" />
                    {formatNumber(likeCount)}
                </span>
            )}
            {typeof shareCount === 'number' && (
                <span className="flex items-center gap-1">
                    <Share2 className="w-4 h-4 text-emerald-400" />
                    {formatNumber(shareCount)}
                </span>
            )}
            {typeof outlierScore === 'number' && (
                <span className="text-pink-400 font-mono font-bold">
                    {outlierScore.toFixed(1)}x
                </span>
            )}
        </div>
    );
}

export default OutlierMetrics;
