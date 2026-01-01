/**
 * useAudioCapture - Real-time Microphone Audio Capture Hook
 * 
 * Captures microphone audio as 16-bit PCM, 16kHz mono
 * and streams chunks to the provided callback
 * 
 * Compatible with Gemini Live API audio format:
 * - Sample rate: 16000 Hz
 * - Bit depth: 16-bit
 * - Channels: Mono
 * - Chunk size: ~100ms chunks (1600 samples)
 * 
 * Usage:
 *   const { start, stop, isCapturing, error } = useAudioCapture({
 *     onAudioData: (pcmBase64) => sendToWebSocket(pcmBase64)
 *   });
 */

import { useState, useCallback, useRef, useEffect } from 'react';

// Audio configuration for Gemini Live compatibility
const TARGET_SAMPLE_RATE = 16000;
const CHUNK_DURATION_MS = 100;  // 100ms chunks
const SAMPLES_PER_CHUNK = TARGET_SAMPLE_RATE * CHUNK_DURATION_MS / 1000;  // 1600 samples

interface UseAudioCaptureOptions {
    onAudioData: (pcmBase64: string) => void;
    onSilenceDetected?: () => void;
    onSpeechDetected?: () => void;
    silenceThreshold?: number;  // 0-1, default 0.01
    silenceTimeoutMs?: number;  // ms to wait before signaling silence
}

interface AudioCaptureState {
    isCapturing: boolean;
    error: string | null;
    isSpeaking: boolean;
    audioLevel: number;  // 0-1 normalized
}

export function useAudioCapture(options: UseAudioCaptureOptions) {
    const {
        onAudioData,
        onSilenceDetected,
        onSpeechDetected,
        silenceThreshold = 0.01,
        silenceTimeoutMs = 1500,
    } = options;

    const [state, setState] = useState<AudioCaptureState>({
        isCapturing: false,
        error: null,
        isSpeaking: false,
        audioLevel: 0,
    });

    // Refs
    const streamRef = useRef<MediaStream | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const workletNodeRef = useRef<AudioWorkletNode | null>(null);
    const scriptProcessorRef = useRef<ScriptProcessorNode | null>(null);
    const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
    const resamplerRef = useRef<LinearResampler | null>(null);
    const isMountedRef = useRef(true);

    // Cleanup on unmount
    useEffect(() => {
        isMountedRef.current = true;
        return () => {
            isMountedRef.current = false;
            stopCapture();
        };
    }, []);

    // Start audio capture
    const startCapture = useCallback(async () => {
        if (state.isCapturing) return;

        try {
            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    sampleRate: { ideal: TARGET_SAMPLE_RATE },
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                },
            });

            if (!isMountedRef.current) {
                stream.getTracks().forEach(t => t.stop());
                return;
            }

            streamRef.current = stream;

            // Create AudioContext
            const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
                sampleRate: TARGET_SAMPLE_RATE,
            });
            audioContextRef.current = audioContext;

            // If browser sample rate differs, we need resampling
            const needsResampling = audioContext.sampleRate !== TARGET_SAMPLE_RATE;
            if (needsResampling) {
                resamplerRef.current = new LinearResampler(
                    audioContext.sampleRate,
                    TARGET_SAMPLE_RATE
                );
            }

            // Create source from stream
            const source = audioContext.createMediaStreamSource(stream);

            // Try AudioWorklet first, fall back to ScriptProcessor
            try {
                await setupAudioWorklet(audioContext, source);
            } catch (workletError) {
                console.warn('AudioWorklet not available, using ScriptProcessor:', workletError);
                setupScriptProcessor(audioContext, source);
            }

            if (isMountedRef.current) {
                setState(prev => ({
                    ...prev,
                    isCapturing: true,
                    error: null,
                }));
            }

            console.log('🎤 Audio capture started');

        } catch (err) {
            console.error('Failed to start audio capture:', err);
            if (isMountedRef.current) {
                setState(prev => ({
                    ...prev,
                    isCapturing: false,
                    error: err instanceof Error ? err.message : 'Microphone access denied',
                }));
            }
        }
    }, [state.isCapturing]);

    // Setup AudioWorklet (modern approach)
    const setupAudioWorklet = async (
        audioContext: AudioContext,
        source: MediaStreamAudioSourceNode
    ) => {
        // Create AudioWorklet processor inline as a blob
        const workletCode = `
            class PCMProcessor extends AudioWorkletProcessor {
                constructor() {
                    super();
                    this.buffer = [];
                    this.bufferSize = ${SAMPLES_PER_CHUNK};
                }
                
                process(inputs, outputs, parameters) {
                    const input = inputs[0];
                    if (!input || !input[0]) return true;
                    
                    const samples = input[0];
                    this.buffer.push(...samples);
                    
                    while (this.buffer.length >= this.bufferSize) {
                        const chunk = this.buffer.splice(0, this.bufferSize);
                        this.port.postMessage({ type: 'audio', samples: chunk });
                    }
                    
                    return true;
                }
            }
            registerProcessor('pcm-processor', PCMProcessor);
        `;

        const blob = new Blob([workletCode], { type: 'application/javascript' });
        const workletUrl = URL.createObjectURL(blob);

        await audioContext.audioWorklet.addModule(workletUrl);
        URL.revokeObjectURL(workletUrl);

        const workletNode = new AudioWorkletNode(audioContext, 'pcm-processor');
        workletNodeRef.current = workletNode;

        workletNode.port.onmessage = (event) => {
            if (event.data.type === 'audio') {
                processAudioChunk(event.data.samples);
            }
        };

        source.connect(workletNode);
        // Don't connect to destination (we don't want to hear ourselves)
    };

    // Setup ScriptProcessor (fallback for older browsers)
    const setupScriptProcessor = (
        audioContext: AudioContext,
        source: MediaStreamAudioSourceNode
    ) => {
        const bufferSize = 4096;  // Must be power of 2
        const scriptProcessor = audioContext.createScriptProcessor(bufferSize, 1, 1);
        scriptProcessorRef.current = scriptProcessor;

        let accumulatedSamples: number[] = [];

        scriptProcessor.onaudioprocess = (event) => {
            const inputData = event.inputBuffer.getChannelData(0);
            accumulatedSamples.push(...Array.from(inputData));

            while (accumulatedSamples.length >= SAMPLES_PER_CHUNK) {
                const chunk = accumulatedSamples.splice(0, SAMPLES_PER_CHUNK);
                processAudioChunk(chunk);
            }
        };

        source.connect(scriptProcessor);
        scriptProcessor.connect(audioContext.destination);  // Needed for ScriptProcessor to work
    };

    // Process audio chunk and send to callback
    const processAudioChunk = useCallback((samples: number[]) => {
        if (!isMountedRef.current) return;

        // Apply resampling if needed
        let processedSamples = samples;
        if (resamplerRef.current) {
            processedSamples = resamplerRef.current.resample(samples);
        }

        // Calculate audio level (RMS)
        const rms = Math.sqrt(
            processedSamples.reduce((sum, s) => sum + s * s, 0) / processedSamples.length
        );

        // Voice Activity Detection (VAD)
        const isSpeaking = rms > silenceThreshold;

        if (isMountedRef.current) {
            setState(prev => ({
                ...prev,
                audioLevel: Math.min(1, rms * 10),  // Normalize for display
                isSpeaking,
            }));
        }

        // Silence detection
        if (isSpeaking) {
            if (silenceTimerRef.current) {
                clearTimeout(silenceTimerRef.current);
                silenceTimerRef.current = null;
            }
            onSpeechDetected?.();
        } else {
            if (!silenceTimerRef.current) {
                silenceTimerRef.current = setTimeout(() => {
                    onSilenceDetected?.();
                    silenceTimerRef.current = null;
                }, silenceTimeoutMs);
            }
        }

        // Convert Float32 to Int16 PCM
        const pcmInt16 = float32ToInt16(processedSamples);

        // Convert to Base64
        const pcmBase64 = arrayBufferToBase64(pcmInt16.buffer as ArrayBuffer);

        // Send to callback
        onAudioData(pcmBase64);
    }, [onAudioData, onSilenceDetected, onSpeechDetected, silenceThreshold, silenceTimeoutMs]);

    // Stop audio capture
    const stopCapture = useCallback(() => {
        // Stop media stream
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }

        // Close audio context
        if (audioContextRef.current) {
            audioContextRef.current.close().catch(console.error);
            audioContextRef.current = null;
        }

        // Disconnect nodes
        if (workletNodeRef.current) {
            workletNodeRef.current.disconnect();
            workletNodeRef.current = null;
        }
        if (scriptProcessorRef.current) {
            scriptProcessorRef.current.disconnect();
            scriptProcessorRef.current = null;
        }

        // Clear timers
        if (silenceTimerRef.current) {
            clearTimeout(silenceTimerRef.current);
            silenceTimerRef.current = null;
        }

        // Clear resampler
        resamplerRef.current = null;

        if (isMountedRef.current) {
            setState(prev => ({
                ...prev,
                isCapturing: false,
                isSpeaking: false,
                audioLevel: 0,
            }));
        }

        console.log('🎤 Audio capture stopped');
    }, []);

    return {
        start: startCapture,
        stop: stopCapture,
        isCapturing: state.isCapturing,
        isSpeaking: state.isSpeaking,
        audioLevel: state.audioLevel,
        error: state.error,
    };
}

// ==================
// Utility Classes
// ==================

/**
 * Simple linear resampler for converting sample rates
 */
class LinearResampler {
    private ratio: number;
    private lastSample: number = 0;
    private accumulator: number = 0;

    constructor(fromRate: number, toRate: number) {
        this.ratio = toRate / fromRate;
    }

    resample(input: number[]): number[] {
        const output: number[] = [];

        for (let i = 0; i < input.length; i++) {
            this.accumulator += this.ratio;

            while (this.accumulator >= 1) {
                // Linear interpolation
                const t = (this.accumulator - 1) / this.ratio;
                const sample = this.lastSample + t * (input[i] - this.lastSample);
                output.push(sample);
                this.accumulator -= 1;
            }

            this.lastSample = input[i];
        }

        return output;
    }
}

// ==================
// Utility Functions
// ==================

/**
 * Convert Float32Array samples to Int16Array (16-bit PCM)
 */
function float32ToInt16(samples: number[]): Int16Array {
    const int16 = new Int16Array(samples.length);

    for (let i = 0; i < samples.length; i++) {
        // Clamp to [-1, 1] and scale to Int16 range
        const clamped = Math.max(-1, Math.min(1, samples[i]));
        int16[i] = clamped < 0
            ? clamped * 0x8000
            : clamped * 0x7FFF;
    }

    return int16;
}

/**
 * Convert ArrayBuffer to Base64 string
 */
function arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
}

export default useAudioCapture;
