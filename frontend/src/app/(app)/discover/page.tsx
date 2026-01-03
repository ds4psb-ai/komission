"use client";

import { useTranslations } from 'next-intl';

/**
 * /discover → / (홈) 리다이렉트
 */
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function DiscoverRedirect() {
    const router = useRouter();

    useEffect(() => {
        router.replace('/');
    }, [router]);

    return null;
}
