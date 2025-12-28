"use client";

/**
 * Session Layout - SessionProvider 래핑
 * 
 * 문서: docs/21_PAGE_IA_REDESIGN.md
 * - /session/* 하위 페이지에 SessionContext 제공
 */
import { SessionProvider } from '@/contexts/SessionContext';

export default function SessionLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <SessionProvider>
            {children}
        </SessionProvider>
    );
}
