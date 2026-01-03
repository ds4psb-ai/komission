'use client';

/**
 * ViewCountBadge - Shared component for view count display
 * 
 * Used by:
 * - UnifiedOutlierCard (homepage)
 * - /ops/outliers page (custom cards)
 * 
 * Shows: 👁️ 123K
 */

import React from 'react';

interface ViewCountBadgeProps {
    viewCount: number;
    size?: 'sm' | 'md';
    className?: string;
}

/**
 * Format number to readable format (e.g., 1.2M, 123K)
 */
export function formatViewCount(num: number): string {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
}

export function ViewCountBadge({
    viewCount,
    size = 'sm',
    className = '',
}: ViewCountBadgeProps) {
    const sizeClasses = size === 'md'
        ? 'px-2.5 py-1 text-xs'
        : 'px-2 py-1 text-[10px]';

    return (
        <div className={`flex items-center gap-1 bg-black/70 rounded-full ${sizeClasses} ${className}`}>
            <span>👁️</span>
            <span className="text-white font-medium">{formatViewCount(viewCount)}</span>
        </div>
    );
}

export default ViewCountBadge;
