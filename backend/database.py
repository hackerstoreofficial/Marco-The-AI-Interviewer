"""
Database connection and operations for Marco AI Interview Simulator
"""

import aiosqlite
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
import json
import logging

from .config import settings

logger = logging.getLogger(__name__)


class Database:
    """Async SQLite database manager"""
    
    def __init__(self, db_path: Path = settings.DATABASE_PATH):
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self):
        """Establish database connection"""
        self._connection = await aiosqlite.connect(str(self.db_path))
        self._connection.row_factory = aiosqlite.Row
        logger.info(f"Connected to database: {self.db_path}")
    
    async def disconnect(self):
        """Close database connection"""
        if self._connection:
            await self._connection.close()
            logger.info("Disconnected from database")
    
    async def execute(self, query: str, params: tuple = ()) -> aiosqlite.Cursor:
        """Execute a query"""
        cursor = await self._connection.execute(query, params)
        await self._connection.commit()
        return cursor
    
    async def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict]:
        """Fetch single row"""
        cursor = await self._connection.execute(query, params)
        row = await cursor.fetchone()
        return dict(row) if row else None
    
    async def fetch_all(self, query: str, params: tuple = ()) -> List[Dict]:
        """Fetch all rows"""
        cursor = await self._connection.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    # Candidate operations
    async def create_candidate(self, name: str, email: str, phone: str, 
                              target_position: str, resume_text: str = "",
                              parsed_data: Dict = None) -> int:
        """Create new candidate"""
        # Extract parsed data fields
        parsed = parsed_data or {}
        skills = json.dumps(parsed.get('skills', []))
        experience = json.dumps(parsed.get('experience', []))
        projects = json.dumps(parsed.get('projects', []))
        
        query = """
            INSERT INTO candidates (name, email, phone, target_position, resume_text, skills, experience, projects)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor = await self.execute(
            query,
            (name, email, phone, target_position, resume_text, skills, experience, projects)
        )
        return cursor.lastrowid
    
    async def get_candidate(self, candidate_id: int) -> Optional[Dict]:
        """Get candidate by ID"""
        query = "SELECT * FROM candidates WHERE id = ?"
        return await self.fetch_one(query, (candidate_id,))
    
    # Interview session operations
    async def create_session(self, candidate_id: int, api_provider: str, 
                            encrypted_api_key: str = "", api_model: str = "", 
                            api_base_url: str = "") -> int:
        """Create new interview session"""
        query = """
            INSERT INTO interview_sessions 
            (candidate_id, api_provider, encrypted_api_key, api_model, api_base_url, status)
            VALUES (?, ?, ?, ?, ?, 'in_progress')
        """
        cursor = await self.execute(
            query,
            (candidate_id, api_provider, encrypted_api_key, api_model, api_base_url)
        )
        return cursor.lastrowid
    
    async def get_session(self, session_id: int) -> Optional[Dict]:
        """Get session by ID"""
        query = "SELECT * FROM interview_sessions WHERE id = ?"
        return await self.fetch_one(query, (session_id,))
    
    async def update_session_status(self, session_id: int, status: str, 
                                   termination_reason: str = None):
        """Update session status"""
        query = """
            UPDATE interview_sessions 
            SET status = ?, termination_reason = ?, end_time = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        await self.execute(
            query,
            (status, termination_reason, session_id)
        )
    
    async def increment_violation(self, session_id: int, violation_type: str):
        """Increment violation count"""
        if violation_type == 'gaze':
            query = "UPDATE interview_sessions SET gaze_violations = gaze_violations + 1 WHERE id = ?"
        else:  # tab_switch
            query = "UPDATE interview_sessions SET tab_switch_count = tab_switch_count + 1 WHERE id = ?"
        await self.execute(query, (session_id,))
    
    # Question operations
    async def add_question(self, session_id: int, question_text: str, 
                          question_number: int) -> int:
        """Add interview question"""
        query = """
            INSERT INTO interview_questions (session_id, question_number, question_text)
            VALUES (?, ?, ?)
        """
        cursor = await self.execute(query, (session_id, question_number, question_text))
        return cursor.lastrowid
    
    async def get_session_questions(self, session_id: int) -> List[Dict]:
        """Get all questions for session"""
        query = "SELECT * FROM interview_questions WHERE session_id = ? ORDER BY question_number"
        return await self.fetch_all(query, (session_id,))
    
    # Answer operations
    async def add_answer(self, question_id: int, answer_text: str, 
                        session_id: int, audio_duration: float = 0):
        """Add interview answer"""
        query = """
            INSERT INTO interview_answers 
            (question_id, session_id, answer_text, answer_duration_seconds)
            VALUES (?, ?, ?, ?)
        """
        await self.execute(query, (question_id, session_id, answer_text, audio_duration))
    
    async def get_session_answers(self, session_id: int) -> List[Dict]:
        """Get all answers for session"""
        query = """
            SELECT a.*, q.question_text, q.question_number
            FROM interview_answers a
            JOIN interview_questions q ON a.question_id = q.id
            WHERE q.session_id = ?
            ORDER BY q.question_number
        """
        return await self.fetch_all(query, (session_id,))
    
    # Evaluation operations
    async def create_evaluation(self, session_id: int, overall_score: float,
                               technical_score: float, clarity_score: float,
                               relevance_score: float, detailed_feedback: Dict):
        """Create evaluation"""
        query = """
            INSERT INTO evaluations 
            (session_id, overall_score, technical_accuracy_score, 
             clarity_score, relevance_score, detailed_feedback)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        await self.execute(
            query,
            (session_id, overall_score, technical_score, clarity_score, 
             relevance_score, json.dumps(detailed_feedback))
        )
    
    async def get_evaluation(self, session_id: int) -> Optional[Dict]:
        """Get evaluation for session"""
        query = "SELECT * FROM evaluations WHERE session_id = ?"
        return await self.fetch_one(query, (session_id,))
    
    # Proctoring operations
    async def log_proctoring_event(self, session_id: int, event_type: str, 
                                   severity: str = 'warning', details: Dict = None):
        """Log proctoring event"""
        query = """
            INSERT INTO proctoring_events (session_id, event_type, event_severity, event_details)
            VALUES (?, ?, ?, ?)
        """
        await self.execute(
            query,
            (session_id, event_type, severity, json.dumps(details or {}))
        )


# Global database instance
db = Database()
