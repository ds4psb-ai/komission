/**
 * Text Coach Bubble - Phase 1
 * 
 * Minimal text coaching overlay (subtitle-style)
 */

import React, { useEffect, useRef } from 'react';
import {
    View,
    Text,
    StyleSheet,
    Animated,
} from 'react-native';
import { TextCoach, Persona } from '../hooks/useCoachingWebSocket';

// ============================================================
// Types
// ============================================================

interface TextCoachBubbleProps {
    coach: TextCoach | null;
}

// ============================================================
// Constants
// ============================================================

const PERSONA_STYLES: Record<Persona, { color: string; prefix: string }> = {
    drill_sergeant: { color: '#ef4444', prefix: '🎬' },
    bestie: { color: '#f472b6', prefix: '✨' },
    chill_guide: { color: '#3b82f6', prefix: '🧘' },
    hype_coach: { color: '#f59e0b', prefix: '⚡' },
};

const PRIORITY_OPACITY: Record<string, number> = {
    critical: 1,
    high: 0.95,
    medium: 0.85,
    low: 0.7,
};

// ============================================================
// Component
// ============================================================

export function TextCoachBubble({ coach }: TextCoachBubbleProps) {
    const fadeAnim = useRef(new Animated.Value(0)).current;
    const translateY = useRef(new Animated.Value(20)).current;

    useEffect(() => {
        if (coach) {
            // Animate in
            Animated.parallel([
                Animated.timing(fadeAnim, {
                    toValue: 1,
                    duration: 200,
                    useNativeDriver: true,
                }),
                Animated.spring(translateY, {
                    toValue: 0,
                    tension: 100,
                    friction: 10,
                    useNativeDriver: true,
                }),
            ]).start();

            // Auto-hide
            const hideTimer = setTimeout(() => {
                Animated.parallel([
                    Animated.timing(fadeAnim, {
                        toValue: 0,
                        duration: 300,
                        useNativeDriver: true,
                    }),
                    Animated.timing(translateY, {
                        toValue: 20,
                        duration: 300,
                        useNativeDriver: true,
                    }),
                ]).start();
            }, coach.duration_ms - 300);

            return () => clearTimeout(hideTimer);
        }
    }, [coach, fadeAnim, translateY]);

    if (!coach) return null;

    const personaStyle = PERSONA_STYLES[coach.persona] || PERSONA_STYLES.chill_guide;

    return (
        <Animated.View
            style={[
                styles.container,
                {
                    opacity: fadeAnim,
                    transform: [{ translateY }],
                },
            ]}
            pointerEvents="none"
        >
            <View
                style={[
                    styles.bubble,
                    { backgroundColor: personaStyle.color + 'E0' },
                ]}
            >
                <Text style={styles.prefix}>{personaStyle.prefix}</Text>
                <Text style={styles.message}>{coach.message}</Text>
            </View>
        </Animated.View>
    );
}

// ============================================================
// Styles
// ============================================================

const styles = StyleSheet.create({
    container: {
        position: 'absolute',
        bottom: 150,
        left: 20,
        right: 20,
        alignItems: 'center',
    },
    bubble: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingVertical: 10,
        paddingHorizontal: 16,
        borderRadius: 20,
        maxWidth: '90%',
    },
    prefix: {
        fontSize: 18,
        marginRight: 8,
    },
    message: {
        color: '#fff',
        fontSize: 15,
        fontWeight: '500',
        flexShrink: 1,
    },
});

export default TextCoachBubble;
