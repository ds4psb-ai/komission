"use client";

import React, { useState, useRef, useEffect, useCallback } from 'react';

interface FilmingGuideProps {
    isOpen: boolean;
    onClose: () => void;
    guideVideoUrl?: string;  // Optional guide video to overlay
    bpm?: number;            // BPM for beat timer
    duration?: number;       // Duration in seconds
    onRecordingComplete?: (blob: Blob, syncOffset: number) => void;
}

/**
 * Ghost Overlay Filming Guide
 * 
 * CTO Decision: NO real-time AR pose detection (causes mobile overheating)
 * Instead: Simple transparent video overlay + beat timer + audio sync slider
 */
export function FilmingGuide({
    isOpen,
    onClose,
    guideVideoUrl,
    bpm = 120,
    duration = 15,
    onRecordingComplete
}: FilmingGuideProps) {
    // State
    const [isRecording, setIsRecording] = useState(false);
    const [countdown, setCountdown] = useState<number | null>(null);
    const [recordingTime, setRecordingTime] = useState(0);
    const [beatCount, setBeatCount] = useState(0);
    const [syncOffset, setSyncOffset] = useState(0);  // -0.5s to +0.5s
    const [showSyncUI, setShowSyncUI] = useState(false);
    const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);

    // Refs
    const videoRef = useRef<HTMLVideoElement>(null);
    const guideVideoRef = useRef<HTMLVideoElement>(null);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const chunksRef = useRef<Blob[]>([]);

    // Beat interval in ms
    const beatInterval = (60 / bpm) * 1000;

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (streamRef.current) {
                streamRef.current.getTracks().forEach(track => track.stop());
            }
        };
    }, []);

    // ESC to close
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose();
        };
        if (isOpen) {
            window.addEventListener('keydown', handleKeyDown);
            return () => window.removeEventListener('keydown', handleKeyDown);
        }
    }, [isOpen, onClose]);

    // Start camera preview
    const startCamera = useCallback(async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'user',
                    width: { ideal: 1080 },
                    height: { ideal: 1920 }  // Portrait mode
                },
                audio: true
            });

            streamRef.current = stream;
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
            }
        } catch (error) {
            console.error('Camera access denied:', error);
            alert('카메라 접근이 거부되었습니다. 권한을 확인해주세요.');
        }
    }, []);

    // Initialize camera when opened
    useEffect(() => {
        if (isOpen) {
            startCamera();
        } else {
            // Cleanup when closed
            if (streamRef.current) {
                streamRef.current.getTracks().forEach(track => track.stop());
                streamRef.current = null;
            }
            setIsRecording(false);
            setRecordingTime(0);
            setBeatCount(0);
            setRecordedBlob(null);
            setShowSyncUI(false);
        }
    }, [isOpen, startCamera]);

    // Recording timer
    useEffect(() => {
        if (!isRecording) return;

        const startTime = Date.now();
        const timer = setInterval(() => {
            const elapsed = (Date.now() - startTime) / 1000;
            setRecordingTime(elapsed);
            setBeatCount(Math.floor(elapsed / (60 / bpm)));

            if (elapsed >= duration) {
                stopRecording();
            }
        }, 50);

        return () => clearInterval(timer);
    }, [isRecording, bpm, duration]);

    // Start countdown then record
    const startCountdown = useCallback(() => {
        setCountdown(3);

        const countdownInterval = setInterval(() => {
            setCountdown(prev => {
                if (prev === null || prev <= 1) {
                    clearInterval(countdownInterval);
                    setCountdown(null);
                    startRecording();
                    return null;
                }
                return prev - 1;
            });
        }, 1000);
    }, []);

    // Start actual recording
    const startRecording = useCallback(() => {
        if (!streamRef.current) return;

        chunksRef.current = [];
        const mediaRecorder = new MediaRecorder(streamRef.current, {
            mimeType: 'video/webm;codecs=vp9'
        });

        mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) {
                chunksRef.current.push(e.data);
            }
        };

        mediaRecorder.onstop = () => {
            const blob = new Blob(chunksRef.current, { type: 'video/webm' });
            setRecordedBlob(blob);
            setShowSyncUI(true);  // Show sync adjustment UI
        };

        mediaRecorderRef.current = mediaRecorder;
        mediaRecorder.start(100);  // Collect data every 100ms
        setIsRecording(true);
        setRecordingTime(0);
        setBeatCount(0);

        // Start guide video if available
        if (guideVideoRef.current) {
            guideVideoRef.current.currentTime = 0;
            guideVideoRef.current.play();
        }
    }, []);

    // Stop recording
    const stopRecording = useCallback(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
            mediaRecorderRef.current.stop();
        }
        setIsRecording(false);

        if (guideVideoRef.current) {
            guideVideoRef.current.pause();
        }
    }, []);

    // Finish with sync offset
    const finishWithSync = useCallback(() => {
        if (recordedBlob && onRecordingComplete) {
            onRecordingComplete(recordedBlob, syncOffset);
        }
        onClose();
    }, [recordedBlob, syncOffset, onRecordingComplete, onClose]);

    if (!isOpen) return null;

    // Progress percentage
    const progress = Math.min((recordingTime / duration) * 100, 100);

    return (
        <div className="fixed inset-0 z-50 bg-black flex flex-col">
            {/* Camera View */}
            <div className="flex-1 relative overflow-hidden">
                {/* User Camera Feed */}
                <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className="absolute inset-0 w-full h-full object-cover"
                    style={{ transform: 'scaleX(-1)' }}  // Mirror mode
                />

                {/* 👻 Ghost Overlay - Transparent Guide Video */}
                {guideVideoUrl && (
                    <video
                        ref={guideVideoRef}
                        src={guideVideoUrl}
                        playsInline
                        muted
                        loop
                        className="absolute inset-0 w-full h-full object-cover pointer-events-none"
                        style={{
                            opacity: 0.3,  // Ghost transparency
                            mixBlendMode: 'screen'
                        }}
                    />
                )}

                {/* Countdown Overlay */}
                {countdown !== null && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/60">
                        <div className="text-9xl font-black text-white animate-pulse">
                            {countdown}
                        </div>
                    </div>
                )}

                {/* Recording Indicator */}
                {isRecording && (
                    <>
                        {/* Top Bar */}
                        <div className="absolute top-0 left-0 right-0 p-4 flex justify-between items-center bg-gradient-to-b from-black/60 to-transparent">
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                                <span className="text-white font-bold text-sm">녹화중</span>
                            </div>
                            <div className="text-white font-mono text-sm">
                                {recordingTime.toFixed(1)}s / {duration}s
                            </div>
                        </div>

                        {/* Progress Bar */}
                        <div className="absolute top-14 left-4 right-4 h-1 bg-white/20 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-violet-500 to-pink-500 transition-all"
                                style={{ width: `${progress}%` }}
                            />
                        </div>

                        {/* 🎵 Beat Timer */}
                        <div className="absolute top-20 left-1/2 transform -translate-x-1/2">
                            <div className={`
                                w-16 h-16 rounded-full flex items-center justify-center
                                border-4 transition-all duration-100
                                ${beatCount % 4 === 0
                                    ? 'bg-violet-500 border-violet-300 scale-110'
                                    : 'bg-white/20 border-white/40 scale-100'}
                            `}>
                                <span className="text-2xl font-black text-white">
                                    {(beatCount % 4) + 1}
                                </span>
                            </div>
                            <div className="text-center mt-2 text-white/60 text-xs">
                                {bpm} BPM
                            </div>
                        </div>
                    </>
                )}

                {/* 🎚️ Audio Sync Adjustment UI */}
                {showSyncUI && recordedBlob && (
                    <div className="absolute inset-0 bg-black/80 flex items-center justify-center">
                        <div className="bg-[#111] border border-white/10 rounded-2xl p-6 max-w-md w-full mx-4">
                            <h3 className="text-xl font-bold text-white mb-2">🎵 오디오 싱크 조절</h3>
                            <p className="text-white/50 text-sm mb-6">
                                영상과 소리가 안 맞으면 슬라이더로 조절하세요
                            </p>

                            {/* Preview */}
                            <video
                                src={URL.createObjectURL(recordedBlob)}
                                controls
                                className="w-full rounded-lg mb-6"
                            />

                            {/* Sync Slider */}
                            <div className="mb-6">
                                <div className="flex justify-between text-xs text-white/40 mb-2">
                                    <span>소리가 빠름 (-0.5s)</span>
                                    <span>소리가 느림 (+0.5s)</span>
                                </div>
                                <input
                                    type="range"
                                    min="-500"
                                    max="500"
                                    value={syncOffset}
                                    onChange={(e) => setSyncOffset(Number(e.target.value))}
                                    className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer
                                               [&::-webkit-slider-thumb]:appearance-none
                                               [&::-webkit-slider-thumb]:w-5
                                               [&::-webkit-slider-thumb]:h-5
                                               [&::-webkit-slider-thumb]:bg-violet-500
                                               [&::-webkit-slider-thumb]:rounded-full
                                               [&::-webkit-slider-thumb]:cursor-pointer"
                                />
                                <div className="text-center text-white font-mono mt-2">
                                    {syncOffset >= 0 ? '+' : ''}{(syncOffset / 1000).toFixed(2)}s
                                </div>
                            </div>

                            {/* Actions */}
                            <div className="flex gap-3">
                                <button
                                    onClick={() => {
                                        setShowSyncUI(false);
                                        setRecordedBlob(null);
                                    }}
                                    className="flex-1 py-3 bg-white/5 border border-white/10 rounded-xl text-white/60 hover:bg-white/10 transition-colors"
                                >
                                    다시 촬영
                                </button>
                                <button
                                    onClick={finishWithSync}
                                    className="flex-1 py-3 bg-violet-500 hover:bg-violet-400 rounded-xl text-white font-bold transition-colors"
                                >
                                    완료 ✓
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Bottom Controls */}
            {!showSyncUI && (
                <div className="p-6 bg-gradient-to-t from-black via-black/80 to-transparent">
                    <div className="flex items-center justify-center gap-8">
                        {/* Close Button */}
                        <button
                            onClick={onClose}
                            className="w-14 h-14 rounded-full bg-white/10 border border-white/20 flex items-center justify-center text-white/60 hover:bg-white/20 transition-colors"
                        >
                            ✕
                        </button>

                        {/* Record Button */}
                        <button
                            onClick={isRecording ? stopRecording : startCountdown}
                            disabled={countdown !== null}
                            className={`
                                w-20 h-20 rounded-full flex items-center justify-center transition-all
                                ${isRecording
                                    ? 'bg-red-500 hover:bg-red-400'
                                    : 'bg-white hover:bg-white/90'}
                                ${countdown !== null ? 'opacity-50' : ''}
                            `}
                        >
                            {isRecording ? (
                                <div className="w-8 h-8 bg-white rounded-sm" />
                            ) : (
                                <div className="w-16 h-16 bg-red-500 rounded-full" />
                            )}
                        </button>

                        {/* Flip Camera (placeholder) */}
                        <button
                            className="w-14 h-14 rounded-full bg-white/10 border border-white/20 flex items-center justify-center text-white/60 hover:bg-white/20 transition-colors"
                        >
                            🔄
                        </button>
                    </div>

                    {/* Ghost Overlay Info */}
                    {guideVideoUrl && !isRecording && (
                        <div className="text-center mt-4 text-white/40 text-xs">
                            👻 Ghost Overlay 활성화 - 가이드 영상을 따라 촬영하세요
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
