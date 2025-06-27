#!/usr/bin/env python
"""
Run benchmarks on all configured models for CPC practice test.

This script runs the full benchmark suite on GPT-4o, Claude 3.5 Sonnet, and Gemini 1.5 Pro,
evaluating their performance on medical coding questions.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import cpc_benchmark
sys.path.insert(0, str(Path(__file__).parent.parent))

from cpc_benchmark.runner import run_benchmarks, quick_test
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    """Run the benchmark suite."""
    parser = argparse.ArgumentParser(
        description="Benchmark LLMs on CPC practice test questions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full benchmark on all models
  python benchmark_all.py
  
  # Run quick test with 5 questions
  python benchmark_all.py --quick-test
  
  # Run on specific models only
  python benchmark_all.py --models openai:gpt-4o anthropic:claude-3-5-sonnet-20241022
  
  # Run on first 20 questions only
  python benchmark_all.py --limit 20
        """
    )
    
    parser.add_argument(
        "--models", 
        nargs="+", 
        help="Specific models to benchmark (format: provider:model-name)"
    )
    parser.add_argument(
        "--limit", 
        type=int, 
        help="Limit number of questions to process"
    )
    parser.add_argument(
        "--quick-test", 
        action="store_true", 
        help="Run quick test with 5 questions"
    )
    parser.add_argument(
        "--questions", 
        default="data/processed/cpc_test.jsonl",
        help="Path to questions JSONL file"
    )
    parser.add_argument(
        "--results-dir", 
        default="results",
        help="Directory to save results"
    )
    
    args = parser.parse_args()
    
    # Check for questions file
    if not Path(args.questions).exists():
        print(f"Error: Questions file not found: {args.questions}")
        print("Run 'make parse' first to generate the questions file.")
        sys.exit(1)
    
    # Check for API keys
    print("Checking API keys...")
    api_keys = {
        "OpenAI": os.getenv("OPENAI_API_KEY"),
        "Anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "Google": os.getenv("GOOGLE_API_KEY")
    }
    
    # Placeholder values to check against
    placeholders = [
        "your_openai_api_key_here",
        "your_anthropic_api_key_here", 
        "your_google_api_key_here"
    ]
    
    available_providers = []
    for provider, key in api_keys.items():
        if key and key not in placeholders:
            print(f"✓ {provider} API key found")
            available_providers.append(provider.lower())
        else:
            if key in placeholders:
                print(f"✗ {provider} API key is a placeholder (set {provider.upper()}_API_KEY)")
            else:
                print(f"✗ {provider} API key not found (set {provider.upper()}_API_KEY)")
    
    if not available_providers:
        print("\nError: No valid API keys found!")
        print("Please set at least one real API key in your environment or .env file.")
        print("\nExample .env file:")
        print("OPENAI_API_KEY=sk-...")
        print("ANTHROPIC_API_KEY=sk-ant-...")
        print("GOOGLE_API_KEY=AIza...")
        sys.exit(1)
    
    print(f"\nAvailable providers: {', '.join(available_providers)}")
    
    # Run appropriate benchmark
    if args.quick_test:
        print("\nRunning quick test...")
        quick_test(num_questions=5)
    else:
        # Filter models based on available API keys
        if args.models:
            models = args.models
        else:
            # Default models based on available API keys
            models = []
            if "openai" in available_providers:
                models.append("openai:gpt-4o")
            if "anthropic" in available_providers:
                models.append("anthropic:claude-3-5-sonnet-20241022")
            if "google" in available_providers:
                models.append("google:gemini-1.5-pro")
        
        # Filter out models for which we don't have API keys
        filtered_models = []
        for model in models:
            provider = model.split(":")[0].lower()
            if provider in available_providers:
                filtered_models.append(model)
            else:
                print(f"Skipping {model} (no API key)")
        
        if not filtered_models:
            print("\nError: No models to benchmark!")
            sys.exit(1)
        
        print(f"\nBenchmarking models: {', '.join(filtered_models)}")
        if args.limit:
            print(f"Limited to {args.limit} questions")
        else:
            print("Running on all 100 questions")
        
        # Run benchmarks
        results = run_benchmarks(
            questions_path=args.questions,
            results_dir=args.results_dir,
            models=filtered_models,
            limit=args.limit,
            verbose=True
        )
        
        if results:
            print("\n" + "="*60)
            print("BENCHMARK COMPLETE!")
            print("="*60)
            print("\nFinal Results:")
            for result in sorted(results, key=lambda x: x.accuracy, reverse=True):
                status = "PASS ✓" if result.passed_70_percent else "FAIL ✗"
                print(f"{result.model_name:40} {result.accuracy:6.2%} ({result.correct_answers:3}/{result.total_questions}) [{status}] Cost: ${result.total_cost:.4f}")
            
            print(f"\nDetailed results saved to: {args.results_dir}/")
        else:
            print("\nNo results generated. Check errors above.")


if __name__ == "__main__":
    main() 