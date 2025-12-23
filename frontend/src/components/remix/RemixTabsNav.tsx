// frontend/src/components/remix/RemixTabsNav.tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSessionStore } from "@/stores/useSessionStore";
import { SESSION_TABS, type SessionTab } from "@/lib/types/session";

interface RemixTabsNavProps {
    nodeId: string;
}

export function RemixTabsNav({ nodeId }: RemixTabsNavProps) {
    const pathname = usePathname();
    const mode = useSessionStore((s) => s.mode);
    const setTab = useSessionStore((s) => s.setTab);

    // Determine current tab from pathname
    const currentTab = pathname.split("/").pop() as SessionTab || "shoot";

    return (
        <nav className="border-b border-white/5 bg-black/30 backdrop-blur-sm sticky top-0 z-30">
            <div className="container mx-auto px-6">
                <div className="flex gap-1 overflow-x-auto py-2 scrollbar-hide">
                    {SESSION_TABS.map(({ tab, label, icon, proOnly }) => {
                        const isActive = currentTab === tab;
                        const isDisabled = proOnly && mode === "simple";

                        if (isDisabled) {
                            return (
                                <button
                                    key={tab}
                                    disabled
                                    className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold text-white/30 cursor-not-allowed"
                                    title="Pro 모드에서만 사용 가능"
                                >
                                    <span>{icon}</span>
                                    <span>{label}</span>
                                    <span className="text-[9px] bg-white/10 px-1.5 py-0.5 rounded">PRO</span>
                                </button>
                            );
                        }

                        return (
                            <Link
                                key={tab}
                                href={`/remix/${nodeId}/${tab}`}
                                onClick={() => setTab(tab)}
                                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${isActive
                                        ? "bg-violet-500 text-white shadow-[0_0_15px_rgba(139,92,246,0.4)]"
                                        : "text-white/60 hover:text-white hover:bg-white/5"
                                    }`}
                            >
                                <span>{icon}</span>
                                <span>{label}</span>
                            </Link>
                        );
                    })}
                </div>
            </div>
        </nav>
    );
}
