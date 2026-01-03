"use client";

import { useTranslations } from 'next-intl';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

/**
 * Redirect from /canvas to /ops/canvas
 * Canvas is now Ops-only feature
 */
export default function CanvasRedirect() {
    const router = useRouter();

    useEffect(() => {
        router.replace('/ops/canvas');
    }, [router]);

    return (
        <div className="min-h-screen bg-black flex items-center justify-center">
            <div className="text-white/60 text-sm">Redirecting to Ops Canvas...</div>
        </div>
    );
}
