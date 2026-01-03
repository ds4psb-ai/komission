"use client";

import React, { useState, useRef, Suspense, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { GoogleLoginButtonCustom } from '@/components/GoogleLoginButton';
import { useAuth } from '@/lib/auth';
import { ACTION_LABELS } from '@/lib/useAuthGate';
import { useTranslations } from 'next-intl';

function LoginContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { login, isLoading: authLoading } = useAuth();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const isMountedRef = useRef(true);
    const t = useTranslations('pages.login');

    // 3D Tilt State
    const cardRef = useRef<HTMLDivElement>(null);
    const [rotate, setRotate] = useState({ x: 0, y: 0 });
    const [spotlight, setSpotlight] = useState({ x: 50, y: 50 });

    const redirectTo = searchParams.get('redirect') || '/my';
    const isSessionExpired = searchParams.get('expired') === 'true';
    const isActionRequired = searchParams.get('required') === 'true';
    const actionType = searchParams.get('action');
    const actionLabel = actionType && ACTION_LABELS[actionType] ? ACTION_LABELS[actionType] : null;

    // Show session expired message on mount
    useEffect(() => {
        if (isSessionExpired) {
            setError(t('sessionExpired'));
        }
    }, [isSessionExpired, t]);

    useEffect(() => {
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!cardRef.current) return;
        const rect = cardRef.current.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        const rotateX = ((y - centerY) / centerY) * -5;
        const rotateY = ((x - centerX) / centerX) * 5;

        setRotate({ x: rotateX, y: rotateY });
        setSpotlight({ x: (x / rect.width) * 100, y: (y / rect.height) * 100 });
    };

    const handleMouseLeave = () => {
        setRotate({ x: 0, y: 0 });
        setSpotlight({ x: 50, y: 50 });
    };

    const handleGoogleSuccess = async (credential: string) => {
        if (isMountedRef.current) {
            setIsLoading(true);
            setError(null);
        }
        try {
            await login(credential);
            // Check for stored redirect path from authGate
            const storedRedirect = typeof window !== 'undefined'
                ? sessionStorage.getItem('authRedirect')
                : null;
            if (storedRedirect) {
                sessionStorage.removeItem('authRedirect');
                sessionStorage.removeItem('pendingAction');
                router.push(storedRedirect);
            } else {
                router.push(redirectTo);
            }
        } catch (err) {
            console.error('Login failed:', err);
            if (isMountedRef.current) {
                setError(err instanceof Error ? err.message : t('loginFailed'));
            }
        } finally {
            if (isMountedRef.current) {
                setIsLoading(false);
            }
        }
    };

    return (
        <div className="min-h-screen bg-[#050505] flex flex-col items-center justify-center p-6 relative overflow-hidden selection:bg-pink-500/30">
            {/* Cinematic Background Aurora - Lime/White */}
            <div className="absolute inset-0 pointer-events-none">
                <div className="absolute top-[-20%] left-[-10%] w-[70vw] h-[70vw] bg-[#c1ff00]/5 rounded-full blur-[120px] animate-[pulse_8s_ease-in-out_infinite]" />
                <div className="absolute bottom-[-20%] right-[-10%] w-[70vw] h-[70vw] bg-white/5 rounded-full blur-[120px] animate-[pulse_10s_ease-in-out_infinite_reverse]" />
            </div>

            {/* Grid Pattern Overlay */}
            <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-[0.03] animate-[pulse_4s_ease-in-out_infinite]" />

            {/* Content Container */}
            <div className="relative z-10 w-full max-w-md perspective-1000">
                {/* Logo Section with Glow */}
                <div className="text-center mb-16 relative group">
                    <div className="absolute -inset-10 bg-gradient-to-r from-[#c1ff00]/10 to-white/5 rounded-full blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-1000" />
                    <Link href="/" className="inline-block relative">
                        <h1 className="text-6xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-white via-white to-white/50 drop-shadow-[0_0_30px_rgba(255,255,255,0.3)]">
                            Komission
                        </h1>
                        <div className="flex items-center justify-center gap-2 mt-3">
                            <span className="w-2 h-2 rounded-full bg-[#c1ff00] animate-pulse shadow-[0_0_10px_#c1ff00]" />
                            <p className="text-white/40 text-sm font-medium tracking-widest uppercase text-[10px]">
                                Viral Intelligence Platform
                            </p>
                        </div>
                    </Link>
                </div>

                {/* 3D Tilt Login Card */}
                <div
                    ref={cardRef}
                    onMouseMove={handleMouseMove}
                    onMouseLeave={handleMouseLeave}
                    style={{
                        transform: `perspective(1000px) rotateX(${rotate.x}deg) rotateY(${rotate.y}deg)`,
                        transition: 'transform 0.1s ease-out'
                    }}
                    className="relative bg-black/40 backdrop-blur-2xl border border-white/10 rounded-[32px] p-10 shadow-2xl group"
                >
                    {/* Dynamic Spotlight Effect */}
                    <div
                        className="absolute inset-0 rounded-[32px] pointer-events-none opacity-50 group-hover:opacity-100 transition-opacity duration-500"
                        style={{
                            background: `radial-gradient(600px circle at ${spotlight.x}% ${spotlight.y}%, rgba(255,255,255,0.06), transparent 40%)`
                        }}
                    />

                    {/* Card Inner Glow - Electric Lime */}
                    <div className="absolute -inset-[1px] bg-gradient-to-br from-[#c1ff00]/10 via-transparent to-[#c1ff00]/5 rounded-[33px] -z-10 blur-sm opacity-50" />

                    <h2 className="text-3xl font-bold text-white text-center mb-3 tracking-tight">
                        {t('welcomeBack')}
                    </h2>
                    <p className="text-white/50 text-center mb-10 text-sm font-medium leading-relaxed">
                        {t('subtitle')}
                    </p>

                    {/* Error Box */}
                    {error && (
                        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-300 text-xs font-bold text-center flex items-center justify-center gap-2 animate-shake">
                            <span>🚫</span> {error}
                        </div>
                    )}

                    {/* Action Required Info Box */}
                    {isActionRequired && !error && (
                        <div className="mb-6 p-4 bg-black/40 border border-[#c1ff00]/20 rounded-xl text-white text-xs font-bold text-center flex items-center justify-center gap-2 font-mono">
                            <span className="text-[#c1ff00]">🔐</span>
                            {actionLabel
                                ? `"${actionLabel}" LOG IN REQUIRED`
                                : 'LOGIN REQUIRED TO ACCESS THIS FEATURE'}
                        </div>
                    )}

                    {/* Google Login Area */}
                    <div className="space-y-4 relative z-20">
                        <div className="transform transition-transform hover:scale-[1.02] active:scale-[0.98]">
                            <GoogleLoginButtonCustom
                                onSuccess={handleGoogleSuccess}
                                onError={() => setError(t('loginFailed'))}
                                isLoading={isLoading || authLoading}
                            />
                        </div>
                    </div>

                    {/* Divider with Text */}
                    <div className="flex items-center gap-4 my-8">
                        <div className="flex-1 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
                        <span className="text-white/20 text-[10px] font-bold uppercase tracking-widest">{t('orContinueAsGuest')}</span>
                        <div className="flex-1 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
                    </div>

                    {/* Guest Button */}
                    <Link
                        href="/"
                        className="block w-full py-4 px-6 bg-white/5 hover:bg-white/10 border border-white/5 hover:border-[#c1ff00]/30 rounded-xl text-center text-white/50 hover:text-white transition-all duration-300 text-sm font-bold relative overflow-hidden group/btn"
                    >
                        <span className="relative z-10 flex items-center justify-center gap-2">
                            <span>🚀</span> {t('continueAsGuest')}
                        </span>
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-[#c1ff00]/10 to-transparent translate-x-[-100%] group-hover/btn:translate-x-[100%] transition-transform duration-1000" />
                    </Link>
                </div>

                {/* Footer Terms */}
                <p className="text-center text-white/20 text-[10px] mt-10 leading-loose">
                    {t('agreeToTerms').split('{terms}')[0]}
                    <Link href="/terms" className="text-white/40 hover:text-white underline decoration-white/20 underline-offset-4 transition-colors">{t('terms')}</Link>
                    {' '}
                    <Link href="/privacy" className="text-white/40 hover:text-white underline decoration-white/20 underline-offset-4 transition-colors">{t('privacy')}</Link>
                </p>
            </div>
        </div>
    );
}

export default function LoginPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-[#050505] flex items-center justify-center">
                <div className="w-10 h-10 border-4 border-[#c1ff00] border-t-transparent rounded-full animate-spin" />
            </div>
        }>
            <LoginContent />
        </Suspense>
    );
}
