#!/usr/bin/env python3
"""
Simple CPC Test Analytics Viewer
"""
import json
from pathlib import Path
from typing import List, Dict, Any

def load_recent_sessions(limit: int = 10) -> List[Dict[str, Any]]:
    """Load recent test sessions"""
    results_dir = Path("cpc_tests")
    if not results_dir.exists():
        print("No test results found. Run a CPC test first.")
        return []
    
    session_files = list(results_dir.glob("session_summary_*.json"))
    session_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    sessions = []
    for session_file in session_files[:limit]:
        try:
            with open(session_file, 'r') as f:
                sessions.append(json.load(f))
        except Exception as e:
            print(f"Error loading {session_file}: {e}")
    
    return sessions

def print_session_summary(session: Dict[str, Any]):
    """Print a summary of a test session"""
    perf = session['performance']
    print(f"\n📊 Session: {session['session_id']} ({session['timestamp'][:19]})")
    print(f"   Score: {perf['correct_answers']}/{perf['total_questions']} ({perf['score_percentage']}%) - {perf['pass_status']}")
    print(f"   Duration: {perf['total_duration_minutes']} min ({perf['avg_time_per_question_seconds']}s per question)")
    
    # Tool usage
    tool_analytics = session['tool_analytics']
    print(f"   Tools: {tool_analytics['total_tool_calls']} calls, {tool_analytics['tools_per_question_avg']} avg per question")
    
    # Top 3 most used tools
    top_tools = list(tool_analytics['tool_frequency'].items())[:3]
    if top_tools:
        tools_str = ", ".join([f"{tool}({count})" for tool, count in top_tools])
        print(f"   Most used: {tools_str}")

def print_category_analysis(sessions: List[Dict[str, Any]]):
    """Print category performance analysis across sessions"""
    print("\n📈 CPC CODING SYSTEM PERFORMANCE")
    print("="*50)
    
    category_totals = {}
    
    for session in sessions:
        for category, stats in session['category_performance'].items():
            if category not in category_totals:
                category_totals[category] = {'total': 0, 'correct': 0}
            category_totals[category]['total'] += stats['total']
            category_totals[category]['correct'] += stats['correct']
    
    # Calculate overall percentages
    for category, totals in category_totals.items():
        accuracy = (totals['correct'] / totals['total']) * 100 if totals['total'] > 0 else 0
        category_totals[category]['accuracy'] = accuracy
    
    # Sort with main coding systems first, then uncategorized
    priority_order = ['HCPCS', 'ICD', 'CPT', '']
    sorted_categories = []
    
    for category in priority_order:
        if category in category_totals:
            sorted_categories.append((category, category_totals[category]))
    
    # Add any other categories that might exist
    for category, stats in category_totals.items():
        if category not in priority_order:
            sorted_categories.append((category, stats))
    
    for category, stats in sorted_categories:
        category_name = category if category else "Uncategorized"
        print(f"{category_name:15} {stats['accuracy']:5.1f}% ({stats['correct']:3d}/{stats['total']:3d})")
    
    # Show insights if we have main categories
    main_categories = {k: v for k, v in category_totals.items() if k in ['HCPCS', 'ICD', 'CPT']}
    if main_categories:
        worst_system = min(main_categories.items(), key=lambda x: x[1]['accuracy'])
        print(f"\n💡 Focus area: {worst_system[0]} coding system ({worst_system[1]['accuracy']:.1f}% accuracy)")

def print_error_analysis(sessions: List[Dict[str, Any]]):
    """Print common error patterns"""
    print("\n🔍 ERROR PATTERN ANALYSIS")
    print("="*50)
    
    all_errors = {}
    slow_questions = []
    
    for session in sessions:
        error_analysis = session['error_analysis']
        
        # Collect error categories
        for category, count in error_analysis['errors_by_category'].items():
            all_errors[category] = all_errors.get(category, 0) + count
        
        # Collect slow questions
        slow_questions.extend(error_analysis['slow_processing_questions'])
    
    # Print most common error categories
    print("Most common error categories:")
    sorted_errors = sorted(all_errors.items(), key=lambda x: x[1], reverse=True)
    for category, count in sorted_errors[:5]:
        print(f"  {category:15} {count:3d} errors")
    
    # Print slowest questions
    if slow_questions:
        print("\nSlowest processing questions:")
        slow_questions.sort(key=lambda x: x['processing_time'], reverse=True)
        for q in slow_questions[:3]:
            print(f"  {q['processing_time']:5.1f}s - {q['category']} (ID: {q['question_id']})")

def main():
    """Main analytics viewer"""
    print("🎯 CPC Test Analytics Viewer")
    print("="*50)
    
    sessions = load_recent_sessions()
    if not sessions:
        return
    
    print(f"Found {len(sessions)} recent test sessions:")
    
    # Print session summaries
    for session in sessions:
        print_session_summary(session)
    
    # Overall analytics
    if len(sessions) > 1:
        print_category_analysis(sessions)
        print_error_analysis(sessions)
    
    print(f"\n💡 Tip: Review individual session files in cpc_tests/ for detailed question-by-question analysis")

if __name__ == "__main__":
    main() 