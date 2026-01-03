"use client";

import { useTranslations } from 'next-intl';

/**
 * Manual Outlier Input - Ops Page
 * 
 * Allows curators to manually add TikTok/Shorts URLs to the outlier database
 * Supports: TikTok, YouTube Shorts, Instagram Reels
 */
import { useState, useEffect, useRef, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
    ArrowLeft, Link2, Loader2, CheckCircle, AlertCircle,
    Video, Sparkles, Tag
} from "lucide-react";

const PLATFORMS = [
    { id: 'tiktok', label: 'TikTok', icon: '🎵', urlPattern: 'tiktok.com' },
    { id: 'youtube', label: 'YouTube Shorts', icon: '▶️', urlPattern: 'youtube.com' },
    { id: 'instagram', label: 'Instagram Reels', icon: '📷', urlPattern: 'instagram.com' },
];

const CATEGORIES = [
    { id: 'meme', label: 'Meme/Reaction' },
    { id: 'review', label: 'Review/Experience' },
    { id: 'beauty', label: 'Beauty' },
    { id: 'food', label: 'F&B/Restaurant' },
    { id: 'fitness', label: 'Fitness' },
    { id: 'lifestyle', label: 'Lifestyle' },
    { id: 'unboxing', label: 'Unboxing/Haul' },
    { id: 'other', label: 'Other' },
];

interface SubmitResult {
    success: boolean;
    message: string;
    itemId?: string;
}

export default function ManualOutlierPage() {
    const router = useRouter();
    const [videoUrl, setVideoUrl] = useState("");
    const [category, setCategory] = useState("meme");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [result, setResult] = useState<SubmitResult | null>(null);
    const isMountedRef = useRef(true);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    // Auto-detect platform from URL
    const detectedPlatform = PLATFORMS.find(p => videoUrl.includes(p.urlPattern))?.id || null;

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        if (!videoUrl.trim() || !detectedPlatform) return;

        if (isMountedRef.current) {
            setIsSubmitting(true);
            setResult(null);
        }

        try {
            const response = await fetch("/api/v1/outliers/items/manual", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    video_url: videoUrl.trim(),
                    category,
                    platform: detectedPlatform,
                }),
            });

            const data = await response.json();

            if (response.ok) {
                if (isMountedRef.current) {
                    setResult({
                        success: true,
                        message: `✅ Registered! ${data.title || 'Outlier'} (${data.outlier_tier || 'N/A'}-Tier)`,
                        itemId: data.id,
                    });
                    setVideoUrl("");
                }
            } else {
                if (isMountedRef.current) {
                    setResult({
                        success: false,
                        message: data.detail || "Registration failed",
                    });
                }
            }
        } catch {
            if (isMountedRef.current) {
                setResult({
                    success: false,
                    message: "Network error",
                });
            }
        } finally {
            if (isMountedRef.current) {
                setIsSubmitting(false);
            }
        }
    };

    return (
        <div className="min-h-screen bg-[#050505] text-white">
            {/* Header */}
            <header className="sticky top-0 z-40 px-4 py-4 backdrop-blur-xl bg-black/80 border-b border-white/10">
                <div className="max-w-2xl mx-auto flex items-center gap-4">
                    <Link href="/ops" className="p-2 rounded-lg hover:bg-white/10 transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <div>
                        <h1 className="text-lg font-bold">Manual Outlier Input</h1>
                        <p className="text-xs text-white/50">Register TikTok/Shorts URLs directly</p>
                    </div>
                </div>
            </header>

            {/* Main Form */}
            <main className="max-w-2xl mx-auto px-4 py-8">
                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* URL Input */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-white/80 flex items-center gap-2">
                            <Link2 className="w-4 h-4" />
                            Video URL
                        </label>
                        <div className="relative">
                            <input
                                type="url"
                                value={videoUrl}
                                onChange={(e) => setVideoUrl(e.target.value)}
                                placeholder="https://www.tiktok.com/@user/video/..."
                                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:border-violet-500/50 transition-colors"
                                disabled={isSubmitting}
                            />
                            {detectedPlatform && (
                                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                                    <span className="px-2 py-1 bg-violet-500/20 text-violet-300 text-xs rounded-lg">
                                        {PLATFORMS.find(p => p.id === detectedPlatform)?.icon} {PLATFORMS.find(p => p.id === detectedPlatform)?.label}
                                    </span>
                                </div>
                            )}
                        </div>
                        <p className="text-xs text-white/40">
                            Supports TikTok, YouTube Shorts, Instagram Reels URLs
                        </p>
                    </div>

                    {/* Category Selection */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-white/80 flex items-center gap-2">
                            <Tag className="w-4 h-4" />
                            Category
                        </label>
                        <div className="grid grid-cols-4 gap-2">
                            {CATEGORIES.map((cat) => (
                                <button
                                    key={cat.id}
                                    type="button"
                                    onClick={() => setCategory(cat.id)}
                                    className={`px-3 py-2 rounded-lg text-xs font-medium transition-all ${category === cat.id
                                        ? 'bg-violet-500 text-white'
                                        : 'bg-white/5 text-white/60 hover:bg-white/10 hover:text-white'
                                        }`}
                                >
                                    {cat.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Submit Button */}
                    <button
                        type="submit"
                        disabled={!videoUrl.trim() || !detectedPlatform || isSubmitting}
                        className="w-full py-4 bg-[#c1ff00] hover:bg-white text-black font-black uppercase tracking-wider rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(193,255,0,0.3)] hover:shadow-[0_0_25px_rgba(255,255,255,0.5)]"
                    >
                        {isSubmitting ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                Extracting metadata...
                            </>
                        ) : (
                            <>
                                <Sparkles className="w-5 h-5" />
                                Register Outlier
                            </>
                        )}
                    </button>

                    {/* Result Message */}
                    {result && (
                        <div className={`p-4 rounded-xl flex items-start gap-3 ${result.success
                            ? 'bg-emerald-500/10 border border-emerald-500/30'
                            : 'bg-red-500/10 border border-red-500/30'
                            }`}>
                            {result.success ? (
                                <CheckCircle className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                            ) : (
                                <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                            )}
                            <div>
                                <p className={`text-sm ${result.success ? 'text-emerald-300' : 'text-red-300'}`}>
                                    {result.message}
                                </p>
                                {result.itemId && (
                                    <Link
                                        href={`/video/${result.itemId}`}
                                        className="text-xs text-violet-400 hover:text-violet-300 mt-1 inline-block"
                                    >
                                        → View Details
                                    </Link>
                                )}
                            </div>
                        </div>
                    )}
                </form>

                {/* Quick Tips */}
                <div className="mt-8 p-4 bg-white/5 border border-white/10 rounded-xl">
                    <div className="flex items-center gap-2 mb-3">
                        <Video className="w-4 h-4 text-cyan-400" />
                        <span className="text-sm font-bold text-white">Registration Tips</span>
                    </div>
                    <ul className="space-y-2 text-xs text-white/60">
                        <li>• TikTok: Share from browser → Copy link</li>
                        <li>• YouTube Shorts: Share video → Copy link</li>
                        <li>• Instagram: Share Reels → Copy link</li>
                        <li>• Duplicate URLs are automatically detected</li>
                    </ul>
                </div>
            </main>
        </div>
    );
}
