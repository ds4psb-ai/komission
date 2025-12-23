"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { useState, useRef, useEffect } from "react";
import { Flame, Network, Puzzle, ShoppingBag, User, Wallet, LogOut } from 'lucide-react';

const navItems = [
    { href: "/", label: "아웃라이어", icon: Flame },
    { href: "/canvas", label: "캔버스", icon: Network },
    { href: "/pipelines", label: "템플릿", icon: Puzzle },
    { href: "/o2o", label: "마켓", icon: ShoppingBag },
    { href: "/my", label: "마이", icon: User },
];

export function AppHeader() {
    const pathname = usePathname();
    const router = useRouter();
    const { user, isAuthenticated, isLoading, logout } = useAuth();
    const [showDropdown, setShowDropdown] = useState(false);
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

    const handleLogout = () => {
        logout();
        setShowDropdown(false);
        router.push('/');
    };

    return (
        <header className="border-b border-white/10 sticky top-0 z-50 bg-black/80 backdrop-blur-xl">
            <div className="container mx-auto px-6 py-4 flex justify-between items-center">
                <Link
                    href="/"
                    className="text-2xl font-bold bg-gradient-to-r from-violet-400 to-pink-400 bg-clip-text text-transparent flex items-center gap-2"
                >
                    Komission
                </Link>

                <nav className="flex items-center gap-6 text-sm font-medium">
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
                                    <div className="absolute right-0 mt-2 w-56 bg-[#111] border border-white/10 rounded-xl shadow-2xl overflow-hidden">
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
            </div>
        </header>
    );
}
