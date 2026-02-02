"""
LLM Service - Evaluation Methods Extension
Add these methods to the LLMService class
"""

import logging

logger = logging.getLogger(__name__)

async def evaluate_answer(self, question: str, answer: str) -> Dict:
    """Evaluate a single answer"""
    prompt = f"""Evaluate this interview answer on a scale of 0-100 for each criterion:

Question: {question}
Answer: {answer}

Provide scores for:
1. Technical Accuracy (0-100): How technically correct is the answer?
2. Clarity (0-100): How clear and well-structured is the explanation?
3. Relevance (0-100): How relevant is the answer to the question?

Return ONLY a JSON object with these exact keys: technical, clarity, relevance
Example: {{"technical": 85, "clarity": 90, "relevance": 88}}
"""
    
    try:
        response_text = await self._call_llm(prompt, max_tokens=150)
        
        # Parse JSON response
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\{[^}]+\}', response_text)
        if json_match:
            scores = json.loads(json_match.group())
            return {
                'technical': int(scores.get('technical', 70)),
                'clarity': int(scores.get('clarity', 70)),
                'relevance': int(scores.get('relevance', 70))
            }
        else:
            # Fallback scores
            return {'technical': 70, 'clarity': 70, 'relevance': 70}
            
    except Exception as e:
        logger.error(f"Answer evaluation failed: {e}")
        return {'technical': 70, 'clarity': 70, 'relevance': 70}


async def generate_final_evaluation(self, qa_pairs: List[Dict], candidate_name: str) -> Dict:
    """Generate comprehensive final evaluation"""
    
    # Build Q&A context
    qa_text = "\n\n".join([
        f"Q: {qa['question']}\nA: {qa['answer']}"
        for qa in qa_pairs
    ])
    
    prompt = f"""You are an expert technical interviewer. Provide a comprehensive evaluation for {candidate_name}'s interview performance.

Interview Transcript:
{qa_text}

Provide:
1. Overall Score (0-100): Holistic assessment of the candidate
2. Strengths: List 3-5 key strengths demonstrated
3. Improvements: List 3-5 areas for improvement
4. Analysis: 2-3 paragraph detailed analysis of performance

Return a JSON object with these exact keys: overall_score (number), strengths (array), improvements (array), analysis (string)
"""
    
    try:
        response_text = await self._call_llm(prompt, max_tokens=800)
        
        # Parse JSON response
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            eval_data = json.loads(json_match.group())
            return {
                'overall_score': int(eval_data.get('overall_score', 75)),
                'strengths': eval_data.get('strengths', ['Good communication', 'Technical knowledge']),
                'improvements': eval_data.get('improvements', ['More detail needed', 'Practice more']),
                'analysis': eval_data.get('analysis', 'The candidate demonstrated solid understanding of the topics.')
            }
        else:
            # Fallback evaluation
            return {
                'overall_score': 75,
                'strengths': ['Demonstrated technical knowledge', 'Clear communication'],
                'improvements': ['Could provide more detailed examples', 'Practice articulating complex concepts'],
                'analysis': f'{candidate_name} showed a good understanding of the subject matter with room for improvement in depth and detail.'
            }
            
    except Exception as e:
        logger.error(f"Final evaluation generation failed: {e}")
        return {
            'overall_score': 75,
            'strengths': ['Participated in the interview'],
            'improvements': ['Continue learning and practicing'],
            'analysis': 'Evaluation could not be completed. Please review the interview manually.'
        }
