#!/usr/bin/env python3
"""
CPC Test Runner - Loads test questions and grades agent performance
"""
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Tuple
from cpc_agent import CPCAgent


def load_test_questions(test_file: Path) -> List[Dict]:
    """Load test questions from JSONL file"""
    questions = []
    with open(test_file, 'r') as f:
        for line in f:
            if line.strip():
                questions.append(json.loads(line.strip()))
    return questions


def run_test(agent: CPCAgent, questions: List[Dict]) -> Tuple[List[Dict], float]:
    """Run the CPC test and return results with timing"""
    results = []
    start_time = time.time()
    
    for i, question in enumerate(questions, 1):
        print(f"Question {i}/{len(questions)}: Processing...")
        
        # Extract question components
        stem = question["stem"]
        options = {
            "A": question["option_a"],
            "B": question["option_b"], 
            "C": question["option_c"],
            "D": question["option_d"]
        }
        correct_answer = question["correct_answer_letter"]
        
        # Get agent's answer with full logging
        agent_answer = agent.answer_question(question, options, correct_answer)
        
        # Record result
        result = {
            "question_id": question["id"],
            "agent_answer": agent_answer,
            "correct_answer": correct_answer,
            "correct": agent_answer == correct_answer,
            "stem": stem,
            "options": options
        }
        results.append(result)
        
        # Show progress
        status = "✓" if result["correct"] else "✗"
        print(f"  {status} Agent: {agent_answer}, Correct: {correct_answer}")
    
    duration = time.time() - start_time
    return results, duration


def grade_test(results: List[Dict]) -> Dict:
    """Calculate test grade and statistics"""
    total_questions = len(results)
    correct_answers = sum(1 for r in results if r["correct"])
    score_percentage = (correct_answers / total_questions) * 100
    
    return {
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "incorrect_answers": total_questions - correct_answers,
        "score_percentage": score_percentage,
        "pass_status": "PASS" if score_percentage >= 70 else "FAIL"
    }


def print_results(grade: Dict, duration: float):
    """Print formatted test results"""
    print("\n" + "="*60)
    print("🎯 CPC TEST RESULTS")
    print("="*60)
    print(f"Score: {grade['correct_answers']}/{grade['total_questions']} ({grade['score_percentage']:.1f}%)")
    print(f"Status: {grade['pass_status']} (70% required to pass)")
    print(f"Duration: {duration/60:.1f} minutes")
    print(f"Avg per question: {duration/grade['total_questions']:.1f} seconds")
    print("="*60)


def main():
    """Main test runner"""
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not found")
    
    # Load test questions
    test_file = Path("data/processed/cpc_test/cpc_test.jsonl")
    if not test_file.exists():
        raise FileNotFoundError(f"Test file not found: {test_file}")
    
    print(f"📝 Loading test questions from {test_file}")
    questions = load_test_questions(test_file)
    print(f"✅ Loaded {len(questions)} questions")
    
    # Initialize agent
    print("🤖 Initializing CPC Agent...")
    agent = CPCAgent(api_key)
    
    # Run test
    print(f"🏃 Running CPC test ({len(questions)} questions)...")
    results, duration = run_test(agent, questions)
    
    # Grade test
    grade = grade_test(results)
    
    # Print results
    print_results(grade, duration)
    
    # Save detailed analytics
    print("\n💾 Saving detailed analytics...")
    analytics = agent.save_session_results(
        total_questions=grade['total_questions'],
        correct_answers=grade['correct_answers'], 
        duration=duration
    )
    
    # Print analytics summary
    print(f"📊 Analytics saved to: cpc_tests/run_{analytics['session_id']}/session_summary_{analytics['session_id']}.json")
    print(f"🔧 Tools used: {analytics['tool_analytics']['total_tool_calls']} calls across {len(analytics['tool_analytics']['tool_frequency'])} tools")
    
    if analytics['category_performance']:
        # Find worst performing main coding system
        main_systems = {k: v for k, v in analytics['category_performance'].items() if k in ['HCPCS', 'ICD', 'CPT']}
        if main_systems:
            worst_system = min(main_systems.items(), key=lambda x: x[1]['accuracy_percentage'])
            print(f"📈 Focus area: {worst_system[0]} coding system ({worst_system[1]['accuracy_percentage']}% accuracy)")
        else:
            # Fallback to any category
            worst_category = next(iter(analytics['category_performance']))
            worst_performance = analytics['category_performance'][worst_category]['accuracy_percentage']
            print(f"📈 Worst performing area: {worst_category or 'Uncategorized'} ({worst_performance}% accuracy)")
    
    return grade


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1) 