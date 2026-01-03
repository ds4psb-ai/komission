'use client';
import { useTranslations } from 'next-intl';

/**
 * AI Analysis Panel
 * MCP LLM Sampling을 활용한 AI 분석 결과 표시 컴포넌트
 */

import React, { useState } from 'react';
import { useAIAnalysis } from '@/lib/mcp-hooks';
import ReactMarkdown from 'react-markdown';

interface AIAnalysisPanelProps {
    outlierId: string;
    title?: string;
    onClose?: () => void;
}

type AnalysisType = 'recommendation' | 'shooting_guide' | 'risk';

const analysisTypeLabels: Record<AnalysisType, { label: string; icon: string; description: string }> = {
    recommendation: {
        label: '추천 분석',
        icon: '🎯',
        description: '왜 이 패턴이 성공했는지 분석',
    },
    shooting_guide: {
        label: '촬영 가이드',
        icon: '🎬',
        description: '재현을 위한 단계별 촬영 방법',
    },
    risk: {
        label: '리스크 분석',
        icon: '⚠️',
        description: '저작권, 정책 위반 등 잠재 위험',
    },
};

export function AIAnalysisPanel({ outlierId, title, onClose }: AIAnalysisPanelProps) {
    const [selectedType, setSelectedType] = useState<AnalysisType>('recommendation');
    const { data, loading, error, analyze, reset } = useAIAnalysis();

    const handleAnalyze = () => {
        analyze(outlierId, selectedType);
    };

    return (
        <div className="ai-analysis-panel">
            <div className="panel-header">
                <h3>🤖 AI 분석</h3>
                {title && <span className="panel-title">{title}</span>}
                {onClose && (
                    <button className="close-btn" onClick={onClose}>
                        ✕
                    </button>
                )}
            </div>

            {/* 분석 유형 선택 */}
            <div className="analysis-types">
                {(Object.keys(analysisTypeLabels) as AnalysisType[]).map((type) => {
                    const { label, icon, description } = analysisTypeLabels[type];
                    return (
                        <button
                            key={type}
                            className={`type-btn ${selectedType === type ? 'active' : ''}`}
                            onClick={() => setSelectedType(type)}
                            disabled={loading}
                        >
                            <span className="type-icon">{icon}</span>
                            <span className="type-label">{label}</span>
                            <span className="type-desc">{description}</span>
                        </button>
                    );
                })}
            </div>

            {/* 분석 실행 버튼 */}
            <div className="action-bar">
                <button
                    className="analyze-btn"
                    onClick={handleAnalyze}
                    disabled={loading}
                >
                    {loading ? (
                        <>
                            <span className="spinner" />
                            AI 분석 중...
                        </>
                    ) : (
                        <>
                            ✨ {analysisTypeLabels[selectedType].label} 시작
                        </>
                    )}
                </button>
                {data && (
                    <button className="reset-btn" onClick={reset}>
                        초기화
                    </button>
                )}
            </div>

            {/* 에러 표시 */}
            {error && (
                <div className="error-message">
                    <span>❌</span>
                    <p>{error}</p>
                </div>
            )}

            {/* 결과 표시 */}
            {data && (
                <div className="analysis-result">
                    <div className="result-header">
                        <span className="result-icon">{analysisTypeLabels[data.analysisType].icon}</span>
                        <span className="result-type">{analysisTypeLabels[data.analysisType].label}</span>
                    </div>
                    <div className="result-content">
                        <ReactMarkdown>{data.content}</ReactMarkdown>
                    </div>
                    <div className="result-footer">
                        <span className="powered-by">💡 MCP LLM Sampling으로 생성</span>
                    </div>
                </div>
            )}

            <style jsx>{`
                .ai-analysis-panel {
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    border-radius: 12px;
                    padding: 20px;
                    color: #fff;
                    max-width: 600px;
                }

                .panel-header {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    margin-bottom: 16px;
                }

                .panel-header h3 {
                    margin: 0;
                    font-size: 18px;
                }

                .panel-title {
                    font-size: 14px;
                    color: #888;
                    flex: 1;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }

                .close-btn {
                    background: none;
                    border: none;
                    color: #888;
                    cursor: pointer;
                    font-size: 18px;
                    padding: 4px 8px;
                }

                .close-btn:hover {
                    color: #fff;
                }

                .analysis-types {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                    margin-bottom: 16px;
                }

                .type-btn {
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

                .type-btn:hover:not(:disabled) {
                    background: rgba(255, 255, 255, 0.1);
                }

                .type-btn.active {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-color: transparent;
                }

                .type-btn:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }

                .type-icon {
                    font-size: 20px;
                }

                .type-label {
                    font-weight: 600;
                    min-width: 80px;
                }

                .type-desc {
                    font-size: 12px;
                    color: rgba(255, 255, 255, 0.7);
                }

                .action-bar {
                    display: flex;
                    gap: 8px;
                    margin-bottom: 16px;
                }

                .analyze-btn {
                    flex: 1;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                    padding: 12px 24px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border: none;
                    border-radius: 8px;
                    color: #fff;
                    font-weight: 600;
                    cursor: pointer;
                    transition: transform 0.2s, box-shadow 0.2s;
                }

                .analyze-btn:hover:not(:disabled) {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
                }

                .analyze-btn:disabled {
                    opacity: 0.7;
                    cursor: not-allowed;
                }

                .reset-btn {
                    padding: 12px 16px;
                    background: rgba(255, 255, 255, 0.1);
                    border: none;
                    border-radius: 8px;
                    color: #fff;
                    cursor: pointer;
                }

                .spinner {
                    display: inline-block;
                    width: 16px;
                    height: 16px;
                    border: 2px solid rgba(255, 255, 255, 0.3);
                    border-top-color: #fff;
                    border-radius: 50%;
                    animation: spin 0.8s linear infinite;
                }

                @keyframes spin {
                    to { transform: rotate(360deg); }
                }

                .error-message {
                    display: flex;
                    align-items: flex-start;
                    gap: 8px;
                    padding: 12px;
                    background: rgba(239, 68, 68, 0.1);
                    border: 1px solid rgba(239, 68, 68, 0.3);
                    border-radius: 8px;
                    margin-bottom: 16px;
                }

                .error-message p {
                    margin: 0;
                    font-size: 14px;
                    color: #fca5a5;
                }

                .analysis-result {
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
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                }

                .result-icon {
                    font-size: 20px;
                }

                .result-type {
                    font-weight: 600;
                }

                .result-content {
                    padding: 16px;
                    font-size: 14px;
                    line-height: 1.6;
                }

                .result-content :global(h1),
                .result-content :global(h2),
                .result-content :global(h3) {
                    margin: 16px 0 8px;
                    font-size: 16px;
                }

                .result-content :global(h1:first-child),
                .result-content :global(h2:first-child) {
                    margin-top: 0;
                }

                .result-content :global(ul),
                .result-content :global(ol) {
                    margin: 8px 0;
                    padding-left: 20px;
                }

                .result-content :global(li) {
                    margin: 4px 0;
                }

                .result-content :global(strong) {
                    color: #a5b4fc;
                }

                .result-content :global(blockquote) {
                    margin: 8px 0;
                    padding-left: 12px;
                    border-left: 3px solid #667eea;
                    color: rgba(255, 255, 255, 0.8);
                }

                .result-footer {
                    padding: 8px 16px;
                    border-top: 1px solid rgba(255, 255, 255, 0.1);
                    font-size: 12px;
                    color: rgba(255, 255, 255, 0.5);
                }

                .powered-by {
                    display: flex;
                    align-items: center;
                    gap: 4px;
                }
            `}</style>
        </div>
    );
}

export default AIAnalysisPanel;
