// Interview Speech Recognition - Whisper Backend Integration (Enhanced)
// This module handles audio recording and Whisper transcription for the interview
// Version 2.0 - Seamless experience with audio detection and retry logic

(function () {
    'use strict';

    console.log('[WHISPER-STT] Initializing enhanced Whisper speech recognition module v2.0');

    const BACKEND_URL = 'http://localhost:8000';
    const CHUNK_DURATION = 6000; // 6 seconds per chunk (better balance)
    const SILENCE_THRESHOLD = 0.01; // Audio level threshold to detect silence
    const MAX_RETRIES = 1; // Retry failed transcriptions once

    // State
    let mediaRecorder = null;
    let audioChunks = [];
    let isProcessing = false;
    let recordingTimer = null;
    let audioContext = null;
    let analyser = null;
    let isListening = false;

    // Detect if audio chunk has speech (not silence)
    function hasAudioContent(audioBlob) {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = async (e) => {
                try {
                    if (!audioContext) {
                        audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    }

                    const audioBuffer = await audioContext.decodeAudioData(e.target.result);
                    const channelData = audioBuffer.getChannelData(0);

                    // Calculate RMS (Root Mean Square) to detect audio level
                    let sum = 0;
                    for (let i = 0; i < channelData.length; i++) {
                        sum += channelData[i] * channelData[i];
                    }
                    const rms = Math.sqrt(sum / channelData.length);

                    console.log('[WHISPER-STT] Audio level:', rms.toFixed(4));
                    resolve(rms > SILENCE_THRESHOLD);
                } catch (error) {
                    console.warn('[WHISPER-STT] Audio detection failed, assuming has content:', error);
                    resolve(true); // If detection fails, assume it has content
                }
            };
            reader.readAsArrayBuffer(audioBlob);
        });
    }

    // Update UI status
    function updateStatus(status) {
        const transcriptEl = document.getElementById('liveTranscript');
        const placeholderEl = document.getElementById('transcriptPlaceholder');

        if (status === 'listening' && !window.interviewState.currentTranscript) {
            if (placeholderEl) {
                placeholderEl.textContent = '🎤 Listening...';
                placeholderEl.classList.remove('hidden');
            }
            if (transcriptEl) {
                transcriptEl.classList.add('hidden');
            }
        } else if (status === 'processing') {
            if (placeholderEl && !window.interviewState.currentTranscript) {
                placeholderEl.textContent = '⏳ Processing...';
            }
        } else if (status === 'ready') {
            if (placeholderEl && !window.interviewState.currentTranscript) {
                placeholderEl.textContent = 'Your answer will appear here as you speak...';
            }
        }
    }

    // Process audio chunk and send to Whisper with retry
    async function processChunk(retryCount = 0) {
        if (audioChunks.length === 0) return;

        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        audioChunks = []; // Clear for next chunk

        console.log('[WHISPER-STT] Processing chunk:', (audioBlob.size / 1024).toFixed(2), 'KB');

        // Check if chunk has actual audio content
        const hasContent = await hasAudioContent(audioBlob);
        if (!hasContent) {
            console.log('[WHISPER-STT] Skipping silent chunk');
            updateStatus('listening');
            return;
        }

        try {
            isProcessing = true;
            updateStatus('processing');

            const formData = new FormData();
            formData.append('audio', audioBlob, 'audio.webm');

            const response = await fetch(`${BACKEND_URL}/api/stt/transcribe`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Backend error: ${response.status}`);
            }

            const result = await response.json();
            const text = result.text || result.transcript || '';

            if (text) {
                console.log('[WHISPER-STT] Transcribed:', text);

                // Update accumulated transcript
                window.interviewState.currentTranscript += text + ' ';

                // Update display
                const transcriptEl = document.getElementById('liveTranscript');
                const placeholderEl = document.getElementById('transcriptPlaceholder');

                if (transcriptEl && placeholderEl) {
                    transcriptEl.textContent = window.interviewState.currentTranscript;
                    transcriptEl.classList.remove('hidden');
                    placeholderEl.classList.add('hidden');

                    // Enable submit button if enough text
                    const submitBtn = document.getElementById('submitAnswerBtn');
                    if (submitBtn && window.interviewState.currentTranscript.trim().length > 10) {
                        submitBtn.disabled = false;
                    }
                }
            } else {
                console.log('[WHISPER-STT] No text returned (silence or noise)');
            }

            updateStatus('listening');

        } catch (error) {
            console.error('[WHISPER-STT] Transcription error:', error);

            // Retry logic
            if (retryCount < MAX_RETRIES) {
                console.log(`[WHISPER-STT] Retrying... (${retryCount + 1}/${MAX_RETRIES})`);
                // Re-add chunks for retry
                audioChunks.unshift(audioBlob);
                setTimeout(() => processChunk(retryCount + 1), 1000);
            } else {
                console.error('[WHISPER-STT] Max retries reached, skipping chunk');
                updateStatus('listening');
            }
        } finally {
            isProcessing = false;
        }
    }

    // Export to window
    window.whisperSTT = {
        start: async function () {
            try {
                console.log('[WHISPER-STT] Requesting microphone access...');
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

                console.log('[WHISPER-STT] Microphone access granted');
                mediaRecorder = new MediaRecorder(stream);

                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                };

                mediaRecorder.onstop = () => {
                    if (!isProcessing) {
                        processChunk();
                    }
                };

                mediaRecorder.start();
                window.interviewState.isRecording = true;
                isListening = true;

                console.log(`[WHISPER-STT] Recording started - sending chunks every ${CHUNK_DURATION / 1000} seconds`);
                updateStatus('listening');

                // Process chunks periodically
                recordingTimer = setInterval(() => {
                    if (window.interviewState.isRecording && mediaRecorder.state === 'recording') {
                        mediaRecorder.stop();
                        mediaRecorder.start(); // Restart for next chunk
                    }
                }, CHUNK_DURATION);

                return true;

            } catch (error) {
                console.error('[WHISPER-STT] Microphone error:', error);
                alert('Failed to access microphone. Please allow microphone permissions.');
                return false;
            }
        },

        stop: function () {
            console.log('[WHISPER-STT] Stopping recording...');

            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
            }

            if (recordingTimer) {
                clearInterval(recordingTimer);
                recordingTimer = null;
            }

            window.interviewState.isRecording = false;
            isListening = false;
            updateStatus('ready');
            console.log('[WHISPER-STT] Recording stopped');
        },

        reset: function () {
            window.interviewState.currentTranscript = '';
            audioChunks = [];
            updateStatus('ready');
            console.log('[WHISPER-STT] Reset transcript');
        }
    };

    console.log('[WHISPER-STT] Module loaded successfully');
    console.log('[WHISPER-STT] Backend URL:', BACKEND_URL);
    console.log('[WHISPER-STT] Chunk duration:', CHUNK_DURATION / 1000, 'seconds');
    console.log('[WHISPER-STT] Silence threshold:', SILENCE_THRESHOLD);
    console.log('[WHISPER-STT] Max retries:', MAX_RETRIES);
})();
