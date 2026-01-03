"use client";

import { useTranslations } from 'next-intl';

/**
 * /outliers → /ops/outliers 리다이렉트
 * 
 * Outlier 관리는 Ops 전용 기능으로 격하됨
 */
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function OutliersRedirect() {
    const router = useRouter();

    useEffect(() => {
        router.replace('/ops/outliers');
    }, [router]);

    return (
        <div className="min-h-screen bg-background flex items-center justify-center">
            <div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
        </div>
    );
}
