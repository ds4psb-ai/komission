'use client';

/**
 * OutlierCardFooter - Shared component for creator info display
 * 
 * Used by:
 * - UnifiedOutlierCard (homepage)
 * - /ops/outliers page (custom cards)
 * 
 * Shows: @creator_username • 2d ago
 */

import React from 'react';

interface OutlierCardFooterProps {
    creatorUsername?: string | null;
    uploadDate?: string | null;
    crawledAt?: string | null;
    className?: string;
}

/**
 * Format date to relative time (e.g., "2d", "3h", "방금")
 */
export function formatRelativeTime(dateString?: string | null): string {
    if (!dateString) return '';
    const date = new Date(dateString);
    if (Number.isNaN(date.getTime())) return '';

    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffHours < 1) return '방금';
    if (diffHours < 24) return `${diffHours}h`;
    if (diffDays < 7) return `${diffDays}d`;
    return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
}

export function OutlierCardFooter({
    creatorUsername,
    uploadDate,
    crawledAt,
    className = '',
}: OutlierCardFooterProps) {
    const displayDate = uploadDate || crawledAt;
    const hasContent = creatorUsername || displayDate;

    if (!hasContent) return null;

    return (
        <div className={`flex items-center gap-2 ${className}`}>
            {creatorUsername && (
                <span className="text-[10px] text-white/60 font-medium">
                    {creatorUsername.startsWith('@') ? creatorUsername : `@${creatorUsername}`}
                </span>
            )}
            {displayDate && (
                <span className="text-[9px] text-white/40">
                    • {formatRelativeTime(displayDate)}
                </span>
            )}
        </div>
    );
}

export default OutlierCardFooter;
