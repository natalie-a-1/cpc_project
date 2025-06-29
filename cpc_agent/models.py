"""
Pydantic Models for CPC Agent System
Contains structured output models for agents
"""
from typing import List, Literal
from pydantic import BaseModel, Field

class CPCAnswer(BaseModel):
    """Structured output for CPC exam answers"""
    answer: Literal["A", "B", "C", "D"] = Field(
        description="The correct answer letter (A, B, C, or D) based on analysis"
    )
    confidence: float = Field(
        description="Confidence level from 0.0 to 1.0",
        ge=0.0,
        le=1.0
    )
    reasoning: str = Field(
        description="Brief explanation of why this answer was chosen"
    )
    code_found: str = Field(
        default="",
        description="The specific code found if applicable (e.g., '70551' for MRI brain)"
    )

class QuestionAnalysis(BaseModel):
    """Analysis of the CPC question type"""
    question_type: Literal["CPT", "HCPCS", "ICD-10", "ANATOMY", "TERMINOLOGY", "GUIDELINES", "COMPLIANCE"] = Field(
        description="Type of medical coding question"
    )
    key_terms: List[str] = Field(
        description="Key medical terms or procedures mentioned"
    )
    requires_web_search: bool = Field(
        description="Whether this question needs web search for accurate answer"
    ) 