// frontend/src/app/o2o/campaigns/create/page.tsx
"use client";

/**
 * 체험단 캠페인 생성 페이지
 * 
 * - video_id 쿼리 파라미터로 연결된 영상 정보 표시
 * - 캠페인 유형 선택 (제품 배송 / 방문 체험 / 촬영 예약)
 * - POST /api/v1/o2o/admin/campaigns로 생성
 */

import { useState, useEffect, Suspense, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { AppHeader } from "@/components/AppHeader";
import {
    ArrowLeft, Rocket, Truck, MapPin, Calendar, Sparkles, Check, AlertCircle
} from "lucide-react";

const CAMPAIGN_TYPES = [
    { type: "shipment", icon: Truck, label: "제품 배송", desc: "크리에이터에게 제품을 배송하고 리뷰 영상을 받습니다" },
    { type: "visit", icon: MapPin, label: "방문 체험", desc: "매장 방문 후 체험 콘텐츠를 제작합니다" },
    { type: "instant", icon: Calendar, label: "촬영 예약", desc: "특정 일정에 촬영을 진행합니다" },
];

function CreateCampaignContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const videoId = searchParams.get("video_id");

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);
    const redirectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const isMountedRef = useRef(true);

    // Form state
    const [campaignType, setCampaignType] = useState<string>("shipment");
    const [title, setTitle] = useState("");
    const [brand, setBrand] = useState("");
    const [category, setCategory] = useState("");
    const [description, setDescription] = useState("");
    const [rewardPoints, setRewardPoints] = useState(500);
    const [rewardProduct, setRewardProduct] = useState("");
    const [maxParticipants, setMaxParticipants] = useState(20);
    const [activeDays, setActiveDays] = useState(30);

    // Video info (if connected)
    const [videoTitle, setVideoTitle] = useState<string | null>(null);

    useEffect(() => {
        if (videoId) {
            // Try to fetch video info
            fetch(`/api/v1/outliers/items/${videoId}`)
                .then(res => res.ok ? res.json() : null)
                .then(data => {
                    if (data) {
                        if (!isMountedRef.current) return;
                        setVideoTitle(data.title);
                        setTitle(`${data.title || "영상"} 체험단`);
                        setCategory(data.category || "");
                    }
                })
                .catch(() => { });
        }
    }, [videoId]);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
            if (redirectTimeoutRef.current) {
                clearTimeout(redirectTimeoutRef.current);
                redirectTimeoutRef.current = null;
            }
        };
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (isMountedRef.current) {
            setLoading(true);
            setError(null);
        }

        try {
            const res = await fetch("/api/v1/o2o/admin/campaigns", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    campaign_type: campaignType,
                    campaign_title: title,
                    brand: brand || null,
                    category: category || null,
                    description: description || null,
                    reward_points: rewardPoints,
                    reward_product: rewardProduct || null,
                    fulfillment_steps: campaignType === "shipment"
                        ? ["배송 신청", "제품 수령", "영상 촬영", "업로드"]
                        : campaignType === "visit"
                            ? ["위치 인증", "체험", "영상 촬영", "업로드"]
                            : ["일정 확인", "촬영 참여", "업로드"],
                    active_days: activeDays,
                    max_participants: maxParticipants,
                }),
            });

            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data.detail || "캠페인 생성에 실패했습니다");
            }

            if (!isMountedRef.current) return;
            setSuccess(true);
            if (redirectTimeoutRef.current) {
                clearTimeout(redirectTimeoutRef.current);
            }
            redirectTimeoutRef.current = setTimeout(() => {
                router.push("/o2o");
            }, 2000);
        } catch (err) {
            if (!isMountedRef.current) return;
            setError(err instanceof Error ? err.message : "오류가 발생했습니다");
        } finally {
            if (isMountedRef.current) {
                setLoading(false);
            }
        }
    };

    if (success) {
        return (
            <div className="min-h-screen bg-[#050505] flex items-center justify-center">
                <div className="text-center space-y-4">
                    <div className="w-16 h-16 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto">
                        <Check className="w-8 h-8 text-emerald-400" />
                    </div>
                    <h1 className="text-2xl font-bold text-white">캠페인이 생성되었습니다!</h1>
                    <p className="text-white/60">곧 O2O 페이지로 이동합니다...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#050505]">
            <AppHeader />

            {/* Header */}
            <div className="sticky top-0 z-40 bg-zinc-950/80 backdrop-blur-lg border-b border-white/10">
                <div className="max-w-3xl mx-auto px-4 py-3 flex items-center gap-4">
                    <button onClick={() => router.back()} className="flex items-center gap-2 text-white/60 hover:text-white">
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <h1 className="text-lg font-bold text-white">체험단 캠페인 열기</h1>
                </div>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="max-w-3xl mx-auto px-4 py-8 space-y-8">
                {/* Connected Video */}
                {videoTitle && (
                    <div className="p-4 bg-violet-500/10 border border-violet-500/20 rounded-xl">
                        <div className="flex items-center gap-2 text-violet-300 text-sm mb-1">
                            <Sparkles className="w-4 h-4" />
                            연결된 영상
                        </div>
                        <p className="text-white font-medium">{videoTitle}</p>
                    </div>
                )}

                {/* Campaign Type Selection */}
                <div className="space-y-3">
                    <label className="text-sm font-bold text-white/80">캠페인 유형</label>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        {CAMPAIGN_TYPES.map(({ type, icon: Icon, label, desc }) => (
                            <button
                                key={type}
                                type="button"
                                onClick={() => setCampaignType(type)}
                                className={`p-4 rounded-xl border text-left transition-all ${campaignType === type
                                    ? "bg-violet-500/20 border-violet-500/50"
                                    : "bg-white/5 border-white/10 hover:border-white/20"
                                    }`}
                            >
                                <Icon className={`w-6 h-6 mb-2 ${campaignType === type ? "text-violet-400" : "text-white/50"}`} />
                                <div className="font-bold text-white">{label}</div>
                                <div className="text-xs text-white/50 mt-1">{desc}</div>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Basic Info */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <label className="text-sm font-bold text-white/80">캠페인 제목 *</label>
                        <input
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="예: 신제품 스킨케어 리뷰 체험단"
                            required
                            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-white/30 focus:border-violet-500/50 focus:outline-none"
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-bold text-white/80">브랜드명</label>
                        <input
                            type="text"
                            value={brand}
                            onChange={(e) => setBrand(e.target.value)}
                            placeholder="예: 브랜드A"
                            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-white/30 focus:border-violet-500/50 focus:outline-none"
                        />
                    </div>
                </div>

                <div className="space-y-2">
                    <label className="text-sm font-bold text-white/80">캠페인 설명</label>
                    <textarea
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="캠페인 상세 내용을 입력하세요..."
                        rows={3}
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-white/30 focus:border-violet-500/50 focus:outline-none resize-none"
                    />
                </div>

                {/* Rewards */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <label className="text-sm font-bold text-white/80">포인트 보상</label>
                        <input
                            type="number"
                            value={rewardPoints}
                            onChange={(e) => setRewardPoints(parseInt(e.target.value) || 0)}
                            min={0}
                            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:border-violet-500/50 focus:outline-none"
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-bold text-white/80">제품 보상 (선택)</label>
                        <input
                            type="text"
                            value={rewardProduct}
                            onChange={(e) => setRewardProduct(e.target.value)}
                            placeholder="예: 스킨케어 세트 (50,000원 상당)"
                            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-white/30 focus:border-violet-500/50 focus:outline-none"
                        />
                    </div>
                </div>

                {/* Limits */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-2">
                        <label className="text-sm font-bold text-white/80">카테고리</label>
                        <input
                            type="text"
                            value={category}
                            onChange={(e) => setCategory(e.target.value)}
                            placeholder="예: beauty"
                            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-white/30 focus:border-violet-500/50 focus:outline-none"
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-bold text-white/80">최대 참여 인원</label>
                        <input
                            type="number"
                            value={maxParticipants}
                            onChange={(e) => setMaxParticipants(parseInt(e.target.value) || 1)}
                            min={1}
                            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:border-violet-500/50 focus:outline-none"
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-bold text-white/80">모집 기간 (일)</label>
                        <input
                            type="number"
                            value={activeDays}
                            onChange={(e) => setActiveDays(parseInt(e.target.value) || 1)}
                            min={1}
                            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:border-violet-500/50 focus:outline-none"
                        />
                    </div>
                </div>

                {/* Error */}
                {error && (
                    <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3">
                        <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
                        <p className="text-red-300 text-sm">{error}</p>
                    </div>
                )}

                {/* Submit */}
                <button
                    type="submit"
                    disabled={loading || !title}
                    className="w-full py-4 bg-gradient-to-r from-violet-500 to-pink-500 text-white font-bold rounded-xl hover:brightness-110 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                    {loading ? (
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                        <>
                            <Rocket className="w-5 h-5" />
                            캠페인 열기
                        </>
                    )}
                </button>

                <p className="text-center text-xs text-white/40">
                    캠페인을 열면 크리에이터들이 신청할 수 있습니다
                </p>
            </form>
        </div>
    );
}

export default function CreateCampaignPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-[#050505] flex items-center justify-center">
                <div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
            </div>
        }>
            <CreateCampaignContent />
        </Suspense>
    );
}
