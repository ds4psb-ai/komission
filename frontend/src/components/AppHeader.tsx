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

const navItems = [
    { href: "/trending", label: "트렌딩", icon: TrendingUp },
    { href: "/for-you", label: "추천", icon: Sparkles },
    { href: "/boards", label: "실험", icon: FlaskConical },
    { href: "/knowledge/hooks", label: "훅", icon: Zap },
    { href: "/my", label: "마이", icon: User },
];

export function AppHeader() {
    const pathname = usePathname();
    const router = useRouter();
    const { user, isAuthenticated, isLoading, logout } = useAuth();
    const [showDropdown, setShowDropdown] = useState(false);
    const [showMobileMenu, setShowMobileMenu] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

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

    const handleLogout = () => {
        logout();
        setShowDropdown(false);
        setShowMobileMenu(false);
        router.push('/');
    };

    return (
        <>
            <header className="border-b border-white/10 sticky top-0 z-50 bg-black/80 backdrop-blur-xl">
                <div className="container mx-auto px-4 md:px-6 py-3 md:py-4 flex justify-between items-center">
                    {/* Logo */}
                    <Link
                        href="/"
                        className="text-xl md:text-2xl font-bold bg-gradient-to-r from-violet-400 to-pink-400 bg-clip-text text-transparent flex items-center gap-2"
                    >
                        Komission
                    </Link>

                    {/* Desktop Navigation */}
                    <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
                        {navItems.map((item) => {
                            const isActive = pathname === item.href ||
                                (item.href !== "/" && pathname.startsWith(item.href));

                            return (
                                <Link
                                    key={item.href}
                                    href={item.href}
                                    className={`transition-colors ${isActive
                                        ? "text-white"
                                        : "text-white/60 hover:text-white"
                                        }`}
                                >
                                    <span className="flex items-center gap-1.5">
                                        <item.icon className="w-3.5 h-3.5" />
                                        {item.label}
                                    </span>
                                </Link>
                            );
                        })}

                        {/* Auth Section */}
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
                                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-pink-500 flex items-center justify-center text-white text-sm font-bold">
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
                                    className="px-4 py-2 bg-violet-500 hover:bg-violet-400 rounded-lg text-white text-sm font-bold transition-colors"
                                >
                                    로그인
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
                                className="px-3 py-1.5 bg-violet-500 rounded-lg text-white text-sm font-bold"
                            >
                                로그인
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
            </header>

            {/* Mobile Menu Overlay */}
            {showMobileMenu && (
                <div className="md:hidden fixed inset-0 z-40 bg-black/95 backdrop-blur-xl animate-fadeIn">
                    <div className="pt-20 px-6">
                        <nav className="space-y-2">
                            {navItems.map((item) => {
                                const isActive = pathname === item.href ||
                                    (item.href !== "/" && pathname.startsWith(item.href));

                                return (
                                    <Link
                                        key={item.href}
                                        href={item.href}
                                        onClick={() => setShowMobileMenu(false)}
                                        className={`flex items-center gap-3 px-4 py-4 rounded-xl text-lg font-medium transition-all ${isActive
                                            ? "bg-violet-500/20 text-white border border-violet-500/50"
                                            : "text-white/60 hover:text-white hover:bg-white/5"
                                            }`}
                                    >
                                        <item.icon className="w-5 h-5" />
                                        {item.label}
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
            )}
        </>
    );
}
