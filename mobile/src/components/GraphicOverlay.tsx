/**
 * Graphic Overlay - Phase 1
 * 
 * Visual coaching guide overlay for composition, timing, actions
 */

import React, { useEffect, useRef } from 'react';
import {
    View,
    Text,
    StyleSheet,
    Animated,
    Dimensions,
} from 'react-native';
import { GraphicGuide } from '../hooks/useCoachingWebSocket';

const { width, height } = Dimensions.get('window');

// ============================================================
// Types
// ============================================================

interface GraphicOverlayProps {
    guide: GraphicGuide | null;
    showGrid?: boolean;
}

// ============================================================
// Constants
// ============================================================

const ARROW_ICONS: Record<string, string> = {
    up: '⬆️',
    down: '⬇️',
    left: '⬅️',
    right: '➡️',
};

const ACTION_ICONS: Record<string, string> = {
    look_camera: '👁️',
    action_now: '🎬',
    hold: '✋',
    smile: '😊',
};

const PRIORITY_COLORS: Record<string, string> = {
    critical: '#ef4444',
    high: '#f59e0b',
    medium: '#3b82f6',
    low: '#6b7280',
};

// ============================================================
// Component
// ============================================================

export function GraphicOverlay({ guide, showGrid = true }: GraphicOverlayProps) {
    const fadeAnim = useRef(new Animated.Value(0)).current;
    const scaleAnim = useRef(new Animated.Value(0.9)).current;

    useEffect(() => {
        if (guide) {
            // Animate in
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

            // Auto-hide after duration
            const hideTimer = setTimeout(() => {
                Animated.timing(fadeAnim, {
                    toValue: 0,
                    duration: 300,
                    useNativeDriver: true,
                }).start();
            }, guide.message_duration_ms - 300);

            return () => clearTimeout(hideTimer);
        }
    }, [guide, fadeAnim, scaleAnim]);

    if (!guide) return null;

    const [targetX, targetY] = guide.target_position;
    const posX = targetX * width;
    const posY = targetY * height;

    return (
        <View style={styles.container} pointerEvents="none">
            {/* Grid Overlay (Rule of Thirds) */}
            {showGrid && guide.grid_type === 'rule_of_thirds' && (
                <View style={styles.gridContainer}>
                    {/* Vertical lines */}
                    <View style={[styles.gridLine, styles.gridVertical1]} />
                    <View style={[styles.gridLine, styles.gridVertical2]} />
                    {/* Horizontal lines */}
                    <View style={[styles.gridLine, styles.gridHorizontal1]} />
                    <View style={[styles.gridLine, styles.gridHorizontal2]} />
                </View>
            )}

            {/* Center Grid */}
            {showGrid && guide.grid_type === 'center' && (
                <View style={styles.centerCrossContainer}>
                    <View style={styles.centerCrossH} />
                    <View style={styles.centerCrossV} />
                </View>
            )}

            {/* Target Position Indicator */}
            <Animated.View
                style={[
                    styles.targetIndicator,
                    {
                        left: posX - 30,
                        top: posY - 30,
                        opacity: fadeAnim,
                        transform: [{ scale: scaleAnim }],
                        borderColor: PRIORITY_COLORS[guide.priority] || PRIORITY_COLORS.medium,
                    },
                ]}
            >
                {/* Arrow Direction */}
                {guide.arrow_direction && (
                    <Text style={styles.arrowIcon}>
                        {ARROW_ICONS[guide.arrow_direction]}
                    </Text>
                )}

                {/* Action Icon */}
                {guide.action_icon && !guide.arrow_direction && (
                    <Text style={styles.actionIcon}>
                        {ACTION_ICONS[guide.action_icon]}
                    </Text>
                )}
            </Animated.View>

            {/* Message Bubble */}
            <Animated.View
                style={[
                    styles.messageBubble,
                    {
                        opacity: fadeAnim,
                        transform: [{ scale: scaleAnim }],
                        backgroundColor: PRIORITY_COLORS[guide.priority] + 'DD',
                    },
                ]}
            >
                <Text style={styles.messageText}>{guide.message}</Text>
            </Animated.View>
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
    },

    // Grid styles
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
    gridVertical1: {
        left: '33.33%',
        top: 0,
        bottom: 0,
        width: 1,
    },
    gridVertical2: {
        left: '66.66%',
        top: 0,
        bottom: 0,
        width: 1,
    },
    gridHorizontal1: {
        top: '33.33%',
        left: 0,
        right: 0,
        height: 1,
    },
    gridHorizontal2: {
        top: '66.66%',
        left: 0,
        right: 0,
        height: 1,
    },

    // Center cross
    centerCrossContainer: {
        position: 'absolute',
        left: '50%',
        top: '50%',
        marginLeft: -20,
        marginTop: -20,
        width: 40,
        height: 40,
    },
    centerCrossH: {
        position: 'absolute',
        top: 19,
        left: 0,
        right: 0,
        height: 2,
        backgroundColor: 'rgba(255, 255, 255, 0.5)',
    },
    centerCrossV: {
        position: 'absolute',
        left: 19,
        top: 0,
        bottom: 0,
        width: 2,
        backgroundColor: 'rgba(255, 255, 255, 0.5)',
    },

    // Target indicator
    targetIndicator: {
        position: 'absolute',
        width: 60,
        height: 60,
        borderRadius: 30,
        borderWidth: 3,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: 'rgba(0, 0, 0, 0.3)',
    },
    arrowIcon: {
        fontSize: 28,
    },
    actionIcon: {
        fontSize: 24,
    },

    // Message bubble
    messageBubble: {
        position: 'absolute',
        bottom: 120,
        left: 20,
        right: 20,
        paddingVertical: 12,
        paddingHorizontal: 16,
        borderRadius: 12,
    },
    messageText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: '600',
        textAlign: 'center',
    },
});

export default GraphicOverlay;
