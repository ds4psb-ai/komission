"use client";

/**
 * Video Detail Page with Virlo-style layout
 * /video/[id]
 * 
 * Layout:
 * - Left: Video embed player
 * - Right: Viral Guide + Experience Campaign options (conditional)
 */
import React, { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { AppHeader } from '@/components/AppHeader';
import { StoryboardPanel } from '@/components/video/StoryboardPanel';
import { CoachingSession } from '@/components/CoachingSession';
import {
    ArrowLeft, Play, ExternalLink, Bookmark, Copy, Check,
    Target, Clock, Sparkles, Eye, Heart, TrendingUp,
    Camera, Mic, Film, Users, Truck, MapPin, Calendar,
    ChevronRight, Award, Star, Lock, Rocket, Video
} from 'lucide-react';

// ==================
// Types
// ==================

interface VideoAnalysis {
    hook_pattern?: string;
    hook_score?: number;
    hook_duration_sec?: number;
    visual_patterns?: string[];
    audio_pattern?: string;
    engagement_peak_sec?: number;
    best_comment?: string;
    shotlist?: string[];
    timing?: string[];
    do_not?: string[];
    // Temporal Variation Theory: 불변/가변 가이드
    invariant?: string[];  // 🔒 절대 유지해야 할 요소
    variable?: string[];   // ✨ 창의성 발휘 가능 요소
}

interface VideoDetail {
    id: string;
    video_url: string;
    platform: 'tiktok' | 'instagram' | 'youtube';
    title: string;
    thumbnail_url?: string;
    creator?: string;
    category: string;
    tags?: string[];
    view_count: number;
    like_count?: number;
    engagement_rate?: number;
    outlier_tier?: 'S' | 'A' | 'B' | 'C' | null;
    creator_avg_views?: number;
    analysis?: VideoAnalysis;
    rawVdg?: RawVDG | null;
    hasCampaign?: boolean;
    campaignType?: 'product' | 'visit' | 'delivery';
}

// RawVDG type for Storyboard
interface RawVDG {
    title: string;
    title_ko: string;
    total_duration: number;
    scene_count: number;
    scenes: Array<{
        scene_id: string;
        scene_number: number;
        time_start: number;
        time_end: number;
        duration_sec: number;
        time_label: string;
        role: string;
        role_en: string;
        summary: string;
        summary_ko: string;
        dialogue: string;
        comedic_device: string[];
        camera: {
            shot: string;
            shot_en: string;
            move: string;
            move_en: string;
            angle: string;
            angle_en: string;
        };
        location: string;
        lighting: string;
        lighting_en: string;
        edit_pace: string;
        edit_pace_en: string;
        audio_events: Array<{
            label: string;
            label_en: string;
            intensity: string;
        }>;
        music: string;
        ambient: string;
    }>;
}

// No demo data - all data comes from API
const DEMO_VIDEOS: Record<string, VideoDetail> = {};

// ==================
// Platform Embed
// ==================

function VideoEmbed({ video }: { video: VideoDetail }) {
    const [resolvedVideoId, setResolvedVideoId] = useState<string | null>(null);
    const [isResolving, setIsResolving] = useState(false);
    const [, setResolveFailed] = useState(false);

    // Check if it's a TikTok short link
    const isShortLink = video.platform === 'tiktok' &&
        (video.video_url.includes('vt.tiktok.com') || video.video_url.includes('vm.tiktok.com'));

    const extractId = (url: string) => {
        if (video.platform === 'tiktok') {
            const standardMatch = url.match(/video\/(\d+)/);
            if (standardMatch) return standardMatch[1];
            return null;
        }
        if (video.platform === 'youtube') {
            const match = url.match(/(?:shorts\/|v=|\/embed\/)([a-zA-Z0-9_-]+)/);
            return match ? match[1] : null;
        }
        return null;
    };

    // Resolve short link via API
    useEffect(() => {
        let isActive = true;

        if (isShortLink && !resolvedVideoId && !isResolving) {
            setIsResolving(true);
            fetch(`/api/v1/outliers/utils/resolve-url?url=${encodeURIComponent(video.video_url)}`)
                .then(res => res.json())
                .then(data => {
                    if (!isActive) return;
                    if (data.content_id) {
                        setResolvedVideoId(data.content_id);
                    } else {
                        setResolveFailed(true);
                    }
                })
                .catch(() => {
                    if (!isActive) return;
                    setResolveFailed(true);
                })
                .finally(() => {
                    if (isActive) {
                        setIsResolving(false);
                    }
                });
        }

        return () => {
            isActive = false;
        };
    }, [isShortLink, video.video_url, resolvedVideoId, isResolving]);

    // Try direct extraction first
    const directVideoId = extractId(video.video_url);
    const videoId = directVideoId || resolvedVideoId;

    // Loading state for short link resolution
    if (isShortLink && isResolving) {
        return (
            <div className="relative w-full h-full flex items-center justify-center bg-zinc-950/50 rounded-2xl">
                <div className="relative w-full max-w-[340px] aspect-[9/16] bg-gradient-to-br from-zinc-900 to-zinc-800 rounded-2xl overflow-hidden shadow-2xl flex flex-col items-center justify-center p-6">
                    <div className="w-8 h-8 border-2 border-white/20 border-t-pink-500 rounded-full animate-spin mb-4" />
                    <p className="text-white/60 text-sm">링크 처리 중...</p>
                </div>
            </div>
        );
    }

    // Fallback if no video ID found
    if (!videoId) {
        return (
            <div className="relative w-full h-full flex items-center justify-center bg-zinc-950/50 rounded-2xl">
                <div className="relative w-full max-w-[340px] aspect-[9/16] bg-gradient-to-br from-zinc-900 to-zinc-800 rounded-2xl overflow-hidden shadow-2xl flex flex-col items-center justify-center p-6">
                    <a href={video.video_url} target="_blank" rel="noopener noreferrer" className="text-center">
                        <Play className="w-16 h-16 text-white/40 mx-auto mb-4" />
                        <p className="text-white/60 text-sm">외부에서 재생</p>
                    </a>
                </div>
            </div>
        );
    }

    if (video.platform === 'tiktok') {
        // Use TikTok player with loop=1 to auto-replay (Virlo-style UX)
        return (
            <div className="relative w-full h-full flex items-center justify-center bg-zinc-950/50 rounded-2xl">
                <div className="relative w-full max-w-[340px] aspect-[9/16] bg-black rounded-2xl overflow-hidden shadow-2xl">
                    <iframe
                        src={`https://www.tiktok.com/player/v1/${videoId}?loop=1&autoplay=0&music_info=0&description=0`}
                        className="absolute inset-0 w-full h-full border-0"
                        allow="fullscreen"
                        allowFullScreen
                    />
                </div>
            </div>
        );
    }

    // YouTube with loop enabled
    return (
        <div className="relative w-full h-full flex items-center justify-center bg-zinc-950/50 rounded-2xl">
            <div className="relative w-full max-w-[340px] aspect-[9/16] bg-black rounded-2xl overflow-hidden shadow-2xl">
                <iframe
                    src={`https://www.youtube.com/embed/${videoId}?autoplay=0&rel=0&loop=1&playlist=${videoId}`}
                    className="absolute inset-0 w-full h-full border-0"
                    allow="fullscreen"
                    allowFullScreen
                />
            </div>
        </div>
    );
}

// ==================
// Viral Guide Panel (Compact - Korean)
// ==================

function ViralGuidePanel({ analysis }: { analysis?: VideoAnalysis }) {
    if (!analysis) return null;

    return (
        <div className="space-y-3">
            {/* Hook - 핵심 훅 요약 */}
            <div className="p-4 bg-gradient-to-br from-cyan-500/10 to-blue-500/10 border border-cyan-500/30 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                        <Target className="w-4 h-4 text-cyan-400" />
                        <span className="text-sm font-bold text-white">🎣 훅 패턴</span>
                    </div>
                    {typeof analysis.hook_score === 'number' && (
                        <span className="px-2 py-0.5 bg-cyan-500/20 rounded text-xs text-cyan-300 font-mono">
                            {analysis.hook_score < 1
                                ? `${(analysis.hook_score * 10).toFixed(1)}/10`
                                : `${analysis.hook_score}/10`}
                        </span>
                    )}
                </div>
                <div className="text-lg font-bold text-white mb-1">
                    {analysis.hook_pattern === 'pattern_break' ? '패턴 브레이크' :
                        analysis.hook_pattern === 'visual_reaction' ? '시각적 리액션' :
                            analysis.hook_pattern === 'unboxing' ? '언박싱' :
                                analysis.hook_pattern || '-'}
                </div>
                {typeof analysis.hook_duration_sec === 'number' && (
                    <div className="flex items-center gap-1 text-xs text-white/60">
                        <Clock className="w-3 h-3" />
                        처음 {analysis.hook_duration_sec}초 안에 시청자 잡기
                    </div>
                )}
            </div>

            {/* Visual + Audio 통합 */}
            <div className="grid grid-cols-2 gap-2">
                {/* Visual */}
                {analysis.visual_patterns && analysis.visual_patterns.length > 0 && (
                    <div className="p-3 bg-white/5 border border-white/10 rounded-xl">
                        <div className="flex items-center gap-1.5 mb-2">
                            <Camera className="w-3.5 h-3.5 text-pink-400" />
                            <span className="text-xs font-bold text-white">📷 영상 기법</span>
                        </div>
                        <div className="flex flex-wrap gap-1">
                            {analysis.visual_patterns.slice(0, 4).map((p, i) => (
                                <span key={i} className="px-1.5 py-0.5 bg-pink-500/10 border border-pink-500/30 rounded text-[10px] text-pink-300">
                                    {p}
                                </span>
                            ))}
                        </div>
                    </div>
                )}

                {/* Audio */}
                {analysis.audio_pattern && (
                    <div className="p-3 bg-white/5 border border-white/10 rounded-xl">
                        <div className="flex items-center gap-1.5 mb-2">
                            <Mic className="w-3.5 h-3.5 text-emerald-400" />
                            <span className="text-xs font-bold text-white">🎵 오디오</span>
                        </div>
                        <span className="px-1.5 py-0.5 bg-emerald-500/10 border border-emerald-500/30 rounded text-[10px] text-emerald-300">
                            {analysis.audio_pattern}
                        </span>
                    </div>
                )}
            </div>

            {/* 주의사항 */}
            {analysis.do_not && analysis.do_not.length > 0 && (
                <div className="p-3 bg-red-500/5 border border-red-500/20 rounded-xl">
                    <div className="text-xs text-red-300 font-bold mb-1">⛔ 주의</div>
                    {analysis.do_not.map((item, i) => (
                        <div key={i} className="text-xs text-red-300/70">• {item}</div>
                    ))}
                </div>
            )}

            {/* Invariant - 절대 유지 */}
            {analysis.invariant && analysis.invariant.length > 0 && (
                <div className="p-3 bg-gradient-to-br from-orange-500/10 to-red-500/10 border border-orange-500/30 rounded-xl">
                    <div className="flex items-center gap-2 mb-2">
                        <Lock className="w-3.5 h-3.5 text-orange-400" />
                        <span className="text-xs font-bold text-orange-300">🔒 핵심 유지 요소</span>
                    </div>
                    <div className="space-y-1">
                        {analysis.invariant.slice(0, 3).map((item, i) => (
                            <div key={i} className="text-[11px] text-white/80 flex items-start gap-1.5">
                                <span className="text-orange-400">•</span>
                                <span>{item}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Variable - 창의성 발휘 */}
            {analysis.variable && analysis.variable.length > 0 && (
                <div className="p-3 bg-gradient-to-br from-emerald-500/10 to-teal-500/10 border border-emerald-500/30 rounded-xl">
                    <div className="flex items-center gap-2 mb-2">
                        <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                        <span className="text-xs font-bold text-emerald-300">✨ 변주 가능 요소</span>
                    </div>
                    <div className="space-y-1">
                        {analysis.variable.slice(0, 3).map((item, i) => (
                            <div key={i} className="text-[11px] text-white/80 flex items-start gap-1.5">
                                <span className="text-emerald-400">✓</span>
                                <span>{item}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

// ==================
// Campaign Panel
// ==================

function CampaignPanel({ video }: { video: VideoDetail }) {
    const [selectedType, setSelectedType] = useState<'product' | 'visit' | 'delivery'>(video.campaignType || 'product');

    return (
        <div className="p-4 bg-gradient-to-br from-violet-500/10 to-pink-500/10 border border-violet-500/30 rounded-xl">
            <div className="flex items-center gap-2 mb-4">
                <Users className="w-4 h-4 text-violet-400" />
                <span className="text-sm font-bold text-white">숏폼 체험단</span>
                <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-300 text-[10px] font-bold rounded-full">모집중</span>
            </div>

            <div className="grid grid-cols-3 gap-2 mb-4">
                {[
                    { type: 'product', icon: Truck, label: '제품 배송' },
                    { type: 'visit', icon: MapPin, label: '방문 체험' },
                    { type: 'delivery', icon: Calendar, label: '촬영 예약' },
                ].map(({ type, icon: Icon, label }) => (
                    <button
                        key={type}
                        onClick={() => setSelectedType(type as any)}
                        className={`p-3 rounded-lg border text-center transition-all ${selectedType === type
                            ? 'bg-violet-500/20 border-violet-500/50 text-violet-300'
                            : 'bg-white/5 border-white/10 text-white/60 hover:text-white'
                            }`}
                    >
                        <Icon className="w-5 h-5 mx-auto mb-1" />
                        <span className="text-[10px] font-bold">{label}</span>
                    </button>
                ))}
            </div>

            <div className="space-y-2 mb-4 text-xs">
                <div className="flex justify-between"><span className="text-white/60">참여</span><span className="text-white font-bold">12/20명</span></div>
                <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
                    <div className="h-full w-3/5 bg-gradient-to-r from-violet-500 to-pink-500 rounded-full" />
                </div>
                <div className="flex justify-between"><span className="text-white/60">예상 노출</span><span className="text-emerald-400 font-bold">500K~2M</span></div>
            </div>

            <button className="w-full py-3 bg-gradient-to-r from-violet-500 to-pink-500 text-white text-sm font-bold rounded-xl hover:brightness-110 transition-all flex items-center justify-center gap-2">
                <Sparkles className="w-4 h-4" />
                캠페인 참여 신청
            </button>
        </div>
    );
}

// ==================
// Main Component
// ==================

export default function VideoDetailPage() {
    const params = useParams();
    const router = useRouter();
    const videoId = params?.id as string;

    const [video, setVideo] = useState<VideoDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [copied, setCopied] = useState(false);
    const copiedTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const isMountedRef = useRef(true);
    const [showCoaching, setShowCoaching] = useState(false);
    const [coachingMode, setCoachingMode] = useState<'homage' | 'variation' | 'campaign'>('variation');
    const [showModeSelector, setShowModeSelector] = useState(false);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
            if (copiedTimeoutRef.current) {
                clearTimeout(copiedTimeoutRef.current);
                copiedTimeoutRef.current = null;
            }
        };
    }, []);

    useEffect(() => {
        async function loadVideo() {
            // First check if it's a demo video
            if (DEMO_VIDEOS[videoId]) {
                if (isMountedRef.current) {
                    setVideo(DEMO_VIDEOS[videoId]);
                    setLoading(false);
                }
                return;
            }

            // Try to fetch from API
            try {
                const res = await fetch(`/api/v1/outliers/items/${videoId}`);
                if (res.ok) {
                    const data = await res.json();
                    if (!isMountedRef.current) return;
                    setVideo({
                        id: data.id,
                        video_url: data.video_url,
                        platform: data.platform || 'youtube',
                        title: data.title || 'Untitled',
                        thumbnail_url: data.thumbnail_url,
                        category: data.category || 'general',
                        view_count: data.view_count || 0,
                        like_count: data.like_count,
                        engagement_rate: data.engagement_rate,
                        outlier_tier: data.outlier_tier,
                        creator_avg_views: data.creator_avg_views,
                        hasCampaign: false,
                        // VDG 분석 데이터 (FR-008: Hook, Shotlist, Audio, Timing)
                        analysis: data.analysis ? {
                            hook_pattern: data.analysis.hook_pattern,
                            hook_score: data.analysis.hook_score,
                            hook_duration_sec: data.analysis.hook_duration_sec,
                            visual_patterns: data.analysis.visual_patterns,
                            audio_pattern: data.analysis.audio_pattern,
                            shotlist: data.analysis.shotlist,
                            timing: data.analysis.timing,
                            do_not: data.analysis.do_not,
                            invariant: data.analysis.invariant,
                            variable: data.analysis.variable,
                            // Handle best_comment as object or string
                            best_comment: typeof data.analysis.best_comment === 'object'
                                ? data.analysis.best_comment?.text
                                : data.analysis.best_comment,
                        } : undefined,
                        // Raw VDG for Storyboard UI
                        rawVdg: data.raw_vdg || null,
                    });
                    setLoading(false);
                    return;
                }
            } catch (e) {
                console.error('Failed to fetch video:', e);
            }

            // Fallback to demo if API fails
            if (isMountedRef.current) {
                setVideo(DEMO_VIDEOS['demo-tiktok-1']);
                setLoading(false);
            }
        }

        loadVideo();
    }, [videoId]);

    const handleCopyLink = async () => {
        if (!video) return;

        try {
            if (!navigator.clipboard?.writeText) {
                alert('클립보드를 사용할 수 없습니다. 주소를 직접 복사해주세요.');
                return;
            }
            await navigator.clipboard.writeText(video.video_url);
            setCopied(true);
            if (copiedTimeoutRef.current) {
                clearTimeout(copiedTimeoutRef.current);
            }
            copiedTimeoutRef.current = setTimeout(() => setCopied(false), 2000);
        } catch (e) {
            console.error('Failed to copy link:', e);
            alert('링크 복사에 실패했습니다.');
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
                <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin" />
            </div>
        );
    }

    if (!video) {
        return (
            <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
                <div className="text-center">
                    <div className="text-4xl mb-4">🎬</div>
                    <p className="text-white/60">영상을 찾을 수 없습니다</p>
                    <Link href="/" className="mt-4 inline-block text-violet-400 hover:text-violet-300">← 홈으로</Link>
                </div>
            </div>
        );
    }

    const tierConfig = video.outlier_tier ? {
        S: { icon: Award, color: 'text-amber-400', bg: 'bg-amber-500/20' },
        A: { icon: Star, color: 'text-purple-400', bg: 'bg-purple-500/20' },
        B: { icon: Star, color: 'text-blue-400', bg: 'bg-blue-500/20' },
        C: { icon: Star, color: 'text-zinc-400', bg: 'bg-zinc-500/20' },
    }[video.outlier_tier] : null;

    const multiplier = video.creator_avg_views ? Math.round(video.view_count / video.creator_avg_views) : 0;

    return (
        <div className="min-h-screen bg-[#050505]">
            <AppHeader />

            {/* Header */}
            <div className="sticky top-0 z-40 bg-zinc-950/80 backdrop-blur-lg border-b border-white/10">
                <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
                    <button onClick={() => router.back()} className="flex items-center gap-2 text-white/60 hover:text-white">
                        <ArrowLeft className="w-5 h-5" />
                        <span className="text-sm">뒤로</span>
                    </button>

                    <div className="flex items-center gap-2">
                        <button onClick={handleCopyLink} className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-white/60 hover:text-white">
                            {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                        </button>
                        <button className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-white/60 hover:text-white">
                            <Bookmark className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-7xl mx-auto px-4 py-6">
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                    {/* Left: Video */}
                    <div className="lg:col-span-5">
                        <div className="sticky top-20">
                            <VideoEmbed video={video} />

                            <div className="mt-4 space-y-3">
                                <h1 className="text-xl font-bold text-white">{video.title}</h1>

                                <div className="flex items-center gap-3">
                                    {video.creator && (
                                        <span className="text-sm text-white/60">@{video.creator}</span>
                                    )}
                                    {tierConfig && (
                                        <div className={`flex items-center gap-1 px-2 py-1 rounded-full ${tierConfig.bg} ${tierConfig.color} text-xs font-bold`}>
                                            <tierConfig.icon className="w-3 h-3" />
                                            {video.outlier_tier}-Tier
                                            {multiplier > 0 && <span className="font-mono ml-1">{multiplier}x</span>}
                                        </div>
                                    )}
                                </div>

                                <div className="flex items-center gap-4 text-sm text-white/50">
                                    <span className="flex items-center gap-1"><Eye className="w-4 h-4" />{(video.view_count / 1000000).toFixed(1)}M</span>
                                    {typeof video.like_count === 'number' && (
                                        <span className="flex items-center gap-1">
                                            <Heart className="w-4 h-4" />
                                            {(video.like_count / 1000000).toFixed(1)}M
                                        </span>
                                    )}
                                    {typeof video.engagement_rate === 'number' && (
                                        <span className="flex items-center gap-1 text-emerald-400">
                                            <TrendingUp className="w-4 h-4" />
                                            {(video.engagement_rate * 100).toFixed(1)}%
                                        </span>
                                    )}
                                </div>

                                {video.tags && (
                                    <div className="flex flex-wrap gap-2">
                                        {video.tags.map((tag, i) => (
                                            <span key={i} className="px-2 py-1 bg-white/5 border border-white/10 rounded text-xs text-white/50">
                                                #{tag}
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Right: Guide + Campaign */}
                    <div className="lg:col-span-7 space-y-6">
                        <div>
                            <div className="flex items-center gap-2 mb-4">
                                <Sparkles className="w-5 h-5 text-cyan-400" />
                                <h2 className="text-lg font-bold text-white">바이럴 가이드</h2>
                                <ChevronRight className="w-4 h-4 text-white/40" />
                                <span className="text-sm text-white/50">{video.category}</span>
                            </div>
                            <ViralGuidePanel analysis={video.analysis} />
                        </div>

                        {/* Storyboard Panel - 씬별 스토리보드 UI */}
                        {video.rawVdg && (
                            <StoryboardPanel rawVdg={video.rawVdg} defaultExpanded={true} />
                        )}

                        {video.hasCampaign ? (
                            <div>
                                <div className="flex items-center gap-2 mb-4">
                                    <Users className="w-5 h-5 text-violet-400" />
                                    <h2 className="text-lg font-bold text-white">체험단 캠페인</h2>
                                </div>
                                <CampaignPanel video={video} />
                            </div>
                        ) : (
                            <div className="p-4 bg-gradient-to-br from-violet-500/5 to-pink-500/5 border border-violet-500/20 rounded-xl">
                                <div className="flex items-center gap-2 mb-3">
                                    <Users className="w-4 h-4 text-violet-400" />
                                    <span className="text-sm font-bold text-white">체험단 캠페인</span>
                                </div>
                                <p className="text-xs text-white/50 mb-4">이 영상으로 체험단을 모집하고 싶으신가요?</p>
                                <button
                                    onClick={() => router.push(`/o2o/campaigns/create?video_id=${video.id}`)}
                                    className="w-full py-3 bg-gradient-to-r from-violet-500 to-pink-500 text-white text-sm font-bold rounded-xl hover:brightness-110 transition-all flex items-center justify-center gap-2"
                                >
                                    <Rocket className="w-4 h-4" />
                                    체험단 열기
                                </button>
                                <p className="text-[10px] text-white/30 mt-2 text-center">크리에이터들이 이 영상을 오마주합니다</p>
                            </div>
                        )}

                        {video.analysis?.best_comment && (
                            <div className="p-4 bg-white/5 border border-white/10 rounded-xl">
                                <div className="text-xs text-white/40 mb-2">💬 Top Comment</div>
                                <p className="text-white/80">"{video.analysis.best_comment}"</p>
                            </div>
                        )}

                        {/* 🎙️ AI Coaching CTA - NEW */}
                        <div className="p-4 bg-gradient-to-br from-cyan-500/10 to-emerald-500/10 border border-cyan-500/30 rounded-xl">
                            <div className="flex items-center gap-2 mb-3">
                                <Video className="w-4 h-4 text-cyan-400" />
                                <span className="text-sm font-bold text-white">AI 코칭 촬영</span>
                                <span className="px-2 py-0.5 bg-cyan-500/20 text-cyan-300 text-[10px] font-bold rounded-full">NEW</span>
                            </div>
                            <p className="text-xs text-white/50 mb-4">AI가 실시간으로 촬영을 도와드립니다</p>

                            <button
                                onClick={() => setShowModeSelector(true)}
                                className="w-full py-3 bg-gradient-to-r from-cyan-500 to-emerald-500 text-white text-sm font-bold rounded-xl hover:brightness-110 transition-all flex items-center justify-center gap-2"
                            >
                                <Mic className="w-4 h-4" />
                                🎬 촬영 시작하기
                            </button>
                        </div>

                        {/* View Original Button - Virlo-style at bottom of sidebar */}
                        <a
                            href={video.video_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="w-full flex items-center justify-center gap-2 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-white/70 hover:text-white transition-all"
                        >
                            <ExternalLink className="w-4 h-4" />
                            <span className="text-sm font-medium">원본 보기</span>
                        </a>
                    </div>
                </div>
            </div>

            {/* Mode Selector Bottom Sheet */}
            {showModeSelector && (
                <div className="fixed inset-0 z-50 bg-black/80 flex items-end justify-center">
                    <div className="w-full max-w-lg bg-zinc-900 rounded-t-2xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-bold text-white">촬영 모드 선택</h3>
                            <button onClick={() => setShowModeSelector(false)} className="text-white/60">✕</button>
                        </div>

                        <div className="space-y-3 mb-6">
                            {[
                                { mode: 'homage' as const, icon: '🎯', label: '오마쥬', desc: '원본을 최대한 따라하기' },
                                { mode: 'variation' as const, icon: '✨', label: '변주', desc: '핵심은 유지, 나만의 스타일로' },
                                { mode: 'campaign' as const, icon: '📦', label: '체험단', desc: '제품/장소 홍보 촬영' },
                            ].map(({ mode, icon, label, desc }) => (
                                <button
                                    key={mode}
                                    onClick={() => {
                                        setCoachingMode(mode);
                                        setShowModeSelector(false);
                                        setShowCoaching(true);
                                    }}
                                    className={`w-full p-4 rounded-xl border text-left transition-all ${coachingMode === mode
                                        ? 'bg-cyan-500/20 border-cyan-500/50'
                                        : 'bg-white/5 border-white/10 hover:border-white/30'
                                        }`}
                                >
                                    <div className="flex items-center gap-3">
                                        <span className="text-2xl">{icon}</span>
                                        <div>
                                            <div className="font-bold text-white">{label}</div>
                                            <div className="text-xs text-white/50">{desc}</div>
                                        </div>
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Coaching Session Modal */}
            <CoachingSession
                isOpen={showCoaching}
                onClose={() => setShowCoaching(false)}
                videoId={video.id}
                mode={coachingMode}
                onComplete={(sessionId) => {
                    console.log('Coaching completed:', sessionId);
                    setShowCoaching(false);
                }}
            />
        </div>
    );
}
