"""
CPC benchmark package for evaluating language models on medical coding questions.

This package provides tools to benchmark various LLMs (GPT-4o, Claude 3.5, Gemini 1.5)
on CPC practice test questions to evaluate their performance on medical coding tasks.
"""

from .models import ModelProvider, OpenAIProvider, AnthropicProvider, GoogleProvider
from .benchmark import Benchmark, BenchmarkResult
from .evaluator import Evaluator
from .runner import run_benchmarks

__all__ = [
    'ModelProvider',
    'OpenAIProvider', 
    'AnthropicProvider',
    'GoogleProvider',
    'Benchmark',
    'BenchmarkResult',
    'Evaluator',
    'run_benchmarks'
]

__version__ = '0.1.0'
