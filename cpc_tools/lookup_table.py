"""
Simple lookup table builder
"""
import json
from typing import List, Dict, Any
from pathlib import Path

class LookupTableBuilder:
    """Simple lookup table builder"""
    
    def build_lookup_table(self, code_data: List[Dict[str, Any]], output_dir: Path):
        """Build simple lookup table"""
        print("Building lookup table...")
        
        lookup_table = {}
        for item in code_data:
            code = item['code']
            lookup_table[code] = {
                'code': code,
                'description': item['description'],
                'code_type': item['code_type']
            }
        
        # Save lookup table
        lookup_path = output_dir / "lookup_table.json"
        with open(lookup_path, 'w') as f:
            json.dump(lookup_table, f, indent=2)
        
        print(f"Saved lookup table with {len(lookup_table)} codes to {lookup_path}")
        return lookup_table 