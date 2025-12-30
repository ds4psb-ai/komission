'use client';

/**
 * TikTokPlayer - Reusable TikTok video player component
 * 
 * Features:
 * - Virlo-style v1 player with postMessage unmute
 * - weserv.nl thumbnail proxy for CORS
 * - Multiple size variants (sm/md/lg)
 * - Hover preview support
 */

import { useState, useRef } from 'react';

// Extract TikTok video ID from various URL formats
export function extractTikTokVideoId(url: string): string | null {
    if (!url) return null;
    const patterns = [
        /video\/(\d+)/,
        /\/v\/(\d+)/,
        /tiktok\.com\/.*?(\d{15,})/
    ];
    for (const pattern of patterns) {
        const match = url.match(pattern);
        if (match) return match[1];
    }
    return null;
}

// Proxy thumbnail URL through weserv.nl
export function getProxiedThumbnailUrl(thumbnailUrl: string): string {
    if (!thumbnailUrl) return '';
    return `https://images.weserv.nl/?url=${encodeURIComponent(thumbnailUrl)}&output=jpg&default=404`;
}

interface TikTokPlayerProps {
    videoUrl: string;
    thumbnailUrl?: string;
    size?: 'sm' | 'md' | 'lg';
    showUnmute?: boolean;
    autoplay?: boolean;
    loop?: boolean;
    showControls?: boolean;
    className?: string;
}

const SIZE_CONFIG = {
    sm: 'w-32',      // 128px - for small cards
    md: 'w-64',      // 256px - for medium cards  
    lg: 'w-80',      // 320px - for modal/detail view
};

export function TikTokPlayer({
    videoUrl,
    thumbnailUrl,
    size = 'lg',
    showUnmute = true,
    autoplay = true,
    loop = true,
    showControls = true,
    className = '',
}: TikTokPlayerProps) {
    const videoId = extractTikTokVideoId(videoUrl);
    const [isMuted, setIsMuted] = useState(true);
    const iframeRef = useRef<HTMLIFrameElement>(null);

    // Virlo-style v1 player URL - ALWAYS starts muted for autoplay
    const embedUrl = videoId
        ? `https://www.tiktok.com/player/v1/${videoId}?autoplay=${autoplay ? 1 : 0}&loop=${loop ? 1 : 0}&mute=1&controls=${showControls ? 1 : 0}&progress_bar=${showControls ? 1 : 0}&play_button=${showControls ? 1 : 0}&volume_control=${showControls ? 1 : 0}&fullscreen_button=${showControls ? 1 : 0}`
        : null;

    // Proxied thumbnail
    const proxiedThumb = thumbnailUrl ? getProxiedThumbnailUrl(thumbnailUrl) : null;

    // Virlo's exact postMessage implementation
    const handleToggleMute = (e: React.MouseEvent) => {
        e.stopPropagation();
        const iframe = iframeRef.current;
        if (!iframe?.contentWindow) return;

        // Send postMessage to TikTok player - 'unMute' has capital M
        iframe.contentWindow.postMessage({
            type: isMuted ? 'unMute' : 'mute',
            'x-tiktok-player': true,
            value: undefined
        }, '*');

        setIsMuted(!isMuted);
    };

    if (!videoId) {
        return (
            <div className={`relative aspect-[9/16] ${SIZE_CONFIG[size]} bg-zinc-900 rounded-2xl flex flex-col items-center justify-center gap-3 ${className}`}>
                <span className="text-4xl">⚠️</span>
                <span className="text-xs text-red-400 font-bold">비디오 ID 없음</span>
                <span className="text-[10px] text-white/40 text-center px-4">
                    URL에서 video ID를 추출할 수 없습니다
                </span>
            </div>
        );
    }

    return (
        <div className={`relative aspect-[9/16] ${SIZE_CONFIG[size]} bg-black rounded-2xl overflow-hidden border-2 border-white/20 ${className}`}>
            {/* Thumbnail as base layer */}
            {proxiedThumb && (
                <img
                    src={proxiedThumb}
                    alt="Video thumbnail"
                    className="absolute inset-0 w-full h-full object-cover"
                    loading="lazy"
                />
            )}

            {/* TikTok iframe */}
            {embedUrl && (
                <iframe
                    ref={iframeRef}
                    src={embedUrl}
                    className="absolute inset-0 w-full h-full"
                    allowFullScreen
                    allow="autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share; microphone; camera"
                    frameBorder="0"
                />
            )}

            {/* Virlo-style Unmute Button */}
            {showUnmute && (
                <button
                    onClick={handleToggleMute}
                    className="absolute left-4 top-1/2 -translate-y-1/2 p-3 rounded-full bg-black/50 backdrop-blur-sm border border-white/20 hover:bg-black/70 transition-colors z-10"
                    title={isMuted ? '음소거 해제' : '음소거'}
                >
                    {isMuted ? (
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                            <line x1="23" y1="9" x2="17" y2="15" />
                            <line x1="17" y1="9" x2="23" y2="15" />
                        </svg>
                    ) : (
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                            <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
                            <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
                        </svg>
                    )}
                </button>
            )}
        </div>
    );
}

// Hover preview version (minimal, no controls)
interface TikTokHoverPreviewProps {
    videoUrl: string;
    thumbnailUrl?: string;
    isHovering: boolean;
    className?: string;
}

export function TikTokHoverPreview({
    videoUrl,
    thumbnailUrl,
    isHovering,
    className = '',
}: TikTokHoverPreviewProps) {
    const videoId = extractTikTokVideoId(videoUrl);
    const proxiedThumb = thumbnailUrl ? getProxiedThumbnailUrl(thumbnailUrl) : null;

    const previewUrl = videoId
        ? `https://www.tiktok.com/player/v1/${videoId}?autoplay=1&loop=1&mute=1&controls=0&progress_bar=0&play_button=0&volume_control=0&fullscreen_button=0`
        : null;

    return (
        <div className={`relative aspect-[9/16] bg-gradient-to-br from-pink-500/20 to-cyan-500/20 overflow-hidden ${className}`}>
            {/* Static Thumbnail */}
            {proxiedThumb ? (
                <img
                    src={proxiedThumb}
                    alt=""
                    className="absolute inset-0 w-full h-full object-cover"
                    loading="lazy"
                />
            ) : (
                <div className="absolute inset-0 flex items-center justify-center text-5xl opacity-30">
                    {videoId ? '🎵' : '⚠️'}
                </div>
            )}

            {/* Hover Preview Iframe */}
            {isHovering && previewUrl && (
                <iframe
                    src={previewUrl}
                    className="absolute inset-0 w-full h-full z-[1] pointer-events-none"
                    allow="autoplay; encrypted-media"
                    frameBorder="0"
                />
            )}

            {/* Gradient overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent z-[2] pointer-events-none" />
        </div>
    );
}

export default TikTokPlayer;
