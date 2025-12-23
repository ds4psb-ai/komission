"use client";

import { useEffect, useState } from "react";
import { api, O2OLocation } from "@/lib/api";
import { AppHeader } from "@/components/AppHeader";
import { Badge } from "@/components/ui/Badge";

export default function O2OPage() {
    const [locations, setLocations] = useState<O2OLocation[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedLoc, setSelectedLoc] = useState<O2OLocation | null>(null);
    const [verifying, setVerifying] = useState(false);

    const getTypeMeta = (type?: string) => {
        const normalized = type?.toLowerCase() || "";
        if (normalized.includes("ship") || normalized.includes("delivery")) {
            return { label: "배송", intent: "brand" as const, desc: "배송 후 촬영" };
        }
        if (normalized.includes("instant") || normalized.includes("digital")) {
            return { label: "즉시", intent: "cyan" as const, desc: "바로 촬영 가능" };
        }
        return { label: "방문", intent: "warning" as const, desc: "위치 인증 필요" };
    };

    const selectedTypeMeta = selectedLoc ? getTypeMeta(selectedLoc.campaign_type) : null;

    useEffect(() => {
        fetchLocations();
    }, []);

    async function fetchLocations() {
        try {
            const data = await api.listO2OLocations();
            setLocations(data);
            if (data.length > 0) setSelectedLoc(data[0]);
        } catch (err) {
            console.warn('O2O 캠페인 로드 실패', err);
        } finally {
            setLoading(false);
        }
    }

    async function handleVerify() {
        if (!selectedLoc) return;
        if (!confirm(`${selectedLoc.place_name} 위치 인증을 시도하시겠습니까?`)) return;

        setVerifying(true);

        if (!navigator.geolocation) {
            alert("브라우저가 위치 정보를 지원하지 않습니다.");
            setVerifying(false);
            return;
        }

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                try {
                    const { latitude, longitude } = position.coords;
                    const res = await api.verifyLocation(selectedLoc.location_id, latitude, longitude);
                    alert(`✅ 인증 성공! ${res.points_awarded} 포인트 획득\n(거리: ${res.distance}m)`);
                } catch (err) {
                    alert(err instanceof Error ? err.message : "인증 실패");
                } finally {
                    setVerifying(false);
                }
            },
            (error) => {
                alert("위치 정보를 가져올 수 없습니다: " + error.message);
                setVerifying(false);
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );
    }

    return (
        <div className="min-h-screen bg-black text-white flex flex-col">
            <AppHeader />

            {/* Map Background (Mock) */}
            <div className="absolute inset-0 z-0 bg-slate-900">
                {/* Simulated Map Visuals */}
                <div className="w-full h-full opacity-30 bg-[url('https://upload.wikimedia.org/wikipedia/commons/e/ec/Seoul_City_Wall.jpg')] bg-cover bg-center grayscale mix-blend-luminosity"></div>
                <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent"></div>

                {/* Map Markers */}
                {locations.map((loc, idx) => (
                    <div
                        key={loc.id}
                        className={`absolute cursor-pointer transition-all duration-500 group ${selectedLoc?.id === loc.id ? 'z-40 scale-110' : 'z-30 opacity-60 hover:opacity-100'}`}
                        style={{ top: `${40 + (idx * 20)}%`, left: `${30 + (idx * 30)}%` }}
                        onClick={() => setSelectedLoc(loc)}
                    >
                        <div className="relative">
                            <div className={`w-4 h-4 rounded-full ${selectedLoc?.id === loc.id ? 'bg-violet-500 animate-ping' : 'bg-white'} absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2`}></div>
                            <div className={`w-12 h-12 rounded-full border-4 ${selectedLoc?.id === loc.id ? 'border-violet-500 bg-black' : 'border-white bg-black'} flex items-center justify-center shadow-[0_0_30px_rgba(0,0,0,0.5)]`}>
                                <span className="text-xl">📍</span>
                            </div>
                        </div>
                        <div className={`absolute top-14 left-1/2 -translate-x-1/2 whitespace-nowrap px-3 py-1 rounded-lg bg-black/80 backdrop-blur-md border border-white/10 text-xs font-bold ${selectedLoc?.id === loc.id ? 'text-violet-400' : 'text-white'}`}>
                            {loc.place_name}
                        </div>
                    </div>
                ))}
            </div>

            {/* Bottom Sheet / Card Overlay */}
            <div className="absolute bottom-0 left-0 right-0 z-40 p-6 md:p-12 flex justify-center pointer-events-none">
                {selectedLoc ? (
                    <div className="glass-panel w-full max-w-3xl rounded-3xl p-0 overflow-hidden pointer-events-auto animate-pulse-glow hover:animate-none transition-all">
                        <div className="grid grid-cols-1 md:grid-cols-2">
                            {/* Image Side */}
                            <div className="h-48 md:h-auto bg-slate-800 relative">
                                <div className="absolute inset-0 flex items-center justify-center text-6xl opacity-20">🏢</div>
                                <div className="absolute inset-0 bg-gradient-to-r from-violet-900/50 to-transparent mix-blend-overlay"></div>
                                <div className="absolute top-4 left-4">
                                    <span className="bg-black/50 backdrop-blur px-3 py-1 rounded-full text-xs font-bold border border-white/10 text-white">
                                        {selectedLoc.brand || 'Partner Brand'}
                                    </span>
                                </div>
                            </div>

                            {/* Info Side */}
                            <div className="p-6 md:p-8">
                                <div className="flex justify-between items-start mb-4">
                                    <div>
                                        <h2 className="text-2xl font-bold mb-1">{selectedLoc.campaign_title}</h2>
                                        <p className="text-sm text-white/50">{selectedLoc.address}</p>
                                    </div>
                                    {selectedTypeMeta && (
                                        <div className="flex flex-col items-end gap-2">
                                            <Badge variant="outline" intent={selectedTypeMeta.intent}>
                                                {selectedTypeMeta.label}
                                            </Badge>
                                            <span className="text-[10px] text-white/40">
                                                {selectedTypeMeta.desc}
                                            </span>
                                        </div>
                                    )}
                                </div>

                                <div className="space-y-4 mb-8">
                                    <div className="flex items-center justify-between p-3 bg-white/5 rounded-xl border border-white/5">
                                        <span className="text-sm text-white/60">Reward</span>
                                        <span className="text-lg font-mono font-bold text-violet-400">+{selectedLoc.reward_points} P</span>
                                    </div>
                                    {selectedLoc.reward_product && (
                                        <div className="flex items-center justify-between p-3 bg-white/5 rounded-xl border border-white/5">
                                            <span className="text-sm text-white/60">Product</span>
                                            <span className="text-sm font-bold text-white">{selectedLoc.reward_product}</span>
                                        </div>
                                    )}
                                </div>

                                <button
                                    onClick={handleVerify}
                                    disabled={verifying}
                                    className="w-full py-4 bg-violet-600 hover:bg-violet-500 disabled:bg-violet-800 disabled:cursor-not-allowed text-white font-bold rounded-xl transition-all shadow-[0_0_20px_rgba(139,92,246,0.4)] flex items-center justify-center gap-2"
                                >
                                    {verifying ? (
                                        <>
                                            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                            <span>인증 중...</span>
                                        </>
                                    ) : (
                                        <span>📍 Check-in via GPS</span>
                                    )}
                                </button>
                            </div>
                        </div>
                    </div>
                ) : (
                    loading && (
                        <div className="bg-black/80 backdrop-blur px-6 py-3 rounded-full border border-white/10 flex items-center gap-3">
                            <div className="w-4 h-4 rounded-full border-2 border-t-transparent border-white animate-spin"></div>
                            <span className="text-sm">Locating Campaigns...</span>
                        </div>
                    )
                )}
            </div>
        </div>
    );
}
