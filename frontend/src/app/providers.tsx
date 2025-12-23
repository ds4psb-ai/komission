"use client";

import { AuthProvider } from '@/lib/auth';
import { SceneProvider } from '@/contexts/SceneContext';
import { WorkContextProvider } from '@/contexts/WorkContext';
import { ReactNode } from 'react';

export function Providers({ children }: { children: ReactNode }) {
    return (
        <AuthProvider>
            <SceneProvider>
                <WorkContextProvider>
                    {/* ContextBar removed - SessionHUD handles context display in remix layout */}
                    {children}
                </WorkContextProvider>
            </SceneProvider>
        </AuthProvider>
    );
}

