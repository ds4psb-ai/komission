/**
 * Coaching Mode Selector - Phase 1
 * 
 * Output Mode + Persona selection UI
 */

import React from 'react';
import {
    View,
    Text,
    StyleSheet,
    Pressable,
    ScrollView,
} from 'react-native';
import { OutputMode, Persona } from '../hooks/useCoachingWebSocket';

// ============================================================
// Types
// ============================================================

interface CoachingModeSelectorProps {
    outputMode: OutputMode;
    persona: Persona;
    onOutputModeChange: (mode: OutputMode) => void;
    onPersonaChange: (persona: Persona) => void;
    disabled?: boolean;
}

// ============================================================
// Constants
// ============================================================

const OUTPUT_MODES: Array<{ key: OutputMode; label: string; icon: string; desc: string }> = [
    { key: 'graphic', label: '그래픽', icon: '🎯', desc: '화면 오버레이 (무음)' },
    { key: 'text', label: '텍스트', icon: '📝', desc: '조용한 자막' },
    { key: 'audio', label: '음성', icon: '🔊', desc: 'TTS 코칭' },
    { key: 'graphic_audio', label: '풀 코칭', icon: '🎬', desc: '그래픽+음성' },
];

const PERSONAS: Array<{ key: Persona; label: string; icon: string; desc: string }> = [
    { key: 'drill_sergeant', label: '빡센 디렉터', icon: '🎬', desc: '날카롭고 단호함' },
    { key: 'bestie', label: '찐친', icon: '✨', desc: '다정하고 자연스러움' },
    { key: 'chill_guide', label: '릴렉스 가이드', icon: '🧘', desc: 'ASMR급 차분함' },
    { key: 'hype_coach', label: '하이퍼 부스터', icon: '⚡', desc: '텐션 200%' },
];

// ============================================================
// Component
// ============================================================

export function CoachingModeSelector({
    outputMode,
    persona,
    onOutputModeChange,
    onPersonaChange,
    disabled = false,
}: CoachingModeSelectorProps) {
    return (
        <View style={styles.container}>
            {/* Output Mode Section */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>출력 모드</Text>
                <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                    <View style={styles.optionsRow}>
                        {OUTPUT_MODES.map((mode) => (
                            <Pressable
                                key={mode.key}
                                style={[
                                    styles.optionCard,
                                    outputMode === mode.key && styles.optionCardSelected,
                                    disabled && styles.optionCardDisabled,
                                ]}
                                onPress={() => !disabled && onOutputModeChange(mode.key)}
                            >
                                <Text style={styles.optionIcon}>{mode.icon}</Text>
                                <Text style={[
                                    styles.optionLabel,
                                    outputMode === mode.key && styles.optionLabelSelected,
                                ]}>
                                    {mode.label}
                                </Text>
                                <Text style={styles.optionDesc}>{mode.desc}</Text>
                            </Pressable>
                        ))}
                    </View>
                </ScrollView>
            </View>

            {/* Persona Section */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>코칭 페르소나</Text>
                <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                    <View style={styles.optionsRow}>
                        {PERSONAS.map((p) => (
                            <Pressable
                                key={p.key}
                                style={[
                                    styles.optionCard,
                                    persona === p.key && styles.optionCardSelected,
                                    disabled && styles.optionCardDisabled,
                                ]}
                                onPress={() => !disabled && onPersonaChange(p.key)}
                            >
                                <Text style={styles.optionIcon}>{p.icon}</Text>
                                <Text style={[
                                    styles.optionLabel,
                                    persona === p.key && styles.optionLabelSelected,
                                ]}>
                                    {p.label}
                                </Text>
                                <Text style={styles.optionDesc}>{p.desc}</Text>
                            </Pressable>
                        ))}
                    </View>
                </ScrollView>
            </View>
        </View>
    );
}

// ============================================================
// Styles
// ============================================================

const styles = StyleSheet.create({
    container: {
        padding: 16,
    },
    section: {
        marginBottom: 20,
    },
    sectionTitle: {
        fontSize: 14,
        fontWeight: '600',
        color: 'rgba(255, 255, 255, 0.7)',
        marginBottom: 12,
    },
    optionsRow: {
        flexDirection: 'row',
        gap: 12,
    },
    optionCard: {
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        borderRadius: 12,
        padding: 12,
        minWidth: 100,
        alignItems: 'center',
        borderWidth: 2,
        borderColor: 'transparent',
    },
    optionCardSelected: {
        backgroundColor: 'rgba(139, 92, 246, 0.3)',
        borderColor: 'rgba(139, 92, 246, 0.8)',
    },
    optionCardDisabled: {
        opacity: 0.5,
    },
    optionIcon: {
        fontSize: 24,
        marginBottom: 6,
    },
    optionLabel: {
        fontSize: 12,
        fontWeight: '600',
        color: 'rgba(255, 255, 255, 0.9)',
        marginBottom: 4,
    },
    optionLabelSelected: {
        color: '#fff',
    },
    optionDesc: {
        fontSize: 10,
        color: 'rgba(255, 255, 255, 0.5)',
        textAlign: 'center',
    },
});

export default CoachingModeSelector;
