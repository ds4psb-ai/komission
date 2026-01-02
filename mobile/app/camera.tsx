/**
 * Camera Screen - Hardened Version
 * 
 * Features:
 * - 4K/H.265 recording with automatic fallback
 * - Cross-platform support (iPhone + Galaxy)
 * - Adaptive quality based on device status
 * - Frame rate stability fixes
 * - Optimized WebSocket coaching integration
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { View, Text, StyleSheet, Pressable, Alert, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
    Camera,
    useCameraDevice,
    VideoFile,
    CameraRuntimeError,
} from 'react-native-vision-camera';

// Hooks
import { useCoachingWebSocket } from '@/hooks/useCoachingWebSocket';
import { useOptimizedCameraFormat, validateFormat, supports4K30fps } from '@/hooks/useCameraFormat';
import { useDeviceStatus, formatBatteryLevel, getBatteryIcon } from '@/hooks/useDeviceStatus';

// Config
import {
    RecordingConfig,
    buildRecordingOptions,
    getFileSizeEstimate,
    isH265Supported,
} from '@/config/recordingConfig';

// Components
import { CoachingOverlay } from '@/components/CoachingOverlay';
import { RecordButton } from '@/components/RecordButton';
import { QualityBadge } from '@/components/QualityBadge';
import { DeviceStatusBar } from '@/components/DeviceStatusBar';
import { useSessionPersistence } from '@/hooks/useSessionPersistence';

// Phase 1-5+ Components
import { CoachingModeSelector } from '@/components/CoachingModeSelector';
import { GraphicOverlay } from '@/components/GraphicOverlay';
import { TextCoachBubble } from '@/components/TextCoachBubble';
import { ShotlistTimeline } from '@/components/ShotlistTimeline';
import { FeedbackInput } from '@/components/FeedbackInput';
import { SessionStatsOverlay } from '@/components/SessionStatsOverlay';
import type {
    OutputMode,
    Persona,
    GraphicGuide,
    TextCoach,
    VdgCoachingData,
    AdaptiveResponse,
    SignalPromotion,
} from '@/hooks/useCoachingWebSocket';

// Phase 1.1-1.2: DirectorPack
import { useDirectorPack } from '@/hooks/useDirectorPack';
import { useLocalSearchParams } from 'expo-router';

export default function CameraScreen() {
    const router = useRouter();
    const cameraRef = useRef<Camera>(null);

    // ============================================================
    // Device Status (Battery, Network, Storage)
    // ============================================================
    const deviceStatus = useDeviceStatus();
    const [recordingConfig, setRecordingConfig] = useState<RecordingConfig>(
        deviceStatus.recommendedConfig
    );

    // Update config when device status changes
    useEffect(() => {
        if (deviceStatus.isReady) {
            setRecordingConfig(deviceStatus.recommendedConfig);
        }
    }, [deviceStatus.recommendedConfig, deviceStatus.isReady]);

    // ============================================================
    // Camera Setup
    // ============================================================
    const [hasPermission, setHasPermission] = useState(false);
    const [isRecording, setIsRecording] = useState(false);
    const [recordingTime, setRecordingTime] = useState(0);
    const [cameraError, setCameraError] = useState<string | null>(null);

    // ============================================================
    // Coaching Settings (Voice/Text toggles)
    // ============================================================
    const [voiceEnabled, setVoiceEnabled] = useState(true);
    const [textEnabled, setTextEnabled] = useState(true);
    const [showCompositionGuide, setShowCompositionGuide] = useState(false);

    // Phase 1: Output Mode + Persona
    const [outputMode, setOutputMode] = useState<OutputMode>('graphic');
    const [persona, setPersona] = useState<Persona>('chill_guide');
    const [showModeSelector, setShowModeSelector] = useState(false);

    // Phase 1-5+ State for received messages
    const [currentGraphicGuide, setCurrentGraphicGuide] = useState<GraphicGuide | null>(null);
    const [currentTextCoach, setCurrentTextCoach] = useState<TextCoach | null>(null);
    const [lastAdaptiveResponse, setLastAdaptiveResponse] = useState<AdaptiveResponse | null>(null);
    const [lastPromotion, setLastPromotion] = useState<SignalPromotion | null>(null);

    // ============================================================
    // Phase 1.2: DirectorPack with Real-time Step Tracking
    // ============================================================
    const { pattern: patternId } = useLocalSearchParams<{ pattern?: string }>();
    const {
        guideData,
        getCurrentGuideStep,
        getUpcomingGuideStep,
    } = useDirectorPack(patternId || null);

    // Current and upcoming steps based on recording time
    const currentStep = isRecording ? getCurrentGuideStep(recordingTime) : null;
    const upcomingStep = isRecording ? getUpcomingGuideStep(recordingTime) : null;

    // Get back camera
    const device = useCameraDevice('back');

    // Get optimized format with frame rate stability fixes
    const formatResult = useOptimizedCameraFormat(device, recordingConfig);
    const formatWarnings = formatResult.format
        ? validateFormat(formatResult, recordingConfig)
        : [];

    // Check 4K support
    const has4K = supports4K30fps(device);
    const hasH265 = isH265Supported();

    // ============================================================
    // WebSocket Coaching
    // ============================================================
    const sessionId = useRef(`${Platform.OS}_${Date.now()}_${Math.random().toString(36).slice(2)}`);
    const {
        feedback,
        isConnected,
        connect,
        disconnect,
        sendControl,
        // Phase 1-5+ additions
        vdgData,
        sendUserFeedback,
    } = useCoachingWebSocket(sessionId.current, {
        voiceEnabled,
        // Phase 1: Output Mode + Persona
        outputMode,
        persona,
        // Phase 1-5+ callbacks
        onGraphicGuide: setCurrentGraphicGuide,
        onTextCoach: setCurrentTextCoach,
        onAdaptiveResponse: setLastAdaptiveResponse,
        onSignalPromotion: setLastPromotion,
    });

    // ============================================================
    // Session Persistence (DB integration for RL)
    // ============================================================
    const {
        session,
        createSession,
        logIntervention,
        endSession,
    } = useSessionPersistence();

    // ============================================================
    // Permission Handling
    // ============================================================
    useEffect(() => {
        (async () => {
            try {
                const cameraStatus = await Camera.requestCameraPermission();
                const micStatus = await Camera.requestMicrophonePermission();
                setHasPermission(
                    cameraStatus === 'granted' && micStatus === 'granted'
                );
            } catch (error) {
                console.error('Permission error:', error);
                setHasPermission(false);
            }
        })();
    }, []);

    // ============================================================
    // Recording Timer
    // ============================================================
    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (isRecording) {
            interval = setInterval(() => {
                setRecordingTime((prev) => prev + 1);
            }, 1000);
        } else {
            setRecordingTime(0);
        }
        return () => clearInterval(interval);
    }, [isRecording]);

    // ============================================================
    // Camera Error Handler
    // ============================================================
    const handleCameraError = useCallback((error: CameraRuntimeError) => {
        console.error('Camera error:', error.code, error.message);
        setCameraError(error.message);

        // Handle specific errors
        if (error.code === 'session/camera-not-ready') {
            // Retry after a short delay
            setTimeout(() => setCameraError(null), 1000);
        }
    }, []);

    // ============================================================
    // Recording Handlers
    // ============================================================
    const startRecording = useCallback(async () => {
        if (!cameraRef.current || !formatResult.format) {
            Alert.alert('오류', '카메라가 준비되지 않았습니다.');
            return;
        }

        // Show warnings if any
        if (deviceStatus.warnings.length > 0) {
            console.log('Recording warnings:', deviceStatus.warnings);
        }

        try {
            // Connect to coaching WebSocket
            connect();
            sendControl('start');

            setIsRecording(true);
            setCameraError(null);

            // Build recording options with H.265 if supported
            const options = buildRecordingOptions(
                recordingConfig,
                handleRecordingFinished,
                handleRecordingError
            );

            console.log('Starting recording with config:', {
                quality: recordingConfig.quality,
                codec: recordingConfig.codec,
                bitrate: recordingConfig.bitrate,
                resolution: `${recordingConfig.width}×${recordingConfig.height}`,
            });

            await cameraRef.current.startRecording(options);
        } catch (error) {
            console.error('Start recording error:', error);
            setIsRecording(false);
            disconnect();
            Alert.alert('녹화 시작 실패', String(error));
        }
    }, [connect, disconnect, sendControl, recordingConfig, formatResult.format, deviceStatus.warnings]);

    const stopRecording = useCallback(async () => {
        if (!cameraRef.current || !isRecording) return;

        try {
            sendControl('stop');
            await cameraRef.current.stopRecording();
            disconnect();
            setIsRecording(false);
        } catch (error) {
            console.error('Stop recording error:', error);
            setIsRecording(false);
            disconnect();
        }
    }, [isRecording, disconnect, sendControl]);

    const handleRecordingFinished = useCallback((video: VideoFile) => {
        console.log('Recording saved:', {
            path: video.path,
            duration: video.duration,
        });

        const estimatedSize = getFileSizeEstimate(recordingTime, recordingConfig);

        Alert.alert(
            '촬영 완료! 🎬',
            [
                `⏱️ ${formatTime(recordingTime)}`,
                `📹 ${recordingConfig.quality.toUpperCase()} / ${recordingConfig.codec.toUpperCase()}`,
                `💾 약 ${estimatedSize}`,
            ].join('\n'),
            [
                {
                    text: '웹앱에서 업로드',
                    onPress: () => {
                        // TODO: Deep link to web app with video path
                        router.back();
                    },
                },
                {
                    text: '다시 촬영',
                    style: 'cancel',
                    onPress: () => setRecordingTime(0),
                },
            ]
        );
    }, [recordingTime, recordingConfig, router]);

    const handleRecordingError = useCallback((error: CameraRuntimeError) => {
        console.error('Recording error:', error);
        setIsRecording(false);
        disconnect();

        Alert.alert(
            '녹화 오류',
            `${error.message}\n\n코드: ${error.code}`,
            [{ text: '확인' }]
        );
    }, [disconnect]);

    // ============================================================
    // Utility Functions
    // ============================================================
    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    // ============================================================
    // Render: Permission Denied
    // ============================================================
    if (!hasPermission) {
        return (
            <SafeAreaView style={styles.container}>
                <View style={styles.centerContent}>
                    <Text style={styles.permissionIcon}>📷</Text>
                    <Text style={styles.permissionTitle}>카메라 권한 필요</Text>
                    <Text style={styles.permissionText}>
                        4K AI 코칭을 위해{'\n'}카메라와 마이크 권한이 필요합니다
                    </Text>
                    <Pressable
                        style={styles.permissionButton}
                        onPress={() => Camera.requestCameraPermission()}
                    >
                        <Text style={styles.permissionButtonText}>권한 허용하기</Text>
                    </Pressable>
                    <Pressable style={styles.backLink} onPress={() => router.back()}>
                        <Text style={styles.backLinkText}>← 돌아가기</Text>
                    </Pressable>
                </View>
            </SafeAreaView>
        );
    }

    // ============================================================
    // Render: No Device
    // ============================================================
    if (!device || !formatResult.format) {
        return (
            <SafeAreaView style={styles.container}>
                <View style={styles.centerContent}>
                    <Text style={styles.errorIcon}>⚠️</Text>
                    <Text style={styles.errorTitle}>카메라를 찾을 수 없습니다</Text>
                    <Text style={styles.errorText}>
                        {!device
                            ? '기기에서 카메라를 감지할 수 없습니다.'
                            : `지원되지 않는 포맷: ${recordingConfig.quality}`}
                    </Text>
                    <Pressable style={styles.backLink} onPress={() => router.back()}>
                        <Text style={styles.backLinkText}>← 돌아가기</Text>
                    </Pressable>
                </View>
            </SafeAreaView>
        );
    }

    // ============================================================
    // Render: Camera View
    // ============================================================
    return (
        <View style={styles.container}>
            {/* Camera Preview */}
            <Camera
                ref={cameraRef}
                style={StyleSheet.absoluteFill}
                device={device}
                format={formatResult.format}
                isActive={!cameraError}
                video={true}
                audio={true}
                videoHdr={recordingConfig.enableHDR && formatResult.supportsHDR}
                videoStabilizationMode="off"
                onError={handleCameraError}
            />

            {/* Coaching Overlay (Original) */}
            <CoachingOverlay
                feedback={feedback}
                isConnected={isConnected}
                recordingTime={recordingTime}
                isRecording={isRecording}
                voiceEnabled={voiceEnabled}
                textEnabled={textEnabled}
                onVoiceToggle={setVoiceEnabled}
                onTextToggle={setTextEnabled}
                compositionGuide={showCompositionGuide ? { type: 'rule_of_thirds', enabled: true } : undefined}
            />

            {/* Phase 1: Graphic Overlay with Real-time DirectorPack Steps */}
            {isRecording && outputMode !== 'text' && outputMode !== 'audio' && (
                <GraphicOverlay
                    guide={currentGraphicGuide}
                    currentStep={currentStep}
                    upcomingStep={upcomingStep}
                    gridType={showCompositionGuide ? 'rule_of_thirds' : 'none'}
                    recordingTime={recordingTime}
                    showGrid={showCompositionGuide}
                />
            )}

            {/* Phase 1: Text Coach Bubble */}
            {isRecording && (outputMode === 'text' || outputMode === 'graphic') && (
                <TextCoachBubble coach={currentTextCoach} />
            )}

            {/* Phase 2: Shotlist Timeline */}
            {isRecording && vdgData && (
                <ShotlistTimeline
                    vdgData={vdgData}
                    currentTime={recordingTime}
                    totalDuration={guideData.duration}  // From DirectorPack
                />
            )}

            {/* Phase 3: Feedback Input */}
            {isRecording && (
                <FeedbackInput
                    onSend={sendUserFeedback}
                    lastResponse={lastAdaptiveResponse}
                    disabled={!isConnected}
                />
            )}

            {/* Phase 5+: Signal Promotion */}
            <SessionStatsOverlay
                promotion={lastPromotion}
                onDismiss={() => setLastPromotion(null)}
            />

            {/* Controls Layer */}
            <SafeAreaView style={styles.controlsContainer} edges={['top', 'bottom']}>
                {/* Top Bar */}
                <View style={styles.topBar}>
                    {/* Back Button */}
                    <Pressable
                        style={styles.backButton}
                        onPress={() => router.back()}
                        disabled={isRecording}
                    >
                        <Text style={styles.backButtonText}>✕</Text>
                    </Pressable>

                    {/* Recording Time */}
                    {isRecording && (
                        <View style={styles.timeContainer}>
                            <View style={styles.recordingDot} />
                            <Text style={styles.timeText}>{formatTime(recordingTime)}</Text>
                        </View>
                    )}

                    {/* Quality Badge */}
                    <QualityBadge
                        quality={recordingConfig.quality}
                        codec={recordingConfig.codec}
                        hasH265={hasH265}
                        has4K={has4K}
                    />
                </View>

                {/* Device Status Bar (Warnings) */}
                {!isRecording && deviceStatus.warnings.length > 0 && (
                    <DeviceStatusBar
                        warnings={deviceStatus.warnings}
                        batteryLevel={deviceStatus.batteryLevel}
                        batteryCharging={deviceStatus.batteryCharging}
                    />
                )}

                {/* Camera Error */}
                {cameraError && (
                    <View style={styles.errorBanner}>
                        <Text style={styles.errorBannerText}>⚠️ {cameraError}</Text>
                    </View>
                )}

                {/* Bottom Controls */}
                <View style={styles.bottomBar}>
                    {/* Format Info (Debug) */}
                    {__DEV__ && (
                        <Text style={styles.debugText}>
                            {formatResult.formatInfo} | {recordingConfig.codec.toUpperCase()}
                        </Text>
                    )}

                    {/* Record Button */}
                    <RecordButton
                        isRecording={isRecording}
                        onPress={isRecording ? stopRecording : startRecording}
                    />

                    {/* Estimated File Size */}
                    {isRecording && (
                        <Text style={styles.fileSizeText}>
                            ~{getFileSizeEstimate(recordingTime, recordingConfig)}
                        </Text>
                    )}
                </View>
            </SafeAreaView>
        </View>
    );
}

// ============================================================
// Styles
// ============================================================
const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#000',
    },
    centerContent: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 32,
    },
    permissionIcon: {
        fontSize: 64,
        marginBottom: 24,
    },
    permissionTitle: {
        fontSize: 24,
        fontWeight: '700',
        color: '#fff',
        marginBottom: 12,
    },
    permissionText: {
        fontSize: 16,
        color: 'rgba(255,255,255,0.6)',
        textAlign: 'center',
        marginBottom: 32,
        lineHeight: 24,
    },
    permissionButton: {
        backgroundColor: '#3b82f6',
        paddingVertical: 14,
        paddingHorizontal: 28,
        borderRadius: 12,
    },
    permissionButtonText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: '600',
    },
    backLink: {
        marginTop: 24,
        padding: 12,
    },
    backLinkText: {
        color: 'rgba(255,255,255,0.5)',
        fontSize: 14,
    },
    errorIcon: {
        fontSize: 64,
        marginBottom: 24,
    },
    errorTitle: {
        fontSize: 20,
        fontWeight: '600',
        color: '#fff',
        marginBottom: 12,
    },
    errorText: {
        fontSize: 14,
        color: 'rgba(255,255,255,0.5)',
        textAlign: 'center',
    },
    controlsContainer: {
        ...StyleSheet.absoluteFillObject,
        justifyContent: 'space-between',
    },
    topBar: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingHorizontal: 20,
        paddingTop: 12,
    },
    backButton: {
        width: 44,
        height: 44,
        borderRadius: 22,
        backgroundColor: 'rgba(0,0,0,0.4)',
        justifyContent: 'center',
        alignItems: 'center',
    },
    backButtonText: {
        color: '#fff',
        fontSize: 20,
    },
    timeContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'rgba(0,0,0,0.5)',
        paddingVertical: 8,
        paddingHorizontal: 16,
        borderRadius: 20,
    },
    recordingDot: {
        width: 8,
        height: 8,
        borderRadius: 4,
        backgroundColor: '#ef4444',
        marginRight: 8,
    },
    timeText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: '600',
        fontVariant: ['tabular-nums'],
    },
    errorBanner: {
        backgroundColor: 'rgba(239, 68, 68, 0.9)',
        paddingVertical: 8,
        paddingHorizontal: 16,
        marginHorizontal: 20,
        borderRadius: 8,
    },
    errorBannerText: {
        color: '#fff',
        fontSize: 14,
        textAlign: 'center',
    },
    bottomBar: {
        alignItems: 'center',
        paddingBottom: 24,
    },
    debugText: {
        color: 'rgba(255,255,255,0.4)',
        fontSize: 10,
        marginBottom: 16,
        fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    },
    fileSizeText: {
        color: 'rgba(255,255,255,0.5)',
        fontSize: 12,
        marginTop: 12,
    },
});
