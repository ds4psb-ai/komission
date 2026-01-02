/**
 * Graphic Overlay - Phase 1.3 Enhanced
 * 
 * Ported from frontend: CompositionGuide.tsx (232 lines)
 * 
 * Features:
 * - Grid overlays: rule_of_thirds, center, golden
 * - Target circle with crosshair
 * - Movement arrows with direction detection
 * - Countdown timer for timing
 * - Action icons (look_camera, smile, hold, action_now)
 * - Pulse/bounce animations
 * - Priority-based colors
 * - GuideStep integration
 */

import React, { useEffect, useRef, useState } from 'react';
import {
    View,
    Text,
    StyleSheet,
    Animated,
    Dimensions,
    Easing,
} from 'react-native';
import { GraphicGuide } from '../hooks/useCoachingWebSocket';
import { GuideStep } from '../services/directorPackService';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

// ============================================================
// Types
// ============================================================

export interface GraphicOverlayProps {
    /** WebSocket guide (from server) */
    guide?: GraphicGuide | null;

    /** DirectorPack step (from useDirectorPack) */
    currentStep?: GuideStep | null;
    upcomingStep?: GuideStep | null;

    /** Grid type override */
    gridType?: 'rule_of_thirds' | 'center' | 'golden' | 'none';

    /** Recording time for countdown */
    recordingTime?: number;

    /** Show grid overlay */
    showGrid?: boolean;

    /** Countdown target (seconds) */
    countdownTarget?: number;

    /** Action icon override */
    actionIcon?: 'look_camera' | 'smile' | 'move_left' | 'move_right' | 'move_up' | 'move_down' | 'hold' | 'action_now';

    /** Arrow direction override */
    arrowDirection?: 'left' | 'right' | 'up' | 'down' | 'center';

    /** Target position [x, y] 0-1 normalized */
    targetPosition?: [number, number];

    /** Message override */
    message?: string;

    /** Priority for color */
    priority?: 'critical' | 'high' | 'medium' | 'low';

    /** Visibility */
    visible?: boolean;
}

// ============================================================
// Constants
// ============================================================

const PRIORITY_COLORS: Record<string, string> = {
    critical: '#ef4444',  // red
    high: '#f97316',      // orange
    medium: '#eab308',    // yellow
    low: '#22c55e',       // green
};

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

const ARROW_ICONS: Record<string, string> = {
    left: '⬅️',
    right: '➡️',
    up: '⬆️',
    down: '⬇️',
    center: '🎯',
};

// ============================================================
// Component
// ============================================================

export function GraphicOverlay({
    guide,
    currentStep,
    upcomingStep,
    gridType = 'none',
    recordingTime = 0,
    showGrid = true,
    countdownTarget,
    actionIcon,
    arrowDirection,
    targetPosition = [0.5, 0.5],
    message,
    priority = 'medium',
    visible = true,
}: GraphicOverlayProps) {
    // Animations
    const fadeAnim = useRef(new Animated.Value(0)).current;
    const scaleAnim = useRef(new Animated.Value(0.9)).current;
    const pulseAnim = useRef(new Animated.Value(1)).current;
    const bounceAnim = useRef(new Animated.Value(0)).current;

    // Derived values from guide or props
    const effectiveGridType = guide?.grid_type || gridType;
    const effectiveTargetPos = guide?.target_position || targetPosition;
    const effectiveArrowDir = guide?.arrow_direction || arrowDirection;
    const effectiveActionIcon = guide?.action_icon || actionIcon;
    const effectiveMessage = guide?.message || currentStep?.action || message;
    const effectivePriority = guide?.priority || currentStep?.priority || priority;
    const color = PRIORITY_COLORS[effectivePriority] || PRIORITY_COLORS.medium;

    // Countdown calculation
    const countdownSec = countdownTarget
        ? Math.max(0, countdownTarget - recordingTime)
        : upcomingStep
            ? Math.max(0, upcomingStep.timeWindow[0] - recordingTime)
            : null;

    // ============================================================
    // Animations
    // ============================================================

    // Fade in/out
    useEffect(() => {
        if (visible && (guide || currentStep || effectiveMessage)) {
            Animated.parallel([
                Animated.timing(fadeAnim, {
                    toValue: 1,
                    duration: 200,
                    useNativeDriver: true,
                }),
                Animated.spring(scaleAnim, {
                    toValue: 1,
                    tension: 100,
                    friction: 8,
                    useNativeDriver: true,
                }),
            ]).start();
        } else {
            Animated.timing(fadeAnim, {
                toValue: 0,
                duration: 300,
                useNativeDriver: true,
            }).start();
        }
    }, [visible, guide, currentStep, effectiveMessage, fadeAnim, scaleAnim]);

    // Pulse animation for target circle
    useEffect(() => {
        const pulse = Animated.loop(
            Animated.sequence([
                Animated.timing(pulseAnim, {
                    toValue: 1.05,
                    duration: 1000,
                    easing: Easing.inOut(Easing.ease),
                    useNativeDriver: true,
                }),
                Animated.timing(pulseAnim, {
                    toValue: 1,
                    duration: 1000,
                    easing: Easing.inOut(Easing.ease),
                    useNativeDriver: true,
                }),
            ])
        );
        pulse.start();
        return () => pulse.stop();
    }, [pulseAnim]);

    // Bounce animation for arrows/icons
    useEffect(() => {
        const bounce = Animated.loop(
            Animated.sequence([
                Animated.timing(bounceAnim, {
                    toValue: -10,
                    duration: 500,
                    easing: Easing.inOut(Easing.ease),
                    useNativeDriver: true,
                }),
                Animated.timing(bounceAnim, {
                    toValue: 0,
                    duration: 500,
                    easing: Easing.inOut(Easing.ease),
                    useNativeDriver: true,
                }),
            ])
        );
        bounce.start();
        return () => bounce.stop();
    }, [bounceAnim]);

    // ============================================================
    // Render
    // ============================================================

    if (!visible) return null;

    const [targetX, targetY] = effectiveTargetPos;
    const posX = targetX * SCREEN_WIDTH;
    const posY = targetY * SCREEN_HEIGHT;

    return (
        <View style={styles.container} pointerEvents="none">
            {/* ============================================ */}
            {/* Grid Overlays */}
            {/* ============================================ */}

            {/* Rule of Thirds */}
            {showGrid && effectiveGridType === 'rule_of_thirds' && (
                <View style={styles.gridContainer}>
                    <View style={[styles.gridLine, styles.gridVertical1]} />
                    <View style={[styles.gridLine, styles.gridVertical2]} />
                    <View style={[styles.gridLine, styles.gridHorizontal1]} />
                    <View style={[styles.gridLine, styles.gridHorizontal2]} />
                </View>
            )}

            {/* Center Grid with Target */}
            {showGrid && effectiveGridType === 'center' && (
                <View style={[styles.centerTarget, { left: posX - 40, top: posY - 40 }]}>
                    <Animated.View
                        style={[
                            styles.targetCircle,
                            {
                                borderColor: color,
                                transform: [{ scale: pulseAnim }],
                            },
                        ]}
                    />
                    {/* Crosshair */}
                    <View style={[styles.crosshairH, { backgroundColor: color }]} />
                    <View style={[styles.crosshairV, { backgroundColor: color }]} />
                </View>
            )}

            {/* Golden Ratio Grid */}
            {showGrid && effectiveGridType === 'golden' && (
                <View style={styles.gridContainer}>
                    <View style={[styles.gridLine, { left: '38.2%', top: 0, bottom: 0, width: 1 }]} />
                    <View style={[styles.gridLine, { left: '61.8%', top: 0, bottom: 0, width: 1 }]} />
                    <View style={[styles.gridLine, { top: '38.2%', left: 0, right: 0, height: 1 }]} />
                    <View style={[styles.gridLine, { top: '61.8%', left: 0, right: 0, height: 1 }]} />
                </View>
            )}

            {/* ============================================ */}
            {/* Arrow Direction */}
            {/* ============================================ */}
            {effectiveArrowDir && (
                <Animated.View
                    style={[
                        styles.arrowContainer,
                        { transform: [{ translateY: bounceAnim }] },
                    ]}
                >
                    <Text style={styles.arrowIcon}>
                        {ARROW_ICONS[effectiveArrowDir]}
                    </Text>
                </Animated.View>
            )}

            {/* ============================================ */}
            {/* Action Icon */}
            {/* ============================================ */}
            {effectiveActionIcon && !effectiveArrowDir && (
                <Animated.View
                    style={[
                        styles.actionIconContainer,
                        { transform: [{ translateY: bounceAnim }] },
                    ]}
                >
                    <Text style={styles.actionIconText}>
                        {ACTION_ICONS[effectiveActionIcon] || '🎬'}
                    </Text>
                </Animated.View>
            )}

            {/* ============================================ */}
            {/* Countdown Timer */}
            {/* ============================================ */}
            {countdownSec !== null && countdownSec <= 5 && countdownSec > 0 && (
                <Animated.View
                    style={[
                        styles.countdownContainer,
                        countdownSec <= 1 && styles.countdownCritical,
                    ]}
                >
                    <Text
                        style={[
                            styles.countdownText,
                            countdownSec <= 1 && styles.countdownTextCritical,
                        ]}
                    >
                        {Math.ceil(countdownSec)}
                    </Text>
                </Animated.View>
            )}

            {/* ============================================ */}
            {/* Pre-Alert (Upcoming Step) */}
            {/* ============================================ */}
            {upcomingStep && (
                <Animated.View
                    style={[
                        styles.preAlertContainer,
                        { opacity: fadeAnim },
                    ]}
                >
                    <View style={styles.preAlertBadge}>
                        <Text style={styles.preAlertTime}>
                            {Math.ceil(upcomingStep.timeWindow[0] - recordingTime)}초 후
                        </Text>
                    </View>
                    <Text style={styles.preAlertAction}>{upcomingStep.action}</Text>
                </Animated.View>
            )}

            {/* ============================================ */}
            {/* Current Step / Message */}
            {/* ============================================ */}
            {effectiveMessage && (
                <Animated.View
                    style={[
                        styles.messageBubble,
                        {
                            opacity: fadeAnim,
                            transform: [{ scale: scaleAnim }],
                            borderLeftColor: color,
                        },
                    ]}
                >
                    {currentStep?.icon && (
                        <Text style={styles.stepIcon}>{currentStep.icon}</Text>
                    )}
                    <View style={styles.messageContent}>
                        {currentStep?.time && (
                            <Text style={[styles.stepTime, { color }]}>
                                {currentStep.time}
                            </Text>
                        )}
                        <Text style={styles.messageText}>{effectiveMessage}</Text>
                        {currentStep?.reason && (
                            <Text style={styles.stepReason}>
                                💡 {currentStep.reason}
                            </Text>
                        )}
                    </View>
                </Animated.View>
            )}

            {/* ============================================ */}
            {/* Priority Badge */}
            {/* ============================================ */}
            {effectivePriority === 'critical' && (
                <View style={styles.priorityBadge}>
                    <Text style={styles.priorityBadgeText}>🔴 CRITICAL</Text>
                </View>
            )}
        </View>
    );
}

// ============================================================
// Styles
// ============================================================

const styles = StyleSheet.create({
    container: {
        position: 'absolute',
        left: 0,
        right: 0,
        top: 0,
        bottom: 0,
        zIndex: 50,
    },

    // Grid
    gridContainer: {
        position: 'absolute',
        left: 0,
        right: 0,
        top: 0,
        bottom: 0,
    },
    gridLine: {
        position: 'absolute',
        backgroundColor: 'rgba(255, 255, 255, 0.3)',
    },
    gridVertical1: { left: '33.33%', top: 0, bottom: 0, width: 1 },
    gridVertical2: { left: '66.66%', top: 0, bottom: 0, width: 1 },
    gridHorizontal1: { top: '33.33%', left: 0, right: 0, height: 1 },
    gridHorizontal2: { top: '66.66%', left: 0, right: 0, height: 1 },

    // Center Target
    centerTarget: {
        position: 'absolute',
        width: 80,
        height: 80,
        justifyContent: 'center',
        alignItems: 'center',
    },
    targetCircle: {
        width: 80,
        height: 80,
        borderRadius: 40,
        borderWidth: 3,
    },
    crosshairH: {
        position: 'absolute',
        width: 20,
        height: 2,
    },
    crosshairV: {
        position: 'absolute',
        width: 2,
        height: 20,
    },

    // Arrow
    arrowContainer: {
        position: 'absolute',
        left: '50%',
        top: '50%',
        marginLeft: -30,
        marginTop: -30,
    },
    arrowIcon: {
        fontSize: 60,
    },

    // Action Icon
    actionIconContainer: {
        position: 'absolute',
        left: '50%',
        top: '30%',
        marginLeft: -36,
    },
    actionIconText: {
        fontSize: 72,
    },

    // Countdown
    countdownContainer: {
        position: 'absolute',
        right: 20,
        top: 80,
    },
    countdownCritical: {
        // Add pulse effect via animation
    },
    countdownText: {
        fontSize: 64,
        fontWeight: 'bold',
        color: '#fff',
        textShadowColor: 'rgba(0, 0, 0, 0.5)',
        textShadowOffset: { width: 2, height: 2 },
        textShadowRadius: 4,
    },
    countdownTextCritical: {
        color: '#ef4444',
    },

    // Pre-Alert
    preAlertContainer: {
        position: 'absolute',
        top: 100,
        left: 16,
        right: 16,
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'rgba(245, 158, 11, 0.9)',
        borderRadius: 10,
        padding: 10,
    },
    preAlertBadge: {
        backgroundColor: 'rgba(0, 0, 0, 0.3)',
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 6,
        marginRight: 10,
    },
    preAlertTime: {
        color: '#fff',
        fontSize: 12,
        fontWeight: '600',
    },
    preAlertAction: {
        color: '#fff',
        fontSize: 14,
        fontWeight: '500',
        flex: 1,
    },

    // Message Bubble
    messageBubble: {
        position: 'absolute',
        bottom: 140,
        left: 16,
        right: 16,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        borderRadius: 12,
        padding: 14,
        flexDirection: 'row',
        alignItems: 'flex-start',
        borderLeftWidth: 4,
    },
    stepIcon: {
        fontSize: 28,
        marginRight: 12,
    },
    messageContent: {
        flex: 1,
    },
    stepTime: {
        fontSize: 12,
        fontWeight: '600',
        marginBottom: 4,
    },
    messageText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: '500',
    },
    stepReason: {
        color: 'rgba(34, 197, 94, 0.8)',
        fontSize: 12,
        marginTop: 6,
    },

    // Priority Badge
    priorityBadge: {
        position: 'absolute',
        top: 60,
        left: '50%',
        marginLeft: -50,
        backgroundColor: 'rgba(239, 68, 68, 0.9)',
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: 16,
    },
    priorityBadgeText: {
        color: '#fff',
        fontSize: 12,
        fontWeight: '700',
    },
});

export default GraphicOverlay;
