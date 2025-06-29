"""
Medical Knowledge Expert Agent
Specialized agent for anatomy, terminology, and healthcare regulations
"""
from agents import Agent, WebSearchTool
from ..models import CPCAnswer

def create_medical_knowledge_agent() -> Agent:
    """Create agent for anatomy, terminology, and general medical knowledge"""
    return Agent(
        name="Medical Knowledge Expert",
        instructions="""You are an expert in medical terminology, anatomy, and healthcare regulations.

Areas of expertise:
- Medical terminology (prefixes, suffixes, root words)
- Human anatomy and physiology
- Healthcare regulations (HIPAA, Medicare rules)
- Coding guidelines and compliance
- Medical abbreviations and their meanings

CRITICAL INSTRUCTIONS:
1. For anatomy questions, focus on the specific body system
2. For terminology, break down the word components
3. For regulations, cite specific rules or acts
4. Use WebSearchTool to verify current information
5. ALWAYS return CPCAnswer with answer as A, B, C, or D""",
        output_type=CPCAnswer,
        tools=[WebSearchTool()]
    ) 