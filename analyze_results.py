#!/usr/bin/env python3
"""
CPC Test Results Analyzer
Analyzes test results to identify patterns in missed questions
"""

import json
import sys
from pathlib import Path
from collections import Counter
from typing import Dict, List
from datetime import datetime

def load_results(json_file: str) -> Dict:
    """Load test results from JSON file"""
    try:
        with open(json_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File {json_file} not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {json_file}")
        sys.exit(1)

def extract_category_from_tools(tools_used: List[str]) -> str:
    """Extract the specialist category from tools_used list"""
    for tool in tools_used:
        if "_Specialist" in tool:
            # Extract category from "CPT_Specialist" -> "CPT"
            return tool.replace("_Specialist", "")
    return "Unknown"

def analyze_missed_categories(results: Dict) -> Dict[str, int]:
    """Analyze which categories were missed most often"""
    missed_categories = []
    
    for result in results.get("detailed_results", []):
        if not result.get("is_correct", True):  # Question was missed
            tools_used = result.get("tools_used", [])
            category = extract_category_from_tools(tools_used)
            missed_categories.append(category)
    
    return Counter(missed_categories)

def save_analysis_to_json(analysis_data: Dict, input_file: str) -> str:
    """Save analysis results to JSON file"""
    input_path = Path(input_file)
    # Create output filename based on input file
    output_filename = f"analysis_report_{input_path.stem.replace('session_summary_', '')}.json"
    output_path = input_path.parent / output_filename
    
    try:
        with open(output_path, 'w') as f:
            json.dump(analysis_data, f, indent=2, default=str)
        return str(output_path)
    except Exception as e:
        print(f"Error saving analysis to JSON: {e}")
        return None

def print_and_analyze(results: Dict, input_file: str) -> Dict:
    """Print comprehensive analysis and return structured data for JSON export"""
    print("=" * 60)
    print("CPC TEST RESULTS ANALYSIS")
    print("=" * 60)
    
    # Overall performance
    performance = results.get("performance", {})
    total = performance.get("total_questions", 0)
    correct = performance.get("correct_answers", 0)
    missed = total - correct
    
    print(f"\n📊 OVERALL PERFORMANCE:")
    print(f"   Total Questions: {total}")
    print(f"   Correct Answers: {correct}")
    print(f"   Missed Questions: {missed}")
    print(f"   Score: {performance.get('score_percentage', 0)}%")
    print(f"   Status: {performance.get('pass_status', 'Unknown')}")
    
    # Analyze missed categories
    missed_categories = analyze_missed_categories(results)
    
    # Initialize analysis data structure
    analysis_data = {
        "analysis_timestamp": datetime.now().isoformat(),
        "source_file": input_file,
        "overall_performance": {
            "total_questions": total,
            "correct_answers": correct,
            "missed_questions": missed,
            "score_percentage": performance.get('score_percentage', 0),
            "status": performance.get('pass_status', 'Unknown'),
            "duration_minutes": performance.get('total_duration_minutes', 0)
        },
        "missed_categories_analysis": {
            "categories": dict(missed_categories.most_common()) if missed_categories else {},
            "most_common_category": None,
            "detailed_missed_questions": []
        }
    }
    
    print(f"\n❌ MISSED QUESTIONS BY CATEGORY:")
    if not missed_categories:
        print("   No missed questions found!")
        return analysis_data
    
    # Sort by frequency (most missed first)
    sorted_categories = missed_categories.most_common()
    
    for i, (category, count) in enumerate(sorted_categories, 1):
        percentage = (count / missed) * 100
        print(f"   {i}. {category}: {count} questions ({percentage:.1f}% of missed)")
    
    # Highlight the most common missed category
    if sorted_categories:
        most_missed_category, most_missed_count = sorted_categories[0]
        analysis_data["missed_categories_analysis"]["most_common_category"] = {
            "category": most_missed_category,
            "count": most_missed_count,
            "percentage_of_missed": (most_missed_count / missed) * 100
        }
        
        print(f"\n🎯 MOST COMMON MISSED CATEGORY:")
        print(f"   {most_missed_category} - {most_missed_count} questions missed")
        
        # Show and collect specific missed questions for the top category
        print(f"\n📝 MISSED {most_missed_category} QUESTIONS:")
        question_count = 0
        missed_questions_details = []
        
        for result in results.get("detailed_results", []):
            if not result.get("is_correct", True):
                tools_used = result.get("tools_used", [])
                category = extract_category_from_tools(tools_used)
                if category == most_missed_category:
                    question_count += 1
                    question_id = result.get("question_id", "Unknown")
                    stem = result.get("question_stem", "")
                    agent_answer = result.get("agent_answer", "?")
                    correct_answer = result.get("correct_answer", "?")
                    
                    # Add to detailed analysis data
                    missed_questions_details.append({
                        "question_id": question_id,
                        "question_stem": stem,
                        "agent_answer": agent_answer,
                        "correct_answer": correct_answer,
                        "category": category
                    })
                    
                    # Print (limit display to first 5)
                    if question_count <= 5:
                        stem_display = stem[:80] + "..." if len(stem) > 80 else stem
                        print(f"   Q{question_id}: {stem_display}")
                        print(f"        Agent: {agent_answer} | Correct: {correct_answer}")
                    elif question_count == 6:
                        remaining = most_missed_count - 5
                        if remaining > 0:
                            print(f"        ... and {remaining} more (see JSON for full details)")
        
        analysis_data["missed_categories_analysis"]["detailed_missed_questions"] = missed_questions_details
    
    return analysis_data

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python analyze_results.py <session_summary_file.json>")
        print("Example: python analyze_results.py cpc_tests/run_20250628_185014/session_summary_20250628_185014.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    # Load and analyze results
    results = load_results(json_file)
    analysis_data = print_and_analyze(results, json_file)
    
    # Save analysis to JSON
    json_output_path = save_analysis_to_json(analysis_data, json_file)
    
    if json_output_path:
        print(f"\n💾 Analysis saved to: {json_output_path}")
    else:
        print(f"\n❌ Failed to save analysis to JSON")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
