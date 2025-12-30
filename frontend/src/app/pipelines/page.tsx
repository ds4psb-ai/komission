"use client";

/**
 * /pipelines → /ops/pipelines 리다이렉트
 * 
 * Pipeline 마켓플레이스는 Ops 전용 기능으로 격하됨
 */
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function PipelinesRedirect() {
    const router = useRouter();

    useEffect(() => {
        router.replace('/ops/pipelines');
    }, [router]);

    return (
        <div className="min-h-screen bg-black flex items-center justify-center">
            <div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
        </div>
    );
}
