/**
 * Session Stats Overlay - Phase 5+
 * 
 * Auto-learning stats and signal promotion display
 */

import React, { useEffect, useRef } from 'react';
import {
    View,
    Text,
    StyleSheet,
    Animated,
    Pressable,
} from 'react-native';
import { SignalPromotion, AxisMetrics } from '../hooks/useCoachingWebSocket';

// ============================================================
// Types
// ============================================================

interface SessionStatsProps {
    promotion: SignalPromotion | null;
    onDismiss?: () => void;
}

// ============================================================
// Component
// ============================================================

export function SessionStatsOverlay({ promotion, onDismiss }: SessionStatsProps) {
    const slideAnim = useRef(new Animated.Value(-200)).current;
    const opacityAnim = useRef(new Animated.Value(0)).current;

    useEffect(() => {
        if (promotion) {
            Animated.parallel([
                Animated.spring(slideAnim, {
                    toValue: 0,
                    tension: 80,
                    friction: 10,
                    useNativeDriver: true,
                }),
                Animated.timing(opacityAnim, {
                    toValue: 1,
                    duration: 300,
                    useNativeDriver: true,
                }),
            ]).start();
        }
    }, [promotion, slideAnim, opacityAnim]);

    const handleDismiss = () => {
        Animated.parallel([
            Animated.timing(slideAnim, {
                toValue: -200,
                duration: 200,
                useNativeDriver: true,
            }),
            Animated.timing(opacityAnim, {
                toValue: 0,
                duration: 200,
                useNativeDriver: true,
            }),
        ]).start(() => onDismiss?.());
    };

    if (!promotion) return null;

    const { axis_metrics: metrics, candidates } = promotion;

    return (
        <Animated.View
            style={[
                styles.container,
                {
                    transform: [{ translateY: slideAnim }],
                    opacity: opacityAnim,
                },
            ]}
        >
            <View style={styles.header}>
                <View style={styles.headerLeft}>
                    <Text style={styles.headerIcon}>🎉</Text>
                    <Text style={styles.headerTitle}>신규 패턴 발견!</Text>
                </View>
                <Pressable onPress={handleDismiss}>
                    <Text style={styles.closeButton}>✕</Text>
                </Pressable>
            </View>

            {/* Axis Metrics */}
            <View style={styles.metricsRow}>
                <MetricCard
                    label="준수율 향상"
                    value={metrics.compliance_lift}
                    icon="📈"
                    positive
                />
                <MetricCard
                    label="성과 향상"
                    value={metrics.outcome_lift}
                    icon="⬆️"
                    positive
                />
                <MetricCard
                    label="클러스터"
                    value={String(metrics.cluster_count)}
                    icon="🎯"
                />
            </View>

            {/* Ready Status */}
            <View style={[
                styles.statusBadge,
                metrics.is_ready ? styles.statusReady : styles.statusPending,
            ]}>
                <Text style={styles.statusText}>
                    {metrics.is_ready ? '✅ 승격 준비 완료' : '⏳ 데이터 수집 중'}
                </Text>
            </View>

            {/* Candidates Preview */}
            {candidates.length > 0 && (
                <View style={styles.candidatesSection}>
                    <Text style={styles.candidatesTitle}>
                        {candidates.length}개 패턴 후보:
                    </Text>
                    {candidates.slice(0, 3).map((c, i) => (
                        <Text key={i} style={styles.candidateItem}>
                            • {c.signal_key}
                        </Text>
                    ))}
                </View>
            )}
        </Animated.View>
    );
}

// ============================================================
// Sub-components
// ============================================================

function MetricCard({
    label,
    value,
    icon,
    positive = false,
}: {
    label: string;
    value: string;
    icon: string;
    positive?: boolean;
}) {
    return (
        <View style={styles.metricCard}>
            <Text style={styles.metricIcon}>{icon}</Text>
            <Text style={[styles.metricValue, positive && styles.metricValuePositive]}>
                {value}
            </Text>
            <Text style={styles.metricLabel}>{label}</Text>
        </View>
    );
}

// ============================================================
// Styles
// ============================================================

const styles = StyleSheet.create({
    container: {
        position: 'absolute',
        top: 80,
        left: 16,
        right: 16,
        backgroundColor: 'rgba(30, 30, 40, 0.95)',
        borderRadius: 16,
        padding: 16,
        borderWidth: 1,
        borderColor: 'rgba(139, 92, 246, 0.5)',
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 12,
    },
    headerLeft: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    headerIcon: {
        fontSize: 20,
        marginRight: 8,
    },
    headerTitle: {
        color: '#fff',
        fontSize: 16,
        fontWeight: '700',
    },
    closeButton: {
        color: 'rgba(255, 255, 255, 0.5)',
        fontSize: 18,
        padding: 4,
    },
    metricsRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: 12,
    },
    metricCard: {
        flex: 1,
        alignItems: 'center',
        padding: 8,
    },
    metricIcon: {
        fontSize: 16,
        marginBottom: 4,
    },
    metricValue: {
        color: '#fff',
        fontSize: 16,
        fontWeight: '700',
    },
    metricValuePositive: {
        color: '#22c55e',
    },
    metricLabel: {
        color: 'rgba(255, 255, 255, 0.6)',
        fontSize: 10,
        marginTop: 2,
    },
    statusBadge: {
        paddingVertical: 6,
        paddingHorizontal: 12,
        borderRadius: 20,
        alignSelf: 'center',
    },
    statusReady: {
        backgroundColor: 'rgba(34, 197, 94, 0.3)',
    },
    statusPending: {
        backgroundColor: 'rgba(245, 158, 11, 0.3)',
    },
    statusText: {
        color: '#fff',
        fontSize: 12,
        fontWeight: '600',
    },
    candidatesSection: {
        marginTop: 12,
        paddingTop: 12,
        borderTopWidth: 1,
        borderTopColor: 'rgba(255, 255, 255, 0.1)',
    },
    candidatesTitle: {
        color: 'rgba(255, 255, 255, 0.7)',
        fontSize: 12,
        marginBottom: 6,
    },
    candidateItem: {
        color: 'rgba(255, 255, 255, 0.5)',
        fontSize: 11,
        marginLeft: 8,
    },
});

export default SessionStatsOverlay;
