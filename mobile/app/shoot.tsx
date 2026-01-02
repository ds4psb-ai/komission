/**
 * Shoot Screen - Phase 1.4
 * 
 * Ported from frontend: session/shoot/page.tsx (696 lines)
 * 
 * Features:
 * - DirectorPack loading with offline/error handling
 * - Checkpoint-based shooting guide
 * - Priority-sorted steps with reasons
 * - Tips section
 * - Start recording CTA
 */

import React, { useState, useMemo, useCallback } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    Pressable,
    ActivityIndicator,
    RefreshControl,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useDirectorPack } from '@/hooks/useDirectorPack';
import { sortStepsByPriority, GuideStep } from '@/services/directorPackService';

// ============================================================
// Constants
// ============================================================

const PRIORITY_STYLES: Record<string, { bg: string; border: string; text: string }> = {
    critical: { bg: 'rgba(239, 68, 68, 0.1)', border: 'rgba(239, 68, 68, 0.3)', text: '#fca5a5' },
    high: { bg: 'rgba(249, 115, 22, 0.1)', border: 'rgba(249, 115, 22, 0.3)', text: '#fdba74' },
    medium: { bg: 'rgba(234, 179, 8, 0.1)', border: 'rgba(234, 179, 8, 0.3)', text: '#fde047' },
    low: { bg: 'rgba(34, 197, 94, 0.1)', border: 'rgba(34, 197, 94, 0.3)', text: '#86efac' },
};

// ============================================================
// Component
// ============================================================

export default function ShootScreen() {
    const router = useRouter();
    const { pattern: patternId } = useLocalSearchParams<{ pattern?: string }>();

    const {
        guideData,
        isLoading,
        error,
        isOffline,
        retry,
    } = useDirectorPack(patternId || null);

    const [refreshing, setRefreshing] = useState(false);

    // Sort steps by priority
    const sortedSteps = useMemo(() => {
        return sortStepsByPriority(guideData.steps);
    }, [guideData.steps]);

    // Handle refresh
    const onRefresh = useCallback(async () => {
        setRefreshing(true);
        retry();
        // Simulate minimum refresh time
        await new Promise(resolve => setTimeout(resolve, 500));
        setRefreshing(false);
    }, [retry]);

    // Navigate to camera with pattern
    const handleStartRecording = useCallback(() => {
        router.push({
            pathname: '/camera',
            params: patternId ? { pattern: patternId } : {},
        });
    }, [router, patternId]);

    return (
        <SafeAreaView style={styles.container} edges={['top']}>
            {/* Header */}
            <View style={styles.header}>
                <Pressable
                    style={styles.backButton}
                    onPress={() => router.back()}
                >
                    <Text style={styles.backButtonText}>←</Text>
                </Pressable>
                <View style={styles.headerCenter}>
                    <Text style={styles.headerIcon}>🎬</Text>
                    <Text style={styles.headerTitle}>촬영 가이드</Text>
                    {guideData.isLive && (
                        <View style={styles.liveBadge}>
                            <Text style={styles.liveBadgeText}>LIVE</Text>
                        </View>
                    )}
                </View>
                <View style={styles.headerRight} />
            </View>

            <ScrollView
                style={styles.scrollView}
                contentContainerStyle={styles.scrollContent}
                refreshControl={
                    <RefreshControl
                        refreshing={refreshing}
                        onRefresh={onRefresh}
                        tintColor="#a78bfa"
                    />
                }
            >
                {/* Offline Banner */}
                {isOffline && (
                    <View style={styles.offlineBanner}>
                        <View style={styles.offlineDot} />
                        <Text style={styles.offlineText}>
                            오프라인 상태입니다. 인터넷 연결을 확인해주세요.
                        </Text>
                    </View>
                )}

                {/* No Pattern Warning */}
                {!patternId && !isLoading && (
                    <View style={styles.infoBanner}>
                        <Text style={styles.infoBannerTitle}>ℹ️ 패턴을 선택하지 않았습니다</Text>
                        <Text style={styles.infoBannerText}>
                            기본 촬영 가이드를 표시합니다.
                        </Text>
                        <Pressable
                            style={styles.infoBannerLink}
                            onPress={() => router.push('/for-you')}
                        >
                            <Text style={styles.infoBannerLinkText}>
                                패턴 선택하러 가기 →
                            </Text>
                        </Pressable>
                    </View>
                )}

                {/* Loading State */}
                {isLoading && (
                    <View style={styles.loadingContainer}>
                        <ActivityIndicator size="large" color="#a78bfa" />
                        <Text style={styles.loadingText}>가이드 불러오는 중...</Text>
                    </View>
                )}

                {/* Error Banner */}
                {error && !isLoading && (
                    <View style={styles.errorBanner}>
                        <View style={styles.errorBannerHeader}>
                            <Text style={styles.errorBannerIcon}>⚠️</Text>
                            <View style={styles.errorBannerContent}>
                                <Text style={styles.errorBannerTitle}>
                                    Director Pack을 불러오지 못했습니다
                                </Text>
                                <Text style={styles.errorBannerText}>
                                    기본 가이드를 표시합니다. ({error})
                                </Text>
                            </View>
                            <Pressable onPress={retry} style={styles.retryButton}>
                                <Text style={styles.retryButtonText}>🔄</Text>
                            </Pressable>
                        </View>
                    </View>
                )}

                {/* Pattern Summary */}
                {!isLoading && (
                    <View style={styles.patternCard}>
                        <Text style={styles.patternTitle}>{guideData.title}</Text>
                        {guideData.goal && guideData.goal !== guideData.title && (
                            <Text style={styles.patternGoal}>🎯 {guideData.goal}</Text>
                        )}
                        <View style={styles.patternMeta}>
                            <Text style={styles.patternMetaItem}>⏱️ {guideData.duration}초</Text>
                            <Text style={styles.patternMetaItem}>🎵 {guideData.bpm} BPM</Text>
                        </View>
                    </View>
                )}

                {/* Step-by-Step Guide */}
                {!isLoading && (
                    <View style={styles.section}>
                        <Text style={styles.sectionTitle}>
                            촬영 순서 ({guideData.steps.length}개)
                        </Text>
                        <View style={styles.stepsContainer}>
                            {sortedSteps.map((step, index) => (
                                <StepCard key={step.ruleId || index} step={step} />
                            ))}
                        </View>
                    </View>
                )}

                {/* Tips */}
                {!isLoading && guideData.tips.length > 0 && (
                    <View style={styles.section}>
                        <Text style={styles.sectionTitle}>💡 촬영 팁</Text>
                        <View style={styles.tipsContainer}>
                            {guideData.tips.map((tip, index) => (
                                <View key={index} style={styles.tipCard}>
                                    <Text style={styles.tipBullet}>•</Text>
                                    <Text style={styles.tipText}>{tip}</Text>
                                </View>
                            ))}
                        </View>
                    </View>
                )}

                {/* Spacer for CTA */}
                <View style={styles.ctaSpacer} />
            </ScrollView>

            {/* Start Recording CTA */}
            {!isLoading && (
                <View style={styles.ctaContainer}>
                    <Pressable
                        style={styles.ctaButton}
                        onPress={handleStartRecording}
                    >
                        <Text style={styles.ctaIcon}>▶️</Text>
                        <Text style={styles.ctaText}>촬영 시작하기</Text>
                    </Pressable>
                </View>
            )}
        </SafeAreaView>
    );
}

// ============================================================
// Step Card Component
// ============================================================

function StepCard({ step }: { step: GuideStep }) {
    const priorityStyle = step.priority
        ? PRIORITY_STYLES[step.priority]
        : PRIORITY_STYLES.medium;

    return (
        <View
            style={[
                styles.stepCard,
                {
                    backgroundColor: priorityStyle.bg,
                    borderColor: priorityStyle.border,
                },
            ]}
        >
            <Text style={styles.stepIcon}>{step.icon}</Text>
            <View style={styles.stepContent}>
                <View style={styles.stepHeader}>
                    <Text style={styles.stepTime}>{step.time}</Text>
                    {step.priority && (
                        <View
                            style={[
                                styles.priorityBadge,
                                { backgroundColor: priorityStyle.border },
                            ]}
                        >
                            <Text
                                style={[styles.priorityBadgeText, { color: priorityStyle.text }]}
                            >
                                {step.priority.toUpperCase()}
                            </Text>
                        </View>
                    )}
                </View>
                <Text style={styles.stepAction}>{step.action}</Text>
                {step.reason && (
                    <Text style={styles.stepReason}>💡 {step.reason}</Text>
                )}
            </View>
        </View>
    );
}

// ============================================================
// Styles
// ============================================================

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0a0a0f',
    },

    // Header
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: 16,
        paddingVertical: 12,
        borderBottomWidth: 1,
        borderBottomColor: 'rgba(255, 255, 255, 0.05)',
    },
    backButton: {
        width: 40,
        height: 40,
        justifyContent: 'center',
        alignItems: 'center',
        borderRadius: 20,
    },
    backButtonText: {
        color: '#fff',
        fontSize: 20,
    },
    headerCenter: {
        flex: 1,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
    },
    headerIcon: {
        fontSize: 20,
    },
    headerTitle: {
        color: '#fff',
        fontSize: 18,
        fontWeight: '700',
    },
    liveBadge: {
        backgroundColor: 'rgba(34, 197, 94, 0.2)',
        paddingHorizontal: 8,
        paddingVertical: 2,
        borderRadius: 8,
    },
    liveBadgeText: {
        color: '#4ade80',
        fontSize: 10,
        fontWeight: '600',
    },
    headerRight: {
        width: 40,
    },

    // Scroll
    scrollView: {
        flex: 1,
    },
    scrollContent: {
        padding: 16,
        paddingBottom: 100,
    },

    // Banners
    offlineBanner: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        borderWidth: 1,
        borderColor: 'rgba(239, 68, 68, 0.2)',
        borderRadius: 12,
        padding: 12,
        marginBottom: 16,
    },
    offlineDot: {
        width: 8,
        height: 8,
        borderRadius: 4,
        backgroundColor: '#ef4444',
        marginRight: 12,
    },
    offlineText: {
        color: '#fca5a5',
        fontSize: 13,
        flex: 1,
    },

    infoBanner: {
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 1,
        borderColor: 'rgba(59, 130, 246, 0.2)',
        borderRadius: 12,
        padding: 16,
        marginBottom: 16,
    },
    infoBannerTitle: {
        color: '#93c5fd',
        fontSize: 14,
        fontWeight: '600',
    },
    infoBannerText: {
        color: 'rgba(255, 255, 255, 0.5)',
        fontSize: 12,
        marginTop: 4,
    },
    infoBannerLink: {
        marginTop: 12,
    },
    infoBannerLinkText: {
        color: '#60a5fa',
        fontSize: 12,
        textDecorationLine: 'underline',
    },

    errorBanner: {
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        borderWidth: 1,
        borderColor: 'rgba(245, 158, 11, 0.2)',
        borderRadius: 12,
        padding: 12,
        marginBottom: 16,
    },
    errorBannerHeader: {
        flexDirection: 'row',
        alignItems: 'flex-start',
    },
    errorBannerIcon: {
        fontSize: 18,
        marginRight: 12,
    },
    errorBannerContent: {
        flex: 1,
    },
    errorBannerTitle: {
        color: '#fcd34d',
        fontSize: 14,
        fontWeight: '600',
    },
    errorBannerText: {
        color: 'rgba(255, 255, 255, 0.5)',
        fontSize: 12,
        marginTop: 4,
    },
    retryButton: {
        padding: 8,
    },
    retryButtonText: {
        fontSize: 16,
    },

    // Loading
    loadingContainer: {
        alignItems: 'center',
        paddingVertical: 48,
    },
    loadingText: {
        color: 'rgba(255, 255, 255, 0.5)',
        fontSize: 14,
        marginTop: 12,
    },

    // Pattern Card
    patternCard: {
        backgroundColor: 'rgba(139, 92, 246, 0.1)',
        borderWidth: 1,
        borderColor: 'rgba(139, 92, 246, 0.2)',
        borderRadius: 16,
        padding: 16,
        marginBottom: 24,
    },
    patternTitle: {
        color: '#fff',
        fontSize: 18,
        fontWeight: '700',
    },
    patternGoal: {
        color: 'rgba(255, 255, 255, 0.6)',
        fontSize: 14,
        marginTop: 8,
    },
    patternMeta: {
        flexDirection: 'row',
        gap: 16,
        marginTop: 12,
    },
    patternMetaItem: {
        color: 'rgba(255, 255, 255, 0.5)',
        fontSize: 12,
    },

    // Section
    section: {
        marginBottom: 24,
    },
    sectionTitle: {
        color: 'rgba(255, 255, 255, 0.6)',
        fontSize: 14,
        fontWeight: '500',
        marginBottom: 12,
    },

    // Steps
    stepsContainer: {
        gap: 8,
    },
    stepCard: {
        flexDirection: 'row',
        alignItems: 'flex-start',
        borderWidth: 1,
        borderRadius: 12,
        padding: 12,
    },
    stepIcon: {
        fontSize: 28,
        marginRight: 12,
    },
    stepContent: {
        flex: 1,
    },
    stepHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
        marginBottom: 4,
    },
    stepTime: {
        color: '#a78bfa',
        fontSize: 12,
        fontWeight: '600',
    },
    priorityBadge: {
        paddingHorizontal: 6,
        paddingVertical: 2,
        borderRadius: 4,
    },
    priorityBadgeText: {
        fontSize: 10,
        fontWeight: '600',
    },
    stepAction: {
        color: 'rgba(255, 255, 255, 0.8)',
        fontSize: 14,
    },
    stepReason: {
        color: 'rgba(74, 222, 128, 0.7)',
        fontSize: 12,
        marginTop: 6,
    },

    // Tips
    tipsContainer: {
        gap: 8,
    },
    tipCard: {
        flexDirection: 'row',
        alignItems: 'flex-start',
        backgroundColor: 'rgba(245, 158, 11, 0.05)',
        borderWidth: 1,
        borderColor: 'rgba(245, 158, 11, 0.1)',
        borderRadius: 8,
        padding: 10,
    },
    tipBullet: {
        color: '#fbbf24',
        fontSize: 14,
        marginRight: 8,
    },
    tipText: {
        color: 'rgba(255, 255, 255, 0.7)',
        fontSize: 13,
        flex: 1,
    },

    // CTA
    ctaSpacer: {
        height: 80,
    },
    ctaContainer: {
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        padding: 16,
        paddingBottom: 32,
        backgroundColor: '#0a0a0f',
        borderTopWidth: 1,
        borderTopColor: 'rgba(255, 255, 255, 0.05)',
    },
    ctaButton: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#8b5cf6',
        paddingVertical: 16,
        borderRadius: 16,
        gap: 8,
    },
    ctaIcon: {
        fontSize: 18,
    },
    ctaText: {
        color: '#fff',
        fontSize: 18,
        fontWeight: '700',
    },
});
