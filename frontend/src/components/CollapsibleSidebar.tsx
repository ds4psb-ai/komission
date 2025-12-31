"use client";

/**
 * CollapsibleSidebar - LMSys Arena Style
 * 
 * Features:
 * - 48px (collapsed) ↔ 200px (expanded) toggle
 * - Logo hover animation (K → Sparkles)
 * - NavGroup with Flyout menus
 * - Invisible Bridge for stable hover
 */

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useRef, useEffect } from "react";
import { useAuth } from "@/lib/auth";
import {
    Network, User, Wallet, LogOut, Radar, FlaskConical,
    Zap, BookOpen, Sparkles, TrendingUp, BarChart3,
    ChevronLeft, ChevronRight, MessageCircle, ExternalLink,
    PanelLeftOpen, PanelLeftClose
} from "lucide-react";

// ============================================
// Data Definitions
// ============================================

interface NavItem {
    href: string;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
}

interface NavGroupData {
    id: string;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    items: NavItem[];
}

interface BottomItemData {
    id: string;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    href: string;
    external?: boolean;
    flyout?: {
        title: string;
        description?: string;
        items?: { label: string; href: string }[];
        cta?: string;
    };
}

const navGroups: NavGroupData[] = [
    {
        id: "content",
        label: "콘텐츠",
        icon: Sparkles,
        items: [
            { href: "/", label: "홈", icon: TrendingUp },
            { href: "/for-you", label: "추천", icon: Sparkles },
        ]
    },
    {
        id: "knowledge",
        label: "지식",
        icon: BookOpen,
        items: [
            { href: "/knowledge/hooks", label: "훅 라이브러리", icon: Zap },
            { href: "/knowledge/patterns", label: "패턴 분석", icon: BarChart3 },
            { href: "/boards", label: "실험 보드", icon: FlaskConical },
        ]
    },
    {
        id: "ops",
        label: "운영",
        icon: Radar,
        items: [
            { href: "/ops", label: "Ops Console", icon: Radar },
            { href: "/ops/outliers", label: "아웃라이어", icon: TrendingUp },
            { href: "/ops/canvas", label: "캔버스", icon: Network },
        ]
    }
];

const bottomItems: BottomItemData[] = [
    {
        id: "my",
        label: "마이페이지",
        icon: User,
        href: "/my",
        flyout: {
            title: "계정",
            items: [
                { label: "프로필", href: "/my" },
                { label: "로열티 내역", href: "/my/royalty" },
            ]
        }
    },
    {
        id: "kakao",
        label: "카카오톡 상담",
        icon: MessageCircle,
        href: "http://pf.kakao.com/_YxhVvj",
        external: true,
        flyout: {
            title: "고객 지원",
            description: "궁금한 점을 1:1로 상담하세요",
            cta: "상담 시작하기"
        }
    }
];

// ============================================
// Sub Components
// ============================================

interface FlyoutPanelProps {
    title: string;
    description?: string;
    items?: { label: string; href: string }[];
    cta?: string;
    ctaHref?: string;
    external?: boolean;
}

function FlyoutPanel({ title, description, items, cta, ctaHref, external }: FlyoutPanelProps) {
    return (
        <div className="w-56 bg-[#111] border border-white/10 rounded-xl shadow-2xl overflow-hidden">
            <div className="p-3 border-b border-white/10">
                <div className="font-bold text-white">{title}</div>
                {description && (
                    <div className="text-xs text-white/50 mt-1">{description}</div>
                )}
            </div>

            {items && items.length > 0 && (
                <div className="p-2">
                    {items.map((item) => (
                        <Link
                            key={item.href}
                            href={item.href}
                            className="flex items-center gap-2 px-3 py-2 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
                        >
                            {item.label}
                        </Link>
                    ))}
                </div>
            )}

            {cta && (
                <div className="p-3 border-t border-white/10">
                    {external ? (
                        <a
                            href={ctaHref}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center justify-center gap-2 w-full px-4 py-2 bg-[#FAE100] hover:bg-[#FFE812] text-black font-bold rounded-lg transition-colors"
                        >
                            {cta}
                            <ExternalLink className="w-3 h-3" />
                        </a>
                    ) : (
                        <Link
                            href={ctaHref || "#"}
                            className="flex items-center justify-center gap-2 w-full px-4 py-2 bg-violet-500 hover:bg-violet-400 text-white font-bold rounded-lg transition-colors"
                        >
                            {cta}
                        </Link>
                    )}
                </div>
            )}
        </div>
    );
}

interface NavGroupProps {
    group: NavGroupData;
    isExpanded: boolean;
    activeFlyoutId: string | null;
    onActivate: (id: string | null, rect: DOMRect | null) => void;
}

function NavGroup({ group, isExpanded, activeFlyoutId, onActivate }: NavGroupProps) {
    const pathname = usePathname();
    const groupRef = useRef<HTMLDivElement>(null);
    const [showTooltip, setShowTooltip] = useState(false);
    const [tooltipRect, setTooltipRect] = useState<DOMRect | null>(null);
    const tooltipTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    useEffect(() => {
        return () => {
            if (tooltipTimeoutRef.current) {
                clearTimeout(tooltipTimeoutRef.current);
                tooltipTimeoutRef.current = null;
            }
        };
    }, []);

    const isActive = group.items.some(
        item => pathname === item.href || pathname.startsWith(item.href + "/")
    );

    const isFlyoutActive = activeFlyoutId === group.id;

    const handleMouseEnter = () => {
        // Start tooltip delay timer
        if (!isExpanded && groupRef.current) {
            const rect = groupRef.current.getBoundingClientRect();
            setTooltipRect(rect);
            tooltipTimeoutRef.current = setTimeout(() => {
                setShowTooltip(true);
            }, 300); // 300ms delay for tooltip
        }
    };

    const handleMouseLeave = () => {
        // Clear tooltip
        if (tooltipTimeoutRef.current) {
            clearTimeout(tooltipTimeoutRef.current);
            tooltipTimeoutRef.current = null;
        }
        setShowTooltip(false);
        setTooltipRect(null);
    };

    const handleClick = () => {
        if (!isExpanded && groupRef.current) {
            if (isFlyoutActive) {
                onActivate(null, null);
            } else {
                onActivate(group.id, groupRef.current.getBoundingClientRect());
            }
        }
    };

    return (
        <div
            ref={groupRef}
            className="relative"
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
            onClick={handleClick}
        >
            {/* Group Icon (collapsed) or Label (expanded) */}
            {!isExpanded ? (
                <div
                    className={`w-full flex items-center justify-center px-3 py-2.5 rounded-lg transition-all cursor-pointer ${isActive || isFlyoutActive
                        ? "bg-violet-500/20 text-white"
                        : "text-white/60 hover:text-white hover:bg-white/10"
                        }`}
                >
                    <group.icon className="w-5 h-5 flex-shrink-0" />

                    {/* Delayed Tooltip - fixed position to escape overflow */}
                    {showTooltip && !isFlyoutActive && tooltipRect && (
                        <div
                            className="fixed px-3 py-2 bg-black/90 backdrop-blur-md border border-white/10 rounded-lg text-sm font-medium text-white whitespace-nowrap z-[9999] shadow-[0_0_20px_rgba(0,0,0,0.5)] pointer-events-none animate-in fade-in zoom-in-95 duration-200"
                            style={{
                                left: tooltipRect.right + 12,
                                top: tooltipRect.top + tooltipRect.height / 2,
                                transform: 'translateY(-50%)'
                            }}
                        >
                            {group.label}
                        </div>
                    )}
                </div>
            ) : (
                /* Expanded: Show sub-items inline without accordion */
                <div className="mb-4">
                    {/* Group Label as section header */}
                    <div className="px-3 py-2 text-[10px] font-bold text-white/30 uppercase tracking-widest">
                        {group.label}
                    </div>
                    {/* Sub-items */}
                    <div className="space-y-0.5">
                        {group.items.map((item) => {
                            const itemActive = pathname === item.href || pathname.startsWith(item.href + "/");
                            return (
                                <Link
                                    key={item.href}
                                    href={item.href}
                                    className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${itemActive
                                        ? "text-white bg-violet-500/20"
                                        : "text-white/60 hover:text-white hover:bg-white/5"
                                        }`}
                                >
                                    <item.icon className="w-4 h-4 flex-shrink-0" />
                                    <span className="truncate">{item.label}</span>
                                </Link>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
}

// ============================================
// Main Component
// ============================================

interface CollapsibleSidebarProps {
    isExpanded: boolean;
    onToggle: () => void;
}

export function CollapsibleSidebar({ isExpanded, onToggle }: CollapsibleSidebarProps) {
    const pathname = usePathname();
    const { user, isAuthenticated, logout } = useAuth();
    const [isLogoHovered, setIsLogoHovered] = useState(false);

    // Flyout State
    const [activeFlyout, setActiveFlyout] = useState<{ id: string; rect: DOMRect } | null>(null);

    const handleActivate = (id: string | null, rect: DOMRect | null) => {
        if (id && rect) {
            setActiveFlyout({ id, rect });
        } else {
            setActiveFlyout(null);
        }
    };

    // Close flyout when clicking outside
    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (activeFlyout && !(e.target as Element).closest('aside')) {
                setActiveFlyout(null);
            }
        };
        document.addEventListener('click', handleClickOutside);
        return () => document.removeEventListener('click', handleClickOutside);
    }, [activeFlyout]);


    // Find active group/item data for the flyout
    const activeGroup = navGroups.find(g => g.id === activeFlyout?.id);
    const activeBottom = bottomItems.find(b => b.id === activeFlyout?.id);

    return (
        <aside
            className={`fixed left-0 top-0 h-screen bg-black/90 backdrop-blur-xl border-r border-white/10 z-50 flex flex-col transition-all duration-300 ${isExpanded ? "w-52" : "w-14"
                }`}
            onMouseLeave={() => setActiveFlyout(null)}
        >
            {/* Logo Section */}
            <div className="p-3 border-b border-white/10">
                <button
                    onClick={onToggle}
                    onMouseEnter={() => setIsLogoHovered(true)}
                    onMouseLeave={() => setIsLogoHovered(false)}
                    className="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-white/10 transition-all group"
                >
                    <div className="w-8 h-8 flex items-center justify-center flex-shrink-0 relative">
                        {/* Gradient Definition for Icon Stroke */}
                        <svg width="0" height="0" className="absolute">
                            <defs>
                                <linearGradient id="k-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                    <stop offset="0%" stopColor="#a78bfa" />
                                    <stop offset="100%" stopColor="#f472b6" />
                                </linearGradient>
                            </defs>
                        </svg>

                        {isLogoHovered && !isExpanded ? (
                            <PanelLeftOpen
                                style={{ stroke: "url(#k-gradient)" }}
                                className="w-5 h-5 animate-pulse"
                            />
                        ) : (
                            <span className="font-black text-xl bg-gradient-to-br from-violet-400 to-pink-400 bg-clip-text text-transparent group-hover:scale-110 transition-transform">
                                K
                            </span>
                        )}
                    </div>
                    {isExpanded && (
                        <div className="flex items-center justify-between flex-1 pr-2 animate-fadeIn">
                            <span className="font-bold text-white whitespace-nowrap">Komission</span>
                            {isLogoHovered && (
                                <PanelLeftClose
                                    style={{ stroke: "url(#k-gradient)" }}
                                    className="w-5 h-5 animate-in fade-in slide-in-from-left-1 duration-200"
                                />
                            )}
                        </div>
                    )}
                </button>
            </div>

            {/* Navigation Groups */}
            <nav className="flex-1 p-2 space-y-1 overflow-y-auto overflow-x-hidden scrollbar-thin">
                {navGroups.map((group) => (
                    <NavGroup
                        key={group.id}
                        group={group}
                        isExpanded={isExpanded}
                        activeFlyoutId={activeFlyout?.id || null}
                        onActivate={handleActivate}
                    />
                ))}
            </nav>

            {/* Bottom Section */}
            <div className="p-2 border-t border-white/10 space-y-1">
                {bottomItems.map((item) => (
                    <div
                        key={item.id}
                        className="relative"
                    >
                        {item.external ? (
                            <a
                                href={item.href}
                                onClick={(e) => {
                                    if (!isExpanded && item.flyout) {
                                        e.preventDefault();
                                        if (activeFlyout?.id === item.id) {
                                            handleActivate(null, null);
                                        } else {
                                            handleActivate(item.id, e.currentTarget.getBoundingClientRect());
                                        }
                                    }
                                }}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors"
                            >
                                <item.icon className="w-5 h-5 flex-shrink-0" />
                                {isExpanded && (
                                    <span className="text-sm font-medium whitespace-nowrap animate-fadeIn">{item.label}</span>
                                )}
                            </a>
                        ) : (
                            <Link
                                href={item.href}
                                onClick={(e) => {
                                    // If collapsed and has flyout, toggle flyout instead of navigating
                                    if (!isExpanded && item.flyout) {
                                        e.preventDefault();
                                        if (activeFlyout?.id === item.id) {
                                            handleActivate(null, null);
                                        } else {
                                            handleActivate(item.id, e.currentTarget.getBoundingClientRect());
                                        }
                                    }
                                }}
                                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${pathname.startsWith(item.href)
                                    ? "bg-violet-500/20 text-white"
                                    : "text-white/60 hover:text-white hover:bg-white/10"
                                    }`}
                            >
                                <item.icon className="w-5 h-5 flex-shrink-0" />
                                {isExpanded && (
                                    <span className="text-sm font-medium whitespace-nowrap animate-fadeIn">{item.label}</span>
                                )}
                            </Link>
                        )}
                    </div>
                ))}

                {/* User Info - Clickable to profile */}
                {isAuthenticated && user && (
                    <div className="pt-2 border-t border-white/10 mt-2">
                        <Link
                            href="/my"
                            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors hover:bg-white/10 ${pathname === '/my' ? 'bg-violet-500/20' : ''
                                }`}
                        >
                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-pink-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                                {user.name?.charAt(0) || user.email?.charAt(0) || 'U'}
                            </div>
                            {isExpanded && (
                                <div className="overflow-hidden animate-fadeIn">
                                    <div className="text-sm font-medium text-white truncate">
                                        {user.name || "User"}
                                    </div>
                                    <div className="text-xs text-white/40 truncate">
                                        {user.k_points?.toLocaleString() ?? 0} K
                                    </div>
                                </div>
                            )}
                        </Link>
                    </div>
                )}
            </div>

            {/* Expand/Collapse Toggle */}
            <div className="p-2 border-t border-white/10">
                <button
                    onClick={onToggle}
                    className="w-full flex items-center justify-center p-2 rounded-lg text-white/40 hover:text-white hover:bg-white/10 transition-colors"
                >
                    {isExpanded ? (
                        <ChevronLeft className="w-5 h-5" />
                    ) : (
                        <ChevronRight className="w-5 h-5" />
                    )}
                </button>
            </div>

            {/* GLOBAL FLYOUT LAYER */}
            {!isExpanded && activeFlyout && (activeGroup || (activeBottom && activeBottom.flyout)) && (
                <div
                    className="fixed z-[100] animate-fadeIn pl-4" // pl-4 creates a safe buffer zone visually
                    style={{
                        top: activeFlyout.rect.top,
                        left: activeFlyout.rect.right, // Position exactly at the edge
                    }}
                >

                    {/* Render Active Group Flyout - Sub-items only, no title */}
                    {activeGroup && (
                        <div className="w-44 bg-[#111] border border-white/10 rounded-xl shadow-2xl overflow-hidden relative z-10">
                            <div className="p-1.5 space-y-0.5">
                                {activeGroup.items.map((item) => (
                                    <Link
                                        key={item.href}
                                        href={item.href}
                                        className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${pathname === item.href
                                            ? "text-white bg-violet-500/20"
                                            : "text-white/60 hover:text-white hover:bg-white/10"
                                            }`}
                                    >
                                        <item.icon className="w-4 h-4" />
                                        {item.label}
                                    </Link>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Render Active Bottom Flyout */}
                    {activeBottom && activeBottom.flyout && (
                        <div className="relative z-10">
                            <FlyoutPanel
                                title={activeBottom.flyout.title}
                                description={activeBottom.flyout.description}
                                items={activeBottom.flyout.items}
                                cta={activeBottom.flyout.cta}
                                ctaHref={activeBottom.href}
                                external={activeBottom.external}
                            />
                        </div>
                    )}
                </div>
            )}
        </aside>
    );
}
