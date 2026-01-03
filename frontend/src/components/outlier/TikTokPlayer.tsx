'use client';
import { useTranslations } from 'next-intl';
import Image from 'next/image';

/**
 * TikTokPlayer - Reusable TikTok video player component
 * 
 * Features:
 * - Virlo-style v1 player with postMessage unmute
 * - Next.js Image Optimization for stable thumbnail loading
 * - Multiple size variants (sm/md/lg)
 * - Hover preview support
 */

import { useState, useRef } from 'react';

// Extract video ID from various URL formats (TikTok and YouTube)
export function extractTikTokVideoId(url: string): string | null {
    return extractVideoId(url);
}

// Multi-platform video ID extraction
export function extractVideoId(url: string): string | null {
    if (!url) return null;

    // TikTok patterns
    const tiktokPatterns = [
        /video\/(\d+)/,
        /\/v\/(\d+)/,
        /tiktok\.com\/.*?(\d{15,})/
    ];
    for (const pattern of tiktokPatterns) {
        const match = url.match(pattern);
        if (match) return match[1];
    }

    // YouTube patterns (shorts, watch, youtu.be)
    const youtubePatterns = [
        /shorts\/([^?/]+)/,           // youtube.com/shorts/VIDEO_ID
        /[?&]v=([^?&]+)/,             // youtube.com/watch?v=VIDEO_ID
        /youtu\.be\/([^?/]+)/,        // youtu.be/VIDEO_ID
        /embed\/([^?/]+)/,            // youtube.com/embed/VIDEO_ID
    ];
    for (const pattern of youtubePatterns) {
        const match = url.match(pattern);
        if (match) return match[1];
    }

    // Instagram patterns (reel shortcode)
    // URLs: /reel/DS-reO9DxJi/ , /p/ABC123/ , /reels/ABC123/
    const instagramPatterns = [
        /\/reel\/([A-Za-z0-9_-]+)/,   // instagram.com/reel/SHORTCODE
        /\/reels\/([A-Za-z0-9_-]+)/,  // instagram.com/reels/SHORTCODE
        /\/p\/([A-Za-z0-9_-]+)/,      // instagram.com/p/SHORTCODE (posts/videos)
    ];
    for (const pattern of instagramPatterns) {
        const match = url.match(pattern);
        if (match) return match[1];
    }

    return null;
}

// Detect platform from URL
export function detectPlatform(url: string): 'tiktok' | 'youtube' | 'instagram' | 'unknown' {
    if (!url) return 'unknown';
    if (url.includes('tiktok.com')) return 'tiktok';
    if (url.includes('youtube.com') || url.includes('youtu.be')) return 'youtube';
    if (url.includes('instagram.com')) return 'instagram';
    return 'unknown';
}

// Proxy thumbnail URL through weserv.nl
// For Instagram, includes fallback handling since CDN URLs expire quickly
export function getProxiedThumbnailUrl(thumbnailUrl: string, videoUrl?: string): string {
    if (!thumbnailUrl) {
        // If no thumbnail but we have a video URL, try to generate a fallback
        if (videoUrl && videoUrl.includes('instagram.com')) {
            // Use Instagram's embed as a pseudo-thumbnail (won't work as img, but signals we tried)
            return '';
        }
        return '';
    }
    return `https://images.weserv.nl/?url=${encodeURIComponent(thumbnailUrl)}&output=jpg&default=404`;
}

// Get Instagram shortcode from URL for fallback display
export function getInstagramShortcode(url: string): string | null {
    if (!url) return null;
    const match = url.match(/\/(reel|p|reels)\/([A-Za-z0-9_-]+)/);
    return match ? match[2] : null;
}

interface TikTokPlayerProps {
    videoUrl: string;
    thumbnailUrl?: string;
    size?: 'sm' | 'md' | 'lg' | 'full';
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
    full: 'w-full',  // Responsive width
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
    const videoId = extractVideoId(videoUrl);
    const platform = detectPlatform(videoUrl);
    const [isMuted, setIsMuted] = useState(true);
    const iframeRef = useRef<HTMLIFrameElement>(null);

    // Platform-specific embed URL
    let embedUrl: string | null = null;
    if (videoId) {
        if (platform === 'youtube') {
            // YouTube Shorts embed - with enablejsapi for postMessage control
            embedUrl = `https://www.youtube.com/embed/${videoId}?autoplay=${autoplay ? 1 : 0}&loop=${loop ? 1 : 0}&mute=${autoplay ? 1 : 0}&controls=${showControls ? 1 : 0}&playsinline=1&enablejsapi=1&origin=${typeof window !== 'undefined' ? window.location.origin : ''}`;
        } else if (platform === 'instagram') {
            // Instagram Reel embed - official embed URL pattern (Virlo reverse-engineered)
            embedUrl = `https://www.instagram.com/reel/${videoId}/embed/?autoplay=1`;
        } else {
            // TikTok embed (default)
            embedUrl = `https://www.tiktok.com/player/v1/${videoId}?autoplay=${autoplay ? 1 : 0}&loop=${loop ? 1 : 0}&mute=1&controls=${showControls ? 1 : 0}&progress_bar=${showControls ? 1 : 0}&play_button=${showControls ? 1 : 0}&volume_control=${showControls ? 1 : 0}&fullscreen_button=${showControls ? 1 : 0}`;
        }
    }

    // Proxied thumbnail
    const proxiedThumb = thumbnailUrl ? getProxiedThumbnailUrl(thumbnailUrl) : null;

    // Platform-specific unmute implementation
    const handleToggleMute = (e: React.MouseEvent) => {
        e.stopPropagation();
        const iframe = iframeRef.current;
        if (!iframe?.contentWindow) return;

        if (platform === 'youtube') {
            // YouTube IFrame API postMessage
            // unMute: {"event":"command","func":"unMute","args":[]}
            // mute: {"event":"command","func":"mute","args":[]}
            iframe.contentWindow.postMessage(JSON.stringify({
                event: 'command',
                func: isMuted ? 'unMute' : 'mute',
                args: []
            }), '*');
        } else {
            // TikTok postMessage - 'unMute' has capital M
            iframe.contentWindow.postMessage({
                type: isMuted ? 'unMute' : 'mute',
                'x-tiktok-player': true,
                value: undefined
            }, '*');
        }

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

// Hover preview version with optional mute control
interface TikTokHoverPreviewProps {
    videoUrl: string;
    thumbnailUrl?: string;
    isHovering: boolean;
    showMuteOnHover?: boolean;
    className?: string;
}

export function TikTokHoverPreview({
    videoUrl,
    thumbnailUrl,
    isHovering,
    showMuteOnHover = false,
    className = '',
}: TikTokHoverPreviewProps) {
    const [thumbnailError, setThumbnailError] = useState(false);
    const [isMuted, setIsMuted] = useState(true);
    const iframeRef = useRef<HTMLIFrameElement>(null);
    const videoId = extractVideoId(videoUrl);
    const platform = detectPlatform(videoUrl);
    const proxiedThumb = thumbnailUrl ? getProxiedThumbnailUrl(thumbnailUrl) : null;

    // Platform-specific preview URL
    let previewUrl: string | null = null;
    if (videoId) {
        if (platform === 'youtube') {
            previewUrl = `https://www.youtube.com/embed/${videoId}?autoplay=1&mute=1&loop=1&controls=0&playsinline=1&enablejsapi=1&origin=${typeof window !== 'undefined' ? window.location.origin : ''}`;
        } else if (platform === 'instagram') {
            previewUrl = `https://www.instagram.com/reel/${videoId}/embed/?autoplay=1`;
        } else {
            previewUrl = `https://www.tiktok.com/player/v1/${videoId}?autoplay=1&loop=1&mute=1&controls=0&progress_bar=0&play_button=0&volume_control=0&fullscreen_button=0`;
        }
    }

    // Platform-specific unmute implementation
    const handleToggleMute = (e: React.MouseEvent) => {
        e.stopPropagation();
        const iframe = iframeRef.current;
        if (!iframe?.contentWindow) return;

        if (platform === 'youtube') {
            iframe.contentWindow.postMessage(JSON.stringify({
                event: 'command',
                func: isMuted ? 'unMute' : 'mute',
                args: []
            }), '*');
        } else {
            // TikTok postMessage - 'unMute' has capital M
            iframe.contentWindow.postMessage({
                type: isMuted ? 'unMute' : 'mute',
                'x-tiktok-player': true,
                value: undefined
            }, '*');
        }

        setIsMuted(!isMuted);
    };

    // For Instagram, show embed immediately if thumbnail fails or is missing
    const showInstagramEmbed = platform === 'instagram' && (!proxiedThumb || thumbnailError);

    return (
        <div className={`relative aspect-[9/16] bg-gradient-to-br from-pink-500/20 to-cyan-500/20 overflow-hidden ${className}`}>
            {/* Instagram fallback: Show embed directly when thumbnail unavailable */}
            {showInstagramEmbed && previewUrl ? (
                <iframe
                    ref={iframeRef}
                    src={previewUrl}
                    className="absolute inset-0 w-full h-full"
                    allow="autoplay; encrypted-media"
                    frameBorder="0"
                    loading="lazy"
                />
            ) : proxiedThumb && !thumbnailError ? (
                <Image
                    src={proxiedThumb}
                    alt=""
                    fill
                    className="object-cover"
                    sizes="(max-width: 768px) 50vw, 320px"
                    unoptimized={false}
                    onError={() => setThumbnailError(true)}
                />
            ) : (
                <div className="absolute inset-0 flex items-center justify-center text-5xl opacity-30">
                    {videoId ? '🎵' : '⚠️'}
                </div>
            )}

            {/* Hover Preview Iframe (for non-Instagram or when thumbnail is showing) */}
            {isHovering && previewUrl && !showInstagramEmbed && (
                <iframe
                    ref={iframeRef}
                    src={previewUrl}
                    className="absolute inset-0 w-full h-full z-[1]"
                    allow="autoplay; encrypted-media"
                    frameBorder="0"
                />
            )}

            {/* Mute button - shown on hover */}
            {showMuteOnHover && isHovering && (
                <button
                    onClick={handleToggleMute}
                    className="absolute left-2 top-1/2 -translate-y-1/2 p-2 rounded-full bg-black/60 backdrop-blur-sm border border-white/20 hover:bg-black/80 transition-all z-[10] opacity-80 hover:opacity-100"
                    title={isMuted ? '음소거 해제' : '음소거'}
                >
                    {isMuted ? (
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                            <line x1="23" y1="9" x2="17" y2="15" />
                            <line x1="17" y1="9" x2="23" y2="15" />
                        </svg>
                    ) : (
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                            <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
                            <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
                        </svg>
                    )}
                </button>
            )}

            {/* Gradient overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent z-[2] pointer-events-none" />
        </div>
    );
}

export default TikTokPlayer;
