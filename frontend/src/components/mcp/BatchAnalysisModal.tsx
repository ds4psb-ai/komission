'use client';
import { useTranslations } from 'next-intl';

/**
 * Batch Analysis Modal
 * 여러 아웃라이어의 트렌드 분석을 위한 모달 컴포넌트
 */

import React, { useState } from 'react';
import { useBatchAnalysis } from '@/lib/mcp-hooks';
import ReactMarkdown from 'react-markdown';

interface BatchAnalysisModalProps {
    selectedIds: string[];
    onClose: () => void;
}

type SummaryFocus = 'trends' | 'comparison' | 'strategy';

const focusOptions: Record<SummaryFocus, { label: string; icon: string; description: string }> = {
    trends: {
        label: '트렌드 분석',
        icon: '📈',
        description: '공통 패턴과 현재 트렌드 파악',
    },
    comparison: {
        label: '비교 분석',
        icon: '⚖️',
        description: '콘텐츠 간 성과 비교 및 차별점',
    },
    strategy: {
        label: '전략 제안',
        icon: '🎯',
        description: '즉시 적용 가능한 콘텐츠 전략',
    },
};

export function BatchAnalysisModal({ selectedIds, onClose }: BatchAnalysisModalProps) {
    const [focus, setFocus] = useState<SummaryFocus>('trends');
    const { data, loading, error, analyze } = useBatchAnalysis();

    const handleAnalyze = () => {
        analyze(selectedIds, focus);
    };

    const isValid = selectedIds.length >= 2 && selectedIds.length <= 10;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>📊 AI 배치 분석</h2>
                    <button className="close-btn" onClick={onClose}>✕</button>
                </div>

                <div className="selection-info">
                    <span className="count">{selectedIds.length}개</span>
                    <span className="label">아웃라이어 선택됨</span>
                    {!isValid && (
                        <span className="warning">
                            {selectedIds.length < 2 ? '* 최소 2개 필요' : '* 최대 10개까지'}
                        </span>
                    )}
                </div>

                {/* 분석 초점 선택 */}
                <div className="focus-options">
                    {(Object.keys(focusOptions) as SummaryFocus[]).map((f) => {
                        const { label, icon, description } = focusOptions[f];
                        return (
                            <button
                                key={f}
                                className={`focus-btn ${focus === f ? 'active' : ''}`}
                                onClick={() => setFocus(f)}
                                disabled={loading}
                            >
                                <span className="focus-icon">{icon}</span>
                                <div className="focus-text">
                                    <span className="focus-label">{label}</span>
                                    <span className="focus-desc">{description}</span>
                                </div>
                            </button>
                        );
                    })}
                </div>

                {/* 분석 버튼 */}
                <button
                    className="analyze-btn"
                    onClick={handleAnalyze}
                    disabled={loading || !isValid}
                >
                    {loading ? (
                        <>
                            <span className="spinner" />
                            AI가 분석 중...
                        </>
                    ) : (
                        <>✨ {focusOptions[focus].label} 시작</>
                    )}
                </button>

                {/* 에러 */}
                {error && (
                    <div className="error-box">
                        <span>❌</span>
                        <p>{error}</p>
                    </div>
                )}

                {/* 결과 */}
                {data && (
                    <div className="result-box">
                        <div className="result-header">
                            <span>{focusOptions[data.summaryFocus].icon}</span>
                            <span>{focusOptions[data.summaryFocus].label}</span>
                            <span className="result-count">({data.outlierCount}개 분석)</span>
                        </div>
                        <div className="result-content">
                            <ReactMarkdown>{data.content}</ReactMarkdown>
                        </div>
                    </div>
                )}

                <style jsx>{`
                    .modal-overlay {
                        position: fixed;
                        inset: 0;
                        background: rgba(0, 0, 0, 0.7);
                        backdrop-filter: blur(4px);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        z-index: 1000;
                    }

                    .modal-content {
                        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                        border-radius: 16px;
                        padding: 24px;
                        width: 90%;
                        max-width: 600px;
                        max-height: 80vh;
                        overflow-y: auto;
                        color: #fff;
                    }

                    .modal-header {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 16px;
                    }

                    .modal-header h2 {
                        margin: 0;
                        font-size: 20px;
                    }

                    .close-btn {
                        background: none;
                        border: none;
                        color: #888;
                        font-size: 20px;
                        cursor: pointer;
                    }

                    .selection-info {
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        padding: 12px 16px;
                        background: rgba(102, 126, 234, 0.1);
                        border-radius: 8px;
                        margin-bottom: 16px;
                    }

                    .count {
                        font-size: 24px;
                        font-weight: 700;
                        color: #667eea;
                    }

                    .label {
                        color: rgba(255, 255, 255, 0.7);
                    }

                    .warning {
                        margin-left: auto;
                        color: #fbbf24;
                        font-size: 12px;
                    }

                    .focus-options {
                        display: flex;
                        flex-direction: column;
                        gap: 8px;
                        margin-bottom: 16px;
                    }

                    .focus-btn {
                        display: flex;
                        align-items: center;
                        gap: 12px;
                        padding: 12px 16px;
                        background: rgba(255, 255, 255, 0.05);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        border-radius: 8px;
                        color: #fff;
                        cursor: pointer;
                        transition: all 0.2s;
                        text-align: left;
                    }

                    .focus-btn:hover:not(:disabled) {
                        background: rgba(255, 255, 255, 0.1);
                    }

                    .focus-btn.active {
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        border-color: transparent;
                    }

                    .focus-icon {
                        font-size: 24px;
                    }

                    .focus-text {
                        display: flex;
                        flex-direction: column;
                        gap: 2px;
                    }

                    .focus-label {
                        font-weight: 600;
                    }

                    .focus-desc {
                        font-size: 12px;
                        color: rgba(255, 255, 255, 0.7);
                    }

                    .analyze-btn {
                        width: 100%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 8px;
                        padding: 14px 24px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        border: none;
                        border-radius: 8px;
                        color: #fff;
                        font-size: 16px;
                        font-weight: 600;
                        cursor: pointer;
                        margin-bottom: 16px;
                    }

                    .analyze-btn:disabled {
                        opacity: 0.5;
                        cursor: not-allowed;
                    }

                    .spinner {
                        width: 18px;
                        height: 18px;
                        border: 2px solid rgba(255, 255, 255, 0.3);
                        border-top-color: #fff;
                        border-radius: 50%;
                        animation: spin 0.8s linear infinite;
                    }

                    @keyframes spin {
                        to { transform: rotate(360deg); }
                    }

                    .error-box {
                        display: flex;
                        gap: 8px;
                        padding: 12px;
                        background: rgba(239, 68, 68, 0.1);
                        border-radius: 8px;
                        margin-bottom: 16px;
                    }

                    .error-box p {
                        margin: 0;
                        color: #fca5a5;
                    }

                    .result-box {
                        background: rgba(255, 255, 255, 0.05);
                        border-radius: 8px;
                        overflow: hidden;
                    }

                    .result-header {
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        padding: 12px 16px;
                        background: rgba(255, 255, 255, 0.05);
                        font-weight: 600;
                    }

                    .result-count {
                        font-weight: 400;
                        color: rgba(255, 255, 255, 0.5);
                        font-size: 14px;
                    }

                    .result-content {
                        padding: 16px;
                        font-size: 14px;
                        line-height: 1.6;
                    }

                    .result-content :global(h1),
                    .result-content :global(h2),
                    .result-content :global(h3) {
                        font-size: 16px;
                        margin: 16px 0 8px;
                    }

                    .result-content :global(ul),
                    .result-content :global(ol) {
                        padding-left: 20px;
                    }
                `}</style>
            </div>
        </div>
    );
}

export default BatchAnalysisModal;
