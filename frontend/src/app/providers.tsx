"use client";

import { AuthProvider } from '@/lib/auth';
import { SceneProvider } from '@/contexts/SceneContext';
import { ConsentProvider } from '@/contexts/ConsentContext';
import { ReactNode } from 'react';

export function Providers({ children }: { children: ReactNode }) {
    return (
        <AuthProvider>
            <ConsentProvider>
                <SceneProvider>
                    {children}
                </SceneProvider>
            </ConsentProvider>
        </AuthProvider>
    );
}
