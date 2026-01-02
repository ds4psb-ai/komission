'use client';

import React from 'react';

/**
 * CompositionGuide - 그래픽 구도 오버레이
 * 
 * 촬영 중 잡음 없이 구도 가이드를 제공
 * 디폴트 코칭 모드 (셀프 촬영 시)
 */

interface CompositionGuideProps {
    /** 가이드 타입 */
    guideType: 'composition' | 'timing' | 'action';

    /** 목표 위치 [x, y] 0-1 정규화 */
    targetPosition?: [number, number];

    /** 현재 피사체 위치 (감지된) */
    currentPosition?: [number, number];

    /** 그리드 타입 */
    gridType?: 'rule_of_thirds' | 'center' | 'golden';

    /** 카운트다운 (초) */
    countdownSec?: number;

    /** 액션 아이콘 */
    actionIcon?: 'look_camera' | 'smile' | 'move_left' | 'move_right' | 'move_up' | 'move_down' | 'hold' | 'action_now';

    /** 화살표 방향 */
    arrowDirection?: 'left' | 'right' | 'up' | 'down' | 'center';

    /** 메시지 (텍스트 힌트) */
    message?: string;

    /** 규칙 우선순위 (색상 결정) */
    priority?: 'critical' | 'high' | 'medium' | 'low';

    /** 표시 여부 */
    visible?: boolean;
}

// 우선순위별 색상
const PRIORITY_COLORS = {
    critical: '#ef4444', // red
    high: '#f97316',     // orange
    medium: '#eab308',   // yellow
    low: '#22c55e',      // green
};

// 액션 아이콘 이모지
const ACTION_ICONS: Record<string, string> = {
    look_camera: '👀',
    smile: '😊',
    move_left: '⬅️',
    move_right: '➡️',
    move_up: '⬆️',
    move_down: '⬇️',
    hold: '✋',
    action_now: '🎬',
};

export function CompositionGuide({
    guideType,
    targetPosition = [0.5, 0.5],
    currentPosition,
    gridType = 'center',
    countdownSec,
    actionIcon,
    arrowDirection,
    message,
    priority = 'medium',
    visible = true,
}: CompositionGuideProps) {
    if (!visible) return null;

    const color = PRIORITY_COLORS[priority];

    // 화면 좌표로 변환 (percentage)
    const targetX = targetPosition[0] * 100;
    const targetY = targetPosition[1] * 100;

    // 피사체 이동 방향 계산
    const needsMove = currentPosition && (
        Math.abs(currentPosition[0] - targetPosition[0]) > 0.1 ||
        Math.abs(currentPosition[1] - targetPosition[1]) > 0.1
    );

    return (
        <div className="composition-guide" style={{
            position: 'absolute',
            inset: 0,
            pointerEvents: 'none',
            zIndex: 50,
        }}>
            {/* 그리드 오버레이 */}
            {gridType === 'rule_of_thirds' && (
                <div className="grid-overlay" style={{ position: 'absolute', inset: 0 }}>
                    {/* 세로선 2개 */}
                    <div style={{ position: 'absolute', left: '33.33%', top: 0, bottom: 0, width: 1, background: 'rgba(255,255,255,0.3)' }} />
                    <div style={{ position: 'absolute', left: '66.66%', top: 0, bottom: 0, width: 1, background: 'rgba(255,255,255,0.3)' }} />
                    {/* 가로선 2개 */}
                    <div style={{ position: 'absolute', top: '33.33%', left: 0, right: 0, height: 1, background: 'rgba(255,255,255,0.3)' }} />
                    <div style={{ position: 'absolute', top: '66.66%', left: 0, right: 0, height: 1, background: 'rgba(255,255,255,0.3)' }} />
                </div>
            )}

            {gridType === 'center' && (
                <div className="center-guide" style={{
                    position: 'absolute',
                    left: `${targetX}%`,
                    top: `${targetY}%`,
                    transform: 'translate(-50%, -50%)',
                }}>
                    {/* 중앙 타겟 원 */}
                    <div style={{
                        width: 80,
                        height: 80,
                        borderRadius: '50%',
                        border: `3px solid ${color}`,
                        opacity: 0.8,
                        animation: 'pulse 2s ease-in-out infinite',
                    }} />
                    {/* 십자선 */}
                    <div style={{
                        position: 'absolute',
                        left: '50%',
                        top: '50%',
                        width: 20,
                        height: 2,
                        background: color,
                        transform: 'translate(-50%, -50%)',
                    }} />
                    <div style={{
                        position: 'absolute',
                        left: '50%',
                        top: '50%',
                        width: 2,
                        height: 20,
                        background: color,
                        transform: 'translate(-50%, -50%)',
                    }} />
                </div>
            )}

            {/* 이동 화살표 */}
            {needsMove && arrowDirection && (
                <div style={{
                    position: 'absolute',
                    left: '50%',
                    top: '50%',
                    transform: 'translate(-50%, -50%)',
                    fontSize: 48,
                    animation: 'bounce 1s ease-in-out infinite',
                }}>
                    {arrowDirection === 'left' && '⬅️'}
                    {arrowDirection === 'right' && '➡️'}
                    {arrowDirection === 'up' && '⬆️'}
                    {arrowDirection === 'down' && '⬇️'}
                    {arrowDirection === 'center' && '🎯'}
                </div>
            )}

            {/* 타이밍 카운트다운 */}
            {guideType === 'timing' && countdownSec !== undefined && (
                <div style={{
                    position: 'absolute',
                    right: 20,
                    top: 20,
                    fontSize: 64,
                    fontWeight: 'bold',
                    color: countdownSec <= 1 ? '#ef4444' : '#ffffff',
                    textShadow: '2px 2px 4px rgba(0,0,0,0.5)',
                    animation: countdownSec <= 3 ? 'pulse 0.5s ease-in-out infinite' : undefined,
                }}>
                    {Math.ceil(countdownSec)}
                </div>
            )}

            {/* 액션 아이콘 */}
            {guideType === 'action' && actionIcon && (
                <div style={{
                    position: 'absolute',
                    left: '50%',
                    top: '30%',
                    transform: 'translateX(-50%)',
                    fontSize: 72,
                    animation: 'bounce 0.5s ease-in-out infinite',
                }}>
                    {ACTION_ICONS[actionIcon] || '🎬'}
                </div>
            )}

            {/* 텍스트 힌트 (하단) */}
            {message && (
                <div style={{
                    position: 'absolute',
                    bottom: 80,
                    left: '50%',
                    transform: 'translateX(-50%)',
                    background: 'rgba(0,0,0,0.7)',
                    color: '#ffffff',
                    padding: '12px 24px',
                    borderRadius: 8,
                    fontSize: 18,
                    fontWeight: 500,
                    maxWidth: '80%',
                    textAlign: 'center',
                    borderLeft: `4px solid ${color}`,
                }}>
                    {message}
                </div>
            )}

            {/* CSS 애니메이션 */}
            <style jsx>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.8; transform: translate(-50%, -50%) scale(1); }
          50% { opacity: 1; transform: translate(-50%, -50%) scale(1.05); }
        }
        @keyframes bounce {
          0%, 100% { transform: translate(-50%, -50%) translateY(0); }
          50% { transform: translate(-50%, -50%) translateY(-10px); }
        }
      `}</style>
        </div>
    );
}

export default CompositionGuide;
