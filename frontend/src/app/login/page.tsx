"use client";

import React, { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { GoogleLoginButtonCustom } from '@/components/GoogleLoginButton';
import { useAuth } from '@/lib/auth';

export default function LoginPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { login, isLoading: authLoading } = useAuth();

    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Where to redirect after login
    const redirectTo = searchParams.get('redirect') || '/my';

    const handleGoogleSuccess = async (credential: string) => {
        setIsLoading(true);
        setError(null);

        try {
            await login(credential);
            router.push(redirectTo);
        } catch (err) {
            console.error('Login failed:', err);
            setError(err instanceof Error ? err.message : '로그인에 실패했습니다.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleGoogleError = (err: Error) => {
        console.error('Google Sign-In error:', err);
        setError('Google 로그인에 실패했습니다. 다시 시도해주세요.');
    };

    return (
        <div className="min-h-screen bg-black flex flex-col items-center justify-center p-6">
            {/* Ambient Background */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-violet-500/20 rounded-full blur-3xl" />
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-pink-500/20 rounded-full blur-3xl" />
            </div>

            {/* Content */}
            <div className="relative z-10 w-full max-w-md">
                {/* Logo */}
                <div className="text-center mb-12">
                    <Link href="/" className="inline-block">
                        <h1 className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-pink-400">
                            Komission
                        </h1>
                        <p className="text-white/40 text-sm mt-2">바이럴 콘텐츠 인텔리전스</p>
                    </Link>
                </div>

                {/* Login Card */}
                <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8">
                    <h2 className="text-2xl font-bold text-white text-center mb-2">
                        시작하기
                    </h2>
                    <p className="text-white/60 text-center mb-8">
                        계정으로 로그인하고 바이럴 컨텐츠를 분석하세요
                    </p>

                    {/* Error Message */}
                    {error && (
                        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm text-center">
                            {error}
                        </div>
                    )}

                    {/* Google Login Button */}
                    <div className="space-y-4">
                        <GoogleLoginButtonCustom
                            onSuccess={handleGoogleSuccess}
                            onError={handleGoogleError}
                            isLoading={isLoading || authLoading}
                        />
                    </div>

                    {/* Divider */}
                    <div className="flex items-center gap-4 my-8">
                        <div className="flex-1 h-px bg-white/10" />
                        <span className="text-white/30 text-xs">또는</span>
                        <div className="flex-1 h-px bg-white/10" />
                    </div>

                    {/* Guest Access */}
                    <Link
                        href="/"
                        className="block w-full py-4 px-6 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-center text-white/60 hover:text-white transition-colors"
                    >
                        둘러보기만 할게요
                    </Link>
                </div>

                {/* Terms */}
                <p className="text-center text-white/30 text-xs mt-8">
                    로그인하면 Komission의{' '}
                    <Link href="/terms" className="underline hover:text-white/50">이용약관</Link>
                    {' '}및{' '}
                    <Link href="/privacy" className="underline hover:text-white/50">개인정보처리방침</Link>
                    에 동의하게 됩니다.
                </p>
            </div>
        </div>
    );
}
