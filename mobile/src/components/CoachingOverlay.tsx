/**
 * Coaching Overlay - Enhanced Version
 *
 * Features:
 * - Audio/Text coaching toggles
 * - Minimal, non-intrusive UI design
 * - Extensible slots for future enhancements:
 *   - Composition guides (rule of thirds, golden ratio)
 *   - Lighting recommendations
 *   - Subject/material suggestions
 *   - Mise-en-scène recommendations
 *
 * Design: Glassmorphism with fade animations
 */

import React, { useState } from 'react';
import {
    View,
    Text,
    StyleSheet,
    Animated,
    Pressable,
    Switch,
} from 'react-native';

// ============================================================
// Types
// ============================================================

export interface CoachingFeedback {
    type: 'feedback';
    message: string;
    priority: 'low' | 'medium' | 'high' | 'critical';
    source?: 'rule' | 'composition' | 'lighting' | 'mise_en_scene';
    rule_id?: string;
}

export interface CompositionGuide {
    type: 'rule_of_thirds' | 'golden_ratio' | 'center' | 'custom';
    enabled: boolean;
    opacity?: number;
}

export interface LightingRecommendation {
    currentBrightness: 'too_dark' | 'optimal' | 'too_bright';
    suggestion?: string;
}

export interface CoachingOverlayProps {
    // Core props
    feedback: CoachingFeedback | null;
    isConnected: boolean;
    recordingTime: number;
    isRecording: boolean;

    // Coaching settings
    voiceEnabled: boolean;
    textEnabled: boolean;
    onVoiceToggle: (enabled: boolean) => void;
    onTextToggle: (enabled: boolean) => void;

    // Future enhancement slots (Phase 2+)
    compositionGuide?: CompositionGuide;
    lightingRecommendation?: LightingRecommendation;
    miseEnSceneHint?: string;
}

// ============================================================
// Component
// ============================================================

export function CoachingOverlay({
    feedback,
    isConnected,
    recordingTime,
    isRecording,
    voiceEnabled,
    textEnabled,
    onVoiceToggle,
    onTextToggle,
    compositionGuide,
    lightingRecommendation,
    miseEnSceneHint,
}: CoachingOverlayProps) {
    const fadeAnim = React.useRef(new Animated.Value(0)).current;
    const [showSettings, setShowSettings] = useState(false);

    // Fade in when new feedback arrives
    React.useEffect(() => {
        if (feedback && textEnabled) {
            Animated.sequence([
                Animated.timing(fadeAnim, {
                    toValue: 1,
                    duration: 300,
                    useNativeDriver: true,
                }),
                Animated.delay(4000),
                Animated.timing(fadeAnim, {
                    toValue: 0,
                    duration: 500,
                    useNativeDriver: true,
                }),
            ]).start();
        }
    }, [feedback, fadeAnim, textEnabled]);

    const getPriorityStyle = (priority: string) => {
        switch (priority) {
            case 'critical':
                return styles.priorityCritical;
            case 'high':
                return styles.priorityHigh;
            case 'medium':
                return styles.priorityMedium;
            default:
                return styles.priorityLow;
        }
    };

    const getPriorityIcon = (priority: string) => {
        switch (priority) {
            case 'critical':
                return '🚨';
            case 'high':
                return '⚠️';
            case 'medium':
                return '💡';
            default:
                return '✨';
        }
    };

    return (
        <View style={styles.container} pointerEvents="box-none">
            {/* ============================================================ */}
            {/* TOP: Connection Status + Settings Toggle */}
            {/* ============================================================ */}
            {isRecording && (
                <View style={styles.topBar}>
                    {/* Connection Status */}
                    <View style={styles.statusContainer}>
                        <View
                            style={[
                                styles.statusDot,
                                isConnected ? styles.statusConnected : styles.statusDisconnected,
                            ]}
                        />
                        <Text style={styles.statusText}>
                            {isConnected ? 'AI 코칭' : '연결 중...'}
                        </Text>
                    </View>

                    {/* Settings Toggle */}
                    <Pressable
                        style={styles.settingsButton}
                        onPress={() => setShowSettings(!showSettings)}
                    >
                        <Text style={styles.settingsIcon}>⚙️</Text>
                    </Pressable>
                </View>
            )}

            {/* ============================================================ */}
            {/* SETTINGS PANEL (Voice/Text Toggles) */}
            {/* ============================================================ */}
            {showSettings && isRecording && (
                <View style={styles.settingsPanel}>
                    {/* Voice Toggle */}
                    <View style={styles.settingsRow}>
                        <Text style={styles.settingsLabel}>🔊 음성 코칭</Text>
                        <Switch
                            value={voiceEnabled}
                            onValueChange={onVoiceToggle}
                            trackColor={{ false: 'rgba(255,255,255,0.2)', true: 'rgba(59,130,246,0.6)' }}
                            thumbColor={voiceEnabled ? '#3b82f6' : '#fff'}
                        />
                    </View>

                    {/* Text Toggle */}
                    <View style={styles.settingsRow}>
                        <Text style={styles.settingsLabel}>📝 텍스트 코칭</Text>
                        <Switch
                            value={textEnabled}
                            onValueChange={onTextToggle}
                            trackColor={{ false: 'rgba(255,255,255,0.2)', true: 'rgba(34,197,94,0.6)' }}
                            thumbColor={textEnabled ? '#22c55e' : '#fff'}
                        />
                    </View>
                </View>
            )}

            {/* ============================================================ */}
            {/* FEEDBACK MESSAGE (Non-intrusive, bottom-center) */}
            {/* ============================================================ */}
            {feedback && textEnabled && isRecording && (
                <Animated.View
                    style={[
                        styles.feedbackContainer,
                        getPriorityStyle(feedback.priority),
                        { opacity: fadeAnim },
                    ]}
                >
                    <Text style={styles.feedbackIcon}>
                        {getPriorityIcon(feedback.priority)}
                    </Text>
                    <Text style={styles.feedbackText}>{feedback.message}</Text>
                </Animated.View>
            )}

            {/* ============================================================ */}
            {/* FUTURE: Composition Guide Overlay (Phase 2) */}
            {/* ============================================================ */}
            {compositionGuide?.enabled && (
                <View style={styles.compositionGuide}>
                    {compositionGuide.type === 'rule_of_thirds' && (
                        <>
                            {/* Vertical lines */}
                            <View style={[styles.gridLine, styles.gridVertical1]} />
                            <View style={[styles.gridLine, styles.gridVertical2]} />
                            {/* Horizontal lines */}
                            <View style={[styles.gridLine, styles.gridHorizontal1]} />
                            <View style={[styles.gridLine, styles.gridHorizontal2]} />
                        </>
                    )}
                </View>
            )}

            {/* ============================================================ */}
            {/* FUTURE: Lighting Recommendation (Phase 2) */}
            {/* ============================================================ */}
            {lightingRecommendation && lightingRecommendation.currentBrightness !== 'optimal' && (
                <View style={styles.lightingHint}>
                    <Text style={styles.lightingText}>
                        {lightingRecommendation.currentBrightness === 'too_dark'
                            ? '💡 조명을 밝게 해주세요'
                            : '🔅 조명이 너무 밝습니다'}
                    </Text>
                </View>
            )}

            {/* ============================================================ */}
            {/* FUTURE: Mise-en-scène Hint (Phase 2) */}
            {/* ============================================================ */}
            {miseEnSceneHint && (
                <View style={styles.miseEnSceneHint}>
                    <Text style={styles.miseEnSceneText}>🎬 {miseEnSceneHint}</Text>
                </View>
            )}
        </View>
    );
}

// ============================================================
// Styles - Minimal, Non-intrusive Design
// ============================================================

const styles = StyleSheet.create({
    container: {
        ...StyleSheet.absoluteFillObject,
        justifyContent: 'space-between',
        paddingTop: 120,
        paddingBottom: 150,
        paddingHorizontal: 16,
    },

    // Top Bar
    topBar: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    statusContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'rgba(0, 0, 0, 0.4)',
        paddingVertical: 6,
        paddingHorizontal: 12,
        borderRadius: 16,
    },
    statusDot: {
        width: 6,
        height: 6,
        borderRadius: 3,
        marginRight: 6,
    },
    statusConnected: {
        backgroundColor: '#22c55e',
    },
    statusDisconnected: {
        backgroundColor: '#f59e0b',
    },
    statusText: {
        color: 'rgba(255, 255, 255, 0.8)',
        fontSize: 11,
        fontWeight: '500',
    },
    settingsButton: {
        width: 36,
        height: 36,
        borderRadius: 18,
        backgroundColor: 'rgba(0, 0, 0, 0.4)',
        justifyContent: 'center',
        alignItems: 'center',
    },
    settingsIcon: {
        fontSize: 16,
    },

    // Settings Panel (Glassmorphism)
    settingsPanel: {
        position: 'absolute',
        top: 160,
        right: 16,
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        borderRadius: 12,
        padding: 12,
        borderWidth: 1,
        borderColor: 'rgba(255, 255, 255, 0.1)',
    },
    settingsRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingVertical: 8,
        minWidth: 160,
    },
    settingsLabel: {
        color: 'rgba(255, 255, 255, 0.9)',
        fontSize: 13,
        marginRight: 16,
    },

    // Feedback Container (Bottom-center, non-intrusive)
    feedbackContainer: {
        position: 'absolute',
        bottom: 180,
        left: 20,
        right: 20,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        paddingVertical: 14,
        paddingHorizontal: 20,
        borderRadius: 16,
        borderWidth: 1,
        // Glassmorphism
        backgroundColor: 'rgba(0, 0, 0, 0.6)',
    },
    feedbackIcon: {
        fontSize: 18,
        marginRight: 10,
    },
    feedbackText: {
        color: '#fff',
        fontSize: 15,
        fontWeight: '500',
        textAlign: 'center',
        lineHeight: 22,
        flex: 1,
    },

    // Priority styles (border colors)
    priorityLow: {
        borderColor: 'rgba(34, 197, 94, 0.6)',
    },
    priorityMedium: {
        borderColor: 'rgba(59, 130, 246, 0.6)',
    },
    priorityHigh: {
        borderColor: 'rgba(245, 158, 11, 0.6)',
    },
    priorityCritical: {
        borderColor: 'rgba(239, 68, 68, 0.8)',
        backgroundColor: 'rgba(239, 68, 68, 0.2)',
    },

    // Composition Guide (Rule of Thirds)
    compositionGuide: {
        ...StyleSheet.absoluteFillObject,
        pointerEvents: 'none',
    },
    gridLine: {
        position: 'absolute',
        backgroundColor: 'rgba(255, 255, 255, 0.15)',
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

    // Lighting Hint
    lightingHint: {
        position: 'absolute',
        top: '50%',
        left: 20,
        right: 20,
        alignItems: 'center',
    },
    lightingText: {
        color: 'rgba(255, 200, 100, 0.9)',
        fontSize: 14,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        paddingVertical: 8,
        paddingHorizontal: 16,
        borderRadius: 12,
    },

    // Mise-en-scène Hint
    miseEnSceneHint: {
        position: 'absolute',
        top: 200,
        left: 20,
        right: 20,
        alignItems: 'center',
    },
    miseEnSceneText: {
        color: 'rgba(255, 255, 255, 0.8)',
        fontSize: 12,
        backgroundColor: 'rgba(0, 0, 0, 0.4)',
        paddingVertical: 6,
        paddingHorizontal: 12,
        borderRadius: 10,
        fontStyle: 'italic',
    },
});
