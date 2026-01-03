"use client";

/**
 * AppHeader with Mobile Navigation (PEGL v1.0)
 * 
 * Features:
 * - Responsive navigation
 * - Mobile hamburger menu
 * - User dropdown
 * - Role Switch (Creator ↔ Business)
 * - Ops Console link
 * - Language Toggle (i18n)
 */
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { useRoleOptional } from "@/contexts/RoleContext";
import { useState, useRef, useEffect } from "react";
import {
    Network, User, Wallet, LogOut, Radar, FlaskConical,
    Zap, BookOpen, Sparkles, Menu, X, TrendingUp, BarChart3
} from 'lucide-react';
import { useTranslations, useLocale } from 'next-intl';
import { LanguageToggle } from '@/components/ui/LanguageToggle';

// Nav items with translation keys
const navItemKeys = [
    { href: "/", labelKey: "home", icon: TrendingUp },
    { href: "/for-you", labelKey: "forYou", icon: Sparkles },
    { href: "/boards", labelKey: "boards", icon: FlaskConical },
    { href: "/knowledge/hooks", labelKey: "hookPatterns", icon: Zap },
    { href: "/my", labelKey: "myPage", icon: User },
];

export function AppHeader() {
    const pathname = usePathname();
    const router = useRouter();
    const { user, isAuthenticated, isLoading, logout } = useAuth();
    const [showDropdown, setShowDropdown] = useState(false);
    const [showMobileMenu, setShowMobileMenu] = useState(false);
    const [isScrolled, setIsScrolled] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    // i18n hooks
    const t = useTranslations('sidebar');
    const tCommon = useTranslations('common');
    const locale = useLocale();

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setShowDropdown(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Close mobile menu on route change
    useEffect(() => {
        setShowMobileMenu(false);
    }, [pathname]);

    // Scroll effect for header
    useEffect(() => {
        const handleScroll = () => {
            setIsScrolled(window.scrollY > 50);
        };
        window.addEventListener('scroll', handleScroll, { passive: true });
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const handleLogout = () => {
        logout();
        setShowDropdown(false);
        setShowMobileMenu(false);
        router.push('/');
    };

    return (
        <>
            <header className={`sticky top-0 z-50 transition-all duration-300 ${isScrolled
                ? 'bg-black/80 backdrop-blur-xl border-b border-[#c1ff00]/20 shadow-[0_4px_30px_rgba(0,0,0,0.5)]'
                : 'bg-transparent border-b border-transparent'
                }`}>
                <div className="container mx-auto px-4 md:px-6 py-3 md:py-4 flex justify-between items-center">
                    {/* Logo */}
                    <Link
                        href="/"
                        className="text-xl md:text-2xl font-black italic tracking-tighter text-[#c1ff00] flex items-center gap-2"
                    >
                        KOMISSION
                    </Link>

                    {/* Desktop Navigation */}
                    <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
                        {navItemKeys.map((item) => {
                            const isActive = pathname === item.href ||
                                (item.href !== "/" && pathname.startsWith(item.href));

                            return (
                                <Link
                                    key={item.href}
                                    href={item.href}
                                    className={`transition-all duration-300 font-bold tracking-wide uppercase text-xs ${isActive
                                        ? "text-[#c1ff00] drop-shadow-[0_0_8px_rgba(193,255,0,0.5)]"
                                        : "text-white/40 hover:text-white"
                                        }`}
                                >
                                    <span className="flex items-center gap-1.5">
                                        <item.icon className="w-3.5 h-3.5" />
                                        {t(item.labelKey)}
                                    </span>
                                </Link>
                            );
                        })}

                        {/* Language Toggle */}
                        <LanguageToggle currentLocale={locale} />
                        <div className="ml-4 pl-4 border-l border-white/10">
                            {isLoading ? (
                                <div className="w-8 h-8 rounded-full bg-white/10 animate-pulse" />
                            ) : isAuthenticated && user ? (
                                <div className="relative" ref={dropdownRef}>
                                    <button
                                        onClick={() => setShowDropdown(!showDropdown)}
                                        className="flex items-center gap-2 hover:opacity-80 transition-opacity"
                                    >
                                        {user.profile_image ? (
                                            <img
                                                src={user.profile_image}
                                                alt={user.name || 'Profile'}
                                                className="w-8 h-8 rounded-full border border-white/20"
                                            />
                                        ) : (
                                            <div className="w-8 h-8 rounded-full bg-[#c1ff00] flex items-center justify-center text-black text-sm font-bold shadow-[0_0_10px_rgba(193,255,0,0.3)]">
                                                {(user.name || user.email)?.[0]?.toUpperCase() || '?'}
                                            </div>
                                        )}
                                        <span className="text-white/60 text-xs hidden sm:block">
                                            {user.k_points.toLocaleString()} K
                                        </span>
                                    </button>

                                    {/* Dropdown Menu */}
                                    {showDropdown && (
                                        <div className="absolute right-0 mt-2 w-56 bg-[#111] border border-white/10 rounded-xl shadow-2xl overflow-hidden animate-fadeIn">
                                            <div className="p-4 border-b border-white/10">
                                                <div className="font-bold text-white truncate">
                                                    {user.name || 'User'}
                                                </div>
                                                <div className="text-xs text-white/40 truncate">
                                                    {user.email}
                                                </div>
                                            </div>
                                            <div className="p-2">
                                                <Link
                                                    href="/my"
                                                    className="block px-4 py-2 rounded-lg text-white/60 hover:text-white hover:bg-white/5 transition-colors"
                                                    onClick={() => setShowDropdown(false)}
                                                >
                                                    <span className="flex items-center gap-2"><User className="w-4 h-4" /> 마이페이지</span>
                                                </Link>
                                                <Link
                                                    href="/my/royalty"
                                                    className="block px-4 py-2 rounded-lg text-white/60 hover:text-white hover:bg-white/5 transition-colors"
                                                    onClick={() => setShowDropdown(false)}
                                                >
                                                    <span className="flex items-center gap-2"><Wallet className="w-4 h-4" /> 로열티 내역</span>
                                                </Link>
                                                <Link
                                                    href="/ops"
                                                    className="block px-4 py-2 rounded-lg text-white/60 hover:text-white hover:bg-white/5 transition-colors"
                                                    onClick={() => setShowDropdown(false)}
                                                >
                                                    <span className="flex items-center gap-2"><Radar className="w-4 h-4" /> Ops Console</span>
                                                </Link>
                                                <button
                                                    onClick={handleLogout}
                                                    className="w-full text-left px-4 py-2 rounded-lg text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors"
                                                >
                                                    <span className="flex items-center gap-2"><LogOut className="w-4 h-4" /> 로그아웃</span>
                                                </button>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <Link
                                    href="/login"
                                    className="px-5 py-2 bg-[#c1ff00] hover:bg-[#b0e600] rounded-full text-black text-xs font-black uppercase tracking-wider transition-all hover:scale-105 shadow-[0_0_15px_rgba(193,255,0,0.3)]"
                                >
                                    LOGIN
                                </Link>
                            )}
                        </div>
                    </nav>

                    {/* Mobile Menu Button */}
                    <div className="flex md:hidden items-center gap-3">
                        {/* Mobile Auth */}
                        {isAuthenticated && user ? (
                            <Link href="/my">
                                {user.profile_image ? (
                                    <img
                                        src={user.profile_image}
                                        alt={user.name || 'Profile'}
                                        className="w-8 h-8 rounded-full border border-white/20"
                                    />
                                ) : (
                                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-pink-500 flex items-center justify-center text-white text-sm font-bold">
                                        {(user.name || user.email)?.[0]?.toUpperCase() || '?'}
                                    </div>
                                )}
                            </Link>
                        ) : (
                            <Link
                                href="/login"
                                className="px-3 py-1.5 bg-[#c1ff00] rounded-full text-black text-xs font-black uppercase"
                            >
                                LOGIN
                            </Link>
                        )}

                        {/* Hamburger */}
                        <button
                            onClick={() => setShowMobileMenu(!showMobileMenu)}
                            className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                        >
                            {showMobileMenu ? (
                                <X className="w-6 h-6 text-white" />
                            ) : (
                                <Menu className="w-6 h-6 text-white" />
                            )}
                        </button>
                    </div>
                </div>
            </header >

            {/* Mobile Menu Overlay */}
            {
                showMobileMenu && (
                    <div className="md:hidden fixed inset-0 z-40 bg-black/95 backdrop-blur-xl animate-fadeIn">
                        <div className="pt-20 px-6">
                            <nav className="space-y-2">
                                {navItemKeys.map((item) => {
                                    const isActive = pathname === item.href ||
                                        (item.href !== "/" && pathname.startsWith(item.href));

                                    return (
                                        <Link
                                            key={item.href}
                                            href={item.href}
                                            onClick={() => setShowMobileMenu(false)}
                                            className={`flex items-center gap-3 px-4 py-4 rounded-xl text-lg font-black uppercase tracking-wider transition-all ${isActive
                                                ? "text-[#c1ff00] bg-white/5"
                                                : "text-white/40 hover:text-white hover:bg-white/5"
                                                }`}
                                        >
                                            <item.icon className="w-5 h-5" />
                                            {t(item.labelKey)}
                                        </Link>
                                    );
                                })}
                            </nav>

                            {/* Mobile User Section */}
                            {isAuthenticated && user && (
                                <div className="mt-8 pt-8 border-t border-white/10">
                                    <div className="flex items-center gap-3 mb-6">
                                        {user.profile_image ? (
                                            <img
                                                src={user.profile_image}
                                                alt={user.name || 'Profile'}
                                                className="w-12 h-12 rounded-full border border-white/20"
                                            />
                                        ) : (
                                            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-violet-500 to-pink-500 flex items-center justify-center text-white text-xl font-bold">
                                                {(user.name || user.email)?.[0]?.toUpperCase() || '?'}
                                            </div>
                                        )}
                                        <div>
                                            <div className="font-bold text-white">{user.name || 'User'}</div>
                                            <div className="text-sm text-violet-400">{user.k_points.toLocaleString()} K Points</div>
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        <Link
                                            href="/my/royalty"
                                            onClick={() => setShowMobileMenu(false)}
                                            className="flex items-center gap-3 px-4 py-3 rounded-xl text-white/60 hover:text-white hover:bg-white/5 transition-colors"
                                        >
                                            <Wallet className="w-5 h-5" />
                                            로열티 내역
                                        </Link>
                                        <Link
                                            href="/ops"
                                            onClick={() => setShowMobileMenu(false)}
                                            className="flex items-center gap-3 px-4 py-3 rounded-xl text-white/60 hover:text-white hover:bg-white/5 transition-colors"
                                        >
                                            <Radar className="w-5 h-5" />
                                            Ops Console
                                        </Link>
                                        <button
                                            onClick={handleLogout}
                                            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-red-400 hover:bg-red-500/10 transition-colors"
                                        >
                                            <LogOut className="w-5 h-5" />
                                            로그아웃
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )
            }
        </>
    );
}
