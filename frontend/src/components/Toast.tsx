"use client";

import React, { createContext, useContext, useState, useCallback, ReactNode, useEffect, useRef } from 'react';

// --- Types ---
type ToastType = 'success' | 'error' | 'info' | 'warning';

interface Toast {
    id: string;
    message: string;
    type: ToastType;
}

interface ToastContextValue {
    showToast: (message: string, type?: ToastType) => void;
}

// --- Context ---
const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast() {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error('useToast must be used within ToastProvider');
    }
    return context;
}

// --- Provider ---
export function ToastProvider({ children }: { children: ReactNode }) {
    const [toasts, setToasts] = useState<Toast[]>([]);
    const timeoutsRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

    const showToast = useCallback((message: string, type: ToastType = 'info') => {
        const id = typeof crypto !== 'undefined' && 'randomUUID' in crypto
            ? crypto.randomUUID()
            : `toast_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
        setToasts(prev => [...prev, { id, message, type }]);

        // Auto remove after 3 seconds
        const timeoutId = setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id));
            timeoutsRef.current.delete(id);
        }, 3000);
        timeoutsRef.current.set(id, timeoutId);
    }, []);

    const removeToast = useCallback((id: string) => {
        const timeoutId = timeoutsRef.current.get(id);
        if (timeoutId) {
            clearTimeout(timeoutId);
            timeoutsRef.current.delete(id);
        }
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);

    useEffect(() => {
        return () => {
            timeoutsRef.current.forEach(clearTimeout);
            timeoutsRef.current.clear();
        };
    }, []);

    return (
        <ToastContext.Provider value={{ showToast }}>
            {children}

            {/* Toast Container */}
            <div className="fixed bottom-6 right-6 z-[9999] flex flex-col gap-2 pointer-events-none">
                {toasts.map(toast => (
                    <div
                        key={toast.id}
                        onClick={() => removeToast(toast.id)}
                        className={`
                            pointer-events-auto cursor-pointer
                            px-4 py-3 rounded-xl shadow-2xl
                            flex items-center gap-3
                            transform transition-all duration-300
                            animate-slide-in
                            ${toast.type === 'success' ? 'bg-emerald-500/90 text-white' : ''}
                            ${toast.type === 'error' ? 'bg-red-500/90 text-white' : ''}
                            ${toast.type === 'info' ? 'bg-blue-500/90 text-white' : ''}
                            ${toast.type === 'warning' ? 'bg-amber-500/90 text-black' : ''}
                        `}
                    >
                        <span className="text-lg">
                            {toast.type === 'success' && '✓'}
                            {toast.type === 'error' && '✕'}
                            {toast.type === 'info' && 'ℹ'}
                            {toast.type === 'warning' && '⚠'}
                        </span>
                        <span className="font-medium text-sm">{toast.message}</span>
                    </div>
                ))}
            </div>
        </ToastContext.Provider>
    );
}
