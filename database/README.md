# Marco Database Documentation

## Overview
SQLite3 database for storing candidate profiles, interview sessions, and AI evaluations.

## Database Location
`database/marco_interviews.db`

## Quick Start

### Initialize Database
```bash
python database/init_db.py
```

### Reset Database (Delete & Recreate)
```bash
python database/init_db.py --reset
```

### Clear Database (Interactive with Confirmation)
```bash
python database/clear_database.py
```

**Features:**
- Shows current database statistics before deletion
- Requires typing 'DELETE' to confirm
- Automatically reinitializes with clean schema
- Force mode available: `python database/clear_database.py --force`

## Schema Structure

### Tables

#### 1. **candidates**
Stores candidate profile and resume data.
- `id` - Primary key
- `name`, `email`, `phone`, `target_position` - Basic info
- `resume_filename`, `resume_text` - Resume data
- `skills`, `experience`, `projects` - JSON extracted data

#### 2. **interview_sessions**
Tracks each interview attempt.
- `candidate_id` - Foreign key to candidates
- `api_provider` - 'openai', 'gemini', 'groq'
- `status` - 'in_progress', 'completed', 'terminated'
- `termination_reason` - Why interview ended
- `gaze_violations`, `tab_switch_count` - Proctoring metrics

#### 3. **interview_questions**
Stores questions asked during interview.
- `session_id` - Foreign key
- `question_text`, `question_category`

#### 4. **interview_answers**
Stores candidate responses.
- `question_id`, `session_id` - Foreign keys
- `answer_text` - Transcribed response
- `confidence_score` - STT confidence

#### 5. **evaluations**
AI-generated feedback and scores.
- `session_id` - Foreign key (unique)
- `overall_score`, `technical_accuracy_score`, etc.
- `detailed_feedback`, `strengths`, `improvements`

#### 6. **proctoring_events**
Logs all proctoring violations.
- `session_id` - Foreign key
- `event_type` - 'gaze_shift', 'tab_switch', etc.
- `event_severity` - 'warning', 'violation', 'critical'

## Relationships
- One candidate → Many sessions
- One session → Many questions
- One question → One answer
- One session → One evaluation
- One session → Many proctoring events
