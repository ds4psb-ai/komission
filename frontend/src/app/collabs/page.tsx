"use client";

/**
 * 브랜드 협찬 페이지 (구 O2O)
 * 
 * 바이럴 레퍼런스로 촬영하면 브랜드에서 리워드 제공
 * - 제품 배송 체험
 * - 매장 방문 인증
 * - 즉시 참여 (디지털)
 */
import { useEffect, useState, useRef, useCallback } from "react";
import { api, O2OLocation } from "@/lib/api";
import { AppHeader } from "@/components/AppHeader";
import { Badge } from "@/components/ui/Badge";
import Link from "next/link";

const MAX_RETRY_COUNT = 3;

export default function CollabsPage() {
    const [campaigns, setCampaigns] = useState<O2OLocation[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedCampaign, setSelectedCampaign] = useState<O2OLocation | null>(null);
    const [verifying, setVerifying] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [retryCount, setRetryCount] = useState(0);
    const [isOffline, setIsOffline] = useState(false);
    const [locationPermission, setLocationPermission] = useState<'granted' | 'denied' | 'prompt' | null>(null);
    const isMountedRef = useRef(true);

    // 캠페인 유형 메타데이터
    const getTypeMeta = (type?: string) => {
        const normalized = type?.toLowerCase() || "";
        if (normalized.includes("ship") || normalized.includes("delivery")) {
            return {
                label: "제품 체험",
                intent: "brand" as const,
                desc: "무료 제품 배송 + 리워드",
                emoji: "📦",
                cta: "신청하기"
            };
        }
        if (normalized.includes("instant") || normalized.includes("digital")) {
            return {
                label: "즉시 참여",
                intent: "cyan" as const,
                desc: "바로 촬영 가능",
                emoji: "⚡",
                cta: "참여하기"
            };
        }
        return {
            label: "매장 방문",
            intent: "warning" as const,
            desc: "방문 인증 시 리워드",
            emoji: "📍",
            cta: "GPS 체크인"
        };
    };

    const selectedTypeMeta = selectedCampaign ? getTypeMeta(selectedCampaign.campaign_type) : null;

    // 오프라인 감지
    useEffect(() => {
        const handleOnline = () => setIsOffline(false);
        const handleOffline = () => setIsOffline(true);

        setIsOffline(!navigator.onLine);
        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);

        return () => {
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
        };
    }, []);

    // 위치 권한 확인
    useEffect(() => {
        if ('permissions' in navigator) {
            navigator.permissions.query({ name: 'geolocation' }).then(result => {
                setLocationPermission(result.state);
                result.onchange = () => setLocationPermission(result.state);
            });
        }
    }, []);

    // 컴포넌트 마운트 추적
    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    // 캠페인 로드
    const fetchCampaigns = useCallback(async () => {
        if (isOffline) {
            setError('인터넷 연결을 확인해주세요');
            setLoading(false);
            return;
        }

        try {
            if (isMountedRef.current) {
                setError(null);
                setLoading(true);
            }
            const data = await api.listO2OLocations();
            if (!isMountedRef.current) return;
            setCampaigns(data);
            if (data.length > 0) setSelectedCampaign(data[0]);
        } catch (err) {
            console.warn('협찬 캠페인 로드 실패', err);
            if (!isMountedRef.current) return;
            setCampaigns([]);
            setSelectedCampaign(null);

            let errorMessage = "협찬 캠페인 로드 실패";
            if (err instanceof Error) {
                if (err.message.includes('network') || err.message.includes('fetch')) {
                    errorMessage = "서버에 연결할 수 없습니다";
                } else if (err.message.includes('401') || err.message.includes('403')) {
                    errorMessage = "로그인이 필요합니다";
                } else {
                    errorMessage = err.message;
                }
            }
            setError(errorMessage);
        } finally {
            if (isMountedRef.current) {
                setLoading(false);
            }
        }
    }, [isOffline]);

    useEffect(() => {
        fetchCampaigns();
    }, [fetchCampaigns, retryCount]);

    // 재시도
    const handleRetry = () => {
        if (retryCount >= MAX_RETRY_COUNT) {
            alert('최대 재시도 횟수에 도달했습니다.\n페이지를 새로고침해주세요.');
            return;
        }
        setRetryCount(prev => prev + 1);
    };

    // 위치 인증
    async function handleVerify() {
        if (!selectedCampaign) return;
        if (!confirm(`${selectedCampaign.place_name}에서 체크인하시겠어요?\n\n✅ 인증 성공 시 ${selectedCampaign.reward_points}P 적립!`)) return;

        if (!navigator.onLine) {
            alert('인터넷 연결을 확인해주세요.');
            return;
        }

        if (isMountedRef.current) {
            setVerifying(true);
        }

        if (!navigator.geolocation) {
            alert("브라우저가 위치 정보를 지원하지 않습니다.");
            if (isMountedRef.current) {
                setVerifying(false);
            }
            return;
        }

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                try {
                    const { latitude, longitude } = position.coords;
                    const res = await api.verifyLocation(selectedCampaign.location_id, latitude, longitude);
                    alert(`🎉 체크인 성공!\n\n+${res.points_awarded}P 적립되었어요\n거리: ${res.distance}m`);
                } catch (err) {
                    let message = "체크인 실패";
                    if (err instanceof Error) {
                        if (err.message.includes('100m') || err.message.includes('distance')) {
                            message = "아직 매장에서 조금 멀어요 📍\n\n100m 이내로 이동 후 다시 시도해주세요!";
                        } else {
                            message = err.message;
                        }
                    }
                    alert(message);
                } finally {
                    if (isMountedRef.current) {
                        setVerifying(false);
                    }
                }
            },
            (geoError) => {
                let message = "위치 정보를 가져올 수 없습니다";

                switch (geoError.code) {
                    case geoError.PERMISSION_DENIED:
                        message = "📍 위치 권한이 필요해요!\n\n브라우저 설정에서 위치 권한을 허용해주세요:\n• Safari: 설정 > 개인정보 > 위치 서비스\n• Chrome: 주소창 🔒 클릭 > 위치 허용";
                        break;
                    case geoError.POSITION_UNAVAILABLE:
                        message = "현재 위치를 확인할 수 없어요 📍\n\n• GPS가 켜져 있는지 확인해주세요\n• 실외에서 다시 시도해주세요";
                        break;
                    case geoError.TIMEOUT:
                        message = "위치 확인이 오래 걸려요 ⏱️\n\n실외에서 다시 시도해주세요!";
                        break;
                }

                alert(message);
                if (isMountedRef.current) {
                    setVerifying(false);
                }
            },
            { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
        );
    }

    return (
        <div className="min-h-screen bg-black text-white flex flex-col">
            <AppHeader />

            {/* 오프라인 배너 */}
            {isOffline && (
                <div className="fixed top-16 left-0 right-0 z-50 px-4 py-2 bg-red-500/90 text-center">
                    <span className="text-sm font-medium">
                        📵 오프라인 상태입니다
                    </span>
                </div>
            )}

            {/* 위치 권한 경고 */}
            {locationPermission === 'denied' && (
                <div className="fixed top-16 left-0 right-0 z-50 px-4 py-3 bg-amber-500/90">
                    <div className="max-w-lg mx-auto text-center">
                        <p className="text-sm font-medium text-black">
                            📍 매장 방문 인증을 위해 위치 권한이 필요해요
                        </p>
                        <p className="text-xs text-black/70 mt-1">
                            브라우저 설정에서 위치 권한을 허용해주세요
                        </p>
                    </div>
                </div>
            )}

            {/* 히어로 헤더 */}
            <div className="relative z-10 px-6 pt-20 pb-6 bg-gradient-to-b from-violet-900/30 to-transparent">
                <h1 className="text-2xl font-bold mb-2">🎁 브랜드 협찬</h1>
                <p className="text-white/60 text-sm">
                    바이럴 레퍼런스로 촬영하면<br />
                    브랜드에서 리워드를 드려요!
                </p>
            </div>

            {/* Map Background (Mock) */}
            <div className="absolute inset-0 z-0 bg-slate-900">
                <div className="w-full h-full opacity-20 bg-[url('https://upload.wikimedia.org/wikipedia/commons/e/ec/Seoul_City_Wall.jpg')] bg-cover bg-center grayscale mix-blend-luminosity"></div>
                <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent"></div>

                {/* Map Markers */}
                {campaigns.map((campaign, idx) => (
                    <div
                        key={campaign.id}
                        className={`absolute cursor-pointer transition-all duration-500 group ${selectedCampaign?.id === campaign.id ? 'z-40 scale-110' : 'z-30 opacity-60 hover:opacity-100'}`}
                        style={{ top: `${40 + (idx * 20)}%`, left: `${30 + (idx * 30)}%` }}
                        onClick={() => setSelectedCampaign(campaign)}
                    >
                        <div className="relative">
                            <div className={`w-4 h-4 rounded-full ${selectedCampaign?.id === campaign.id ? 'bg-violet-500 animate-ping' : 'bg-white'} absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2`}></div>
                            <div className={`w-12 h-12 rounded-full border-4 ${selectedCampaign?.id === campaign.id ? 'border-violet-500 bg-black' : 'border-white bg-black'} flex items-center justify-center shadow-[0_0_30px_rgba(0,0,0,0.5)]`}>
                                <span className="text-xl">{getTypeMeta(campaign.campaign_type).emoji}</span>
                            </div>
                        </div>
                        <div className={`absolute top-14 left-1/2 -translate-x-1/2 whitespace-nowrap px-3 py-1 rounded-lg bg-black/80 backdrop-blur-md border border-white/10 text-xs font-bold ${selectedCampaign?.id === campaign.id ? 'text-violet-400' : 'text-white'}`}>
                            {campaign.place_name}
                        </div>
                    </div>
                ))}
            </div>

            {/* 빈 상태 */}
            {!loading && !selectedCampaign && (
                <div className="absolute inset-0 z-30 flex items-center justify-center p-6">
                    <div className="glass-panel max-w-lg w-full rounded-3xl p-8 border border-white/10 bg-black/70 text-center shadow-2xl">
                        <div className="text-4xl mb-4">🎁</div>
                        <h2 className="text-2xl font-bold text-white mb-2">
                            진행 중인 협찬이 없어요
                        </h2>
                        <p className="text-sm text-white/50 mb-4">
                            곧 새로운 브랜드 협찬이 오픈됩니다!<br />
                            알림을 켜두면 가장 먼저 알려드려요.
                        </p>
                        {error && (
                            <div className="text-xs text-red-300/80 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2 mb-4">
                                {error}
                            </div>
                        )}

                        <button
                            onClick={handleRetry}
                            disabled={retryCount >= MAX_RETRY_COUNT}
                            className="px-6 py-2 bg-violet-500 hover:bg-violet-400 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-xl text-sm font-medium transition-colors"
                        >
                            🔄 새로고침 {retryCount > 0 && `(${retryCount}/${MAX_RETRY_COUNT})`}
                        </button>
                    </div>
                </div>
            )}

            {/* Bottom Sheet / Card Overlay */}
            <div className="absolute bottom-0 left-0 right-0 z-40 p-6 md:p-12 flex justify-center pointer-events-none">
                {selectedCampaign ? (
                    <div className="glass-panel w-full max-w-3xl rounded-3xl p-0 overflow-hidden pointer-events-auto">
                        <div className="grid grid-cols-1 md:grid-cols-2">
                            {/* Image Side */}
                            <div className="h-48 md:h-auto bg-slate-800 relative">
                                <div className="absolute inset-0 flex items-center justify-center text-6xl opacity-20">
                                    {selectedTypeMeta?.emoji}
                                </div>
                                <div className="absolute inset-0 bg-gradient-to-r from-violet-900/50 to-transparent mix-blend-overlay"></div>
                                <div className="absolute top-4 left-4">
                                    <span className="bg-black/50 backdrop-blur px-3 py-1 rounded-full text-xs font-bold border border-white/10 text-white">
                                        {selectedCampaign.brand || 'Partner'}
                                    </span>
                                </div>
                                {/* 희소성 표시 */}
                                <div className="absolute bottom-4 left-4 right-4">
                                    <div className="bg-black/60 backdrop-blur px-3 py-2 rounded-xl border border-white/10">
                                        <div className="flex items-center justify-between text-xs">
                                            <span className="text-white/60">마감</span>
                                            <span className="text-amber-400 font-bold">D-7</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Info Side */}
                            <div className="p-6 md:p-8">
                                <div className="flex justify-between items-start mb-4">
                                    <div>
                                        <h2 className="text-xl font-bold mb-1">{selectedCampaign.campaign_title}</h2>
                                        <p className="text-sm text-white/50">{selectedCampaign.address}</p>
                                    </div>
                                    {selectedTypeMeta && (
                                        <Badge variant="outline" intent={selectedTypeMeta.intent}>
                                            {selectedTypeMeta.label}
                                        </Badge>
                                    )}
                                </div>

                                {/* 리워드 강조 */}
                                <div className="space-y-3 mb-6">
                                    <div className="p-4 bg-gradient-to-r from-violet-500/20 to-pink-500/20 rounded-xl border border-violet-500/30">
                                        <div className="text-xs text-white/50 mb-1">🎁 리워드</div>
                                        <div className="flex items-baseline gap-2">
                                            <span className="text-2xl font-bold text-violet-400">+{selectedCampaign.reward_points}P</span>
                                            {selectedCampaign.reward_product && (
                                                <span className="text-sm text-white/70">+ {selectedCampaign.reward_product}</span>
                                            )}
                                        </div>
                                    </div>

                                    {/* 참여 조건 */}
                                    <div className="text-xs text-white/50 flex items-center gap-2">
                                        <span>✓</span>
                                        <span>{selectedTypeMeta?.desc}</span>
                                    </div>
                                </div>

                                {/* CTA 버튼 */}
                                {selectedTypeMeta?.label === '매장 방문' ? (
                                    <button
                                        onClick={handleVerify}
                                        disabled={verifying || isOffline}
                                        className="w-full py-4 bg-gradient-to-r from-violet-500 to-pink-500 hover:from-violet-400 hover:to-pink-400 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold rounded-xl transition-all flex items-center justify-center gap-2"
                                    >
                                        {verifying ? (
                                            <>
                                                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                                <span>위치 확인 중...</span>
                                            </>
                                        ) : (
                                            <span>📍 {selectedTypeMeta.cta}</span>
                                        )}
                                    </button>
                                ) : (
                                    <Link
                                        href={`/collabs/apply?id=${selectedCampaign.id}`}
                                        className="w-full py-4 bg-gradient-to-r from-violet-500 to-pink-500 hover:from-violet-400 hover:to-pink-400 text-white font-bold rounded-xl transition-all flex items-center justify-center gap-2"
                                    >
                                        <span>{selectedTypeMeta?.emoji} {selectedTypeMeta?.cta}</span>
                                    </Link>
                                )}
                            </div>
                        </div>
                    </div>
                ) : (
                    loading && (
                        <div className="bg-black/80 backdrop-blur px-6 py-3 rounded-full border border-white/10 flex items-center gap-3">
                            <div className="w-4 h-4 rounded-full border-2 border-t-transparent border-white animate-spin"></div>
                            <span className="text-sm">협찬 캠페인 불러오는 중...</span>
                        </div>
                    )
                )}
            </div>
        </div>
    );
}
