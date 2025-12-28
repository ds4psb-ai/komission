'use client';

/**
 * BottomNav - Role 기반 모바일 하단 네비게이션
 * 
 * 문서: docs/21_PAGE_IA_REDESIGN.md
 * - Creator 모드: Trending, For You, Shoot, My
 * - Business 모드: Patterns, Evidence, O2O, My
 */
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    TrendingUp, Sparkles, Camera, User,
    BarChart3, FileText, Gift
} from 'lucide-react';

// Role-based nav items
const CREATOR_NAV = [
    { href: '/trending', label: 'Trending', icon: TrendingUp },
    { href: '/for-you', label: 'For You', icon: Sparkles },
    { href: '/session/shoot', label: 'Shoot', icon: Camera },
    { href: '/my', label: 'My', icon: User },
];

const BUSINESS_NAV = [
    { href: '/for-you', label: 'Patterns', icon: BarChart3 },
    { href: '/boards', label: 'Evidence', icon: FileText },
    { href: '/o2o', label: 'O2O', icon: Gift },
    { href: '/my', label: 'My', icon: User },
];

interface BottomNavProps {
    role?: 'creator' | 'business';
}

export function BottomNav({ role = 'creator' }: BottomNavProps) {
    const pathname = usePathname();
    const navItems = role === 'business' ? BUSINESS_NAV : CREATOR_NAV;

    // Check for active state
    const isActive = (href: string) => {
        if (href === '/trending' && pathname === '/') return true;
        if (href === '/for-you' && pathname === '/for-you') return true;
        if (pathname === href) return true;
        if (href !== '/' && href !== '/for-you' && pathname.startsWith(href)) return true;
        return false;
    };

    return (
        <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-black/90 backdrop-blur-xl border-t border-white/10 safe-area-pb">
            <div className="flex items-center justify-around h-16">
                {navItems.map((item) => {
                    const active = isActive(item.href);

                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={`flex flex-col items-center justify-center gap-1 px-4 py-2 transition-all relative ${active
                                ? 'text-violet-400'
                                : 'text-white/40 hover:text-white/70'
                                }`}
                        >
                            <item.icon className={`w-5 h-5 ${active ? 'scale-110' : ''} transition-transform`} />
                            <span className="text-[10px] font-medium">{item.label}</span>
                            {active && (
                                <div className="absolute bottom-1 w-1 h-1 rounded-full bg-violet-400" />
                            )}
                        </Link>
                    );
                })}
            </div>
        </nav>
    );
}

export default BottomNav;
