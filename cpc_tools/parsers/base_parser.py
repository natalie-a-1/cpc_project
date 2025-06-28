"""
Base parser for medical coding data
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pathlib import Path
import pandas as pd

class BaseParser(ABC):
    """Base class for medical coding data parsers"""
    
    def __init__(self, data_path: str):
        self.data_path = Path(data_path)
        self.parsed_data: List[Dict[str, Any]] = []
        
    @abstractmethod
    def parse(self) -> List[Dict[str, Any]]:
        """Parse the medical coding data"""
        pass
    
    def clean_text(self, text: str) -> str:
        """Clean text data"""
        if not text or pd.isna(text):
            return ""
        text = str(text).strip()
        text = " ".join(text.split())
        return text
    
    def create_code_entry(self, code: str, description: str, code_type: str) -> Dict[str, Any]:
        """Create a standardized code entry"""
        return {
            'code': code.strip().upper(),
            'description': self.clean_text(description),
            'code_type': code_type,
            'text_for_embedding': f"{code} {description}"
        }
    
    def validate_code(self, code: str) -> bool:
        """
        Validate that a code meets basic requirements
        
        Args:
            code: Medical code to validate
            
        Returns:
            True if code is valid, False otherwise
        """
        if not code or pd.isna(code):
            return False
        
        code = str(code).strip()
        return len(code) > 0 and not code.isspace()
    
    def save_to_json(self, output_path: str) -> None:
        """
        Save parsed data to JSON file
        
        Args:
            output_path: Path to save JSON file
        """
        import json
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.parsed_data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Saved {len(self.parsed_data)} entries to {output_path}")
    
    def get_data_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of parsed data
        
        Returns:
            Dictionary with summary statistics
        """
        if not self.parsed_data:
            return {"total_codes": 0}
        
        code_types = {}
        for entry in self.parsed_data:
            code_type = entry.get('code_type', 'unknown')
            code_types[code_type] = code_types.get(code_type, 0) + 1
        
        return {
            "total_codes": len(self.parsed_data),
            "code_types": code_types,
            "sample_entry": self.parsed_data[0] if self.parsed_data else None
        } 