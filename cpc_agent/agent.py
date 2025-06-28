"""
CPC Agent using OpenAI Agents Framework
"""
import json
import logging
from typing import Dict, Any, List
from pathlib import Path
import sys
import re
from datetime import datetime
from agents import Agent, function_tool, Runner

# Add the parent directory to Python path to import APIs
sys.path.append(str(Path(__file__).parent.parent))
from apis.hcpcs_api import HCPCSApi
from apis.icd10cm_api import ICD10CMApi
from apis.procedures_api import ProceduresApi
from apis.conditions_api import ConditionsApi

logger = logging.getLogger(__name__)

# Initialize API instances globally for tools
hcpcs_api = HCPCSApi()
icd10cm_api = ICD10CMApi()
procedures_api = ProceduresApi()
conditions_api = ConditionsApi()

# Load medical terminology
def _load_medical_terminology() -> List[Dict]:
    """Load medical terminology from JSONL file"""
    try:
        terms = []
        term_file = Path(__file__).parent.parent / "data" / "processed" / "medical_terminology.jsonl"
        if term_file.exists():
            with open(term_file, 'r') as f:
                for line in f:
                    if line.strip():
                        terms.append(json.loads(line.strip()))
        return terms
    except Exception as e:
        logger.error(f"Error loading medical terminology: {e}")
        return []

medical_terms = _load_medical_terminology()

class CPCTestLogger:
    """Simple logger for CPC test results and analytics"""
    
    def __init__(self):
        self.base_dir = Path("cpc_tests")
        self.base_dir.mkdir(exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Create a subdirectory for this specific test run
        self.results_dir = self.base_dir / f"run_{self.session_id}"
        self.results_dir.mkdir(exist_ok=True)
        self.session_results = []
        
    def log_question_result(self, question_data: Dict[str, Any], agent_response: str, 
                          correct_answer: str, tools_used: List[str], 
                          processing_time: float, trace_id: str = None):
        """Log individual question result with full context"""
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "question_id": question_data.get("id"),
            "question_stem": question_data.get("stem", "")[:200] + "..." if len(question_data.get("stem", "")) > 200 else question_data.get("stem", ""),
            "question_category": self._extract_category(question_data.get("stem", "")),
            "options": {
                "A": question_data.get("option_a", ""),
                "B": question_data.get("option_b", ""), 
                "C": question_data.get("option_c", ""),
                "D": question_data.get("option_d", "")
            },
            "agent_answer": agent_response,
            "correct_answer": correct_answer,
            "is_correct": agent_response == correct_answer,
            "tools_used": tools_used,
            "processing_time_seconds": round(processing_time, 2),
            "trace_id": trace_id
        }
        
        self.session_results.append(result)
        
        # Save individual result immediately
        result_file = self.results_dir / f"question_{self.session_id}_{len(self.session_results):03d}.json"
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
    
    def save_session_summary(self, total_questions: int, correct_answers: int, 
                           duration: float, test_metadata: Dict[str, Any] = None):
        """Save complete session summary with analytics"""
        
        # Calculate analytics
        score_percentage = (correct_answers / total_questions) * 100
        tool_usage = self._analyze_tool_usage()
        category_performance = self._analyze_category_performance()
        error_patterns = self._analyze_error_patterns()
        
        summary = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "test_metadata": test_metadata or {},
            "performance": {
                "total_questions": total_questions,
                "correct_answers": correct_answers,
                "incorrect_answers": total_questions - correct_answers,
                "score_percentage": round(score_percentage, 1),
                "pass_status": "PASS" if score_percentage >= 70 else "FAIL",
                "total_duration_minutes": round(duration / 60, 1),
                "avg_time_per_question_seconds": round(duration / total_questions, 1)
            },
            "tool_analytics": tool_usage,
            "category_performance": category_performance,
            "error_analysis": error_patterns,
            "detailed_results": self.session_results
        }
        
        # Save session summary
        summary_file = self.results_dir / f"session_summary_{self.session_id}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
            
        logger.info(f"Session results saved to: {summary_file}")
        return summary
    
    def _extract_category(self, question_stem: str) -> str:
        """Extract question category based on major coding systems"""
        stem_lower = question_stem.lower()
        
        # Focus on the three main coding systems for CPC
        if any(keyword in stem_lower for keyword in ["hcpcs", "level ii", "durable medical", "equipment", "supply", "prosthetic", "orthotics"]):
            return "HCPCS"
        
        if any(keyword in stem_lower for keyword in ["icd-10", "icd 10", "diagnosis", "condition", "disease", "disorder"]):
            return "ICD"
        
        if any(keyword in stem_lower for keyword in ["cpt", "procedure", "surgery", "surgical", "treatment", "operation", "evaluation", "consultation"]):
            return "CPT"
        
        # Leave blank if not clearly one of the main three
        return ""
    
    def _analyze_tool_usage(self) -> Dict[str, Any]:
        """Analyze which tools were used most frequently"""
        tool_counts = {}
        total_questions = len(self.session_results)
        
        for result in self.session_results:
            for tool in result.get("tools_used", []):
                tool_counts[tool] = tool_counts.get(tool, 0) + 1
        
        return {
            "total_tool_calls": sum(tool_counts.values()),
            "tools_per_question_avg": round(sum(tool_counts.values()) / total_questions, 1) if total_questions > 0 else 0,
            "tool_frequency": dict(sorted(tool_counts.items(), key=lambda x: x[1], reverse=True))
        }
    
    def _analyze_category_performance(self) -> Dict[str, Any]:
        """Analyze performance by question category"""
        category_stats = {}
        
        for result in self.session_results:
            category = result.get("question_category", "unknown")
            if category not in category_stats:
                category_stats[category] = {"total": 0, "correct": 0}
            
            category_stats[category]["total"] += 1
            if result.get("is_correct", False):
                category_stats[category]["correct"] += 1
        
        # Calculate percentages
        for category, stats in category_stats.items():
            stats["accuracy_percentage"] = round((stats["correct"] / stats["total"]) * 100, 1) if stats["total"] > 0 else 0
        
        # Sort by worst performance first
        return dict(sorted(category_stats.items(), key=lambda x: x[1]["accuracy_percentage"]))
    
    def _analyze_error_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in incorrect answers"""
        incorrect_results = [r for r in self.session_results if not r.get("is_correct", False)]
        
        error_categories = {}
        long_processing_questions = []
        
        for result in incorrect_results:
            category = result.get("question_category", "unknown")
            error_categories[category] = error_categories.get(category, 0) + 1
            
            # Flag slow questions (>30 seconds)
            if result.get("processing_time_seconds", 0) > 30:
                long_processing_questions.append({
                    "question_id": result.get("question_id"),
                    "processing_time": result.get("processing_time_seconds"),
                    "category": category
                })
        
        return {
            "total_incorrect": len(incorrect_results),
            "errors_by_category": dict(sorted(error_categories.items(), key=lambda x: x[1], reverse=True)),
            "slow_processing_questions": sorted(long_processing_questions, key=lambda x: x["processing_time"], reverse=True)[:5]
        }

# Define tools using the @function_tool decorator
@function_tool
def search_hcpcs(terms: str, max_results: int = 5) -> Dict[str, Any]:
    """Search HCPCS Level II codes for medical equipment, supplies, and non-physician services"""
    try:
        result = hcpcs_api.search_codes(terms, max_results)
        return {"tool": "HCPCS", "results": result.get("results", [])[:3]}
    except Exception as e:
        logger.error(f"HCPCS search error: {e}")
        return {"error": str(e)}

@function_tool
def search_icd10cm(terms: str, max_results: int = 5) -> Dict[str, Any]:
    """Search ICD-10-CM diagnosis codes"""
    try:
        result = icd10cm_api.search_codes(terms, max_results)
        return {"tool": "ICD-10-CM", "results": result.get("results", [])[:3]}
    except Exception as e:
        logger.error(f"ICD-10-CM search error: {e}")
        return {"error": str(e)}

@function_tool
def search_procedures(terms: str, max_results: int = 5) -> Dict[str, Any]:
    """Search medical procedures"""
    try:
        result = procedures_api.search_procedures(terms, max_results)
        return {"tool": "Procedures", "results": result.get("results", [])[:3]}
    except Exception as e:
        logger.error(f"Procedures search error: {e}")
        return {"error": str(e)}

@function_tool
def search_conditions(terms: str, max_results: int = 5) -> Dict[str, Any]:
    """Search medical conditions and disorders"""
    try:
        result = conditions_api.search_conditions(terms, max_results)
        return {"tool": "Conditions", "results": result.get("results", [])[:3]}
    except Exception as e:
        logger.error(f"Conditions search error: {e}")
        return {"error": str(e)}

@function_tool
def lookup_medical_term(term: str) -> Dict[str, Any]:
    """Look up medical terminology, prefixes, suffixes, anatomy, and coding guidelines"""
    try:
        term_lower = term.lower()
        matches = [t for t in medical_terms if term_lower in t.get("term", "").lower() or term_lower in t.get("definition", "").lower()]
        return {"tool": "Medical Terminology", "results": matches[:3]}
    except Exception as e:
        logger.error(f"Medical terminology lookup error: {e}")
        return {"error": str(e)}

class CPCAgent:
    """CPC medical coding agent using OpenAI Agents framework"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Initialize the CPC agent"""
        # Set the API key as environment variable for the agents framework
        import os
        os.environ['OPENAI_API_KEY'] = api_key
        
        # Enable tracing for detailed analysis (optional - will work without valid key)
        try:
            from agents import set_tracing_export_api_key
            set_tracing_export_api_key(api_key)
        except Exception:
            pass  # Tracing optional
        
        # Define the agent with instructions and tools
        self.agent = Agent(
            name="CPC Medical Coding Expert",
            instructions="""You are a medical coding expert specializing in CPC (Certified Professional Coder) certification.

Your expertise includes:
- ICD-10-CM diagnosis coding
- CPT procedure coding  
- HCPCS Level II codes
- Medical terminology and anatomy
- Coding guidelines and compliance
- Healthcare documentation

When answering CPC exam questions:
1. Analyze the clinical scenario carefully
2. Use available tools to research relevant codes and information
3. Apply proper coding guidelines and conventions
4. Consider all provided options thoroughly
5. Return ONLY the letter of the correct answer (A, B, C, or D)

Always think through the problem step-by-step and use the medical coding tools to verify your reasoning.""",
            tools=[search_hcpcs, search_icd10cm, search_procedures, search_conditions, lookup_medical_term],
            model=model
        )
        
        # Initialize logger
        self.logger = CPCTestLogger()
        self.tools_used = []  # Track tools used in current question
        
        logger.info("Initialized CPC Agent using OpenAI Agents framework")
    
    def answer_question(self, question_data: Dict[str, Any], options: Dict[str, str], correct_answer: str = None) -> str:
        """Answer a CPC test question using the OpenAI Agents framework"""
        
        # Reset tools tracking for this question
        self.tools_used = []
        start_time = datetime.now()
        
        question_text = question_data.get("stem", "") if isinstance(question_data, dict) else str(question_data)
        
        # Format the question with options
        formatted_question = f"""CPC Exam Question:

{question_text}

Options:
A) {options.get('A', '')}
B) {options.get('B', '')} 
C) {options.get('C', '')}
D) {options.get('D', '')}

Please analyze this question step by step, use the available tools to research relevant information, and provide ONLY the letter of the correct answer (A, B, C, or D)."""

        try:
            # Run the agent to get the response with increased max_turns for complex medical questions
            response = Runner.run_sync(
                self.agent, 
                formatted_question, 
                max_turns=25  # Increased from default 10 to allow for complex medical coding research
            )
            
            # Extract tool usage from response
            self._extract_tools_used(response)
            
            # Extract the final answer from the response
            if hasattr(response, 'output') and hasattr(response.output, 'content'):
                answer_text = response.output.content
            elif hasattr(response, 'output'):
                answer_text = str(response.output)
            else:
                answer_text = str(response)
            
            # Extract letter answer
            cleaned = answer_text.strip().upper()
            final_answer = None
            
            if cleaned in {'A', 'B', 'C', 'D'}:
                final_answer = cleaned
            else:
                # Look for pattern like "The answer is C" or similar
                match = re.search(r"\b([ABCD])\b", cleaned)
                if match:
                    final_answer = match.group(1)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Log the result (if we have correct_answer for comparison)
            if correct_answer is not None:
                self.logger.log_question_result(
                    question_data=question_data,
                    agent_response=final_answer or "PARSE_ERROR",
                    correct_answer=correct_answer,
                    tools_used=self.tools_used.copy(),
                    processing_time=processing_time,
                    trace_id=getattr(response, 'trace_id', None)
                )
            
            if final_answer:
                return final_answer
            
            # If we can't extract a valid answer, raise an exception
            raise ValueError(f"Could not extract valid answer (A, B, C, or D) from agent response: '{answer_text}'")
            
        except Exception as e:
            # Still log the error case
            processing_time = (datetime.now() - start_time).total_seconds()
            if correct_answer is not None:
                self.logger.log_question_result(
                    question_data=question_data,
                    agent_response="ERROR",
                    correct_answer=correct_answer,
                    tools_used=self.tools_used.copy(),
                    processing_time=processing_time,
                    trace_id=None
                )
            
            logger.error(f"Error generating answer: {e}")
            # Re-raise the exception instead of defaulting to 'A'
            raise
    
    def _extract_tools_used(self, response) -> None:
        """Extract which tools were used from the agent response"""
        # Extract tool usage from the OpenAI Agents framework response
        if hasattr(response, 'new_items'):
            for item in response.new_items:
                item_type = str(type(item))
                
                # Check for ToolCallItem (when LLM invokes a tool)
                if 'ToolCallItem' in item_type:
                    # Try different ways to get the tool name
                    tool_name = None
                    if hasattr(item, 'raw_item'):
                        if hasattr(item.raw_item, 'function') and hasattr(item.raw_item.function, 'name'):
                            tool_name = item.raw_item.function.name
                        elif hasattr(item.raw_item, 'name'):
                            tool_name = item.raw_item.name
                    elif hasattr(item, 'function_name'):
                        tool_name = item.function_name
                    elif hasattr(item, 'tool_name'):
                        tool_name = item.tool_name
                    
                    if tool_name and tool_name not in self.tools_used:
                        self.tools_used.append(tool_name)
                
                # Check for ToolCallOutputItem (when tool was called and returned)
                elif 'ToolCallOutputItem' in item_type:
                    tool_name = None
                    if hasattr(item, 'tool_name'):
                        tool_name = item.tool_name
                    elif hasattr(item, 'function_name'):
                        tool_name = item.function_name
                    
                    if tool_name and tool_name not in self.tools_used:
                        self.tools_used.append(tool_name)
    
    def save_session_results(self, total_questions: int, correct_answers: int, duration: float) -> Dict[str, Any]:
        """Save complete session analytics"""
        return self.logger.save_session_summary(
            total_questions=total_questions,
            correct_answers=correct_answers, 
            duration=duration,
            test_metadata={
                "agent_model": self.agent.model,
                "tools_available": ["search_hcpcs", "search_icd10cm", "search_procedures", "search_conditions", "lookup_medical_term"]
            }
        )
