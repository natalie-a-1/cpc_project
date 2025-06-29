"""
CPC Test Logger
Handles logging and analytics for CPC test results
"""
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

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