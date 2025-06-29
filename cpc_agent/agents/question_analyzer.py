"""
Question Analyzer Agent
Analyzes CPC exam questions to determine type and routing
"""
from agents import Agent
from ..models import QuestionAnalysis

def create_question_analyzer() -> Agent:
    """Create agent that analyzes questions and routes to appropriate specialist"""
    return Agent(
        name="Question Analyzer",
        instructions="""Analyze CPC exam questions to determine their type and key information.

Classification rules:
- CPT: Questions asking "Which CPT code" or about procedures/services
- HCPCS: Questions about equipment, supplies, drugs (look for HCPCS, DME, wheelchair, CPAP, etc.)
- ICD-10: Questions about diagnosis codes or conditions
- ANATOMY: Questions about body parts, organs, or anatomical structures
- TERMINOLOGY: Questions about medical terms, prefixes, suffixes
- GUIDELINES: Questions about coding rules, sequencing, modifiers
- COMPLIANCE: Questions about Medicare, fraud, HIPAA, NCCI

Extract key medical terms and determine if web search is needed.""",
        output_type=QuestionAnalysis
    ) 