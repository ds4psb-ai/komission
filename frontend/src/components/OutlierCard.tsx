"use client";

import Link from "next/link";
import React, { useState, useRef, useEffect } from "react";
import { useSceneOptional } from "@/contexts/SceneContext";
import type { GeminiAnalysis } from "@/contexts/SceneContext";

/**
 * Node data from API
 */
interface RemixNode {
    id: string;
    node_id: string;
    title: string;
    platform: string;
    layer: string;
    view_count: number;
    performance_delta?: string;
    source_video_url?: string;
    gemini_analysis?: GeminiAnalysis;
    created_at: string;
}

interface OutlierCardProps {
    node: RemixNode;
    index?: number;
}

/**
 * OutlierCard Component
 * 
 * Enhanced card showing:
 * - 3D tilt effect on hover
 * - Gemini 3.0 Pro Timeline Analysis Visualization
 * - Viral Hook Markers
 * - Micro-interaction with SceneContext
 */
export function OutlierCard({ node, index = 0 }: OutlierCardProps) {
    const [rotate, setRotate] = useState({ x: 0, y: 0 });
    const [isVisible, setIsVisible] = useState(false);
    const [hoverProgress, setHoverProgress] = useState(0);
    const cardRef = useRef<HTMLDivElement>(null);

    // 🔗 Scene Context for canvas synchronization
    const sceneContext = useSceneOptional();

    // Animation reveal
    useEffect(() => {
        const timer = setTimeout(() => setIsVisible(true), index * 100);
        return () => clearTimeout(timer);
    }, [index]);

    // Extract Gemini analysis data
    const geminiAnalysis = node.gemini_analysis;
    const dropTimestamps = geminiAnalysis?.metadata?.music_drop_timestamps || [];
    const timeline = geminiAnalysis?.timeline || [];
    const viralHooks = geminiAnalysis?.viral_hooks || [];
    const bpm = geminiAnalysis?.metadata?.bpm;
    const mood = geminiAnalysis?.metadata?.mood;
    const category = geminiAnalysis?.commerce_context?.primary_category;
    const keyAction = geminiAnalysis?.meme_dna?.key_action;
    const viralityScore = geminiAnalysis?.virality_score;

    // Determine video duration estimate (default 15s for shorts/reels if no timeline)
    const lastSegmentEnd = timeline.length > 0 ? timeline[timeline.length - 1].end_time : 0;
    const lastDrop = dropTimestamps.length > 0 ? dropTimestamps[dropTimestamps.length - 1] : 0;
    const videoDuration = Math.max(15, lastSegmentEnd, lastDrop + 2);

    // Current hovered segment based on progress
    const hoveredSegment = timeline.find(
        seg => hoverProgress * videoDuration >= seg.start_time && hoverProgress * videoDuration < seg.end_time
    );

    const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!cardRef.current) return;
        const rect = cardRef.current.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        const rotateX = ((y - centerY) / centerY) * -8;
        const rotateY = ((x - centerX) / centerX) * 8;
        setRotate({ x: rotateX, y: rotateY });

        // Calculate hover progress (0-1) for timeline scrubbing
        const progress = Math.max(0, Math.min(1, x / rect.width));
        setHoverProgress(progress);

        // Sync with Scene Context
        if (sceneContext) {
            sceneContext.setTimestamp(progress * videoDuration);
            // Optionally set selected node on hover if desired, but click is better for selection
            // sceneContext.selectNode(node.node_id, geminiAnalysis); 
        }
    };

    const handleMouseLeave = () => {
        setRotate({ x: 0, y: 0 });
        setHoverProgress(0);
    };

    const getGradient = (layer: string) => {
        switch (layer) {
            case 'master': return 'from-violet-900 via-purple-900 to-indigo-950';
            case 'fork': return 'from-emerald-900 via-green-900 to-teal-950';
            case 'fork_of_fork': return 'from-rose-900 via-pink-900 to-red-950';
            default: return 'from-zinc-800 to-zinc-950';
        }
    };

    const getBadgeStyle = (layer: string) => {
        switch (layer) {
            case 'master': return 'bg-violet-500/10 border-violet-500/30 text-violet-300';
            case 'fork': return 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300';
            case 'fork_of_fork': return 'bg-rose-500/10 border-rose-500/30 text-rose-300';
            default: return 'bg-white/5 border-white/10 text-white/40';
        }
    };

    return (
        <div
            ref={cardRef}
            className={`transition-all duration-700 ease-out transform ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12'
                }`}
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
        >
            <Link href={`/remix/${node.node_id}`} className="group block relative perspective-1000 h-full">
                <div
                    className={`relative aspect-[9/16] rounded-3xl overflow-hidden border border-white/10 
                        group-hover:border-white/20 transition-all duration-300 
                        bg-gradient-to-bl ${getGradient(node.layer)} 
                        shadow-[0_10px_40px_-10px_rgba(0,0,0,0.5)] 
                        group-hover:shadow-[0_20px_50px_-10px_rgba(139,92,246,0.3)]`}
                    style={{
                        transform: `rotateX(${rotate.x}deg) rotateY(${rotate.y}deg)`,
                        transformStyle: 'preserve-3d'
                    }}
                >
                    {/* Ambient Glow */}
                    <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
                        <div className="absolute top-1/4 left-1/4 w-1/2 h-1/2 bg-white/10 blur-3xl rounded-full" />
                    </div>

                    {/* Timeline Analysis Visualization (Bottom Overlay) */}
                    {timeline.length > 0 && (
                        <div className="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-black/90 to-transparent z-20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end pb-4 px-4">
                            {/* Segment Description Tooltip */}
                            <div className="mb-2 h-4">
                                {hoveredSegment && (
                                    <div className="text-[10px] text-white/90 font-medium truncate flex items-center gap-2 animate-fade-in">
                                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                                        {hoveredSegment.description}
                                        <span className="text-cyan-400 font-bold">({hoveredSegment.viral_score}/10)</span>
                                    </div>
                                )}
                            </div>

                            {/* Timeline Bar */}
                            <div className="w-full h-1.5 bg-white/10 rounded-full flex overflow-hidden relative">
                                {timeline.map((seg, i) => {
                                    const width = ((seg.end_time - seg.start_time) / videoDuration) * 100;
                                    // Heatmap coloring based on viral score
                                    const opacity = 0.3 + (seg.viral_score / 20);
                                    const isHovered = hoveredSegment === seg;

                                    return (
                                        <div
                                            key={i}
                                            className={`h-full border-r border-black/20 transition-all duration-200 ${isHovered ? 'bg-cyan-400 brightness-150' : 'bg-purple-500'
                                                }`}
                                            style={{
                                                width: `${width}%`,
                                                opacity: isHovered ? 1 : opacity
                                            }}
                                        />
                                    );
                                })}
                                {/* Scrubber position indicator */}
                                <div
                                    className="absolute top-0 bottom-0 w-0.5 bg-white shadow-[0_0_8px_rgba(255,255,255,0.8)] z-10 pointer-events-none"
                                    style={{ left: `${hoverProgress * 100}%` }}
                                />
                            </div>
                        </div>
                    )}

                    {/* Viral Hooks Markers (Top Overlay) */}
                    {viralHooks.length > 0 && (
                        <div className="absolute top-16 left-4 right-4 z-20 pointer-events-none">
                            {viralHooks.map((hook, i) => (
                                <div
                                    key={i}
                                    className="absolute -translate-x-1/2 flex flex-col items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity delay-100"
                                    style={{ left: `${(hook.timestamp / videoDuration) * 100}%` }}
                                >
                                    <div className="text-xl drop-shadow-lg animate-bounce duration-[2000ms]">🔥</div>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Content Overlay */}
                    <div className="absolute inset-0 flex flex-col justify-between p-6 z-10 pointer-events-none">
                        {/* Top: Layer Badge + BPM */}
                        <div className="flex justify-between items-start">
                            <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider border ${getBadgeStyle(node.layer)}`}>
                                {node.layer === 'master' ? '🔒 MASTER' : node.layer === 'fork' ? '🌿 FORK' : '✨ MUTATION'}
                            </span>
                            <div className="flex gap-2">
                                {viralityScore && (
                                    <span className="px-2 py-1 bg-pink-500/20 backdrop-blur-sm rounded text-[10px] font-mono text-pink-300 border border-pink-500/30">
                                        ⚡ {viralityScore} VS
                                    </span>
                                )}
                                {bpm && (
                                    <span className="px-2 py-1 bg-black/50 backdrop-blur-sm rounded text-[10px] font-mono text-cyan-300 border border-cyan-500/30">
                                        ♫ {bpm}
                                    </span>
                                )}
                            </div>
                        </div>

                        {/* Center: Play Button + Key Action */}
                        <div className="flex-1 flex flex-col items-center justify-center gap-3">
                            <div className="w-16 h-16 rounded-full bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300 transform group-hover:scale-110">
                                <span className="text-3xl ml-1">▶</span>
                            </div>
                            {keyAction && (
                                <div className="px-3 py-1.5 bg-black/60 backdrop-blur-sm rounded-lg text-xs text-white/70 max-w-[80%] text-center opacity-0 group-hover:opacity-100 transition-opacity">
                                    🎬 {keyAction}
                                </div>
                            )}
                        </div>

                        {/* Bottom: Title + Stats (Hidden on Hover to show Timeline) */}
                        <div className="group-hover:opacity-0 transition-opacity duration-300">
                            <h3 className="text-lg font-black text-white mb-2 line-clamp-2 drop-shadow-lg">
                                {node.title}
                            </h3>
                            <div className="flex items-center gap-4 text-sm">
                                <span className="flex items-center gap-1 text-white/60">
                                    👁️ {(node.view_count / 1000).toFixed(0)}K
                                </span>
                                {node.performance_delta && (
                                    <span className={`font-bold ${node.performance_delta.startsWith('+')
                                        ? 'text-emerald-400'
                                        : 'text-red-400'
                                        }`}>
                                        {node.performance_delta}
                                    </span>
                                )}
                                {category && (
                                    <span className="px-2 py-0.5 bg-white/10 rounded text-[10px] text-white/50">
                                        {category}
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Shine Effect */}
                    <div
                        className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
                        style={{
                            background: `linear-gradient(${115 + rotate.y * 2}deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%)`
                        }}
                    />
                </div>
            </Link>
        </div>
    );
}

export default OutlierCard;
