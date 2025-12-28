'use client';

/**
 * SubmissionReviewCard - Admin component for reviewing creator submissions
 * 
 * Phase 6 UX: Enables Guide → Experiment flow by allowing admin
 * to promote CreatorSubmission to OutlierItem for tracking.
 */

import { useState } from 'react';
import { api } from '@/lib/api';
import { CheckCircle, ExternalLink, Loader2, User, Calendar, Tag } from 'lucide-react';

interface SubmissionItem {
    id: string;
    pattern_id: string;
    video_url: string;
    platform: string;
    status: string;
    submitted_at: string;
}

interface SubmissionReviewCardProps {
    submission: SubmissionItem;
    onPromoted?: () => void;
}

export function SubmissionReviewCard({ submission, onPromoted }: SubmissionReviewCardProps) {
    const [promoting, setPromoting] = useState(false);
    const [promoted, setPromoted] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handlePromote = async () => {
        setPromoting(true);
        setError(null);

        try {
            const response = await fetch(`/api/v1/creator/submissions/${submission.id}/promote`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${api.getToken()}`,
                },
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Failed to promote');
            }

            setPromoted(true);
            onPromoted?.();
        } catch (e: any) {
            setError(e.message);
        } finally {
            setPromoting(false);
        }
    };

    const platformColors: Record<string, string> = {
        tiktok: 'bg-pink-500/20 text-pink-400',
        instagram: 'bg-purple-500/20 text-purple-400',
        youtube: 'bg-red-500/20 text-red-400',
    };

    const formatDate = (dateStr: string) => {
        return new Date(dateStr).toLocaleDateString('ko-KR', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    if (promoted) {
        return (
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl">
                <div className="flex items-center gap-2 text-emerald-400">
                    <CheckCircle className="w-5 h-5" />
                    <span className="font-medium">승격 완료 - 추적 시작됨</span>
                </div>
            </div>
        );
    }

    return (
        <div className="p-4 bg-slate-800/50 border border-white/10 rounded-xl space-y-3">
            {/* Header */}
            <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${platformColors[submission.platform] || 'bg-slate-500/20 text-slate-400'}`}>
                        {submission.platform}
                    </span>
                    <span className="text-xs text-white/40">
                        #{submission.id.slice(0, 8)}
                    </span>
                </div>
                <a
                    href={submission.video_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-1.5 hover:bg-white/10 rounded-lg transition-colors"
                >
                    <ExternalLink className="w-4 h-4 text-white/40" />
                </a>
            </div>

            {/* Pattern Info */}
            <div className="flex items-center gap-2 text-sm">
                <Tag className="w-4 h-4 text-violet-400" />
                <span className="text-white/80">{submission.pattern_id}</span>
            </div>

            {/* Submitted At */}
            <div className="flex items-center gap-2 text-xs text-white/50">
                <Calendar className="w-3.5 h-3.5" />
                <span>{formatDate(submission.submitted_at)}</span>
            </div>

            {/* Error Message */}
            {error && (
                <div className="text-xs text-red-400 bg-red-500/10 px-2 py-1 rounded">
                    {error}
                </div>
            )}

            {/* Actions */}
            <button
                onClick={handlePromote}
                disabled={promoting}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-white text-sm font-medium transition-colors"
            >
                {promoting ? (
                    <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        승격 중...
                    </>
                ) : (
                    <>
                        <CheckCircle className="w-4 h-4" />
                        승격하여 추적 시작
                    </>
                )}
            </button>
        </div>
    );
}
