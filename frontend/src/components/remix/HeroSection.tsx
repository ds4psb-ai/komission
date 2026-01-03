// frontend/src/components/remix/HeroSection.tsx
"use client";
import { useTranslations } from 'next-intl';

/**
 * HeroSection - Detail page hero with video preview and hook highlight
 * 
 * Features:
 * - 9:16 video thumbnail/preview
 * - Hook pattern with Korean explanation
 * - Hook strength indicator
 * - Click to play/expand video
 */

import { useState } from "react";
import { Play, Zap, Sparkles, ExternalLink } from "lucide-react";

// Hook pattern Korean mappings
const HOOK_PATTERN_KO: Record<string, { name: string; desc: string; emoji: string }> = {
    pattern_break: { name: "패턴 브레이크", desc: "예상을 깨는 반전으로 시선 고정", emoji: "⚡" },
    visual_reaction: { name: "시각적 리액션", desc: "표정/행동 변화로 감정 전달", emoji: "😲" },
    transformation: { name: "변신/트랜스폼", desc: "Before→After로 호기심 유발", emoji: "✨" },
    reveal: { name: "공개/리빌", desc: "숨겨진 것을 드러내며 긴장감 조성", emoji: "🎁" },
    unboxing: { name: "언박싱", desc: "개봉 과정의 설렘과 기대감 활용", emoji: "📦" },
    challenge: { name: "챌린지", desc: "참여 욕구와 경쟁심 자극", emoji: "🏆" },
    question: { name: "질문 유도", desc: "궁금증을 유발하여 끝까지 시청", emoji: "❓" },
    comparison: { name: "비교", desc: "대조를 통한 차이점 강조", emoji: "⚖️" },
    countdown: { name: "카운트다운", desc: "긴장감과 기대감 동시 유발", emoji: "⏱️" },
    action: { name: "액션", desc: "역동적인 움직임으로 몰입 유도", emoji: "🎬" },
    setup: { name: "셋업", desc: "상황 설정으로 맥락 전달", emoji: "🎭" },
    shock: { name: "충격", desc: "예상치 못한 장면으로 집중력 극대화", emoji: "💥" },
};

interface HookGenome {
    pattern?: string;
    strength?: number;
    hook_summary?: string;
}

interface HeroSectionProps {
    title: string;
    sourceUrl: string;
    thumbnailUrl?: string;
    platform?: string;
    hookGenome?: HookGenome;
    viewCount?: number;
}

export function HeroSection({
    title,
    sourceUrl,
    thumbnailUrl,
    platform,
    hookGenome,
    viewCount,
}: HeroSectionProps) {
    const [showVideo, setShowVideo] = useState(false);

    // Get hook pattern info
    const patternKey = hookGenome?.pattern?.toLowerCase().replace(/\s+/g, "_") || "";
    const patternInfo = HOOK_PATTERN_KO[patternKey] || {
        name: hookGenome?.pattern || "분석 중",
        desc: "훅 패턴을 분석하고 있습니다...",
        emoji: "🎣",
    };
    const strengthPercent = (hookGenome?.strength || 0) * 100;

    // Generate embed URL for video
    const getEmbedUrl = () => {
        if (platform === "youtube" || sourceUrl.includes("youtube") || sourceUrl.includes("youtu.be")) {
            const videoId = sourceUrl.match(/(?:youtube\.com\/(?:watch\?v=|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/)?.[1];
            return videoId ? `https://www.youtube.com/embed/${videoId}` : null;
        }
        return null;
    };

    const embedUrl = getEmbedUrl();

    return (
        <div className="glass-panel rounded-2xl overflow-hidden border border-white/10">
            <div className="flex flex-col md:flex-row">
                {/* Video Preview - Left Side */}
                <div className="relative w-full md:w-[280px] aspect-[9/16] bg-black shrink-0 border-r border-white/10">
                    {showVideo && embedUrl ? (
                        <iframe
                            src={`${embedUrl}?autoplay=1`}
                            className="absolute inset-0 w-full h-full"
                            allow="autoplay; encrypted-media"
                            allowFullScreen
                        />
                    ) : (
                        <>
                            {/* Thumbnail or placeholder */}
                            {thumbnailUrl ? (
                                <img
                                    src={thumbnailUrl}
                                    alt={title}
                                    className="absolute inset-0 w-full h-full object-cover"
                                />
                            ) : (
                                <div className="absolute inset-0 bg-gradient-to-br from-violet-900/50 to-pink-900/50 flex items-center justify-center">
                                    <Sparkles className="w-12 h-12 text-white/20" />
                                </div>
                            )}

                            {/* Play overlay */}
                            <button
                                onClick={() => setShowVideo(true)}
                                className="absolute inset-0 flex items-center justify-center bg-black/40 hover:bg-black/30 transition-colors group"
                            >
                                <div className="w-16 h-16 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center group-hover:scale-110 transition-transform">
                                    <Play className="w-8 h-8 text-white ml-1" fill="white" />
                                </div>
                            </button>

                            {/* Platform badge */}
                            {platform && (
                                <div className="absolute top-3 left-3 px-2 py-1 bg-black/60 backdrop-blur-sm rounded-full text-xs text-white/80 font-medium">
                                    {platform === "youtube" ? "▶️ Shorts" : platform === "tiktok" ? "🎵 TikTok" : "📷 Reels"}
                                </div>
                            )}
                        </>
                    )}
                </div>

                {/* Content - Right Side */}
                <div className="flex-1 p-6 space-y-4">
                    {/* Title */}
                    <div>
                        <h1 className="text-xl font-black text-white line-clamp-2">{title}</h1>
                        {typeof viewCount === 'number' && (
                            <p className="text-sm text-white/50 mt-1">
                                👁️ {viewCount >= 1000 ? `${(viewCount / 1000).toFixed(0)}K` : viewCount} views
                            </p>
                        )}
                    </div>

                    {/* Hook Pattern Highlight */}
                    {hookGenome && (
                        <div className="p-5 bg-gradient-to-br from-violet-500/10 to-pink-500/10 rounded-xl border border-violet-500/20 relative overflow-hidden group">
                            <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity" />

                            <div className="flex items-start gap-4 relative z-10">
                                <span className="text-3xl">{patternInfo.emoji}</span>
                                <div className="flex-1">
                                    <div className="flex items-center gap-2">
                                        <span className="font-bold text-white">{patternInfo.name}</span>
                                        <span className="text-[10px] text-white/40 uppercase">{hookGenome.pattern}</span>
                                    </div>
                                    <p className="text-sm text-violet-200 mt-1">{patternInfo.desc}</p>
                                </div>
                            </div>

                            {/* Strength bar */}
                            <div className="mt-4 space-y-2 relative z-10">
                                <div className="flex items-center justify-between text-xs font-medium">
                                    <span className="text-violet-300/70">HOOK STRENGTH</span>
                                    <span className="text-violet-300">{strengthPercent.toFixed(0)}%</span>
                                </div>
                                <div className="h-2.5 bg-black/40 rounded-full overflow-hidden border border-white/5">
                                    <div
                                        className="h-full bg-gradient-to-r from-violet-500 to-pink-500 rounded-full shadow-[0_0_10px_rgba(139,92,246,0.3)] transition-all duration-1000"
                                        style={{ width: `${strengthPercent}%` }}
                                    />
                                </div>
                            </div>

                            {/* Hook summary */}
                            {hookGenome.hook_summary && (
                                <p className="mt-3 text-xs text-white/70 leading-relaxed border-t border-white/10 pt-3">
                                    💡 {hookGenome.hook_summary}
                                </p>
                            )}
                        </div>
                    )}

                    {/* Original link */}
                    <a
                        href={sourceUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 text-xs text-white/50 hover:text-white/80 transition-colors"
                    >
                        <ExternalLink className="w-3.5 h-3.5" />
                        원본 영상 보기
                    </a>
                </div>
            </div>
        </div>
    );
}

export default HeroSection;
