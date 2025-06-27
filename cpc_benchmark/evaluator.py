"""
Evaluator for assessing model performance on CPC questions.

This module contains the logic for evaluating model responses against correct answers
and calculating various metrics like accuracy, precision, and confusion matrices.
"""

import re
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
import numpy as np


class Evaluator:
    """Evaluates model responses against correct answers."""
    
    def __init__(self):
        """Initialize the evaluator."""
        self.results = []
        self.confusion_matrix = defaultdict(lambda: defaultdict(int))
        
    def extract_answer_letter(self, response: str) -> Optional[str]:
        """
        Extract the answer letter from a model response.
        
        Args:
            response: Raw model response
            
        Returns:
            Extracted letter (A, B, C, or D) or None if not found
        """
        # Clean the response
        response = response.strip().upper()
        
        # First, check if it's just a single letter
        if response in ['A', 'B', 'C', 'D']:
            return response
        
        # Look for patterns like "A)", "A.", "(A)", "A:", "Answer: A"
        patterns = [
            r'^([A-D])[\.)\]:]',  # A. A) A: A]
            r'^\(([A-D])\)',      # (A)
            r'^ANSWER:\s*([A-D])', # Answer: A
            r'^THE ANSWER IS\s*([A-D])',  # The answer is A
            r'^([A-D])\s*[-–—]',  # A - 
            r'^OPTION\s*([A-D])', # Option A
        ]
        
        for pattern in patterns:
            match = re.match(pattern, response)
            if match:
                return match.group(1)
        
        # If no pattern matches, look for isolated occurrences of A, B, C, or D
        # Only match if the letter appears as a word boundary
        for letter in ['A', 'B', 'C', 'D']:
            # Check for isolated letter (with word boundaries)
            isolated_pattern = r'\b' + letter + r'\b'
            if re.search(isolated_pattern, response):
                return letter
        
        return None
    
    def evaluate_response(self, 
                         question_id: int,
                         correct_answer: str, 
                         model_response: str,
                         model_name: str) -> Dict[str, any]:
        """
        Evaluate a single model response.
        
        Args:
            question_id: ID of the question
            correct_answer: The correct answer letter
            model_response: The model's response
            model_name: Name of the model
            
        Returns:
            Dictionary with evaluation results
        """
        # Extract answer letter from response
        predicted_answer = self.extract_answer_letter(model_response)
        
        # Check if extraction was successful
        if predicted_answer is None:
            is_correct = False
            extraction_failed = True
        else:
            is_correct = predicted_answer == correct_answer.upper()
            extraction_failed = False
            # Update confusion matrix
            self.confusion_matrix[correct_answer.upper()][predicted_answer] += 1
        
        result = {
            'question_id': question_id,
            'model_name': model_name,
            'correct_answer': correct_answer.upper(),
            'model_response': model_response,
            'predicted_answer': predicted_answer,
            'is_correct': is_correct,
            'extraction_failed': extraction_failed
        }
        
        self.results.append(result)
        return result
    
    def calculate_metrics(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate evaluation metrics.
        
        Args:
            model_name: If provided, calculate metrics only for this model
            
        Returns:
            Dictionary with metrics
        """
        # Filter results by model if specified
        if model_name:
            results = [r for r in self.results if r['model_name'] == model_name]
        else:
            results = self.results
        
        # Handle case where there are no results
        if not results:
            return {
                'total_questions': 0,
                'correct_answers': 0,
                'accuracy': 0.0,
                'passed_70_percent': False,
                'extraction_failures': 0,
                'confusion_matrix': {},
                'error_analysis': {}
            }
        
        # Count metrics
        total = len(results)
        correct = sum(1 for r in results if r['is_correct'])
        extraction_failures = sum(1 for r in results if r['extraction_failed'])
        
        # Calculate accuracy
        accuracy = correct / total if total > 0 else 0.0
        passed_70 = accuracy >= 0.7
        
        # Build confusion matrix
        confusion = {}
        for r in results:
            actual = r['correct_answer']
            predicted = r['predicted_answer'] or 'None'
            
            if actual not in confusion:
                confusion[actual] = {}
            if predicted not in confusion[actual]:
                confusion[actual][predicted] = 0
            confusion[actual][predicted] += 1
        
        # Analyze errors
        errors = [r for r in results if not r['is_correct']]
        error_analysis = {
            'total_errors': len(errors),
            'extraction_failures': extraction_failures,
            'wrong_answers': len(errors) - extraction_failures
        }
        
        return {
            'total_questions': total,
            'correct_answers': correct,
            'accuracy': accuracy,
            'passed_70_percent': passed_70,
            'extraction_failures': extraction_failures,
            'confusion_matrix': confusion,
            'error_analysis': error_analysis
        }
    
    def generate_report(self, model_names: Optional[List[str]] = None) -> str:
        """
        Generate a comprehensive evaluation report.
        
        Args:
            model_names: List of model names to include in report
            
        Returns:
            Formatted report string
        """
        if not model_names:
            model_names = list(set(r['model_name'] for r in self.results))
        
        report_lines = [
            "=" * 60,
            "CPC PRACTICE TEST BENCHMARK REPORT",
            "=" * 60,
            f"Total Questions: {len(set(r['question_id'] for r in self.results))}",
            f"Models Evaluated: {len(model_names)}",
            "",
            "SUMMARY BY MODEL",
            "-" * 40
        ]
        
        # Summary for each model
        for model in model_names:
            metrics = self.calculate_metrics(model)
            
            report_lines.extend([
                f"\n{model}:",
                f"  Accuracy: {metrics['accuracy']:.2%} ({metrics['correct_answers']}/{metrics['total_questions']})",
                f"  Pass 70%: {'Yes' if metrics['passed_70_percent'] else 'No'}",
                f"  Extraction Failures: {metrics['extraction_failures']}"
            ])
        
        # Overall comparison
        report_lines.extend([
            "",
            "PERFORMANCE RANKING",
            "-" * 40
        ])
        
        # Rank models by accuracy
        model_accuracies = []
        for model in model_names:
            metrics = self.calculate_metrics(model)
            model_accuracies.append((model, metrics['accuracy'], metrics['correct_answers']))
        
        model_accuracies.sort(key=lambda x: x[1], reverse=True)
        
        for i, (model, accuracy, correct) in enumerate(model_accuracies, 1):
            report_lines.append(f"{i}. {model}: {accuracy:.2%} ({correct} correct)")
        
        # Error analysis
        report_lines.extend([
            "",
            "ERROR ANALYSIS",
            "-" * 40
        ])
        
        # Common wrong answers
        wrong_answers = [r for r in self.results if not r['is_correct'] and not r['extraction_failed']]
        if wrong_answers:
            report_lines.append(f"Total Wrong Answers: {len(wrong_answers)}")
            
            # Group errors by correct answer
            error_patterns = defaultdict(list)
            for r in wrong_answers:
                key = f"{r['correct_answer']} → {r['predicted_answer']}"
                error_patterns[key].append(r['question_id'])
            
            report_lines.append("\nMost Common Error Patterns:")
            for pattern, questions in sorted(error_patterns.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
                report_lines.append(f"  {pattern}: {len(questions)} times (questions: {', '.join(map(str, questions[:3]))}{'...' if len(questions) > 3 else ''})")
        
        return "\n".join(report_lines)
    
    def reset(self):
        """Reset the evaluator state."""
        self.results = []
        self.confusion_matrix = defaultdict(lambda: defaultdict(int)) 