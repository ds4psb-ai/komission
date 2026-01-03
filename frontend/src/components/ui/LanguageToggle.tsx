'use client';

import { useTransition } from 'react';
import { useRouter } from 'next/navigation';

interface LanguageToggleProps {
    currentLocale: string;
    className?: string;
}

export function LanguageToggle({ currentLocale, className = '' }: LanguageToggleProps) {
    const router = useRouter();
    const [isPending, startTransition] = useTransition();

    const toggleLocale = () => {
        const newLocale = currentLocale === 'ko' ? 'en' : 'ko';

        // Set cookie
        document.cookie = `NEXT_LOCALE=${newLocale}; path=/; max-age=31536000`;

        // Refresh the page to apply new locale
        startTransition(() => {
            router.refresh();
        });
    };

    return (
        <button
            onClick={toggleLocale}
            disabled={isPending}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 hover:border-[#c1ff00]/30 transition-all text-sm font-medium ${isPending ? 'opacity-50 cursor-wait' : ''} ${className}`}
            aria-label={currentLocale === 'ko' ? 'Switch to English' : '한국어로 변경'}
        >
            <span className="text-[#c1ff00]">🌐</span>
            <span className="text-white/70">
                {currentLocale === 'ko' ? 'EN' : '한'}
            </span>
        </button>
    );
}

export default LanguageToggle;
