"use client";

/**
 * RoleContext - Creator/Business 역할 전환
 * 
 * 문서: docs/21_PAGE_IA_REDESIGN.md
 * - localStorage에 저장
 * - 전역 Context로 관리
 */
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export type UserRole = 'creator' | 'business';

interface RoleContextValue {
    role: UserRole;
    setRole: (role: UserRole) => void;
    toggleRole: () => void;
}

const RoleContext = createContext<RoleContextValue | null>(null);

const STORAGE_KEY = 'komission_user_role';

export function RoleProvider({ children }: { children: ReactNode }) {
    const [role, setRoleState] = useState<UserRole>('creator');
    const [isLoaded, setIsLoaded] = useState(false);

    // Load from localStorage on mount
    useEffect(() => {
        if (typeof window !== 'undefined') {
            const stored = localStorage.getItem(STORAGE_KEY);
            if (stored === 'business' || stored === 'creator') {
                setRoleState(stored);
            }
            setIsLoaded(true);
        }
    }, []);

    // Save to localStorage
    const setRole = (newRole: UserRole) => {
        setRoleState(newRole);
        if (typeof window !== 'undefined') {
            localStorage.setItem(STORAGE_KEY, newRole);
        }
    };

    const toggleRole = () => {
        setRole(role === 'creator' ? 'business' : 'creator');
    };

    // Prevent flash of wrong role
    if (!isLoaded) {
        return null;
    }

    return (
        <RoleContext.Provider value={{ role, setRole, toggleRole }}>
            {children}
        </RoleContext.Provider>
    );
}

export function useRole(): RoleContextValue {
    const context = useContext(RoleContext);
    if (!context) {
        throw new Error('useRole must be used within a RoleProvider');
    }
    return context;
}

export function useRoleOptional(): RoleContextValue | null {
    return useContext(RoleContext);
}

export default RoleContext;
