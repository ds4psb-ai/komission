"use client";

/**
 * ConsentContext - MCP Tool 동의 상태 관리
 * 
 * 제공 기능:
 * - requestConsent(): 동의 요청 모달 표시
 * - executeWithConsent(): 동의 후 자동 실행
 * - consentHistory: 동의 이력 조회
 */
import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import ConsentModal, { ConsentAction, ConsentType } from '@/components/ConsentModal';

// MCP Tool 정의 (동의 필요 Tool만)
export const MCP_TOOLS: Record<string, ConsentAction> = {
    generate_source_pack: {
        id: 'generate_source_pack',
        name: 'Source Pack 생성',
        description: 'NotebookLM 소스팩을 생성합니다. 선택한 패턴 데이터가 포함됩니다.',
        type: 'data_creation',
        details: [
            '선택한 Outlier 데이터가 팩에 포함됩니다',
            '생성된 팩은 NotebookLM에서 사용 가능합니다',
            '팩 데이터는 서버에 저장됩니다',
        ],
    },
    reanalyze_vdg: {
        id: 'reanalyze_vdg',
        name: 'VDG 재분석',
        description: 'Video DNA Genome 분석을 다시 수행합니다. API 비용이 발생합니다.',
        type: 'cost_incur',
        estimatedCost: '~$0.05-0.10 / 영상',
        details: [
            'Gemini Video API 호출',
            '분석 완료까지 5-10분 소요',
            '기존 분석 결과가 덮어쓰기됩니다',
        ],
    },
};

interface ConsentHistoryItem {
    actionId: string;
    timestamp: Date;
    consented: boolean;
}

interface ConsentContextValue {
    // 동의 요청
    requestConsent: (actionId: string, customAction?: Partial<ConsentAction>) => Promise<boolean>;

    // 동의 후 실행
    executeWithConsent: <T>(
        actionId: string,
        executor: () => Promise<T>,
        customAction?: Partial<ConsentAction>
    ) => Promise<T | null>;

    // 이력
    consentHistory: ConsentHistoryItem[];

    // 상태
    isPending: boolean;
}

const ConsentContext = createContext<ConsentContextValue | null>(null);

export function ConsentProvider({ children }: { children: ReactNode }) {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [currentAction, setCurrentAction] = useState<ConsentAction | null>(null);
    const [isPending, setIsPending] = useState(false);
    const [resolver, setResolver] = useState<((value: boolean) => void) | null>(null);
    const [consentHistory, setConsentHistory] = useState<ConsentHistoryItem[]>([]);

    // 동의 요청
    const requestConsent = useCallback((
        actionId: string,
        customAction?: Partial<ConsentAction>
    ): Promise<boolean> => {
        return new Promise((resolve) => {
            const baseAction = MCP_TOOLS[actionId] || {
                id: actionId,
                name: actionId,
                description: 'Unknown action',
                type: 'external_api' as ConsentType,
            };

            const action: ConsentAction = {
                ...baseAction,
                ...customAction,
            };

            setCurrentAction(action);
            setIsModalOpen(true);
            setResolver(() => resolve);
        });
    }, []);

    // 모달 확인
    const handleConfirm = useCallback(() => {
        if (currentAction) {
            setConsentHistory(prev => [...prev, {
                actionId: currentAction.id,
                timestamp: new Date(),
                consented: true,
            }]);
        }

        setIsModalOpen(false);
        resolver?.(true);
        setResolver(null);
        setCurrentAction(null);
    }, [currentAction, resolver]);

    // 모달 취소
    const handleCancel = useCallback(() => {
        if (currentAction) {
            setConsentHistory(prev => [...prev, {
                actionId: currentAction.id,
                timestamp: new Date(),
                consented: false,
            }]);
        }

        setIsModalOpen(false);
        resolver?.(false);
        setResolver(null);
        setCurrentAction(null);
    }, [currentAction, resolver]);

    // 동의 후 실행
    const executeWithConsent = useCallback(async <T,>(
        actionId: string,
        executor: () => Promise<T>,
        customAction?: Partial<ConsentAction>
    ): Promise<T | null> => {
        const consented = await requestConsent(actionId, customAction);

        if (!consented) {
            return null;
        }

        setIsPending(true);
        try {
            const result = await executor();
            return result;
        } finally {
            setIsPending(false);
        }
    }, [requestConsent]);

    const value: ConsentContextValue = {
        requestConsent,
        executeWithConsent,
        consentHistory,
        isPending,
    };

    return (
        <ConsentContext.Provider value={value}>
            {children}
            <ConsentModal
                isOpen={isModalOpen}
                action={currentAction}
                onConfirm={handleConfirm}
                onCancel={handleCancel}
                isLoading={isPending}
            />
        </ConsentContext.Provider>
    );
}

export function useConsent(): ConsentContextValue {
    const context = useContext(ConsentContext);
    if (!context) {
        throw new Error('useConsent must be used within a ConsentProvider');
    }
    return context;
}

export default ConsentContext;
