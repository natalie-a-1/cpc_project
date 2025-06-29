"""
CPC Multi-Agent System - Advanced Medical Coding Test Solver
Uses OpenAI Agents Framework with specialized agents for maximum accuracy
"""
import json
import logging
from typing import Dict, Any, List, Literal
from pathlib import Path
import sys
import re
from datetime import datetime
from pydantic import BaseModel, Field
from agents import Agent, Runner, WebSearchTool, FileSearchTool, function_tool

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from apis.hcpcs_api import HCPCSApi
from apis.icd10cm_api import ICD10CMApi
from apis.procedures_api import ProceduresApi
from apis.conditions_api import ConditionsApi

logger = logging.getLogger(__name__)

# Initialize API instances
hcpcs_api = HCPCSApi()
icd10cm_api = ICD10CMApi()
procedures_api = ProceduresApi()
conditions_api = ConditionsApi()

# Function tools for local APIs
@function_tool
def search_hcpcs_local(terms: str) -> Dict[str, Any]:
    """Search local HCPCS Level II database for medical equipment and supplies"""
    try:
        result = hcpcs_api.search_codes(terms, max_results=5)
        return {"source": "Local HCPCS DB", "results": result.get("results", [])[:3]}
    except Exception as e:
        return {"error": str(e)}

@function_tool
def search_icd10_local(terms: str) -> Dict[str, Any]:
    """Search local ICD-10-CM database for diagnosis codes"""
    try:
        result = icd10cm_api.search_codes(terms, max_results=5)
        return {"source": "Local ICD-10 DB", "results": result.get("results", [])[:3]}
    except Exception as e:
        return {"error": str(e)}

@function_tool
def search_procedures_local(terms: str) -> Dict[str, Any]:
    """Search local procedures database"""
    try:
        result = procedures_api.search_procedures(terms, max_results=5)
        return {"source": "Local Procedures DB", "results": result.get("results", [])[:3]}
    except Exception as e:
        return {"error": str(e)}

@function_tool
def search_conditions_local(terms: str) -> Dict[str, Any]:
    """Search local conditions database"""
    try:
        result = conditions_api.search_conditions(terms, max_results=5)
        return {"source": "Local Conditions DB", "results": result.get("results", [])[:3]}
    except Exception as e:
        return {"error": str(e)}

# Structured output models
class CPCAnswer(BaseModel):
    """Structured output for CPC exam answers"""
    answer: Literal["A", "B", "C", "D"] = Field(
        description="The correct answer letter (A, B, C, or D) based on analysis"
    )
    confidence: float = Field(
        description="Confidence level from 0.0 to 1.0",
        ge=0.0,
        le=1.0
    )
    reasoning: str = Field(
        description="Brief explanation of why this answer was chosen"
    )
    code_found: str = Field(
        default="",
        description="The specific code found if applicable (e.g., '70551' for MRI brain)"
    )

class QuestionAnalysis(BaseModel):
    """Analysis of the CPC question type"""
    question_type: Literal["CPT", "HCPCS", "ICD-10", "ANATOMY", "TERMINOLOGY", "GUIDELINES", "COMPLIANCE"] = Field(
        description="Type of medical coding question"
    )
    key_terms: List[str] = Field(
        description="Key medical terms or procedures mentioned"
    )
    requires_web_search: bool = Field(
        description="Whether this question needs web search for accurate answer"
    )

# Create specialized agents for different question types
def create_cpt_specialist() -> Agent:
    """Create CPT code specialist agent"""
    return Agent(
        name="CPT Code Specialist",
        instructions="""You are a CPT (Current Procedural Terminology) code expert specializing in finding and validating CPT codes.

Your expertise includes:
- Surgical procedures (10000-69999)
- Anesthesia codes (00100-01999)
- Radiology procedures (70000-79999)
- Laboratory and pathology (80000-89999)
- Medicine services (90000-99999)
- Evaluation and Management codes

CRITICAL INSTRUCTIONS:
1. First use search_procedures_local to check local database
2. Use WebSearchTool to search official sources (ama-assn.org, cms.gov, genhealth.ai)
3. Match the EXACT procedure description to the correct CPT code
4. Consider all code options provided in the multiple choice
5. Look for specific details like:
   - Anatomical location (e.g., "floor of mouth" vs "vestibule of mouth")
   - Approach (open vs closed, with/without anesthesia)
   - Complexity (simple vs complex)
6. ALWAYS return your analysis in the structured CPCAnswer format
7. Your answer field MUST be exactly one letter: A, B, C, or D""",
        output_type=CPCAnswer,
        tools=[search_procedures_local, WebSearchTool(search_context_size="high")]
    )

def create_hcpcs_specialist() -> Agent:
    """Create HCPCS Level II specialist agent"""
    return Agent(
        name="HCPCS Level II Specialist", 
        instructions="""You are a HCPCS Level II code expert specializing in:
- Durable Medical Equipment (DME) - E codes
- Prosthetics and Orthotics - L codes
- Medical/Surgical Supplies - A codes
- Drugs and Biologicals - J codes
- Temporary codes - K, G, Q codes

CRITICAL INSTRUCTIONS:
1. Identify the specific item or service type
2. Use search_hcpcs_local first for quick lookup from local database
3. Verify with WebSearchTool if needed for additional information
4. Pay attention to code specifics (e.g., K0001 vs K0002 for wheelchairs)
5. Match the exact description from the question
6. ALWAYS return CPCAnswer with answer as A, B, C, or D""",
        output_type=CPCAnswer,
        tools=[search_hcpcs_local, WebSearchTool()]
    )

def create_icd10_specialist() -> Agent:
    """Create ICD-10-CM diagnosis code specialist"""
    return Agent(
        name="ICD-10-CM Specialist",
        instructions="""You are an ICD-10-CM diagnosis coding expert.

Key principles:
- Code to the highest level of specificity
- Acute conditions before chronic when both present
- Consider laterality (right/left/bilateral)
- Watch for "with/without" distinctions

CRITICAL INSTRUCTIONS:
1. Use search_icd10_local for initial lookup from local database
2. Use search_conditions_local to understand the medical condition
3. Consider all aspects: etiology, anatomic site, severity, laterality
4. Match the exact condition described in the question
5. Verify with WebSearchTool if additional clarification needed
6. ALWAYS return CPCAnswer with answer as A, B, C, or D""",
        output_type=CPCAnswer,
        tools=[search_icd10_local, search_conditions_local, WebSearchTool()]
    )

def create_medical_knowledge_agent() -> Agent:
    """Create agent for anatomy, terminology, and general medical knowledge"""
    return Agent(
        name="Medical Knowledge Expert",
        instructions="""You are an expert in medical terminology, anatomy, and healthcare regulations.

Areas of expertise:
- Medical terminology (prefixes, suffixes, root words)
- Human anatomy and physiology
- Healthcare regulations (HIPAA, Medicare rules)
- Coding guidelines and compliance
- Medical abbreviations and their meanings

CRITICAL INSTRUCTIONS:
1. For anatomy questions, focus on the specific body system
2. For terminology, break down the word components
3. For regulations, cite specific rules or acts
4. Use WebSearchTool to verify current information
5. ALWAYS return CPCAnswer with answer as A, B, C, or D""",
        output_type=CPCAnswer,
        tools=[WebSearchTool()]
    )

def create_question_analyzer() -> Agent:
    """Create agent that analyzes questions and routes to appropriate specialist"""
    return Agent(
        name="Question Analyzer",
        instructions="""Analyze CPC exam questions to determine their type and key information.

Classification rules:
- CPT: Questions asking "Which CPT code" or about procedures/services
- HCPCS: Questions about equipment, supplies, drugs (look for HCPCS, DME, wheelchair, CPAP, etc.)
- ICD-10: Questions about diagnosis codes or conditions
- ANATOMY: Questions about body parts, organs, or anatomical structures
- TERMINOLOGY: Questions about medical terms, prefixes, suffixes
- GUIDELINES: Questions about coding rules, sequencing, modifiers
- COMPLIANCE: Questions about Medicare, fraud, HIPAA, NCCI

Extract key medical terms and determine if web search is needed.""",
        output_type=QuestionAnalysis
    )

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
        
        # Initialize APIs for tools
        self.hcpcs_api = hcpcs_api
        self.icd10cm_api = icd10cm_api
        self.procedures_api = procedures_api
        self.conditions_api = conditions_api
        
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

# Keep the existing CPCTestLogger class
class CPCTestLogger:
    """Logger for CPC test results and analytics"""
    
    def __init__(self):
        self.base_dir = Path("cpc_tests")
        self.base_dir.mkdir(exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_dir = self.base_dir / f"run_{self.session_id}"
        self.results_dir.mkdir(exist_ok=True)
        self.session_results = []
        
    def log_question_result(self, question_data: Dict[str, Any], agent_response: str, 
                          correct_answer: str, tools_used: List[str], 
                          processing_time: float, trace_id: str = None):
        """Log individual question result"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "question_id": question_data.get("id"),
            "question_stem": question_data.get("stem", "")[:200] + "..." if len(question_data.get("stem", "")) > 200 else question_data.get("stem", ""),
            "agent_answer": agent_response,
            "correct_answer": correct_answer,
            "is_correct": agent_response == correct_answer,
            "tools_used": tools_used,
            "processing_time_seconds": round(processing_time, 2),
            "trace_id": trace_id
        }
        
        self.session_results.append(result)
        
        # Save individual result
        result_file = self.results_dir / f"question_{self.session_id}_{len(self.session_results):03d}.json"
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
    
    def save_session_summary(self, total_questions: int, correct_answers: int, 
                           duration: float, test_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Save session summary"""
        score_percentage = (correct_answers / total_questions) * 100
        
        summary = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "test_metadata": test_metadata or {},
            "performance": {
                "total_questions": total_questions,
                "correct_answers": correct_answers,
                "score_percentage": round(score_percentage, 1),
                "pass_status": "PASS" if score_percentage >= 70 else "FAIL",
                "total_duration_minutes": round(duration / 60, 1)
            },
            "detailed_results": self.session_results
        }
        
        summary_file = self.results_dir / f"session_summary_{self.session_id}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
            
        logger.info(f"Results saved to: {summary_file}")
        return summary
