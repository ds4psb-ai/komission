"use client";

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';

// Wizard Steps
type WizardStep = 'mission' | 'capture' | 'verify';

interface MissionData {
    locationId: string;
    placeName: string;
    address: string;
    campaignTitle: string;
    rewardPoints: number;
    lat: number;
    lng: number;
}

export default function WizardPage() {
    const router = useRouter();
    const [currentStep, setCurrentStep] = useState<WizardStep>('mission');
    const [mission, setMission] = useState<MissionData | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isVerifying, setIsVerifying] = useState(false);
    const [verifyResult, setVerifyResult] = useState<{ success: boolean; message: string; points?: number } | null>(null);
    const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(null);
    const isMountedRef = useRef(true);

    // Load available mission
    useEffect(() => {
        loadMission();
    }, []);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    async function loadMission() {
        try {
            const locations = await api.listO2OLocations();
            if (!isMountedRef.current) return;
            if (locations.length > 0) {
                const loc = locations[0];
                setMission({
                    locationId: loc.location_id,
                    placeName: loc.place_name,
                    address: loc.address,
                    campaignTitle: loc.campaign_title,
                    rewardPoints: loc.reward_points,
                    lat: loc.lat,
                    lng: loc.lng,
                });
            }
        } catch (e) {
            console.error(e);
        } finally {
            if (isMountedRef.current) {
                setIsLoading(false);
            }
        }
    }

    function handleNextStep() {
        if (currentStep === 'mission') setCurrentStep('capture');
        else if (currentStep === 'capture') setCurrentStep('verify');
    }

    function handlePrevStep() {
        if (currentStep === 'capture') setCurrentStep('mission');
        else if (currentStep === 'verify') setCurrentStep('capture');
    }

    async function handleVerify() {
        if (!mission) return;

        setIsVerifying(true);

        // Get user's current location
        if (!navigator.geolocation) {
            setVerifyResult({ success: false, message: '이 브라우저는 위치 인증을 지원하지 않습니다.' });
            setIsVerifying(false);
            return;
        }

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                if (!isMountedRef.current) return;
                const { latitude, longitude } = position.coords;
                setUserLocation({ lat: latitude, lng: longitude });

                try {
                    const result = await api.verifyLocation(mission.locationId, latitude, longitude);
                    if (!isMountedRef.current) return;
                    setVerifyResult({
                        success: result.status === 'verified',
                        message: result.message,
                        points: result.points_awarded,
                    });
                } catch (e) {
                    if (isMountedRef.current) {
                        setVerifyResult({ success: false, message: '인증 실패. 다시 시도해주세요.' });
                    }
                } finally {
                    if (isMountedRef.current) {
                        setIsVerifying(false);
                    }
                }
            },
            (error) => {
                if (isMountedRef.current) {
                    setVerifyResult({ success: false, message: '위치 정보를 가져올 수 없습니다. GPS를 확인하세요.' });
                    setIsVerifying(false);
                }
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );
    }

    if (isLoading) {
        return (
            <div className="min-h-screen bg-black text-white flex items-center justify-center">
                <div className="animate-spin text-4xl">⏳</div>
            </div>
        );
    }

    if (!mission) {
        return (
            <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-6">
                <div className="text-6xl mb-6">📍</div>
                <h1 className="text-2xl font-bold mb-2">진행 중인 미션이 없습니다</h1>
                <p className="text-white/50 mb-8 text-center">주변에 새로운 챌린지가 생기면 알려드릴게요!</p>
                <Link href="/" className="px-6 py-3 bg-violet-500 rounded-xl font-bold">
                    홈으로 돌아가기
                </Link>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-black text-white flex flex-col">
            {/* Header */}
            <header className="p-4 border-b border-white/10 flex items-center justify-between">
                <Link href="/" className="text-white/50">✕</Link>
                <span className="font-bold">O2O 미션</span>
                <div className="w-6" />
            </header>

            {/* Progress Indicator */}
            <div className="flex justify-center gap-2 p-4">
                {(['mission', 'capture', 'verify'] as WizardStep[]).map((step, i) => (
                    <div
                        key={step}
                        className={`h-1 w-16 rounded-full transition-colors ${currentStep === step ? 'bg-violet-500' :
                                i < ['mission', 'capture', 'verify'].indexOf(currentStep) ? 'bg-violet-500/50' :
                                    'bg-white/20'
                            }`}
                    />
                ))}
            </div>

            {/* Step Content */}
            <main className="flex-1 p-6 flex flex-col">
                {currentStep === 'mission' && (
                    <div className="flex-1 flex flex-col">
                        <div className="text-center mb-8">
                            <div className="text-6xl mb-4">🎯</div>
                            <h1 className="text-2xl font-bold mb-2">Step 1: 미션 확인</h1>
                            <p className="text-white/50">아래 장소를 방문하고 인증하세요!</p>
                        </div>

                        <div className="bg-white/5 border border-white/10 rounded-2xl p-6 mb-6">
                            <div className="text-lg font-bold mb-1">{mission.placeName}</div>
                            <div className="text-white/50 text-sm mb-4">{mission.address}</div>
                            <div className="flex items-center gap-2 text-violet-400 font-bold">
                                <span>🎁</span>
                                <span>{mission.rewardPoints.toLocaleString()} K-Points</span>
                            </div>
                        </div>

                        <div className="bg-gradient-to-r from-violet-500/20 to-pink-500/20 border border-violet-500/30 rounded-2xl p-4 text-center">
                            <div className="text-sm text-white/70">{mission.campaignTitle}</div>
                        </div>

                        <div className="mt-auto">
                            <button
                                onClick={handleNextStep}
                                className="w-full py-4 bg-gradient-to-r from-violet-500 to-pink-500 rounded-2xl font-bold text-lg"
                            >
                                다음: 촬영하기 →
                            </button>
                        </div>
                    </div>
                )}

                {currentStep === 'capture' && (
                    <div className="flex-1 flex flex-col">
                        <div className="text-center mb-8">
                            <div className="text-6xl mb-4">📸</div>
                            <h1 className="text-2xl font-bold mb-2">Step 2: 촬영</h1>
                            <p className="text-white/50">장소에서 영상이나 사진을 촬영하세요</p>
                        </div>

                        <div className="flex-1 flex items-center justify-center">
                            <div className="aspect-[9/16] w-full max-w-xs bg-white/5 border-2 border-dashed border-white/20 rounded-3xl flex flex-col items-center justify-center">
                                <div className="text-4xl mb-4">📹</div>
                                <p className="text-white/50 text-sm">카메라 앱에서 촬영 후<br />돌아와서 인증하세요</p>
                            </div>
                        </div>

                        <div className="mt-auto space-y-3">
                            <button
                                onClick={handleNextStep}
                                className="w-full py-4 bg-gradient-to-r from-violet-500 to-pink-500 rounded-2xl font-bold text-lg"
                            >
                                다음: 위치 인증 →
                            </button>
                            <button
                                onClick={handlePrevStep}
                                className="w-full py-3 text-white/50"
                            >
                                ← 이전
                            </button>
                        </div>
                    </div>
                )}

                {currentStep === 'verify' && (
                    <div className="flex-1 flex flex-col">
                        <div className="text-center mb-8">
                            <div className="text-6xl mb-4">📍</div>
                            <h1 className="text-2xl font-bold mb-2">Step 3: 위치 인증</h1>
                            <p className="text-white/50">GPS로 현재 위치를 확인합니다</p>
                        </div>

                        {!verifyResult ? (
                            <div className="flex-1 flex flex-col items-center justify-center">
                                <div className="bg-white/5 border border-white/10 rounded-2xl p-6 text-center mb-6 w-full">
                                    <div className="font-bold mb-2">{mission.placeName}</div>
                                    <div className="text-sm text-white/50">{mission.address}</div>
                                </div>

                                <button
                                    onClick={handleVerify}
                                    disabled={isVerifying}
                                    className="px-8 py-4 bg-emerald-500 rounded-2xl font-bold text-lg disabled:opacity-50 flex items-center gap-2"
                                >
                                    {isVerifying ? (
                                        <>
                                            <span className="animate-spin">⏳</span> 인증 중...
                                        </>
                                    ) : (
                                        <>
                                            <span>📍</span> 위치 인증하기
                                        </>
                                    )}
                                </button>
                            </div>
                        ) : (
                            <div className="flex-1 flex flex-col items-center justify-center">
                                <div className={`text-6xl mb-4 ${verifyResult.success ? '' : 'grayscale'}`}>
                                    {verifyResult.success ? '🎉' : '😢'}
                                </div>
                                <h2 className={`text-2xl font-bold mb-2 ${verifyResult.success ? 'text-emerald-400' : 'text-red-400'}`}>
                                    {verifyResult.success ? '인증 성공!' : '인증 실패'}
                                </h2>
                                <p className="text-white/50 mb-4">{verifyResult.message}</p>
                                {verifyResult.points && (
                                    <div className="bg-emerald-500/20 border border-emerald-500/30 rounded-xl px-6 py-3 text-emerald-400 font-bold">
                                        +{verifyResult.points.toLocaleString()} K-Points 획득!
                                    </div>
                                )}
                            </div>
                        )}

                        <div className="mt-auto space-y-3">
                            {verifyResult?.success ? (
                                <Link
                                    href="/"
                                    className="w-full py-4 bg-gradient-to-r from-violet-500 to-pink-500 rounded-2xl font-bold text-lg block text-center"
                                >
                                    완료 🎊
                                </Link>
                            ) : (
                                <>
                                    {verifyResult && (
                                        <button
                                            onClick={() => setVerifyResult(null)}
                                            className="w-full py-4 bg-white/10 rounded-2xl font-bold"
                                        >
                                            다시 시도
                                        </button>
                                    )}
                                    <button
                                        onClick={handlePrevStep}
                                        className="w-full py-3 text-white/50"
                                    >
                                        ← 이전
                                    </button>
                                </>
                            )}
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
