-- Marco AI Interview Simulator Database Schema
-- SQLite3 Database for storing candidate information, interview sessions, and evaluations

-- Table 1: Candidates
-- Stores basic candidate information and resume data
CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    target_position TEXT NOT NULL,
    resume_filename TEXT,
    resume_text TEXT,  -- Extracted text from OCR
    skills TEXT,  -- JSON array of extracted skills
    experience TEXT,  -- JSON array of experience entries
    projects TEXT,  -- JSON array of projects
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: Interview Sessions
-- Tracks each interview attempt with metadata
CREATE TABLE IF NOT EXISTS interview_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL,
    api_provider TEXT NOT NULL,  -- 'openai', 'gemini', 'groq'
    encrypted_api_key TEXT,  -- Encrypted API key for recreating LLM service
    api_model TEXT,  -- Model name (for OpenRouter)
    api_base_url TEXT,  -- Base URL (for OpenRouter)
    status TEXT DEFAULT 'in_progress',  -- 'in_progress', 'completed', 'terminated'
    termination_reason TEXT,  -- 'gaze_violation', 'tab_switch', 'time_limit', 'user_ended', NULL
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    total_questions INTEGER DEFAULT 0,
    gaze_violations INTEGER DEFAULT 0,
    tab_switch_count INTEGER DEFAULT 0,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
);

-- Table 3: Interview Questions
-- Stores each question asked during the interview
CREATE TABLE IF NOT EXISTS interview_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    question_number INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    question_category TEXT,  -- 'technical', 'behavioral', 'situational'
    asked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE
);

-- Table 4: Interview Answers
-- Stores candidate responses with transcripts
CREATE TABLE IF NOT EXISTS interview_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    session_id INTEGER NOT NULL,
    answer_text TEXT NOT NULL,  -- Transcribed answer from STT
    answer_duration_seconds INTEGER,
    confidence_score REAL,  -- Speech recognition confidence (0-1)
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES interview_questions(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE
);

-- Table 5: Evaluations
-- Stores AI-generated evaluation and feedback
CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL UNIQUE,
    overall_score INTEGER NOT NULL,  -- 0-100
    technical_accuracy_score INTEGER,  -- 0-100
    clarity_score INTEGER,  -- 0-100
    relevance_score INTEGER,  -- 0-100
    detailed_feedback TEXT,  -- AI-generated comprehensive feedback
    strengths TEXT,  -- JSON array of strengths
    improvements TEXT,  -- JSON array of improvement areas
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE
);

-- Table 6: Proctoring Events
-- Logs all proctoring violations and events
CREATE TABLE IF NOT EXISTS proctoring_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,  -- 'gaze_shift', 'tab_switch', 'face_lost', 'multiple_faces'
    event_severity TEXT DEFAULT 'warning',  -- 'warning', 'violation', 'critical'
    event_details TEXT,  -- JSON with additional context
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);
CREATE INDEX IF NOT EXISTS idx_sessions_candidate ON interview_sessions(candidate_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON interview_sessions(status);
CREATE INDEX IF NOT EXISTS idx_questions_session ON interview_questions(session_id);
CREATE INDEX IF NOT EXISTS idx_answers_session ON interview_answers(session_id);
CREATE INDEX IF NOT EXISTS idx_proctoring_session ON proctoring_events(session_id);

-- Triggers for automatic timestamp updates
CREATE TRIGGER IF NOT EXISTS update_candidate_timestamp 
AFTER UPDATE ON candidates
BEGIN
    UPDATE candidates SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
