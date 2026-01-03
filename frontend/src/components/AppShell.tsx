"use client";
import { useTranslations } from 'next-intl';

/**
 * AppShell - Layout wrapper with Hybrid Navigation
 * 
 * Desktop (md+): CollapsibleSidebar (left)
 * Mobile (<md): BottomNav (bottom)
 */

import { CollapsibleSidebar } from "./CollapsibleSidebar";
import { usePathname } from "next/navigation";
import { useState } from "react";

// Pages that should NOT show navigation (landing, auth, etc.)
const NO_SIDEBAR_PAGES = ["/login", "/signup", "/privacy", "/terms"];

export function AppShell({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const [isExpanded, setIsExpanded] = useState(false);

    // Check if current page should hide navigation
    const hideSidebar = NO_SIDEBAR_PAGES.some(
        page => pathname === page || pathname.startsWith("/auth/")
    );

    if (hideSidebar) {
        return <>{children}</>;
    }

    return (
        <div className="flex min-h-screen">
            <CollapsibleSidebar
                isExpanded={isExpanded}
                onToggle={() => setIsExpanded(!isExpanded)}
            />
            <main
                className={`flex-1 transition-all duration-300 ${isExpanded ? "ml-52" : "ml-14"
                    }`}
            >
                {children}
            </main>


        </div>
    );
}
