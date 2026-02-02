"""
Interview Router - Handle interview sessions, questions, and answers
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import os

from ..database import Database, db
from ..dependencies import get_tts_service, get_db
from ..llm_service import LLMService, LLMConfig

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/interview", tags=["interview"])


class StartInterviewRequest(BaseModel):
    """Request to start interview"""
    candidate_id: int
    api_provider: str  # openai, gemini, groq, anthropic, openrouter
    api_key: str
    model: Optional[str] = None  # For OpenRouter
    base_url: Optional[str] = None  # For OpenRouter


class StartInterviewResponse(BaseModel):
    """Response after starting interview"""
    session_id: int
    question_id: int
    first_question: str
    total_questions: int
    message: str


class QuestionRequest(BaseModel):
    """Request for next question"""
    session_id: int


class QuestionResponse(BaseModel):
    """Question response"""
    question_id: int
    question_number: int
    question_text: str
    is_last: bool


class AnswerRequest(BaseModel):
    """Submit answer"""
    question_id: int
    answer_text: str
    audio_duration: float = 0.0


class AnswerResponse(BaseModel):
    """Answer submission response"""
    success: bool
    message: str


class EndInterviewRequest(BaseModel):
    """End interview request"""
    session_id: int


# Store LLM services per session (in-memory for now)
_llm_services: Dict[int, LLMService] = {}


@router.post("/start", response_model=StartInterviewResponse)
async def start_interview(
    request: StartInterviewRequest,
    database: Database = Depends(get_db)
):
    """Start new interview session"""
    try:
        # Get candidate
        candidate = await database.get_candidate(request.candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Encrypt API key for storage
        from ..crypto_utils import encrypt_api_key
        encrypted_key = encrypt_api_key(request.api_key)
        
        # Create session with encrypted credentials
        session_id = await database.create_session(
            candidate_id=request.candidate_id,
            api_provider=request.api_provider,
            encrypted_api_key=encrypted_key,
            api_model=request.model or "",
            api_base_url=request.base_url or ""
        )
        
        # Initialize LLM service
        llm_config = LLMConfig(
            provider=request.api_provider,
            api_key=request.api_key,
            model=request.model,
            base_url=request.base_url
        )
        llm_service = LLMService(llm_config)
        _llm_services[session_id] = llm_service
        
        # Parse resume data with error handling
        import json
        parsed_data = {}
        try:
            # Read from separate columns
            skills_raw = candidate.get('skills', '[]')
            experience_raw = candidate.get('experience', '[]')
            projects_raw = candidate.get('projects', '[]')
            
            parsed_data = {
                'skills': json.loads(skills_raw) if skills_raw else [],
                'experience': json.loads(experience_raw) if experience_raw else [],
                'projects': json.loads(projects_raw) if projects_raw else []
            }
        except (json.JSONDecodeError, ValueError) as e:
            # If parsing fails, use basic resume data
            logger.warning(f"Failed to parse resume data for candidate {request.candidate_id}: {e}")
            parsed_data = {
                'skills': [],
                'sections': {
                    'experience': candidate.get('resume_text', '')[:500] if candidate.get('resume_text') else ''
                }
            }
        
        # Generate strictly 1 question for start
        first_question = await llm_service.generate_single_question(
            resume_data=parsed_data,
            target_position=candidate['target_position'],
            previous_questions=[]
        )
        
        # Store first question
        try:
            question_id = await database.add_question(
                session_id=session_id,
                question_text=first_question,
                question_number=1
            )
        except Exception as e:
            logger.error(f"Failed to store first question: {e}")
            raise HTTPException(status_code=500, detail="Database error storing question")
        
        return StartInterviewResponse(
            session_id=session_id,
            question_id=question_id,
            first_question=first_question,
            total_questions=5,  # Hardcoded max for now
            message="Interview started successfully"
        )
    
    except Exception as e:
        logger.error(f"Start interview error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")


@router.post("/question", response_model=QuestionResponse)
async def get_next_question(
    request: QuestionRequest,
    database: Database = Depends(get_db)
):
    """Get next question (generate if needed)"""
    try:
        # Get session info
        session = await database.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
            
        # Get all existing questions
        questions = await database.get_session_questions(request.session_id)
        
        # Get answered questions
        answers = await database.get_session_answers(request.session_id)
        answered_ids = {a['question_id'] for a in answers}
        
        # 1. Check if there's an existing unanswered question
        for q in questions:
            if q['id'] not in answered_ids:
                return QuestionResponse(
                    question_id=q['id'],
                    question_number=q['question_number'],
                    question_text=q['question_text'],
                    is_last=(q['question_number'] == 5)
                )
        
        # 2. If all answered, check if we need to generate a new one
        next_number = len(questions) + 1
        if next_number <= 5:  # Max 5 questions
            # Get LLM service
            llm_service = get_llm_service(request.session_id)
            if not llm_service:
                # Try to re-init service if missing
                try:
                    llm_config = LLMConfig(
                        provider=session['api_provider'],
                        api_key=os.environ.get(f"{session['api_provider'].upper()}_API_KEY", ""),
                        # Only works if API key is in env, otherwise we might fail if it was passed in start request
                        # But typically start_interview initializes it.
                        # For robustness, we should persist API keys encrypted or require re-auth, 
                        # but for now we assume in-memory service exists or we fail.
                    )
                    # Note: This fallback is weak if _llm_services is cleared. 
                    # Ideally we should store API key in DB (encrypted) or session.
                except:
                    logger.error(f"LLM Service not found for session {request.session_id}")
                    raise HTTPException(status_code=500, detail="Interview session invalid (LLM service lost)")

            # Get candidate data for context
            candidate = await database.get_candidate(session['candidate_id'])
            import json
            resume_data = {}
            try:
                if candidate.get('skills'): 
                    resume_data['skills'] = json.loads(candidate['skills']) if isinstance(candidate['skills'], str) else candidate['skills']
                if candidate.get('resume_text'):
                    resume_data['sections'] = {'experience': candidate['resume_text'][:500]}
            except:
                pass

            # Generate new question
            previous_questions = [q['question_text'] for q in questions]
            new_question_text = await llm_service.generate_single_question(
                resume_data=resume_data,
                target_position=candidate['target_position'],
                previous_questions=previous_questions
            )
            
            # Store it
            new_q_id = await database.add_question(
                session_id=request.session_id,
                question_text=new_question_text,
                question_number=next_number
            )
            
            return QuestionResponse(
                question_id=new_q_id,
                question_number=next_number,
                question_text=new_question_text,
                is_last=(next_number == 5)
            )
            
        # 3. No more questions allowed
        raise HTTPException(status_code=404, detail="No more questions available")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get question error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get question: {str(e)}")


@router.post("/answer", response_model=AnswerResponse)
async def submit_answer(
    request: AnswerRequest,
    database: Database = Depends(get_db)
):
    """Submit answer to question"""
    try:
        logger.info(f"Submitting answer for question_id={request.question_id}")
        logger.info(f"Answer text length: {len(request.answer_text)}")
        logger.info(f"Audio duration: {request.audio_duration}")
        
        # Get question to retrieve session_id
        questions = await database.fetch_one(
            "SELECT session_id FROM interview_questions WHERE id = ?",
            (request.question_id,)
        )
        
        if not questions:
            raise HTTPException(status_code=404, detail="Question not found")
        
        session_id = questions['session_id']
        logger.info(f"Retrieved session_id={session_id} for question_id={request.question_id}")
        
        await database.add_answer(
            question_id=request.question_id,
            answer_text=request.answer_text,
            session_id=session_id,
            audio_duration=request.audio_duration
        )
        
        logger.info(f"Answer submitted successfully for question_id={request.question_id}")
        
        return AnswerResponse(
            success=True,
            message="Answer submitted successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Failed to submit answer for question_id={request.question_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error(f"Request data: question_id={request.question_id}, answer_text={request.answer_text[:100]}, audio_duration={request.audio_duration}")
        raise HTTPException(status_code=500, detail=f"Failed to submit answer: {str(e)}")


@router.post("/end")
async def end_interview(
    request: EndInterviewRequest,
    database: Database = Depends(get_db)
):
    """End interview session"""
    try:
        # Update session status
        await database.update_session_status(
            request.session_id,
            status='completed'
        )
        
        # Clean up LLM service
        if request.session_id in _llm_services:
            del _llm_services[request.session_id]
        
        # Cleanup face tracking service
        from ..dependencies import cleanup_face_service
        cleanup_face_service(request.session_id)
        
        return {"message": "Interview ended successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to end interview: {str(e)}")


@router.get("/session/{session_id}")
async def get_session_details(
    session_id: int,
    database: Database = Depends(get_db)
):
    """Get interview session details"""
    try:
        session = await database.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        questions = await database.get_session_questions(session_id)
        answers = await database.get_session_answers(session_id)
        
        return {
            "session": session,
            "questions": questions,
            "answers": answers
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")


def get_llm_service(session_id: int) -> Optional[LLMService]:
    """Get LLM service for session"""
    return _llm_services.get(session_id)
