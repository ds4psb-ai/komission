"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { api } from '@/lib/api';

// ============ Types ============

export interface User {
    id: string;
    email: string;
    name: string | null;
    role: string;
    k_points: number;
    profile_image: string | null;
}

interface AuthState {
    user: User | null;
    token: string | null;
    isLoading: boolean;
    isAuthenticated: boolean;
}

interface AuthContextType extends AuthState {
    login: (googleCredential: string) => Promise<void>;
    logout: () => void;
    refreshUser: () => Promise<void>;
}

// ============ Context ============

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// ============ Provider ============

interface AuthProviderProps {
    children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
    const [state, setState] = useState<AuthState>({
        user: null,
        token: null,
        isLoading: true,
        isAuthenticated: false,
    });

    // Load token from localStorage on mount
    useEffect(() => {
        const storedToken = localStorage.getItem('access_token');
        if (storedToken) {
            setState(prev => ({ ...prev, token: storedToken }));
            fetchUser(storedToken);
        } else {
            setState(prev => ({ ...prev, isLoading: false }));
        }
    }, []);

    // Fetch user profile
    const fetchUser = async (token: string) => {
        try {
            api.setToken(token);
            const user = await api.getMe();
            setState({
                user,
                token,
                isLoading: false,
                isAuthenticated: true,
            });
        } catch (error) {
            console.error('Failed to fetch user:', error);
            // Token is invalid, clear it
            localStorage.removeItem('access_token');
            api.clearToken();
            setState({
                user: null,
                token: null,
                isLoading: false,
                isAuthenticated: false,
            });
        }
    };

    // Login with Google credential
    const login = useCallback(async (googleCredential: string) => {
        setState(prev => ({ ...prev, isLoading: true }));

        try {
            const response = await api.googleAuth(googleCredential);

            // Store token
            localStorage.setItem('access_token', response.access_token);
            api.setToken(response.access_token);

            setState({
                user: response.user,
                token: response.access_token,
                isLoading: false,
                isAuthenticated: true,
            });
        } catch (error) {
            console.error('Login failed:', error);
            setState(prev => ({ ...prev, isLoading: false }));
            throw error;
        }
    }, []);

    // Logout
    const logout = useCallback(() => {
        localStorage.removeItem('access_token');
        api.clearToken();

        setState({
            user: null,
            token: null,
            isLoading: false,
            isAuthenticated: false,
        });
    }, []);

    // Refresh user data
    const refreshUser = useCallback(async () => {
        if (state.token) {
            await fetchUser(state.token);
        }
    }, [state.token]);

    return (
        <AuthContext.Provider value={{
            ...state,
            login,
            logout,
            refreshUser,
        }}>
            {children}
        </AuthContext.Provider>
    );
}

// ============ Hook ============

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

// ============ Protected Route HOC ============

export function withAuth<P extends object>(
    WrappedComponent: React.ComponentType<P>,
    options?: { redirectTo?: string }
) {
    return function AuthenticatedComponent(props: P) {
        const { isAuthenticated, isLoading } = useAuth();

        if (isLoading) {
            return (
                <div className="min-h-screen bg-black flex items-center justify-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-violet-500" />
                </div>
            );
        }

        if (!isAuthenticated) {
            if (typeof window !== 'undefined') {
                window.location.href = options?.redirectTo || '/login';
            }
            return null;
        }

        return <WrappedComponent {...props} />;
    };
}
