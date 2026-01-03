"use client";
import { useTranslations } from 'next-intl';

import { Component, ReactNode } from "react";

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        console.error("ErrorBoundary caught an error:", error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                this.props.fallback || (
                    <ErrorDisplay
                        error={this.state.error}
                        onRetry={() => {
                            this.setState({ hasError: false, error: null });
                            window.location.reload();
                        }}
                    />
                )
            );
        }

        return this.props.children;
    }
}

function ErrorDisplay({ error, onRetry }: { error: Error | null, onRetry: () => void }) {
    const t = useTranslations('components.errorBoundary');
    return (
        <div className="min-h-screen bg-black flex items-center justify-center p-4">
            <div className="glass-panel rounded-3xl p-8 max-w-md text-center">
                <div className="text-6xl mb-4">😵</div>
                <h2 className="text-2xl font-bold text-white mb-2">{t('title')}</h2>
                <p className="text-white/60 mb-6">
                    {error?.message || t('unknown')}
                </p>
                <button
                    onClick={onRetry}
                    className="px-6 py-3 bg-violet-600 hover:bg-violet-500 text-white font-bold rounded-xl transition-colors"
                >
                    {t('retry')}
                </button>
            </div>
        </div>
    );
}
