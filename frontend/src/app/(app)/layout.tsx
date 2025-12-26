'use client';

import { AppHeader } from '@/components/AppHeader';

export default function AppLayout({ children }: { children: React.ReactNode }) {
    return (
        <div className="min-h-screen bg-gradient-to-br from-[#050510] via-[#0a0a1a] to-[#0f0520]">
            <AppHeader />
            <main>{children}</main>
        </div>
    );
}
