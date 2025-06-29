"""
ICD-10-CM Specialist Agent
Specialized agent for International Classification of Diseases diagnosis codes
"""
from agents import Agent, WebSearchTool
from ..models import CPCAnswer
from ..tools import search_icd10_local, search_conditions_local

def create_icd10_specialist() -> Agent:
    """Create ICD-10-CM diagnosis code specialist"""
    return Agent(
        name="ICD-10-CM Specialist",
        instructions="""You are an ICD-10-CM diagnosis coding expert.

Key principles:
- Code to the highest level of specificity
- Acute conditions before chronic when both present
- Consider laterality (right/left/bilateral)
- Watch for "with/without" distinctions

CRITICAL INSTRUCTIONS:
1. Use search_icd10_local for initial lookup from local database
2. Use search_conditions_local to understand the medical condition
3. Consider all aspects: etiology, anatomic site, severity, laterality
4. Match the exact condition described in the question
5. Verify with WebSearchTool if additional clarification needed
6. ALWAYS return CPCAnswer with answer as A, B, C, or D""",
        output_type=CPCAnswer,
        tools=[search_icd10_local, search_conditions_local, WebSearchTool()]
    ) 