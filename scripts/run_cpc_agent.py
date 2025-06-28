#!/usr/bin/env python3
"""
Simple interactive CPC agent runner
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from cpc_agent.agent import CPCAgent

def interactive_mode(agent: CPCAgent):
    """Interactive mode for asking questions"""
    print("🤖 CPC Agent Interactive Mode")
    print("Ask medical coding questions or type 'quit' to exit")
    print("-" * 50)
    
    while True:
        question = input("\nQuestion: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        
        if not question:
            continue
        
        # For interactive mode, we don't have options, so create dummy ones
        options = {'A': '', 'B': '', 'C': '', 'D': ''}
        
        try:
            print("🔍 Searching...")
            answer = agent.answer_question(question, options)
            print(f"💡 Answer: {answer}")
        except Exception as e:
            print(f"❌ Error: {e}")

def test_mode(agent: CPCAgent):
    """Test mode with sample questions"""
    test_questions = [
        {
            "question": "What is the CPT code for a diagnostic colonoscopy?",
            "options": {"A": "45378", "B": "45380", "C": "45381", "D": "45384"}
        },
        {
            "question": "What code should be used for type 2 diabetes without complications?",
            "options": {"A": "E11.9", "B": "E10.9", "C": "E13.9", "D": "E08.9"}
        },
        {
            "question": "Find the HCPCS code for a manual wheelchair",
            "options": {"A": "K0001", "B": "K0002", "C": "K0003", "D": "K0004"}
        },
        {
            "question": "What is the ICD-10 code for essential hypertension?",
            "options": {"A": "I10", "B": "I11.9", "C": "I12.9", "D": "I13.10"}
        }
    ]
    
    print("🧪 Running test queries...")
    print("-" * 50)
    
    for i, test in enumerate(test_questions, 1):
        print(f"\nQuestion {i}: {test['question']}")
        print("Options:", ", ".join([f"{k}: {v}" for k, v in test['options'].items()]))
        
        try:
            answer = agent.answer_question(test['question'], test['options'])
            print(f"Answer: {answer}")
        except Exception as e:
            print(f"Error: {e}")
        
        print("-" * 40)

def main():
    # Load environment variables
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment")
        sys.exit(1)
    
    print("🤖 Initializing CPC Agent...")
    agent = CPCAgent(api_key, "gpt-4o-mini")
    
    # Choose mode
    print("\nChoose mode:")
    print("1. Interactive mode")
    print("2. Test mode")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        interactive_mode(agent)
    elif choice == "2":
        test_mode(agent)
    else:
        print("Invalid choice. Using test mode.")
        test_mode(agent)

if __name__ == "__main__":
    main() 