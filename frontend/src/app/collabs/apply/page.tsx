"use client";

/**
 * 브랜드 협찬 신청 페이지
 * 
 * 캠페인 상세 정보 + 신청 폼
 * - 마감 D-day
 * - 경쟁률 (신청자/정원)
 * - 리워드 상세
 * - 신청 폼
 */
import { useState, useEffect, Suspense, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { AppHeader } from "@/components/AppHeader";
import { api } from "@/lib/api";
import {
    ArrowLeft, Gift, Users, MapPin, Truck, Zap,
    Check, AlertCircle, Calendar, ChevronRight
} from "lucide-react";

interface CampaignDetail {
    id: string;
    campaign_type: string;
    campaign_title: string;
    brand?: string | null;
    category?: string | null;
    reward_points: number;
    reward_product?: string | null;
    description?: string | null;
    fulfillment_steps?: string[] | null;
    place_name?: string | null;
    address?: string | null;
    active_start: string;
    active_end: string;
    max_participants?: number | null;
    current_applicants?: number;
}

function ApplyContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const campaignId = searchParams.get("id");

    const [campaign, setCampaign] = useState<CampaignDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [applying, setApplying] = useState(false);
    const [applied, setApplied] = useState(false);

    // 폼 상태
    const [motivation, setMotivation] = useState("");
    const [socialHandle, setSocialHandle] = useState("");

    const isMountedRef = useRef(true);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    useEffect(() => {
        if (!campaignId) {
            setError("캠페인 ID가 없습니다");
            setLoading(false);
            return;
        }

        async function fetchCampaign() {
            try {
                // 캠페인 목록에서 해당 ID 찾기
                const campaigns = await api.listO2OCampaigns();
                const found = campaigns.find((c: CampaignDetail) => c.id === campaignId);

                if (!found) {
                    throw new Error("캠페인을 찾을 수 없습니다");
                }

                if (isMountedRef.current) {
                    setCampaign(found);
                }
            } catch (err) {
                console.error("캠페인 로드 실패:", err);
                if (isMountedRef.current) {
                    setError(err instanceof Error ? err.message : "로드 실패");
                }
            } finally {
                if (isMountedRef.current) {
                    setLoading(false);
                }
            }
        }

        fetchCampaign();
    }, [campaignId]);

    // D-day 계산
    const getDday = () => {
        if (!campaign) return null;
        const end = new Date(campaign.active_end);
        const now = new Date();
        const diff = Math.ceil((end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

        if (diff < 0) return { text: "마감", color: "text-gray-400" };
        if (diff === 0) return { text: "D-DAY", color: "text-red-400" };
        if (diff <= 3) return { text: `D-${diff}`, color: "text-amber-400" };
        return { text: `D-${diff}`, color: "text-emerald-400" };
    };

    // 경쟁률 계산
    const getCompetition = () => {
        if (!campaign?.max_participants) return null;
        const applicants = campaign.current_applicants || 0;
        const max = campaign.max_participants;
        const ratio = applicants / max;

        return {
            text: `${applicants}/${max}명`,
            percent: Math.min(ratio * 100, 100),
            status: ratio >= 1 ? "full" : ratio >= 0.8 ? "hot" : "open"
        };
    };

    // 유형 메타
    const getTypeMeta = (type?: string) => {
        const normalized = type?.toLowerCase() || "";
        if (normalized.includes("ship") || normalized.includes("delivery")) {
            return { label: "제품 체험", icon: Truck, color: "text-violet-400", desc: "제품 배송 후 촬영" };
        }
        if (normalized.includes("instant") || normalized.includes("digital")) {
            return { label: "즉시 참여", icon: Zap, color: "text-cyan-400", desc: "바로 참여 가능" };
        }
        return { label: "매장 방문", icon: MapPin, color: "text-amber-400", desc: "방문 인증 필요" };
    };

    // 신청 제출
    const handleApply = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!campaignId) return;

        setApplying(true);
        setError(null);

        try {
            await api.applyO2OCampaign(campaignId);

            if (isMountedRef.current) {
                setApplied(true);
            }
        } catch (err) {
            console.error("신청 실패:", err);
            if (isMountedRef.current) {
                setError(err instanceof Error ? err.message : "신청에 실패했습니다");
            }
        } finally {
            if (isMountedRef.current) {
                setApplying(false);
            }
        }
    };

    const dday = getDday();
    const competition = getCompetition();
    const typeMeta = campaign ? getTypeMeta(campaign.campaign_type) : null;
    const TypeIcon = typeMeta?.icon || Gift;

    // 신청 완료
    if (applied) {
        return (
            <div className="min-h-screen bg-[#050505] text-white">
                <AppHeader />
                <div className="flex flex-col items-center justify-center min-h-[80vh] px-6">
                    <div className="w-20 h-20 bg-emerald-500/20 rounded-full flex items-center justify-center mb-6">
                        <Check className="w-10 h-10 text-emerald-400" />
                    </div>
                    <h1 className="text-2xl font-bold mb-2">신청 완료! 🎉</h1>
                    <p className="text-white/60 text-center mb-8">
                        {campaign?.campaign_title}에 신청되었습니다.<br />
                        선정 결과는 My 페이지에서 확인하세요.
                    </p>

                    <div className="space-y-3 w-full max-w-xs">
                        <Link
                            href="/my"
                            className="w-full py-3 bg-violet-500 hover:bg-violet-400 text-white font-bold rounded-xl flex items-center justify-center gap-2"
                        >
                            My 페이지로 이동
                            <ChevronRight className="w-4 h-4" />
                        </Link>
                        <Link
                            href="/collabs"
                            className="w-full py-3 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-xl flex items-center justify-center"
                        >
                            다른 협찬 보기
                        </Link>
                    </div>
                </div>
            </div>
        );
    }

    // 로딩
    if (loading) {
        return (
            <div className="min-h-screen bg-[#050505] flex items-center justify-center">
                <div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    // 에러 (캠페인 못 찾음)
    if (!campaign) {
        return (
            <div className="min-h-screen bg-[#050505] text-white">
                <AppHeader />
                <div className="flex flex-col items-center justify-center min-h-[80vh] px-6">
                    <AlertCircle className="w-12 h-12 text-red-400 mb-4" />
                    <h1 className="text-xl font-bold mb-2">캠페인을 찾을 수 없습니다</h1>
                    <p className="text-white/60 text-center mb-6">{error}</p>
                    <Link
                        href="/collabs"
                        className="px-6 py-3 bg-violet-500 rounded-xl text-white font-medium"
                    >
                        협찬 목록으로
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#050505] text-white pb-32">
            <AppHeader />

            {/* 헤더 */}
            <div className="sticky top-0 z-40 bg-zinc-950/80 backdrop-blur-lg border-b border-white/10">
                <div className="max-w-2xl mx-auto px-4 py-3 flex items-center gap-4">
                    <button onClick={() => router.back()} className="p-2 -ml-2 hover:bg-white/10 rounded-lg">
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <h1 className="text-lg font-bold">협찬 신청</h1>
                </div>
            </div>

            <main className="max-w-2xl mx-auto px-4 py-6 space-y-6">
                {/* 히어로 카드 */}
                <div className="bg-gradient-to-br from-violet-500/20 to-pink-500/20 rounded-3xl overflow-hidden border border-white/10">
                    {/* 상단 뱃지 */}
                    <div className="px-6 pt-6 flex items-center justify-between">
                        <div className={`flex items-center gap-2 ${typeMeta?.color}`}>
                            <TypeIcon className="w-4 h-4" />
                            <span className="text-sm font-medium">{typeMeta?.label}</span>
                        </div>
                        {dday && (
                            <span className={`px-3 py-1 rounded-full text-xs font-bold bg-black/30 ${dday.color}`}>
                                {dday.text}
                            </span>
                        )}
                    </div>

                    {/* 브랜드 & 타이틀 */}
                    <div className="px-6 py-4">
                        {campaign.brand && (
                            <div className="text-xs text-white/50 mb-1">{campaign.brand}</div>
                        )}
                        <h2 className="text-2xl font-bold">{campaign.campaign_title}</h2>
                    </div>

                    {/* 리워드 강조 */}
                    <div className="mx-6 mb-6 p-4 bg-white/5 rounded-2xl">
                        <div className="flex items-center gap-2 text-emerald-400 text-xs font-medium mb-2">
                            <Gift className="w-4 h-4" />
                            리워드
                        </div>
                        <div className="flex items-baseline gap-3">
                            <span className="text-3xl font-bold text-white">+{campaign.reward_points}P</span>
                            {campaign.reward_product && (
                                <span className="text-sm text-white/70">+ {campaign.reward_product}</span>
                            )}
                        </div>
                    </div>

                    {/* 경쟁률 바 */}
                    {competition && (
                        <div className="px-6 pb-6">
                            <div className="flex items-center justify-between text-xs mb-2">
                                <span className="text-white/50 flex items-center gap-1">
                                    <Users className="w-3 h-3" />
                                    신청 현황
                                </span>
                                <span className={`font-bold ${competition.status === "full" ? "text-red-400" :
                                    competition.status === "hot" ? "text-amber-400" : "text-emerald-400"
                                    }`}>
                                    {competition.text}
                                    {competition.status === "hot" && " 🔥"}
                                    {competition.status === "full" && " (마감)"}
                                </span>
                            </div>
                            <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                                <div
                                    className={`h-full transition-all ${competition.status === "full" ? "bg-red-500" :
                                        competition.status === "hot" ? "bg-amber-500" : "bg-emerald-500"
                                        }`}
                                    style={{ width: `${competition.percent}%` }}
                                />
                            </div>
                        </div>
                    )}
                </div>

                {/* 상세 정보 */}
                <div className="space-y-4">
                    {/* 설명 */}
                    {campaign.description && (
                        <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                            <h3 className="text-sm font-bold text-white/80 mb-2">캠페인 설명</h3>
                            <p className="text-sm text-white/60 whitespace-pre-wrap">{campaign.description}</p>
                        </div>
                    )}

                    {/* 진행 단계 */}
                    {campaign.fulfillment_steps && campaign.fulfillment_steps.length > 0 && (
                        <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                            <h3 className="text-sm font-bold text-white/80 mb-3">진행 순서</h3>
                            <div className="flex items-center gap-2 overflow-x-auto pb-2">
                                {campaign.fulfillment_steps.map((step, i) => (
                                    <div key={i} className="flex items-center shrink-0">
                                        <div className="px-3 py-1.5 bg-violet-500/20 rounded-lg text-xs text-violet-300 font-medium">
                                            {i + 1}. {step}
                                        </div>
                                        {i < campaign.fulfillment_steps!.length - 1 && (
                                            <ChevronRight className="w-4 h-4 text-white/20 mx-1" />
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* 마감일 */}
                    <div className="p-4 bg-white/5 rounded-xl border border-white/10 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <Calendar className="w-5 h-5 text-white/40" />
                            <div>
                                <div className="text-sm font-medium">모집 마감</div>
                                <div className="text-xs text-white/50">
                                    {new Date(campaign.active_end).toLocaleDateString('ko-KR', {
                                        year: 'numeric', month: 'long', day: 'numeric'
                                    })}
                                </div>
                            </div>
                        </div>
                        {dday && (
                            <span className={`text-lg font-bold ${dday.color}`}>{dday.text}</span>
                        )}
                    </div>
                </div>

                {/* 신청 폼 */}
                <form onSubmit={handleApply} className="space-y-4 pt-4">
                    <h3 className="text-lg font-bold">신청 정보</h3>

                    <div className="space-y-2">
                        <label className="text-sm font-medium text-white/80">SNS 계정 (선택)</label>
                        <input
                            type="text"
                            value={socialHandle}
                            onChange={(e) => setSocialHandle(e.target.value)}
                            placeholder="@your_tiktok"
                            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-white/30 focus:border-violet-500/50 focus:outline-none"
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium text-white/80">신청 동기 (선택)</label>
                        <textarea
                            value={motivation}
                            onChange={(e) => setMotivation(e.target.value)}
                            placeholder="이 협찬에 참여하고 싶은 이유..."
                            rows={3}
                            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-white/30 focus:border-violet-500/50 focus:outline-none resize-none"
                        />
                    </div>

                    {/* 에러 */}
                    {error && (
                        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3">
                            <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
                            <p className="text-red-300 text-sm">{error}</p>
                        </div>
                    )}
                </form>
            </main>

            {/* 고정 CTA */}
            <div className="fixed bottom-0 left-0 right-0 bg-zinc-950/90 backdrop-blur-lg border-t border-white/10 p-4 safe-area-bottom">
                <div className="max-w-2xl mx-auto">
                    <button
                        onClick={handleApply}
                        disabled={applying || competition?.status === "full"}
                        className="w-full py-4 bg-gradient-to-r from-violet-500 to-pink-500 text-white font-bold rounded-xl hover:brightness-110 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                        {applying ? (
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : competition?.status === "full" ? (
                            "모집 마감"
                        ) : (
                            <>
                                <Gift className="w-5 h-5" />
                                신청하기
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default function ApplyPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-[#050505] flex items-center justify-center">
                <div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
            </div>
        }>
            <ApplyContent />
        </Suspense>
    );
}
