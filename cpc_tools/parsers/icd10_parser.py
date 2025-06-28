"""
ICD-10 Parser - Enhanced for CPC test accuracy
"""
import re
import pandas as pd
from typing import List, Dict, Any
from pathlib import Path
from .base_parser import BaseParser

class ICD10Parser(BaseParser):
    """Parser for ICD-10-CM codes"""
    
    def parse(self) -> List[Dict[str, Any]]:
        """Parse ICD-10-CM codes from data files"""
        print(f"Parsing ICD-10 data from {self.data_path}")
        
        # Parse text files with actual code descriptions
        self._parse_icd10_code_files()
        
        # Parse Excel conversion tables for additional codes
        xlsx_files = list(self.data_path.rglob("*.xlsx"))
        for xlsx_file in xlsx_files:
            if "conversion" in xlsx_file.name.lower():
                self._parse_conversion_table(xlsx_file)
        
        # Remove duplicates
        self._remove_duplicates()
        
        print(f"Parsed {len(self.parsed_data)} ICD-10 codes")
        return self.parsed_data
    
    def _parse_icd10_code_files(self):
        """Parse ICD-10 codes from text files"""
        # Look for code description files
        code_files = list(self.data_path.rglob("icd10cm-codes-2025.txt"))
        code_files.extend(list(self.data_path.rglob("icd10cm-codes-*.txt")))
        
        for file_path in code_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # Parse format: CODE DESCRIPTION
                        # ICD-10 codes are 3-7 characters: letter + 2 digits + optional decimal and more
                        match = re.match(r'^([A-Z]\d{2}(?:\.\w{0,4})?)\s+(.+)$', line)
                        if match:
                            code = match.group(1).strip()
                            description = match.group(2).strip()
                            
                            # Create comprehensive embedding text
                            text_for_embedding = f"ICD-10-CM {code} {description}"
                            
                            entry = {
                                'code': code,
                                'description': description,
                                'code_type': 'ICD-10-CM',
                                'text_for_embedding': text_for_embedding
                            }
                            self.parsed_data.append(entry)
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")
    
    def _parse_conversion_table(self, file_path: Path):
        """Parse ICD-10 codes from conversion table Excel file"""
        try:
            df = pd.read_excel(file_path)
            
            # Look for ICD-10 code and description columns
            for i, col in enumerate(df.columns):
                col_str = str(col).lower()
                if 'icd' in col_str and '10' in col_str:
                    # Check if there's a description column nearby
                    desc_col = None
                    if i + 1 < len(df.columns):
                        next_col = str(df.columns[i + 1]).lower()
                        if 'desc' in next_col or 'diagnosis' in next_col:
                            desc_col = df.columns[i + 1]
                    
                    for _, row in df.iterrows():
                        code = str(row[col]).strip().upper()
                        if re.match(r'^[A-Z]\d{2}(?:\.\w{0,4})?$', code):
                            if desc_col and pd.notna(row[desc_col]):
                                description = str(row[desc_col]).strip()
                            else:
                                # Skip if we already have this code
                                if any(item['code'] == code for item in self.parsed_data):
                                    continue
                                description = f"ICD-10-CM diagnosis code"
                            
                            text_for_embedding = f"ICD-10-CM {code} {description}"
                            
                            entry = {
                                'code': code,
                                'description': description,
                                'code_type': 'ICD-10-CM',
                                'text_for_embedding': text_for_embedding
                            }
                            self.parsed_data.append(entry)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    
    def _remove_duplicates(self):
        """Remove duplicate codes, keeping the one with the best description"""
        unique_codes = {}
        for entry in self.parsed_data:
            code = entry['code']
            if code not in unique_codes or len(entry['description']) > len(unique_codes[code]['description']):
                unique_codes[code] = entry
        
        self.parsed_data = list(unique_codes.values()) 