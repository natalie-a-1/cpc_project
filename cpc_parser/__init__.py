"""
Add commentMore actions
CPC parser package for extracting questions from PDF files.

This package provides tools to parse CPC practice test PDFs and extract
structured question data including stems, options, answers, and explanations.
"""

from .schema import Question, QuestionDataset
from .parse_pdf import CPCTestParser, parse_cpc_test

__all__ = [
    'Question',
    'QuestionDataset', 
    'CPCTestParser',
    'parse_cpc_test'
]

__version__ = '0.1.0'