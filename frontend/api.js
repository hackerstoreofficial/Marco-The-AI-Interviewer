// API Configuration
// API Configuration
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : '/api'; // Relative path for production/same-origin

// API Helper Functions
const api = {
    // Candidate endpoints
    async createProfile(profileData) {
        const response = await fetch(`${API_BASE_URL}/api/candidates/profile`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(profileData)
        });
        if (!response.ok) throw new Error(await response.text());
        return response.json();
    },

    async uploadResume(candidateId, file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE_URL}/api/candidates/resume/${candidateId}`, {
            method: 'POST',
            body: formData
        });
        if (!response.ok) throw new Error(await response.text());
        return response.json();
    },

    async getCandidate(candidateId) {
        const response = await fetch(`${API_BASE_URL}/api/candidates/${candidateId}`);
        if (!response.ok) throw new Error(await response.text());
        return response.json();
    },

    // Interview endpoints
    async startInterview(candidateId, apiProvider, apiKey, model = null, baseUrl = null) {
        const response = await fetch(`${API_BASE_URL}/api/interview/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                candidate_id: candidateId,
                api_provider: apiProvider,
                api_key: apiKey,
                model: model,
                base_url: baseUrl
            })
        });
        if (!response.ok) throw new Error(await response.text());
        return response.json();
    },

    async getNextQuestion(sessionId) {
        const response = await fetch(`${API_BASE_URL}/api/interview/question`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
        if (!response.ok) throw new Error(await response.text());
        return response.json();
    },

    async submitAnswer(questionId, answerText, audioDuration) {
        const response = await fetch(`${API_BASE_URL}/api/interview/answer`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question_id: questionId,
                answer_text: answerText,
                audio_duration: audioDuration
            })
        });
        if (!response.ok) throw new Error(await response.text());
        return response.json();
    },

    async endInterview(sessionId) {
        const response = await fetch(`${API_BASE_URL}/api/interview/end`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
        if (!response.ok) throw new Error(await response.text());
        return response.json();
    },

    // Proctoring endpoints
    async sendProctoringFrame(sessionId, frameBlob) {
        const formData = new FormData();
        formData.append('frame', frameBlob, 'frame.jpg');

        const response = await fetch(`${API_BASE_URL}/api/proctoring/frame/${sessionId}`, {
            method: 'POST',
            body: formData
        });
        if (!response.ok) throw new Error(await response.text());
        return response.json();
    },

    async logTabSwitch(sessionId) {
        const response = await fetch(`${API_BASE_URL}/api/proctoring/tab-switch/${sessionId}`, {
            method: 'POST'
        });
        if (!response.ok) throw new Error(await response.text());
        return response.json();
    },

    async getProctoringStatus(sessionId) {
        const response = await fetch(`${API_BASE_URL}/api/proctoring/status/${sessionId}`);
        if (!response.ok) throw new Error(await response.text());
        return response.json();
    },

    // Evaluation endpoints
    async generateEvaluation(sessionId) {
        const response = await fetch(`${API_BASE_URL}/api/evaluation/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
        if (!response.ok) throw new Error(await response.text());
        return response.json();
    },

    async getEvaluation(sessionId) {
        const response = await fetch(`${API_BASE_URL}/api/evaluation/${sessionId}`);
        if (!response.ok) throw new Error(await response.text());
        return response.json();
    },

    // Speech endpoints
    async textToSpeech(text) {
        const response = await fetch(`${API_BASE_URL}/api/speech/tts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });
        if (!response.ok) throw new Error(await response.text());
        return response.json();
    },

    async speechToText(audioBlob) {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');

        const response = await fetch(`${API_BASE_URL}/api/speech/stt`, {
            method: 'POST',
            body: formData
        });
        if (!response.ok) throw new Error(await response.text());
        return response.json();
    },

    // Config endpoint
    async getConfig() {
        const response = await fetch(`${API_BASE_URL}/api/config`);
        if (!response.ok) throw new Error(await response.text());
        return response.json();
    },

    // Health check
    async healthCheck() {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (!response.ok) throw new Error(await response.text());
        return response.json();
    }
};
