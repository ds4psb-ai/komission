"use client";

import { AuthProvider } from '@/lib/auth';
import { SceneProvider } from '@/contexts/SceneContext';
import { WorkContextProvider } from '@/contexts/WorkContext';
import { ContextBar } from '@/components/ContextBar';
import { ReactNode } from 'react';

export function Providers({ children }: { children: ReactNode }) {
    return (
        <AuthProvider>
            <SceneProvider>
                <WorkContextProvider>
                    <ContextBar />
                    {children}
                </WorkContextProvider>
            </SceneProvider>
        </AuthProvider>
    );
}
