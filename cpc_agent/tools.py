"""
Function Tools for CPC Agent System
Contains function tools for accessing local medical coding APIs
"""
import sys
from pathlib import Path
from typing import Dict, Any
from agents import function_tool

# Add parent directory to path for API imports
sys.path.append(str(Path(__file__).parent.parent))
from apis.hcpcs_api import HCPCSApi
from apis.icd10cm_api import ICD10CMApi
from apis.procedures_api import ProceduresApi
from apis.conditions_api import ConditionsApi

# Initialize API instances
hcpcs_api = HCPCSApi()
icd10cm_api = ICD10CMApi()
procedures_api = ProceduresApi()
conditions_api = ConditionsApi()

@function_tool
def search_hcpcs_local(terms: str) -> Dict[str, Any]:
    """Search local HCPCS Level II database for medical equipment and supplies"""
    try:
        result = hcpcs_api.search_codes(terms, max_results=5)
        return {"source": "Local HCPCS DB", "results": result.get("results", [])[:3]}
    except Exception as e:
        return {"error": str(e)}

@function_tool
def search_icd10_local(terms: str) -> Dict[str, Any]:
    """Search local ICD-10-CM database for diagnosis codes"""
    try:
        result = icd10cm_api.search_codes(terms, max_results=5)
        return {"source": "Local ICD-10 DB", "results": result.get("results", [])[:3]}
    except Exception as e:
        return {"error": str(e)}

@function_tool
def search_procedures_local(terms: str) -> Dict[str, Any]:
    """Search local procedures database"""
    try:
        result = procedures_api.search_procedures(terms, max_results=5)
        return {"source": "Local Procedures DB", "results": result.get("results", [])[:3]}
    except Exception as e:
        return {"error": str(e)}

@function_tool
def search_conditions_local(terms: str) -> Dict[str, Any]:
    """Search local conditions database"""
    try:
        result = conditions_api.search_conditions(terms, max_results=5)
        return {"source": "Local Conditions DB", "results": result.get("results", [])[:3]}
    except Exception as e:
        return {"error": str(e)} 