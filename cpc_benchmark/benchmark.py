"""
Main benchmarking class for running CPC practice test evaluations.

This module contains the Benchmark class that coordinates the entire benchmarking
process, from loading questions to generating results.
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from tqdm import tqdm
import pandas as pd

from cpc_parser import QuestionDataset
from .models import ModelProvider
from .evaluator import Evaluator


@dataclass
class BenchmarkResult:
    """Container for benchmark results."""
    model_name: str
    timestamp: str
    total_questions: int
    correct_answers: int
    accuracy: float
    passed_70_percent: bool
    total_tokens: int
    total_cost: float
    total_time: float
    avg_latency: float
    extraction_failures: int
    detailed_results: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def save_to_json(self, filepath: str):
        """Save results to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def save_to_csv(self, filepath: str):
        """Save detailed results to CSV file."""
        df = pd.DataFrame(self.detailed_results)
        df.to_csv(filepath, index=False)


class Benchmark:
    """Main benchmarking class for evaluating models on CPC questions."""
    
    def __init__(self, 
                 questions_path: str,
                 results_dir: str = "results",
                 verbose: bool = True):
        """
        Initialize the benchmark.
        
        Args:
            questions_path: Path to the JSONL file with questions
            results_dir: Directory to save results
            verbose: Whether to print progress
        """
        self.questions_path = Path(questions_path)
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        
        # Load questions
        self.dataset = QuestionDataset.from_jsonl(str(self.questions_path))
        self.questions = self.dataset.questions
        
        if self.verbose:
            print(f"Loaded {len(self.questions)} questions from {self.questions_path}")
    
    def run_single_model(self, 
                        model_provider: ModelProvider,
                        limit: Optional[int] = None,
                        save_results: bool = True) -> BenchmarkResult:
        """
        Run benchmark on a single model.
        
        Args:
            model_provider: The model provider to benchmark
            limit: Limit number of questions (for testing)
            save_results: Whether to save results to disk
            
        Returns:
            BenchmarkResult object
        """
        model_name = f"{model_provider.__class__.__name__}_{model_provider.model_name}"
        
        if self.verbose:
            print(f"\nBenchmarking {model_name}...")
        
        # Initialize evaluator
        evaluator = Evaluator()
        
        # Reset model metrics
        model_provider.reset_metrics()
        
        # Track timing
        start_time = time.time()
        
        # Determine questions to process
        questions_to_process = self.questions[:limit] if limit else self.questions
        
        # Process each question
        detailed_results = []
        
        for question in tqdm(questions_to_process, desc=f"Processing {model_name}", disable=not self.verbose):
            # Generate prompt
            prompt = question.to_prompt(include_options=True)
            
            try:
                # Get model response
                response_data = model_provider.generate(prompt, max_tokens=10)
                
                # Evaluate response
                eval_result = evaluator.evaluate_response(
                    question_id=question.id,
                    correct_answer=question.correct_answer_letter,
                    model_response=response_data['response'],
                    model_name=model_name
                )
                
                # Combine results
                detailed_result = {
                    **eval_result,
                    'tokens_used': response_data['tokens_used'],
                    'latency': response_data['latency'],
                    'cost': response_data['cost']
                }
                detailed_results.append(detailed_result)
                
            except Exception as e:
                # Handle API errors
                if self.verbose:
                    print(f"\nError processing question {question.id}: {e}")
                
                # Record failure
                detailed_result = {
                    'question_id': question.id,
                    'model_name': model_name,
                    'correct_answer': question.correct_answer_letter,
                    'model_response': f"ERROR: {str(e)}",
                    'predicted_answer': None,
                    'is_correct': False,
                    'extraction_failed': True,
                    'tokens_used': 0,
                    'latency': 0,
                    'cost': 0
                }
                detailed_results.append(detailed_result)
        
        # Calculate total time
        total_time = time.time() - start_time
        
        # Get metrics from evaluator
        metrics = evaluator.calculate_metrics(model_name)
        
        # Create result object
        result = BenchmarkResult(
            model_name=model_name,
            timestamp=datetime.now().isoformat(),
            total_questions=len(questions_to_process),
            correct_answers=metrics['correct_answers'],
            accuracy=metrics['accuracy'],
            passed_70_percent=metrics['passed_70_percent'],
            total_tokens=model_provider.total_tokens,
            total_cost=model_provider.total_cost,
            total_time=total_time,
            avg_latency=total_time / len(questions_to_process) if questions_to_process else 0,
            extraction_failures=metrics['extraction_failures'],
            detailed_results=detailed_results,
            metrics=metrics
        )
        
        # Save results if requested
        if save_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save JSON summary
            json_path = self.results_dir / f"{model_name}_{timestamp}_summary.json"
            result.save_to_json(str(json_path))
            
            # Save CSV details
            csv_path = self.results_dir / f"{model_name}_{timestamp}_details.csv"
            result.save_to_csv(str(csv_path))
            
            if self.verbose:
                print(f"Results saved to {json_path} and {csv_path}")
        
        # Print summary
        if self.verbose:
            print(f"\n{model_name} Results:")
            print(f"  Accuracy: {result.accuracy:.2%} ({result.correct_answers}/{result.total_questions})")
            print(f"  Passed 70%: {'Yes' if result.passed_70_percent else 'No'}")
            print(f"  Total Cost: ${result.total_cost:.4f}")
            print(f"  Total Time: {result.total_time:.2f}s")
            print(f"  Avg Latency: {result.avg_latency:.2f}s per question")
        
        return result
    
    def run_all_models(self,
                      model_providers: List[ModelProvider],
                      limit: Optional[int] = None,
                      save_results: bool = True) -> List[BenchmarkResult]:
        """
        Run benchmark on multiple models.
        
        Args:
            model_providers: List of model providers to benchmark
            limit: Limit number of questions (for testing)
            save_results: Whether to save results
            
        Returns:
            List of BenchmarkResult objects
        """
        results = []
        
        for provider in model_providers:
            try:
                result = self.run_single_model(provider, limit=limit, save_results=save_results)
                results.append(result)
            except Exception as e:
                if self.verbose:
                    print(f"\nError benchmarking {provider.__class__.__name__}: {e}")
                continue
        
        # Generate comparison report
        if results and save_results:
            self._save_comparison_report(results)
        
        return results
    
    def _save_comparison_report(self, results: List[BenchmarkResult]):
        """Save a comparison report of all models."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create comparison data
        comparison_data = []
        for result in results:
            comparison_data.append({
                'Model': result.model_name,
                'Accuracy': result.accuracy,
                'Correct': result.correct_answers,
                'Total': result.total_questions,
                'Passed_70%': result.passed_70_percent,
                'Total_Cost': result.total_cost,
                'Total_Time': result.total_time,
                'Avg_Latency': result.avg_latency,
                'Extraction_Failures': result.extraction_failures
            })
        
        # Save as CSV
        df = pd.DataFrame(comparison_data)
        csv_path = self.results_dir / f"comparison_{timestamp}.csv"
        df.to_csv(csv_path, index=False)
        
        # Save as formatted text report
        evaluator = Evaluator()
        # Add all results to evaluator for report generation
        for result in results:
            evaluator.results.extend(result.detailed_results)
        
        report = evaluator.generate_report([r.model_name for r in results])
        report_path = self.results_dir / f"comparison_{timestamp}_report.txt"
        
        with open(report_path, 'w') as f:
            f.write(report)
            f.write("\n\nCOST ANALYSIS\n")
            f.write("-" * 40 + "\n")
            for result in sorted(results, key=lambda x: x.total_cost):
                f.write(f"{result.model_name}: ${result.total_cost:.4f}\n")
        
        if self.verbose:
            print(f"\nComparison report saved to {report_path}") 