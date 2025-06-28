"""
HCPCS Parser - Enhanced for CPC test accuracy
"""
import re
import pandas as pd
from typing import List, Dict, Any
from pathlib import Path
from .base_parser import BaseParser

class HCPCSParser(BaseParser):
    """Parser for HCPCS codes"""
    
    def parse(self) -> List[Dict[str, Any]]:
        """Parse HCPCS codes from data files"""
        print(f"Parsing HCPCS data from {self.data_path}")
        
        # Parse main HCPCS fixed-width file
        txt_files = list(self.data_path.rglob("HCPC*ANWEB*.txt"))
        for txt_file in txt_files:
            if "proc_notes" not in txt_file.name.lower():
                self._parse_fixed_width_file(txt_file)
        
        # Parse Excel files for additional codes
        xlsx_files = list(self.data_path.rglob("*.xlsx"))
        for xlsx_file in xlsx_files:
            if "HCPC" in xlsx_file.name and "NOC" not in xlsx_file.name and "Changes" not in xlsx_file.name:
                self._parse_xlsx_file(xlsx_file)
        
        # Remove duplicates
        self._remove_duplicates()
        
        print(f"Parsed {len(self.parsed_data)} HCPCS codes")
        return self.parsed_data
    
    def _parse_fixed_width_file(self, file_path: Path):
        """Parse HCPCS fixed-width file based on record layout"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if len(line) < 119:
                        continue
                    
                    # Based on HCPCS record layout:
                    # Positions 1-5: HCPCS Code
                    # Position 11: Record ID Code (3=first line procedure, 7=first line modifier)
                    # Positions 12-91: Long Description
                    # Positions 92-119: Short Description
                    
                    code = line[0:5].strip()
                    rec_id = line[10:11].strip()
                    long_desc = line[11:91].strip()
                    short_desc = line[91:119].strip() if len(line) >= 119 else ""
                    
                    # Only process procedure records (rec_id = '3')
                    if rec_id == '3' and code:
                        # Validate HCPCS code format
                        if re.match(r'^([A-Z]\d{4}|\d{5})$', code):
                            # Use long description, fall back to short if needed
                            description = long_desc if long_desc else short_desc
                            
                            if description:
                                # Determine HCPCS level
                                if code[0].isalpha():
                                    level = "HCPCS Level II"
                                else:
                                    level = "CPT"
                                
                                # Create comprehensive embedding text
                                text_for_embedding = f"{level} {code} {description}"
                                
                                entry = {
                                    'code': code,
                                    'description': description,
                                    'code_type': 'HCPCS',
                                    'text_for_embedding': text_for_embedding,
                                    'level': level,
                                    'short_description': short_desc
                                }
                                self.parsed_data.append(entry)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    
    def _parse_xlsx_file(self, file_path: Path):
        """Parse HCPCS Excel file"""
        try:
            df = pd.read_excel(file_path)
            
            # Identify HCPCS code and description columns
            code_col = None
            desc_col = None
            short_desc_col = None
            
            for col in df.columns:
                col_lower = str(col).lower()
                if 'hcpc' in col_lower and 'code' in col_lower:
                    code_col = col
                elif 'long' in col_lower and 'desc' in col_lower:
                    desc_col = col
                elif 'short' in col_lower and 'desc' in col_lower:
                    short_desc_col = col
                elif not desc_col and 'description' in col_lower:
                    desc_col = col
            
            # Fallback to positional
            if not code_col and len(df.columns) >= 1:
                code_col = df.columns[0]
            if not desc_col and len(df.columns) >= 2:
                desc_col = df.columns[1]
            
            if code_col and desc_col:
                for _, row in df.iterrows():
                    code = str(row[code_col]).strip().upper()
                    description = str(row[desc_col]).strip()
                    short_desc = str(row[short_desc_col]).strip() if short_desc_col and pd.notna(row[short_desc_col]) else ""
                    
                    if re.match(r'^([A-Z]\d{4}|\d{5})$', code) and description and description != 'nan':
                        # Determine HCPCS level
                        if code[0].isalpha():
                            level = "HCPCS Level II"
                        else:
                            level = "CPT"
                        
                        text_for_embedding = f"{level} {code} {description}"
                        
                        entry = {
                            'code': code,
                            'description': description,
                            'code_type': 'HCPCS',
                            'text_for_embedding': text_for_embedding,
                            'level': level,
                            'short_description': short_desc
                        }
                        self.parsed_data.append(entry)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    
    def _remove_duplicates(self):
        """Remove duplicate codes, keeping the one with the longest description"""
        unique_codes = {}
        for entry in self.parsed_data:
            code = entry['code']
            if code not in unique_codes or len(entry['description']) > len(unique_codes[code]['description']):
                unique_codes[code] = entry
        
        self.parsed_data = list(unique_codes.values()) 