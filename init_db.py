import asyncio
from backend.database import db

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT,
        target_position TEXT,
        resume_text TEXT,
        skills TEXT,
        experience TEXT,
        projects TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS interview_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER,
        api_provider TEXT,
        encrypted_api_key TEXT,
        api_model TEXT,
        api_base_url TEXT,
        status TEXT DEFAULT 'in_progress',
        termination_reason TEXT,
        gaze_violations INTEGER DEFAULT 0,
        tab_switch_count INTEGER DEFAULT 0,
        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_time TIMESTAMP,
        FOREIGN KEY (candidate_id) REFERENCES candidates (id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS interview_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        question_number INTEGER,
        question_text TEXT,
        FOREIGN KEY (session_id) REFERENCES interview_sessions (id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS interview_answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER,
        session_id INTEGER,
        answer_text TEXT,
        answer_duration_seconds FLOAT,
        FOREIGN KEY (question_id) REFERENCES interview_questions (id),
        FOREIGN KEY (session_id) REFERENCES interview_sessions (id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS evaluations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        overall_score FLOAT,
        technical_accuracy_score FLOAT,
        clarity_score FLOAT,
        relevance_score FLOAT,
        detailed_feedback TEXT,
        FOREIGN KEY (session_id) REFERENCES interview_sessions (id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS proctoring_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        event_type TEXT,
        event_severity TEXT,
        event_details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES interview_sessions (id)
    );
    """
]

async def init_db():
    print("Initializing Database...")
    await db.connect()
    for query in SCHEMA:
        await db.execute(query)
    await db.disconnect()
    print("Database Initialized Successfully!")

if __name__ == "__main__":
    asyncio.run(init_db())
