"""
Evaluation Router - Generate and retrieve interview evaluations
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import logging  # <--- MOVE THIS TO THE TOP

# INITIALIZE LOGGER GLOBALLY
logger = logging.getLogger(__name__) 

from ..database import Database, db
from ..dependencies import get_db
from ..routers.interview import get_llm_service


router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


class GenerateEvaluationRequest(BaseModel):
    """Request to generate evaluation"""
    session_id: int


class EvaluationResponse(BaseModel):
    """Evaluation data"""
    overall_score: float
    technical_score: float
    clarity_score: float
    relevance_score: float
    strengths: List[str]
    improvements: List[str]
    detailed_analysis: str


@router.post("/generate")
async def generate_evaluation(
    request: GenerateEvaluationRequest,
    database: Database = Depends(get_db)
):
    """Generate evaluation for completed interview"""
    try:
        # Get session
        session = await database.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get candidate
        candidate = await database.get_candidate(session['candidate_id'])
        
        # Get Q&A pairs
        questions = await database.get_session_questions(request.session_id)
        answers = await database.get_session_answers(request.session_id)
        
        # Build Q&A pairs
        qa_pairs = []
        for q in questions:
            answer = next((a for a in answers if a['question_id'] == q['id']), None)
            if answer:
                qa_pairs.append({
                    'question': q['question_text'],
                    'answer': answer['answer_text']
                })
        
        # Get LLM service from cache, or recreate from stored credentials
        llm_service = get_llm_service(request.session_id)
        
        if not llm_service:
            # Service not in cache (server restarted), recreate from stored credentials
            logger.info(f"LLM service not in cache for session {request.session_id}, recreating from stored credentials")
            
            from ..crypto_utils import decrypt_api_key
            from ..llm_service import LLMService, LLMConfig
            
            # Get encrypted credentials from session
            encrypted_key = session.get('encrypted_api_key')
            if not encrypted_key:
                logger.error(f"No encrypted API key found for session {request.session_id}")
                raise HTTPException(
                    status_code=400, 
                    detail="API credentials not found. Please start a new interview."
                )
            
            try:
                # Decrypt API key
                api_key = decrypt_api_key(encrypted_key)
                
                # Recreate LLM service
                llm_config = LLMConfig(
                    provider=session['api_provider'],
                    api_key=api_key,
                    model=session.get('api_model'),
                    base_url=session.get('api_base_url')
                )
                llm_service = LLMService(llm_config)
                logger.info(f"Successfully recreated LLM service for session {request.session_id}")
                
            except Exception as e:
                import traceback
                # REMOVE the logger initialization from here
                logger.error(f"Evaluation generation failed: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise HTTPException(status_code=500, detail=f"Evaluation generation failed: {str(e)}")
        
        # Evaluate each answer
        total_technical = 0
        total_clarity = 0
        total_relevance = 0
        
        for qa in qa_pairs:
            eval_result = await llm_service.evaluate_answer(qa['question'], qa['answer'])
            total_technical += eval_result.get('technical', 70)
            total_clarity += eval_result.get('clarity', 70)
            total_relevance += eval_result.get('relevance', 70)
        
        num_answers = len(qa_pairs) or 1
        technical_score = total_technical / num_answers
        clarity_score = total_clarity / num_answers
        relevance_score = total_relevance / num_answers
        
        # Generate final evaluation
        final_eval = await llm_service.generate_final_evaluation(
            qa_pairs=qa_pairs,
            candidate_name=candidate['name']
        )
        
        overall_score = final_eval.get('overall_score', 75)
        
        # Store evaluation
        await database.create_evaluation(
            session_id=request.session_id,
            overall_score=overall_score,
            technical_score=technical_score,
            clarity_score=clarity_score,
            relevance_score=relevance_score,
            detailed_feedback={
                'strengths': final_eval.get('strengths', []),
                'improvements': final_eval.get('improvements', []),
                'analysis': final_eval.get('analysis', '')
            }
        )
        
        return {
            "success": True,
            "message": "Evaluation generated successfully",
            "overall_score": overall_score
        }
    
    except Exception as e:
        import traceback
        logger.error(f"Evaluation generation failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Evaluation generation failed: {str(e)}")


@router.get("/{session_id}", response_model=EvaluationResponse)
async def get_evaluation(
    session_id: int,
    database: Database = Depends(get_db)
):
    """Get evaluation for session"""
    try:
        evaluation = await database.get_evaluation(session_id)
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        
        # Parse detailed feedback
        import json
        detailed_feedback = json.loads(evaluation.get('detailed_feedback', '{}')) if isinstance(evaluation.get('detailed_feedback'), str) else evaluation.get('detailed_feedback', {})
        
        return EvaluationResponse(
            overall_score=evaluation['overall_score'],
            technical_score=evaluation['technical_accuracy_score'],
            clarity_score=evaluation['clarity_score'],
            relevance_score=evaluation['relevance_score'],
            strengths=detailed_feedback.get('strengths', []),
            improvements=detailed_feedback.get('improvements', []),
            detailed_analysis=detailed_feedback.get('analysis', '')
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get evaluation: {str(e)}")
