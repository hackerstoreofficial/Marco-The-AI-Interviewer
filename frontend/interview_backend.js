// Interview Page Backend Integration Script
// This replaces the dummy interview logic with real backend API calls

// Load API helper
// <script src="api.js"></script> should be added to HTML

// Interview State - Using window.interviewState to avoid conflicts
window.interviewState = window.interviewState || {
    sessionId: null,
    candidateId: null,
    currentQuestionId: null,
    questionNumber: 1,
    totalQuestions: 10,
    gazeViolations: 0,
    tabSwitches: 0,
    timeRemaining: 30 * 60,
    isRecording: false,
    currentTranscript: '',
    answers: [],
    proctoringInterval: null,
    apiConfig: null
};

// Timer
let timerInterval;

function startTimer() {
    timerInterval = setInterval(() => {
        window.interviewState.timeRemaining--;

        const minutes = Math.floor(window.interviewState.timeRemaining / 60);
        const seconds = window.interviewState.timeRemaining % 60;

        document.getElementById('timerMinutes').textContent = String(minutes).padStart(2, '0');
        document.getElementById('timerSeconds').textContent = String(seconds).padStart(2, '0');

        if (window.interviewState.timeRemaining <= 0) {
            endInterview('time_limit');
        }
    }, 1000);
}

// Camera Setup
async function setupCamera() {
    try {
        const permissionsGranted = sessionStorage.getItem('permissionsGranted');

        if (permissionsGranted === 'true') {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: false
            });
            document.getElementById('videoFeed').srcObject = stream;

            // Start proctoring
            startProctoring();
        } else {
            alert('Camera permission required. Redirecting to permissions page...');
            window.location.href = 'permissions.html';
        }
    } catch (err) {
        console.error('Camera access error:', err);
        alert('Failed to access camera. Please check permissions.');
        window.location.href = 'permissions.html';
    }
}

// Proctoring - Send frames to backend
function startProctoring() {
    const video = document.getElementById('videoFeed');
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');

    window.interviewState.proctoringInterval = setInterval(async () => {
        if (!window.interviewState.sessionId) return;

        try {
            // Capture frame
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            context.drawImage(video, 0, 0);

            // Convert to blob
            canvas.toBlob(async (blob) => {
                try {
                    const result = await api.sendProctoringFrame(window.interviewState.sessionId, blob);

                    // Always update violation count from backend
                    window.interviewState.gazeViolations = result.violation_count;
                    document.getElementById('gazeCount').textContent = window.interviewState.gazeViolations;

                    // Show alert if violation detected
                    if (result.violation_detected) {
                        console.warn(`Gaze violation detected! Count: ${result.violation_count}`);
                    }

                    // Check if should terminate
                    if (result.should_terminate) {
                        console.error('Maximum violations reached - terminating interview');
                        endInterview('gaze_violation');
                    }
                } catch (error) {
                    console.error('Proctoring error:', error);
                }
            }, 'image/jpeg', 0.8);
        } catch (error) {
            console.error('Frame capture error:', error);
        }
    }, 3000); // Check every 3 seconds
}

// Tab Switch Detection
document.addEventListener('visibilitychange', async () => {
    if (document.hidden && window.interviewState.sessionId) {
        try {
            const result = await api.logTabSwitch(window.interviewState.sessionId);
            window.interviewState.tabSwitches = result.total_tab_switches;
            document.getElementById('tabCount').textContent = window.interviewState.tabSwitches;

            if (result.should_terminate) {
                endInterview('tab_switch');
            }
        } catch (error) {
            console.error('Tab switch logging error:', error);
        }
    }
});

// Speech Recognition - Using Whisper Backend (whisper_stt.js module)
// No setup needed here, module auto-initializes

// Recording Controls
document.getElementById('recordBtn').addEventListener('click', async () => {
    if (window.whisperSTT && await window.whisperSTT.start()) {
        document.getElementById('recordBtn').classList.add('hidden');
        document.getElementById('stopRecordBtn').classList.remove('hidden');
        document.getElementById('recordingIndicator').classList.remove('hidden');
    } else {
        alert('Failed to start recording. Please check microphone permissions.');
    }
});

document.getElementById('stopRecordBtn').addEventListener('click', () => {
    if (window.whisperSTT) {
        window.whisperSTT.stop();
        document.getElementById('recordBtn').classList.remove('hidden');
        document.getElementById('stopRecordBtn').classList.add('hidden');
        document.getElementById('recordingIndicator').classList.add('hidden');
    }
});

// Text-to-Speech for Question
document.getElementById('speakQuestionBtn').addEventListener('click', () => {
    const questionText = document.getElementById('questionText').textContent;
    const utterance = new SpeechSynthesisUtterance(questionText);
    utterance.rate = 0.9;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
});

// Submit Answer
document.getElementById('submitAnswerBtn').addEventListener('click', async () => {
    if (!window.interviewState.currentQuestionId) return;

    try {
        // Disable button
        document.getElementById('submitAnswerBtn').disabled = true;
        document.getElementById('submitAnswerBtn').textContent = 'Submitting...';

        // Submit answer
        await api.submitAnswer(
            window.interviewState.currentQuestionId,
            window.interviewState.currentTranscript,
            15.0 // Approximate duration
        );

        // Move to next question or end
        if (window.interviewState.questionNumber < window.interviewState.totalQuestions) {
            await loadNextQuestion();
        } else {
            endInterview('completed');
        }
    } catch (error) {
        console.error('Submit answer error:', error);
        alert('Failed to submit answer. Please try again.');
        document.getElementById('submitAnswerBtn').disabled = false;
        document.getElementById('submitAnswerBtn').textContent = 'Submit Answer & Continue →';
    }
});

async function loadNextQuestion() {
    try {
        window.interviewState.questionNumber++;
        window.interviewState.currentTranscript = '';

        document.getElementById('questionNumber').textContent = window.interviewState.questionNumber;
        document.getElementById('liveTranscript').textContent = '';
        document.getElementById('liveTranscript').classList.add('hidden');
        document.getElementById('transcriptPlaceholder').classList.remove('hidden');
        document.getElementById('submitAnswerBtn').disabled = true;
        document.getElementById('submitAnswerBtn').textContent = 'Submit Answer & Continue →';

        // Show loading
        document.getElementById('questionText').innerHTML = '<p class="breathe-animation">Loading next question...</p>';

        // Get next question from backend
        const result = await api.getNextQuestion(window.interviewState.sessionId);

        window.interviewState.currentQuestionId = result.question_id;
        document.getElementById('questionText').innerHTML = `<p>${result.question_text}</p>`;

    } catch (error) {
        console.error('Load next question error:', error);
        document.getElementById('questionText').innerHTML = '<p class="text-error">Failed to load next question. Please refresh the page.</p>';
    }
}

// End Interview
document.getElementById('endInterviewBtn').addEventListener('click', () => {
    if (confirm('Are you sure you want to end the interview early?')) {
        endInterview('user_ended');
    }
});

async function endInterview(reason) {
    clearInterval(timerInterval);
    clearInterval(window.interviewState.proctoringInterval);

    try {
        // End interview on backend
        await api.endInterview(window.interviewState.sessionId);

        // Store session ID for evaluation page
        sessionStorage.setItem('session_id', window.interviewState.sessionId);
        sessionStorage.setItem('terminationReason', reason);

        // Navigate to evaluation
        window.location.href = 'evaluation.html';
    } catch (error) {
        console.error('End interview error:', error);
        // Navigate anyway
        window.location.href = 'evaluation.html';
    }
}

// Initialize Interview
window.addEventListener('load', async () => {
    try {
        // Get candidate ID and API config
        window.interviewState.candidateId = parseInt(sessionStorage.getItem('candidate_id'));
        const apiConfigStr = sessionStorage.getItem('apiConfig');

        if (!window.interviewState.candidateId || !apiConfigStr) {
            alert('Missing candidate or API configuration. Redirecting...');
            window.location.href = 'profile.html';
            return;
        }

        window.interviewState.apiConfig = JSON.parse(apiConfigStr);

        // Setup camera
        await setupCamera();

        // Start timer
        startTimer();

        // Show loading
        document.getElementById('questionText').innerHTML = '<p class="breathe-animation">Starting interview...</p>';

        // Start interview on backend
        const result = await api.startInterview(
            window.interviewState.candidateId,
            window.interviewState.apiConfig.provider,
            window.interviewState.apiConfig.key
        );

        window.interviewState.sessionId = result.session_id;
        window.interviewState.currentQuestionId = result.question_id;
        window.interviewState.totalQuestions = result.total_questions;

        // Display first question
        document.getElementById('questionText').innerHTML = `<p>${result.first_question}</p>`;

        // Start proctoring
        startProctoring();
    } catch (error) {
        console.error('Interview initialization error:', error);

        if (error.message.includes('Failed to fetch')) {
            alert('Backend server is not running. Please start the server and try again.');
        } else {
            alert(`Failed to start interview: ${error.message}`);
        }

        window.location.href = 'permissions.html';
    }
});
