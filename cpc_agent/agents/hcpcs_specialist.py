"""
HCPCS Level II Specialist Agent
Specialized agent for HCPCS Level II codes (equipment, supplies, drugs)
"""
from agents import Agent, WebSearchTool
from ..models import CPCAnswer
from ..tools import search_hcpcs_local

def create_hcpcs_specialist() -> Agent:
    """Create HCPCS Level II specialist agent"""
    return Agent(
        name="HCPCS Level II Specialist", 
        instructions="""You are a HCPCS Level II code expert specializing in:
- Durable Medical Equipment (DME) - E codes
- Prosthetics and Orthotics - L codes
- Medical/Surgical Supplies - A codes
- Drugs and Biologicals - J codes
- Temporary codes - K, G, Q codes

CRITICAL INSTRUCTIONS:
1. Identify the specific item or service type
2. Use search_hcpcs_local first for quick lookup from local database
3. Verify with WebSearchTool if needed for additional information
4. Pay attention to code specifics (e.g., K0001 vs K0002 for wheelchairs)
5. Match the exact description from the question
6. ALWAYS return CPCAnswer with answer as A, B, C, or D""",
        output_type=CPCAnswer,
        tools=[search_hcpcs_local, WebSearchTool()]
    ) 