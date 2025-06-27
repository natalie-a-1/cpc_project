"""
Runner module for executing CPC benchmarks.

This module provides convenient functions for running benchmarks with different
configurations and model combinations.
"""

import os
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging
from dotenv import load_dotenv

from .models import OpenAIProvider, AnthropicProvider, GoogleProvider, ModelProvider
from .benchmark import Benchmark, BenchmarkResult

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_providers(models: Optional[List[str]] = None) -> List[ModelProvider]:
    """
    Create model providers based on configuration.
    
    Args:
        models: List of model identifiers. If None, creates all default models.
                Format: ["openai:gpt-4o", "anthropic:claude-3-5-sonnet", "google:gemini-1.5-pro"]
    
    Returns:
        List of ModelProvider instances
    """
    if models is None:
        # Default models
        models = [
            "openai:gpt-4o",
            "anthropic:claude-3-5-sonnet-20241022",
            "google:gemini-1.5-pro"
        ]
    
    providers = []
    
    for model_spec in models:
        try:
            provider_name, model_name = model_spec.split(":", 1)
            
            if provider_name.lower() == "openai":
                provider = OpenAIProvider(model_name=model_name)
            elif provider_name.lower() == "anthropic":
                provider = AnthropicProvider(model_name=model_name)
            elif provider_name.lower() == "google":
                provider = GoogleProvider(model_name=model_name)
            else:
                logger.warning(f"Unknown provider: {provider_name}")
                continue
            
            providers.append(provider)
            logger.info(f"Created provider: {provider.__class__.__name__} with model {model_name}")
            
        except Exception as e:
            logger.error(f"Error creating provider for {model_spec}: {e}")
            continue
    
    return providers


def run_benchmarks(
    questions_path: str = "data/processed/cpc_test.jsonl",
    results_dir: str = "results",
    models: Optional[List[str]] = None,
    limit: Optional[int] = None,
    verbose: bool = True
) -> List[BenchmarkResult]:
    """
    Run benchmarks on specified models.
    
    Args:
        questions_path: Path to JSONL file with questions
        results_dir: Directory to save results
        models: List of model specifications (e.g., ["openai:gpt-4o"])
        limit: Limit number of questions to process (for testing)
        verbose: Whether to print progress
        
    Returns:
        List of BenchmarkResult objects
    """
    # Create benchmark instance
    benchmark = Benchmark(
        questions_path=questions_path,
        results_dir=results_dir,
        verbose=verbose
    )
    
    # Create providers
    providers = create_providers(models)
    
    if not providers:
        logger.error("No providers created. Check your API keys and model specifications.")
        return []
    
    # Run benchmarks
    results = benchmark.run_all_models(
        model_providers=providers,
        limit=limit,
        save_results=True
    )
    
    return results


def run_single_model_benchmark(
    model_spec: str,
    questions_path: str = "data/processed/cpc_test.jsonl",
    results_dir: str = "results",
    limit: Optional[int] = None,
    verbose: bool = True
) -> Optional[BenchmarkResult]:
    """
    Run benchmark on a single model.
    
    Args:
        model_spec: Model specification (e.g., "openai:gpt-4o")
        questions_path: Path to JSONL file with questions
        results_dir: Directory to save results
        limit: Limit number of questions to process
        verbose: Whether to print progress
        
    Returns:
        BenchmarkResult object or None if error
    """
    providers = create_providers([model_spec])
    
    if not providers:
        return None
    
    benchmark = Benchmark(
        questions_path=questions_path,
        results_dir=results_dir,
        verbose=verbose
    )
    
    return benchmark.run_single_model(
        model_provider=providers[0],
        limit=limit,
        save_results=True
    )


def quick_test(num_questions: int = 5):
    """
    Run a quick test with a few questions on all models.
    
    Args:
        num_questions: Number of questions to test
    """
    print(f"\nRunning quick test with {num_questions} questions...")
    
    # Check for API keys and determine available models
    available_models = []
    
    if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "your_openai_api_key_here":
        available_models.append("openai:gpt-4o")
    else:
        print("⚠ OpenAI API key not found or is placeholder")
        
    if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "your_anthropic_api_key_here":
        available_models.append("anthropic:claude-3-5-sonnet-20241022")
    else:
        print("⚠ Anthropic API key not found or is placeholder")
        
    if os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_API_KEY") != "your_google_api_key_here":
        available_models.append("google:gemini-1.5-pro")
    else:
        print("⚠ Google API key not found or is placeholder")
    
    if not available_models:
        print("\n❌ No valid API keys found!")
        print("Please set real API keys in your .env file:")
        print("  - OPENAI_API_KEY")
        print("  - ANTHROPIC_API_KEY")
        print("  - GOOGLE_API_KEY")
        return
    
    print(f"\nUsing available models: {', '.join(available_models)}")
    
    # Run test with available models only
    results = run_benchmarks(
        models=available_models,
        limit=num_questions
    )
    
    if results:
        print("\n✅ Quick test completed!")
        print("\nSummary:")
        for result in results:
            status = "PASS" if result.passed_70_percent else "FAIL"
            print(f"  {result.model_name}: {result.accuracy:.0%} ({result.correct_answers}/{result.total_questions}) [{status}]")
    else:
        print("\n❌ No results generated. Check the errors above.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run CPC benchmarks")
    parser.add_argument("--models", nargs="+", help="Models to benchmark (e.g., openai:gpt-4o)")
    parser.add_argument("--limit", type=int, help="Limit number of questions")
    parser.add_argument("--questions", default="data/processed/cpc_test.jsonl", help="Path to questions")
    parser.add_argument("--results", default="results", help="Results directory")
    parser.add_argument("--quick-test", action="store_true", help="Run quick test with 5 questions")
    parser.add_argument("--quiet", action="store_true", help="Reduce output")
    
    args = parser.parse_args()
    
    if args.quick_test:
        quick_test()
    else:
        results = run_benchmarks(
            questions_path=args.questions,
            results_dir=args.results,
            models=args.models,
            limit=args.limit,
            verbose=not args.quiet
        ) 