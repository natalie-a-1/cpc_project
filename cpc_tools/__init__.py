"""
CPC Tools - Medical Data Processing
Simple data processor for medical coding data that creates:
1. FAISS vector database for similarity search  
2. JSON lookup table for exact matches
"""

__version__ = "0.1.0"

# Main components
from .lookup_table import LookupTableBuilder
from .parsers import ICD10Parser, CPTParser, HCPCSParser
from .vectorizer import MedicalVectorizer, EmbeddingGenerator
from .medical_terminology import MedicalTerminology

__all__ = [
    "LookupTableBuilder",
    "ICD10Parser", 
    "CPTParser",
    "HCPCSParser", 
    "MedicalVectorizer",
    "EmbeddingGenerator",
    "MedicalTerminology"
] 