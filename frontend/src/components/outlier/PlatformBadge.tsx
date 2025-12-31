'use client';

import React from 'react';

/**
 * PlatformBadge - Platform icon badge component
 * 
 * Shows platform icon (TikTok/YouTube/Instagram) in bottom-left of card
 * Virlo-style design: circular icon with semi-transparent background
 */

type Platform = 'tiktok' | 'youtube' | 'instagram';

interface PlatformBadgeProps {
    platform: Platform | string;
    size?: 'sm' | 'md' | 'lg';
    className?: string;
}

const PLATFORM_CONFIG: Record<string, { icon: React.ReactNode; label: string; bgClass: string; textClass: string }> = {
    tiktok: {
        icon: (
            <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full">
                <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z" />
            </svg>
        ),
        label: 'TikTok',
        bgClass: 'bg-black',
        textClass: 'text-white'
    },
    youtube: {
        icon: (
            <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full">
                <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
            </svg>
        ),
        label: 'YouTube',
        bgClass: 'bg-[#FF0000]',
        textClass: 'text-white'
    },
    instagram: {
        icon: (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
                <rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect>
                <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path>
                <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line>
            </svg>
        ),
        label: 'Instagram',
        bgClass: 'bg-gradient-to-tr from-[#f09433] via-[#dc2743] to-[#bc1888]',
        textClass: 'text-white'
    },
};

const SIZE_CONFIG = {
    sm: 'w-8 h-8 p-2',      // Increased from w-6
    md: 'w-10 h-10 p-2.5',  // Increased from w-8
    lg: 'w-12 h-12 p-3',    // Increased from w-10
};

export function PlatformBadge({ platform, size = 'md', className = '' }: PlatformBadgeProps) {
    const config = PLATFORM_CONFIG[platform.toLowerCase()] || PLATFORM_CONFIG.tiktok;
    const sizeClasses = SIZE_CONFIG[size];

    return (
        <div
            className={`
                flex items-center justify-center rounded-full
                shadow-lg border border-white/10
                ${config.bgClass} ${config.textClass} ${sizeClasses} ${className}
            `}
            title={config.label}
        >
            {config.icon}
        </div>
    );
}

export default PlatformBadge;
