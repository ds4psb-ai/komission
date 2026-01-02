'use client';

import React, { useEffect, useState } from 'react';

/**
 * TextCoachBubble - 텍스트 코칭 컴포넌트
 * 
 * 오디오 대신 텍스트로 조용히 가이드 제공
 * 촬영 중 잡음 방지 + 빠른 피드백
 */

interface TextCoachBubbleProps {
    /** 메시지 내용 */
    message: string;

    /** 표시 시간 (ms) */
    duration?: number;

    /** 스타일 */
    style?: 'minimal' | 'prominent' | 'toast';

    /** 우선순위 (색상 결정) */
    priority?: 'critical' | 'high' | 'medium' | 'low';

    /** 위치 */
    position?: 'top' | 'center' | 'bottom';

    /** 자동 숨김 */
    autoHide?: boolean;

    /** 숨김 콜백 */
    onHide?: () => void;

    /** 페르소나 (아이콘 변경) */
    persona?: 'strict_pd' | 'close_friend' | 'calm_mentor' | 'energetic';
}

// 우선순위별 색상
const PRIORITY_COLORS = {
    critical: { bg: 'rgba(239, 68, 68, 0.9)', border: '#ef4444' },
    high: { bg: 'rgba(249, 115, 22, 0.9)', border: '#f97316' },
    medium: { bg: 'rgba(0, 0, 0, 0.8)', border: '#6b7280' },
    low: { bg: 'rgba(34, 197, 94, 0.9)', border: '#22c55e' },
};

// 페르소나별 아이콘
const PERSONA_ICONS = {
    strict_pd: '📢',
    close_friend: '💬',
    calm_mentor: '🎯',
    energetic: '🔥',
};

export function TextCoachBubble({
    message,
    duration = 3000,
    style = 'minimal',
    priority = 'medium',
    position = 'bottom',
    autoHide = true,
    onHide,
    persona = 'calm_mentor',
}: TextCoachBubbleProps) {
    const [visible, setVisible] = useState(true);
    const [fadeOut, setFadeOut] = useState(false);

    useEffect(() => {
        if (autoHide && duration > 0) {
            const fadeTimer = setTimeout(() => {
                setFadeOut(true);
            }, duration - 300);

            const hideTimer = setTimeout(() => {
                setVisible(false);
                onHide?.();
            }, duration);

            return () => {
                clearTimeout(fadeTimer);
                clearTimeout(hideTimer);
            };
        }
    }, [autoHide, duration, onHide]);

    if (!visible) return null;

    const colors = PRIORITY_COLORS[priority];
    const icon = PERSONA_ICONS[persona];

    // 위치 스타일
    const positionStyles = {
        top: { top: 60, left: '50%', transform: 'translateX(-50%)' },
        center: { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' },
        bottom: { bottom: 100, left: '50%', transform: 'translateX(-50%)' },
    };

    // 스타일별 크기
    const styleConfig = {
        minimal: { padding: '8px 16px', fontSize: 14, maxWidth: '70%' },
        prominent: { padding: '16px 24px', fontSize: 18, maxWidth: '80%' },
        toast: { padding: '12px 20px', fontSize: 16, maxWidth: '90%' },
    };

    const config = styleConfig[style];

    return (
        <div
            className="text-coach-bubble"
            style={{
                position: 'absolute',
                ...positionStyles[position],
                background: colors.bg,
                color: '#ffffff',
                padding: config.padding,
                borderRadius: 12,
                fontSize: config.fontSize,
                fontWeight: 500,
                maxWidth: config.maxWidth,
                textAlign: 'center',
                borderLeft: `4px solid ${colors.border}`,
                boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                zIndex: 60,
                opacity: fadeOut ? 0 : 1,
                transition: 'opacity 0.3s ease-out',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
            }}
        >
            <span style={{ fontSize: config.fontSize + 4 }}>{icon}</span>
            <span>{message}</span>
        </div>
    );
}

/**
 * TextCoachQueue - 텍스트 코칭 큐 관리
 * 
 * 여러 메시지를 순차적으로 표시
 */
interface QueuedMessage {
    id: string;
    message: string;
    priority?: 'critical' | 'high' | 'medium' | 'low';
    duration?: number;
}

interface TextCoachQueueProps {
    messages: QueuedMessage[];
    onMessageComplete?: (id: string) => void;
    persona?: 'strict_pd' | 'close_friend' | 'calm_mentor' | 'energetic';
}

export function TextCoachQueue({
    messages,
    onMessageComplete,
    persona = 'calm_mentor',
}: TextCoachQueueProps) {
    const [currentIndex, setCurrentIndex] = useState(0);

    const handleHide = () => {
        const current = messages[currentIndex];
        if (current) {
            onMessageComplete?.(current.id);
        }
        setCurrentIndex(prev => prev + 1);
    };

    const current = messages[currentIndex];
    if (!current) return null;

    return (
        <TextCoachBubble
            key={current.id}
            message={current.message}
            priority={current.priority}
            duration={current.duration}
            persona={persona}
            onHide={handleHide}
        />
    );
}

export default TextCoachBubble;
