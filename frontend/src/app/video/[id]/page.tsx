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
import { STPFPanel, STPFBadge, STPFQuickView } from '@/components/stpf/STPFComponents';
import { useSTPFAutoAnalyze } from '@/hooks/useSTPF';
import {
    ArrowLeft, Play, ExternalLink, Bookmark, Copy, Check,
    Target, Clock, Sparkles, Eye, Heart, TrendingUp,
    Camera, Mic, Film, Users, Truck, MapPin, Calendar,
    ChevronRight, Award, Star, Lock, Rocket, Video
} from 'lucide-react';
import { useTranslations } from 'next-intl';

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
    best_comments?: Array<{ rank: number; text: string; signal_type?: string; why_it_matters?: string; anchor_ms?: number }>;
    shotlist?: string[];
    timing?: string[];
    do_not?: string[];
    // Temporal Variation Theory: 불변/가변 가이드
    invariant?: string[];  // 🔒 절대 유지해야 할 요소
    variable?: string[];   // ✨ 창의성 발휘 가능 요소
}

// ViralKick from VDG analysis
interface ViralKick {
    kick_id: string;
    title: string;
    mechanism?: string;
    creator_instruction?: string;
    start_ms: number;
    end_ms: number;
    peak_ms?: number;
    confidence?: number;
    proof_ready?: boolean;
    status?: string;
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
    viral_kicks?: ViralKick[];  // P1-1: normalized viral kicks from DB
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
            <div className="relative w-full h-full flex items-center justify-center rounded-2xl">
                <div className="relative w-full max-w-[340px] aspect-[9/16] bg-black border border-white/10 rounded-2xl overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.5)] flex flex-col items-center justify-center p-6">
                    <div className="w-8 h-8 border-2 border-white/20 border-t-[#c1ff00] rounded-full animate-spin mb-4 shadow-[0_0_15px_rgba(193,255,0,0.3)]" />
                    <p className="text-white/60 text-sm font-mono uppercase tracking-widest">Processing Link...</p>
                </div>
            </div>
        );
    }

    // Fallback if no video ID found
    if (!videoId) {
        return (
            <div className="relative w-full h-full flex items-center justify-center rounded-2xl">
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
        // Use TikTokPlayer component with unmute button (Virlo-style UX)
        const { TikTokPlayer } = require('@/components/outlier/TikTokPlayer');
        return (
            <div className="relative w-full h-full flex items-center justify-center rounded-2xl">
                <div className="relative w-full max-w-[340px] aspect-[9/16] bg-black rounded-2xl overflow-hidden shadow-2xl">
                    <TikTokPlayer
                        videoUrl={video.video_url}
                        videoId={videoId}
                        size="full"
                        autoplay={false}
                        loop={true}
                        showControls={true}
                        showUnmute={true}
                        className="w-full h-full"
                    />
                </div>
            </div>
        );
    }

    // YouTube with loop enabled
    return (
        <div className="relative w-full h-full flex items-center justify-center rounded-2xl">
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
        <div className="space-y-4">
            {/* Hook - 핵심 훅 요약 */}
            <div className="p-5 bg-black/40 backdrop-blur-md border border-[#c1ff00]/20 rounded-3xl relative overflow-hidden">
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                        <Target className="w-4 h-4 text-[#c1ff00]" />
                        <span className="text-xs font-black tracking-wider text-[#c1ff00] uppercase">Hook Pattern</span>
                    </div>
                    {typeof analysis.hook_score === 'number' && (
                        <span className={`px-2 py-0.5 rounded text-[10px] font-black font-mono ${analysis.hook_score >= 8 ? 'bg-[#c1ff00] text-black' : 'bg-white/10 text-white'
                            }`}>
                            {analysis.hook_score}/10
                        </span>
                    )}
                </div>
                <div className="text-2xl font-black text-white mb-2 leading-none">
                    {analysis.hook_pattern === 'pattern_break' ? 'PATTERN BREAK' :
                        analysis.hook_pattern === 'visual_reaction' ? 'VISUAL REACTION' :
                            analysis.hook_pattern === 'unboxing' ? 'UNBOXING' :
                                analysis.hook_pattern || '-'}
                </div>
                {typeof analysis.hook_duration_sec === 'number' && (
                    <div className="flex items-center gap-1.5 text-xs text-white/40 font-mono">
                        <Clock className="w-3 h-3 text-[#c1ff00]" />
                        Capture within <span className="text-[#c1ff00] font-bold">{analysis.hook_duration_sec}s</span>
                    </div>
                )}
            </div>

            {/* Timing & Shotlist Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Timing */}
                {analysis.timing && analysis.timing.length > 0 && (
                    <div className="p-4 bg-white/5 border border-white/5 rounded-2xl hover:border-[#c1ff00]/30 transition-colors group">
                        <div className="flex items-center gap-2 mb-3">
                            <Clock className="w-4 h-4 text-[#c1ff00]" />
                            <span className="text-xs font-bold text-white uppercase tracking-wider">Timing</span>
                        </div>
                        <div className="space-y-1.5">
                            {analysis.timing.slice(0, 4).map((t, i) => (
                                <div key={i} className="text-[11px] text-white/60 flex items-center gap-2 font-mono group-hover:text-white transition-colors">
                                    <span className="w-1.5 h-1.5 rounded-full bg-[#c1ff00]" />
                                    {t}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Shotlist */}
                {analysis.shotlist && analysis.shotlist.length > 0 && (
                    <div className="p-4 bg-white/5 border border-white/5 rounded-2xl hover:border-[#c1ff00]/30 transition-colors group">
                        <div className="flex items-center gap-2 mb-3">
                            <Camera className="w-4 h-4 text-[#c1ff00]" />
                            <span className="text-xs font-bold text-white uppercase tracking-wider">Shotlist</span>
                        </div>
                        <div className="space-y-2">
                            {analysis.shotlist.slice(0, 3).map((shot, i) => (
                                <div key={i} className="text-[10px] text-white/60 leading-relaxed font-mono">
                                    <span className="text-[#c1ff00] font-bold mr-1">{i + 1}.</span>
                                    {typeof shot === 'string' ? shot : (shot as any)?.description || ''}
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Invariant & Variable */}
            {analysis.invariant && analysis.invariant.length > 0 && (
                <div className="p-4 bg-black/40 border border-[#c1ff00]/20 rounded-2xl hover:border-[#c1ff00]/50 transition-colors">
                    <div className="flex items-center gap-2 mb-2">
                        <Lock className="w-3.5 h-3.5 text-[#c1ff00]" />
                        <span className="text-xs font-bold text-white uppercase tracking-wider">Invariants (Do Not Change)</span>
                    </div>
                    <div className="space-y-1 pl-1">
                        {analysis.invariant.map((item, i) => (
                            <div key={i} className="text-[11px] text-white/70 flex items-start gap-2 font-mono">
                                <span className="text-[#c1ff00]/50">•</span>
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
        <div className="p-5 bg-black/40 border border-[#c1ff00]/20 rounded-3xl relative overflow-hidden group hover:border-[#c1ff00]/40 transition-colors">
            <div className="absolute top-0 right-0 w-32 h-32 bg-[#c1ff00] blur-[100px] opacity-10 group-hover:opacity-20 transition-opacity" />

            <div className="flex items-center gap-2 mb-6 relative">
                <Users className="w-5 h-5 text-[#c1ff00]" />
                <span className="text-base font-black italic text-white">CAMPAIGN</span>
                <span className="px-2 py-0.5 bg-[#c1ff00] text-black text-[10px] font-black rounded-full animate-pulse">LIVE</span>
            </div>

            <div className="grid grid-cols-3 gap-2 mb-6 relative">
                {[
                    { type: 'product', icon: Truck, label: 'SHIPPING' },
                    { type: 'visit', icon: MapPin, label: 'VISIT' },
                    { type: 'delivery', icon: Calendar, label: 'BOOKING' },
                ].map(({ type, icon: Icon, label }) => (
                    <button
                        key={type}
                        onClick={() => setSelectedType(type as any)}
                        className={`p-3 rounded-2xl border flex flex-col items-center gap-2 transition-all duration-300 ${selectedType === type
                            ? 'bg-[#c1ff00] border-[#c1ff00] text-black shadow-[0_0_15px_rgba(193,255,0,0.4)] scale-105'
                            : 'bg-black/40 border-white/10 text-white/40 hover:text-white hover:border-white/30'
                            }`}
                    >
                        <Icon className="w-5 h-5" />
                        <span className="text-[10px] font-black tracking-wider">{label}</span>
                    </button>
                ))}
            </div>

            <div className="space-y-3 mb-6 text-xs relative">
                <div className="flex justify-between"><span className="text-white/40 font-bold uppercase">Participation</span><span className="text-white font-bold font-mono">12/20</span></div>
                <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
                    <div className="h-full w-3/5 bg-[#c1ff00] rounded-full shadow-[0_0_10px_rgba(193,255,0,0.5)]" />
                </div>
                <div className="flex justify-between"><span className="text-white/40 font-bold uppercase">Est. Reach</span><span className="text-[#c1ff00] font-bold font-mono">500K~2M</span></div>
            </div>

            <button className="w-full py-4 bg-white text-black text-sm font-black uppercase tracking-wider rounded-2xl hover:bg-[#c1ff00] transition-colors flex items-center justify-center gap-2 shadow-lg relative overflow-hidden group/btn">
                <span className="relative z-10 flex items-center gap-2">
                    <Sparkles className="w-4 h-4" />
                    APPLY NOW
                </span>
            </button>
        </div>
    );
}

// ==================
// STPF Decision Panel Component
// ==================

function STPFDecisionPanel({ outlierId }: { outlierId: string }) {
    const [stpfData, setStpfData] = useState<{
        score: number;
        signal: 'GO' | 'CONSIDER' | 'NO-GO';
        grade: { grade: string; label: string; description: string; action: string; kelly_hint: string; color: string } | null;
        kelly: { recommended_effort_percent: number } | null;
        why: string | null;
        how: string[];
    } | null>(null);
    const [loading, setLoading] = useState(true);
    const [expanded, setExpanded] = useState(false);

    useEffect(() => {
        // Simulate STPF analysis based on video metrics
        // In production, this would call api.stpfAnalyzeVdg()
        const fetchSTPF = async () => {
            try {
                // Demo data - replace with actual API call
                const mockScore = Math.floor(600 + Math.random() * 350);
                let signal: 'GO' | 'CONSIDER' | 'NO-GO' = 'CONSIDER';
                let gradeInfo = { grade: 'B', label: 'Dough', description: '검증 필요한 아이디어', action: '프로토타입 테스트', kelly_hint: '10-20% 리소스', color: 'yellow' };

                if (mockScore >= 700) {
                    signal = 'GO';
                    gradeInfo = mockScore >= 850
                        ? { grade: 'S', label: 'Unicorn', description: '즉시 확장 추천', action: '템플릿화, 확장', kelly_hint: '40%+ 리소스', color: 'purple' }
                        : { grade: 'A', label: 'Cash Cow', description: '안정적 성과 기대', action: '리텐션 최적화', kelly_hint: '30% 리소스', color: 'emerald' };
                } else if (mockScore < 400) {
                    signal = 'NO-GO';
                    gradeInfo = { grade: 'C', label: 'Zombie', description: '투자 비추천', action: '다른 패턴 검토', kelly_hint: '5% 이하', color: 'gray' };
                }

                setStpfData({
                    score: mockScore,
                    signal,
                    grade: gradeInfo,
                    kelly: { recommended_effort_percent: mockScore / 30 },
                    why: signal === 'GO' ? '높은 훅 강도와 검증된 패턴 조합' : '패턴 증거 부족 또는 리스크 높음',
                    how: ['훅 타이밍 1초 내 노출', '비주얼 대비 강화', '댓글 유도 CTA'],
                });
            } catch (err) {
                console.error('STPF analysis failed:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchSTPF();
    }, [outlierId]);

    if (loading) {
        return (
            <div className="p-4 bg-gray-800/60 rounded-xl border border-gray-700 animate-pulse">
                <div className="flex items-center gap-3">
                    <div className="w-5 h-5 bg-gray-600 rounded" />
                    <div className="w-24 h-5 bg-gray-600 rounded" />
                    <div className="ml-auto w-20 h-7 bg-gray-600 rounded-full" />
                </div>
            </div>
        );
    }

    if (!stpfData) return null;

    return (
        <STPFPanel
            score={stpfData.score}
            signal={stpfData.signal}
            grade={stpfData.grade || undefined}
            why={stpfData.why || undefined}
            how={stpfData.how}
            kellyPercent={stpfData.kelly?.recommended_effort_percent}
            expanded={expanded}
            onToggle={() => setExpanded(!expanded)}
        />
    );
}

// ==================
// Main Component
// ==================

export default function VideoDetailPage() {
    const params = useParams();
    const router = useRouter();
    const videoId = params?.id as string;
    const t = useTranslations('components.coaching');

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
                        // P1-1: Normalized viral kicks from DB
                        viral_kicks: data.viral_kicks || [],
                    });
                    // DEBUG: Log viral_kicks to verify data flow
                    console.log('📊 Video data loaded:', {
                        id: data.id,
                        viral_kicks_count: data.viral_kicks?.length || 0,
                        viral_kicks: data.viral_kicks,
                        rawVdg: !!data.raw_vdg
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
                    <Link href="/" className="mt-4 inline-block text-[#c1ff00] hover:text-white transition-colors tracking-wide text-sm font-bold">← BACK TO FEED</Link>
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
            <div className="sticky top-0 z-40 bg-black/80 backdrop-blur-xl border-b border-[#c1ff00]/10 shadow-[0_4px_30px_rgba(0,0,0,0.5)]">
                <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
                    <button onClick={() => router.back()} className="flex items-center gap-2 group">
                        <div className="p-2 rounded-full bg-white/5 group-hover:bg-[#c1ff00] transition-colors">
                            <ArrowLeft className="w-4 h-4 text-white group-hover:text-black" />
                        </div>
                        <span className="text-sm font-bold text-white/60 group-hover:text-white transition-colors">BACK</span>
                    </button>

                    <div className="flex items-center gap-2">
                        <button onClick={handleCopyLink} className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 hover:bg-white/10 border border-white/5 hover:border-[#c1ff00]/50 transition-all group">
                            {copied ? <Check className="w-3.5 h-3.5 text-[#c1ff00]" /> : <Copy className="w-3.5 h-3.5 text-white/60 group-hover:text-white" />}
                            <span className="text-xs font-bold text-white/60 group-hover:text-white">{copied ? 'COPIED' : 'SHARE'}</span>
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
                            <div className="relative group">
                                <div className="absolute -inset-1 bg-gradient-to-br from-[#c1ff00] to-purple-600 rounded-3xl opacity-20 group-hover:opacity-40 blur-xl transition-opacity duration-500" />
                                <div className="relative rounded-3xl overflow-hidden border border-white/10 bg-black shadow-2xl w-full max-w-[340px] mx-auto">
                                    <VideoEmbed video={video} />
                                </div>
                            </div>

                            <div className="mt-6 space-y-4 px-2">
                                <h1 className="text-2xl font-black italic tracking-tight text-white leading-tight uppercase">
                                    {video.title}
                                </h1>

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
                        {/* STPF Panel - Hidden for regular users (ops-only feature)
                            TODO: Move to /ops dashboard with proper role check
                        <STPFDecisionPanel outlierId={video.id} />
                        */}

                        <div>
                            <div className="flex items-center gap-2 mb-4 group cursor-default">
                                <Sparkles className="w-5 h-5 text-[#c1ff00] animate-pulse" />
                                <h2 className="text-lg font-black italic text-white uppercase tracking-tight group-hover:text-[#c1ff00] transition-colors">VIRAL GUIDE</h2>
                                <ChevronRight className="w-4 h-4 text-white/20" />
                                <span className="px-2 py-0.5 bg-white/10 rounded-full text-[10px] font-bold text-white/60 uppercase tracking-wider">{video.category}</span>
                            </div>
                            <ViralGuidePanel analysis={video.analysis} />
                        </div>

                        {/* Storyboard Panel - 씬별 스토리보드 UI */}
                        {video.rawVdg && video.rawVdg.scenes && video.rawVdg.scenes.length > 0 ? (
                            <StoryboardPanel rawVdg={video.rawVdg} defaultExpanded={true} />
                        ) : video.viral_kicks && video.viral_kicks.length > 0 ? (
                            /* P1-1: Viral Kicks from normalized DB table */
                            <div className="p-4 bg-[#c1ff00]/5 border border-[#c1ff00]/20 rounded-xl group hover:border-[#c1ff00]/40 transition-colors">
                                <div className="flex items-center gap-2 mb-4">
                                    <Film className="w-4 h-4 text-[#c1ff00]" />
                                    <span className="text-sm font-bold text-white uppercase tracking-wider">VIRAL KICKS</span>
                                    <span className="px-2 py-0.5 bg-[#c1ff00]/20 text-[#c1ff00] text-[10px] font-black rounded-full">
                                        {video.viral_kicks.length} DETECTED
                                    </span>
                                </div>
                                <div className="space-y-3">
                                    {video.viral_kicks.map((kick, i) => (
                                        <div key={kick.kick_id} className="p-3 bg-white/5 border border-white/10 rounded-lg">
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-sm font-bold text-white">{kick.title}</span>
                                                <span className="text-[10px] text-white/50 font-mono">
                                                    {(kick.start_ms / 1000).toFixed(1)}s - {(kick.end_ms / 1000).toFixed(1)}s
                                                </span>
                                            </div>
                                            {kick.mechanism && (
                                                <div className="flex items-center gap-2 mb-2">
                                                    <span className="px-2 py-0.5 bg-cyan-500/20 border border-cyan-500/30 rounded text-[10px] text-cyan-300">
                                                        {kick.mechanism}
                                                    </span>
                                                    {kick.confidence && (
                                                        <span className="text-[10px] text-white/40">
                                                            신뢰도: {(kick.confidence * 100).toFixed(0)}%
                                                        </span>
                                                    )}
                                                </div>
                                            )}
                                            {kick.creator_instruction && (
                                                <p className="text-xs text-white/70 leading-relaxed">
                                                    💡 {kick.creator_instruction}
                                                </p>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ) : (
                            <div className="p-4 bg-white/5 border border-white/10 rounded-xl text-center text-sm text-white/40">
                                스토리보드 데이터가 없습니다
                            </div>
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
                            <div className="p-4 bg-white/5 border border-white/10 rounded-xl hover:border-[#c1ff00]/30 transition-colors group">
                                <div className="flex items-center gap-2 mb-3">
                                    <Users className="w-4 h-4 text-[#c1ff00]" />
                                    <span className="text-sm font-bold text-white uppercase tracking-wider">Remix Campaign</span>
                                </div>
                                <p className="text-xs text-white/50 mb-4">Want to launch a remix campaign with this outlier?</p>
                                <button
                                    onClick={() => router.push(`/o2o/campaigns/create?video_id=${video.id}`)}
                                    className="w-full py-3 bg-[#c1ff00] text-black text-sm font-black uppercase tracking-wider rounded-xl hover:bg-white transition-colors flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(193,255,0,0.3)]"
                                >
                                    <Rocket className="w-4 h-4" />
                                    LAUNCH CAMPAIGN
                                </button>
                                <p className="text-[10px] text-white/30 mt-3 text-center font-mono">
                                    Creators are ready to remix this logic
                                </p>
                            </div>
                        )}

                        {/* Best Comments - Show top 5 */}
                        {video.analysis?.best_comments && video.analysis.best_comments.length > 0 ? (
                            <div className="p-4 bg-white/5 border border-white/10 rounded-xl space-y-3">
                                <div className="text-xs text-white/40 mb-2">💬 베스트 댓글 ({video.analysis.best_comments.length}개)</div>
                                {video.analysis.best_comments.slice(0, 5).map((comment, i) => (
                                    <div key={i} className="flex gap-3 p-2 bg-white/5 rounded-lg">
                                        <span className="text-xs text-white/30 font-mono">#{comment.rank || i + 1}</span>
                                        <div className="flex-1">
                                            <p className="text-white/80 text-sm">"{comment.text}"</p>
                                            {comment.why_it_matters && (
                                                <p className="text-white/50 text-xs mt-1">→ {comment.why_it_matters}</p>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : video.analysis?.best_comment && (
                            <div className="p-4 bg-white/5 border border-white/10 rounded-xl">
                                <div className="text-xs text-white/40 mb-2">💬 Top Comment</div>
                                <p className="text-white/80">"{video.analysis.best_comment}"</p>
                            </div>
                        )}

                        {/* 🎙️ AI Coaching CTA - NEW */}
                        <div className="p-4 bg-black/40 border border-[#c1ff00]/20 rounded-2xl hover:border-[#c1ff00]/40 transition-colors group">
                            <div className="flex items-center gap-2 mb-3">
                                <Video className="w-4 h-4 text-[#c1ff00]" />
                                <span className="text-sm font-black italic text-white uppercase tracking-wider">AI COACHING</span>
                                <span className="px-2 py-0.5 bg-[#c1ff00] text-black text-[10px] font-black uppercase rounded-sm animate-pulse">NEW</span>
                            </div>
                            <p className="text-xs text-white/50 mb-4 font-mono">Real-time AI camera direction & feedback</p>

                            <button
                                onClick={() => setShowModeSelector(true)}
                                className="w-full py-4 bg-[#c1ff00] text-black text-sm font-black uppercase tracking-wider rounded-xl hover:bg-white transition-colors flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(193,255,0,0.3)] hover:shadow-[0_0_20px_rgba(255,255,255,0.5)] group/btn"
                            >
                                <Mic className="w-4 h-4 group-hover/btn:scale-110 transition-transform" />
                                START COACHING
                            </button>
                        </div>

                        {/* View Original Button - Virlo-style at bottom of sidebar */}
                        {/* View Original Button - Virlo-style at bottom of sidebar */}
                        <a
                            href={video.video_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="w-full flex items-center justify-center gap-2 py-3 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-[#c1ff00]/50 rounded-xl text-white/40 hover:text-white transition-all group"
                        >
                            <ExternalLink className="w-4 h-4 group-hover:text-[#c1ff00] transition-colors" />
                            <span className="text-xs font-bold uppercase tracking-widest">View Original</span>
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
                                { mode: 'homage' as const, icon: '🎯', label: t('homage'), desc: t('homageDesc') },
                                { mode: 'variation' as const, icon: '✨', label: t('variation'), desc: t('variationDesc') },
                                { mode: 'campaign' as const, icon: '📦', label: t('campaign'), desc: t('campaignDesc') },
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
