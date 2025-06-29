"""
CPC Multi-Agent System - Advanced Medical Coding Test Solver
Uses OpenAI Agents Framework with specialized agents for maximum accuracy
"""
import logging
from typing import Dict, Any
from datetime import datetime
from agents import Agent, Runner

# Import modular components
from .models import CPCAnswer, QuestionAnalysis
from .logger import CPCTestLogger
from .agents import (
    create_cpt_specialist,
    create_hcpcs_specialist,
    create_icd10_specialist,
    create_medical_knowledge_agent,
    create_question_analyzer
)

logger = logging.getLogger(__name__)



# Main CPC Agent class
class CPCAgent:
    """Advanced multi-agent CPC test solver"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Initialize the CPC multi-agent system"""
        import os
        os.environ['OPENAI_API_KEY'] = api_key
        
        # Initialize specialized agents
        self.question_analyzer = create_question_analyzer()
        self.cpt_specialist = create_cpt_specialist()
        self.hcpcs_specialist = create_hcpcs_specialist()
        self.icd10_specialist = create_icd10_specialist()
        self.medical_expert = create_medical_knowledge_agent()
        
        # Main orchestrator agent with handoffs
        self.orchestrator = Agent(
            name="CPC Test Orchestrator",
            instructions="""You coordinate the CPC exam question answering process.

Process:
1. First, analyze the question to understand what type it is
2. Route to the appropriate specialist agent
3. Ensure the answer is ONLY the letter (A, B, C, or D)
4. Return the final answer

You have access to:
- CPT Specialist: For procedure codes
- HCPCS Specialist: For equipment/supply codes
- ICD-10 Specialist: For diagnosis codes
- Medical Expert: For anatomy, terminology, guidelines""",
            handoffs=[
                self.cpt_specialist,
                self.hcpcs_specialist,
                self.icd10_specialist,
                self.medical_expert
            ],
            model=model
        )
        
        # Test logger
        self.test_logger = CPCTestLogger()
        
        logger.info("Initialized advanced CPC multi-agent system")
    
    def answer_question(self, question_data: Dict[str, Any], options: Dict[str, str], correct_answer: str = None) -> str:
        """Answer a CPC test question using the multi-agent system"""
        start_time = datetime.now()
        
        question_text = question_data.get("stem", "") if isinstance(question_data, dict) else str(question_data)
        
        # Format question with clear instructions
        formatted_input = f"""CPC Exam Question:

{question_text}

Multiple Choice Options:
A) {options.get('A', '')}
B) {options.get('B', '')}
C) {options.get('C', '')}
D) {options.get('D', '')}

CRITICAL: You MUST return ONLY the letter (A, B, C, or D) of the correct answer.
First analyze the question type, then use the appropriate specialist to find the answer."""

        try:
            # First, analyze the question
            analysis_result = Runner.run_sync(
                self.question_analyzer,
                formatted_input,
                max_turns=3
            )
            
            question_type = analysis_result.final_output_as(QuestionAnalysis).question_type
            
            # Route to appropriate specialist based on question type
            if question_type == "CPT":
                # For CPT questions, search for the specific procedure
                procedure_terms = " ".join(analysis_result.final_output_as(QuestionAnalysis).key_terms)
                search_query = f"{formatted_input}\n\nSearch for CPT code for: {procedure_terms}"
                result = Runner.run_sync(self.cpt_specialist, search_query, max_turns=10)
            elif question_type == "HCPCS":
                # Use HCPCS API first, then specialist
                result = Runner.run_sync(self.hcpcs_specialist, formatted_input, max_turns=5)
            elif question_type == "ICD-10":
                # Use ICD-10 API first, then specialist
                result = Runner.run_sync(self.icd10_specialist, formatted_input, max_turns=5)
            else:
                # Medical knowledge questions
                result = Runner.run_sync(self.medical_expert, formatted_input, max_turns=5)
            
            # Extract the structured answer
            final_answer = result.final_output_as(CPCAnswer)
            answer_letter = final_answer.answer
            
            # Log the result
            processing_time = (datetime.now() - start_time).total_seconds()
            if correct_answer is not None:
                self.test_logger.log_question_result(
                    question_data=question_data,
                    agent_response=answer_letter,
                    correct_answer=correct_answer,
                    tools_used=["WebSearchTool", question_type + "_Specialist"],
                    processing_time=processing_time,
                    trace_id=getattr(result, 'trace_id', None)
                )
            
            return answer_letter
            
        except Exception as e:
            logger.error(f"Error in multi-agent system: {e}")
            # Fallback to simple orchestrator
            try:
                simple_result = Runner.run_sync(
                    self.orchestrator,
                    formatted_input + "\n\nIMPORTANT: Return ONLY one letter: A, B, C, or D",
                    max_turns=15
                )
                
                # Try to extract letter from response
                response_text = str(simple_result.final_output)
                for letter in ['A', 'B', 'C', 'D']:
                    if letter in response_text.upper():
                        return letter
                
                raise ValueError("Could not extract answer letter")
                
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                raise

    def save_session_results(self, total_questions: int, correct_answers: int, duration: float) -> Dict[str, Any]:
        """Save session results with analytics"""
        return self.test_logger.save_session_summary(
            total_questions=total_questions,
            correct_answers=correct_answers,
            duration=duration,
            test_metadata={
                "agent_system": "Multi-Agent CPC System",
                "model": self.orchestrator.model,
                "agents": [
                    "Question Analyzer",
                    "CPT Specialist", 
                    "HCPCS Specialist",
                    "ICD-10 Specialist",
                    "Medical Knowledge Expert"
                ],
                "tools": ["WebSearchTool", "Local APIs", "Structured Outputs"]
            }
        )


