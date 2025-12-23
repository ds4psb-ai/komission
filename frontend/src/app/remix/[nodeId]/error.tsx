// frontend/src/app/remix/[nodeId]/error.tsx
"use client";

import { useEffect } from "react";
import Link from "next/link";

interface ErrorProps {
    error: Error & { digest?: string };
    reset: () => void;
}

export default function RemixError({ error, reset }: ErrorProps) {
    useEffect(() => {
        console.error("[RemixError]", error);
    }, [error]);

    return (
        <div className="flex items-center justify-center min-h-[60vh]">
            <div className="text-center max-w-md">
                <div className="text-6xl mb-4">😵</div>
                <h2 className="text-xl font-bold text-white mb-2">문제가 발생했습니다</h2>
                <p className="text-white/60 text-sm mb-6">
                    {error.message || "알 수 없는 오류가 발생했습니다."}
                </p>
                <div className="flex gap-3 justify-center">
                    <button
                        onClick={reset}
                        className="px-6 py-2 bg-violet-500 text-white font-bold rounded-lg hover:bg-violet-400 transition-colors"
                    >
                        다시 시도
                    </button>
                    <Link
                        href="/"
                        className="px-6 py-2 bg-white/10 text-white font-bold rounded-lg hover:bg-white/20 transition-colors"
                    >
                        홈으로
                    </Link>
                </div>
            </div>
        </div>
    );
}
