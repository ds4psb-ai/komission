"use client";

import { AuthProvider } from '@/lib/auth';
import { SceneProvider } from '@/contexts/SceneContext';
import { ReactNode } from 'react';

export function Providers({ children }: { children: ReactNode }) {
    return (
        <AuthProvider>
            <SceneProvider>
                {children}
            </SceneProvider>
        </AuthProvider>
    );
}
