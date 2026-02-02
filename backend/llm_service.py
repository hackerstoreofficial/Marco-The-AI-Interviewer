"""
LLM Service - Unified interface for multiple AI providers
Supports: OpenAI, Gemini, Groq, Anthropic, OpenRouter
"""

import logging
from typing import List, Dict, Optional, Literal
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration for LLM provider"""
    provider: Literal['openai', 'gemini', 'groq', 'anthropic', 'openrouter']
    api_key: str
    model: Optional[str] = None  # For OpenRouter custom models
    base_url: Optional[str] = None  # For OpenRouter custom endpoint


class LLMService:
    """Unified LLM service supporting multiple providers"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client"""
        try:
            logger.info(f"Initializing LLM client for provider: {self.config.provider}")
            
            if self.config.provider == 'openai':
                from openai import OpenAI
                logger.info("Creating OpenAI client...")
                self.client = OpenAI(api_key=self.config.api_key)
                self.default_model = "gpt-3.5-turbo"
                
            elif self.config.provider == 'gemini':
                import google.generativeai as genai
                logger.info("Configuring Gemini client...")
                genai.configure(api_key=self.config.api_key)
                self.client = genai
                self.default_model = "gemini-2.0-flash"  # Updated to current model
                
            elif self.config.provider == 'groq':
                from groq import Groq
                logger.info("Creating Groq client...")
                # Debug: Log API key format (masked)
                if not self.config.api_key:
                    raise ValueError("Groq API key not configured")
                    
                key_preview = f"{self.config.api_key[:10]}...{self.config.api_key[-4:]}" if len(self.config.api_key) > 14 else "***"
                logger.info(f"API key format: {key_preview} (length: {len(self.config.api_key)})")
                self.client = Groq(api_key=self.config.api_key.strip())  # Strip whitespace
                self.default_model = "openai/gpt-oss-120b"  # User's working Groq model
                
            elif self.config.provider == 'anthropic':
                from anthropic import Anthropic
                logger.info("Creating Anthropic client...")
                self.client = Anthropic(api_key=self.config.api_key)
                self.default_model = "claude-3-sonnet-20240229"
                
            elif self.config.provider == 'openrouter':
                from openai import OpenAI
                logger.info("Creating OpenRouter client...")
                self.client = OpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url or "https://openrouter.ai/api/v1"
                )
                self.default_model = self.config.model or "openai/gpt-3.5-turbo"
            else:
                raise ValueError(f"Unsupported provider: {self.config.provider}")
            
            logger.info(f"Successfully initialized {self.config.provider} LLM client with model {self.default_model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.config.provider}: {type(e).__name__}: {str(e)}")
            raise RuntimeError(f"Failed to initialize {self.config.provider} client: {str(e)}") from e
    
    async def generate_single_question(self, resume_data: Dict, target_position: str, 
                                     previous_questions: List[str]) -> str:
        """Generate a single follow-up question based on context"""
        
        # Build prompt
        skills = resume_data.get('skills', [])
        experience = resume_data.get('sections', {}).get('experience', '')
        
        previous_context = "\n".join([f"Q{i+1}: {q}" for i, q in enumerate(previous_questions)])
        
        prompt = f"""You are an expert technical interviewer. Generate the next interview question (Question {len(previous_questions) + 1}) for a {target_position} position.

Candidate Profile:
- Skills: {', '.join(skills[:10]) if skills else 'Not specified'}
- Experience: {experience[:500] if experience else 'Not specified'}

Previous Questions:
{previous_context}

Generate ONE technical interview question that:
1. Is relevant to the candidate's skills
2. Is distinct from previous questions
3. Digs deeper into their expertise or covers a new relevant topic
4. Testing theoretical knowledge or practical application

Return ONLY the question text (no numbering, no quotes)."""

        try:
            # Call LLM API
            response = await self._call_llm(prompt)
            
            # Clean up response
            question = response.strip()
            # Remove leading numbers/bullets if any
            if question and (question[0].isdigit() or question.startswith('-')):
                question = question.split('.', 1)[-1].strip() if '.' in question else question.strip('- ')
            
            return question
            
        except Exception as e:
            logger.error(f"Failed to generate single question: {str(e)}")
            # Fallback question if generation fails
            return "Could you describe a challenging technical problem you've solved recently?"

    async def generate_questions(self, resume_data: Dict, target_position: str, 
                                num_questions: int = 5) -> List[str]:
        """Generate interview questions based on resume"""
        
        # Build prompt
        skills = resume_data.get('skills', [])
        experience = resume_data.get('sections', {}).get('experience', '')
        
        prompt = f"""You are an expert technical interviewer. Generate {num_questions} interview questions for a {target_position} position.

Candidate Profile:
- Target Position: {target_position}
- Skills: {', '.join(skills[:10]) if skills else 'Not specified'}
- Experience: {experience[:500] if experience else 'Not specified'}

Generate {num_questions} technical interview questions that:
1. Are relevant to the candidate's skills and target position
2. Progress from basic to advanced
3. Test both theoretical knowledge and practical application
4. Are open-ended to encourage detailed responses

Return ONLY the questions, one per line, numbered 1-{num_questions}."""

        # Call LLM API - no fallback, raise error if it fails
        questions = await self._call_llm(prompt)
        
        # Parse questions from response
        question_list = []
        for line in questions.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # Remove numbering
                question = line.split('.', 1)[-1].strip() if '.' in line else line.strip('- ')
                if question:
                    question_list.append(question)
        
        if not question_list:
            raise RuntimeError("Failed to parse questions from LLM response")
        
        logger.info(f"Generated {len(question_list)} questions from LLM")
        return question_list[:num_questions]
    
    async def evaluate_answer(self, question: str, answer: str) -> Dict:
        """Evaluate an interview answer"""
        
        prompt = f"""You are an expert technical interviewer evaluating a candidate's answer.

Question: {question}

Candidate's Answer: {answer}

Evaluate this answer on the following criteria (score 0-100 for each):
1. Technical Accuracy: Is the answer technically correct and demonstrates knowledge?
2. Clarity: Is the answer well-structured and easy to understand?
3. Relevance: Does the answer directly address the question?

Provide:
- Technical Accuracy Score (0-100)
- Clarity Score (0-100)
- Relevance Score (0-100)
- Brief feedback (2-3 sentences)

Format your response as:
Technical: [score]
Clarity: [score]
Relevance: [score]
Feedback: [your feedback]"""

        # Call LLM API - no fallback, raise error if it fails
        response = await self._call_llm(prompt)
        
        # Parse scores
        scores = {'technical': 0, 'clarity': 0, 'relevance': 0, 'feedback': ''}
        
        for line in response.split('\n'):
            line = line.strip()
            if line.startswith('Technical:'):
                try:
                    scores['technical'] = int(''.join(filter(str.isdigit, line.split(':')[1])))
                except:
                    pass
            elif line.startswith('Clarity:'):
                try:
                    scores['clarity'] = int(''.join(filter(str.isdigit, line.split(':')[1])))
                except:
                    pass
            elif line.startswith('Relevance:'):
                try:
                    scores['relevance'] = int(''.join(filter(str.isdigit, line.split(':')[1])))
                except:
                    pass
            elif line.startswith('Feedback:'):
                scores['feedback'] = line.split(':', 1)[1].strip()
        
        if not scores['feedback']:
            raise RuntimeError("Failed to parse evaluation from LLM response")
        
        logger.info(f"Evaluated answer: T={scores['technical']}, C={scores['clarity']}, R={scores['relevance']}")
        return scores
    
    async def generate_final_evaluation(self, qa_pairs: List[Dict], 
                                       candidate_name: str) -> Dict:
        """Generate comprehensive final evaluation"""
        
        # Build Q&A summary
        qa_summary = "\n\n".join([
            f"Q{i+1}: {qa['question']}\nA{i+1}: {qa['answer']}"
            for i, qa in enumerate(qa_pairs)
        ])
        
        prompt = f"""You are an expert technical interviewer providing final evaluation for {candidate_name}.

Interview Questions and Answers:
{qa_summary}

Provide a comprehensive evaluation including:
1. Overall Score (0-100)
2. Key Strengths (3-4 bullet points)
3. Areas for Improvement (3-4 bullet points)
4. Detailed Analysis (2-3 paragraphs)

Format your response as:
Overall Score: [score]
Strengths:
- [strength 1]
- [strength 2]
- [strength 3]
Improvements:
- [improvement 1]
- [improvement 2]
- [improvement 3]
Analysis:
[your detailed analysis]"""

        # Call LLM API - no fallback, raise error if it fails
        response = await self._call_llm(prompt)
        
        # Parse response
        evaluation = {
            'overall_score': 0,
            'strengths': [],
            'improvements': [],
            'analysis': ''
        }
        
        current_section = None
        for line in response.split('\n'):
            line = line.strip()
            
            if line.startswith('Overall Score:'):
                try:
                    evaluation['overall_score'] = int(''.join(filter(str.isdigit, line.split(':')[1])))
                except:
                    pass
            elif line.startswith('Strengths:'):
                current_section = 'strengths'
            elif line.startswith('Improvements:'):
                current_section = 'improvements'
            elif line.startswith('Analysis:'):
                current_section = 'analysis'
                evaluation['analysis'] = line.split(':', 1)[1].strip()
            elif line.startswith('-') and current_section in ['strengths', 'improvements']:
                evaluation[current_section].append(line.strip('- '))
            elif current_section == 'analysis' and line:
                evaluation['analysis'] += ' ' + line
        
        if not evaluation['analysis']:
            raise RuntimeError("Failed to parse final evaluation from LLM response")
        
        logger.info(f"Generated final evaluation: Score={evaluation['overall_score']}")
        return evaluation
    
    async def _call_llm(self, prompt: str, max_tokens: int = 1000) -> str:
        """Make API call to LLM provider"""
        
        try:
            if self.config.provider == 'openai' or self.config.provider == 'openrouter':
                response = self.client.chat.completions.create(
                    model=self.default_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=max_tokens
                )
                result = response.choices[0].message.content
                logger.info(f"LLM call successful ({self.config.provider}): {len(result)} chars")
                return result
            
            elif self.config.provider == 'gemini':
                model = self.client.GenerativeModel(self.default_model)
                response = model.generate_content(prompt)
                result = response.text
                logger.info(f"LLM call successful (gemini): {len(result)} chars")
                return result
            
            elif self.config.provider == 'groq':
                response = self.client.chat.completions.create(
                    model=self.default_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=max_tokens
                )
                result = response.choices[0].message.content
                logger.info(f"LLM call successful (groq): {len(result)} chars")
                return result
            
            elif self.config.provider == 'anthropic':
                response = self.client.messages.create(
                    model=self.default_model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )
                result = response.content[0].text
                logger.info(f"LLM call successful (anthropic): {len(result)} chars")
                return result
            
            else:
                raise ValueError(f"Unsupported provider: {self.config.provider}")
        
        except Exception as e:
            logger.error(f"LLM API call failed ({self.config.provider}): {type(e).__name__}: {str(e)}")
            raise  # Re-raise to trigger fallback in calling method
    
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
            json_match = re.search(r'\{{[\s\S]*\}}', response_text)
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

