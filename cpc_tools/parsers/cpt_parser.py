"""
CPT Parser - Enhanced for CPC test accuracy
"""
import re
import pandas as pd
from typing import List, Dict, Any
from pathlib import Path
from .base_parser import BaseParser

class CPTParser(BaseParser):
    """Parser for CPT codes"""
    
    def parse(self) -> List[Dict[str, Any]]:
        """Parse CPT codes from data files"""
        print(f"Parsing CPT data from {self.data_path}")
        
        # Parse text files
        txt_files = list(self.data_path.rglob("*.txt"))
        for txt_file in txt_files:
            self._parse_txt_file(txt_file)
        
        # Parse Excel files
        xlsx_files = list(self.data_path.rglob("*.xlsx"))
        for xlsx_file in xlsx_files:
            self._parse_xlsx_file(xlsx_file)
        
        # Remove duplicates
        self._remove_duplicates()
        
        print(f"Parsed {len(self.parsed_data)} CPT codes")
        return self.parsed_data
    
    def _parse_txt_file(self, file_path: Path):
        """Parse CPT codes from text file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                current_section = ""
                
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Track section headers (e.g., CLINICAL LABORATORY SERVICES)
                    if line.isupper() and len(line) > 10 and not re.match(r'^\d', line):
                        if "SERVICE" in line or "PROCEDURE" in line or "THERAPY" in line:
                            current_section = line
                        continue
                    
                    # Skip headers and notes
                    if line.startswith('"') or line.startswith('INCLUDE') or line.startswith('EXCLUDE'):
                        continue
                    
                    # Parse CPT codes - multiple patterns
                    # Pattern 1: 5 digits followed by description
                    match = re.match(r'^(\d{5})\s+(.+)$', line)
                    if match:
                        code = match.group(1)
                        description = match.group(2).strip()
                        
                        # Clean description
                        description = re.sub(r'\s+', ' ', description)
                        
                        # Create comprehensive embedding text
                        if current_section:
                            text_for_embedding = f"CPT {code} {current_section} {description}"
                        else:
                            text_for_embedding = f"CPT {code} {description}"
                        
                        entry = {
                            'code': code,
                            'description': description,
                            'code_type': 'CPT',
                            'text_for_embedding': text_for_embedding,
                            'section': current_section
                        }
                        self.parsed_data.append(entry)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    
    def _parse_xlsx_file(self, file_path: Path):
        """Parse CPT codes from Excel file"""
        try:
            df = pd.read_excel(file_path)
            
            # Try to identify code and description columns
            code_col = None
            desc_col = None
            
            for col in df.columns:
                col_lower = str(col).lower()
                if 'code' in col_lower or 'cpt' in col_lower:
                    code_col = col
                elif 'description' in col_lower or 'desc' in col_lower or 'procedure' in col_lower:
                    desc_col = col
            
            # Fallback to positional
            if not code_col and len(df.columns) >= 1:
                # First column that contains 5-digit numbers
                for col in df.columns:
                    sample = df[col].dropna().head(10)
                    if any(str(val).strip().isdigit() and len(str(val).strip()) == 5 for val in sample):
                        code_col = col
                        break
            
            if not desc_col and code_col and len(df.columns) > df.columns.get_loc(code_col) + 1:
                desc_col = df.columns[df.columns.get_loc(code_col) + 1]
            
            if code_col and desc_col:
                for _, row in df.iterrows():
                    code = str(row[code_col]).strip()
                    description = str(row[desc_col]).strip()
                    
                    # Validate CPT code format (5 digits)
                    if re.match(r'^\d{5}$', code) and description and description != 'nan':
                        text_for_embedding = f"CPT {code} {description}"
                        
                        entry = {
                            'code': code,
                            'description': description,
                            'code_type': 'CPT',
                            'text_for_embedding': text_for_embedding
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
    
    def get_cpt_by_range(self, start_code: str, end_code: str) -> List[Dict[str, Any]]:
        """
        Get CPT codes within a specific range
        
        Args:
            start_code: Starting CPT code (inclusive)
            end_code: Ending CPT code (inclusive)
            
        Returns:
            List of CPT codes within the range
        """
        start_num = int(start_code)
        end_num = int(end_code)
        
        return [
            entry for entry in self.parsed_data
            if entry['code_type'] == 'CPT' and 
            start_num <= int(entry['code']) <= end_num
        ]
    
    def get_cpt_summary(self) -> Dict[str, Any]:
        """
        Get summary of CPT codes by sections/categories
        
        Returns:
            Summary dictionary
        """
        summary = self.get_data_summary()
        
        # Add CPT-specific analysis
        sections = {}
        for entry in self.parsed_data:
            if entry['code_type'] == 'CPT':
                section = entry.get('section', 'Unknown')
                sections[section] = sections.get(section, 0) + 1
        
        summary['sections'] = sections
        
        # Add code range analysis
        codes = [int(entry['code']) for entry in self.parsed_data if entry['code_type'] == 'CPT']
        if codes:
            summary['code_range'] = {
                'min': min(codes),
                'max': max(codes),
                'total_unique': len(set(codes))
            }
        
        return summary 