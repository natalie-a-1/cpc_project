#!/usr/bin/env python3
"""
Simple medical data processor
Parses medical codes and builds FAISS vector database + lookup table
"""
import sys
import json
from pathlib import Path

# Poetry package imports
from cpc_tools.parsers import ICD10Parser, CPTParser, HCPCSParser
from cpc_tools.vectorizer.medical_vectorizer import MedicalVectorizer
from cpc_tools.lookup_table import LookupTableBuilder

# Configuration
RAW_DATA_DIR = Path("data/raw/unstructured")
OUTPUT_DIR = Path("data/processed")

# Source paths
ICD10_DATA_PATH = RAW_DATA_DIR / "ICD-10-CM-2024"
CPT_DATA_PATH = RAW_DATA_DIR / "CPT"
HCPCS_DATA_PATH = RAW_DATA_DIR / "HCPCS"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def parse_all_data():
    """Parse all medical coding data"""
    print("=== PARSING MEDICAL DATA ===")
    
    all_codes = []
    
    # Parse ICD-10
    try:
        icd10_parser = ICD10Parser(ICD10_DATA_PATH)
        icd10_codes = icd10_parser.parse()
        all_codes.extend(icd10_codes)
    except Exception as e:
        print(f"Error parsing ICD-10: {e}")
    
    # Parse CPT
    try:
        cpt_parser = CPTParser(CPT_DATA_PATH)
        cpt_codes = cpt_parser.parse()
        all_codes.extend(cpt_codes)
    except Exception as e:
        print(f"Error parsing CPT: {e}")
    
    # Parse HCPCS
    try:
        hcpcs_parser = HCPCSParser(HCPCS_DATA_PATH)
        hcpcs_codes = hcpcs_parser.parse()
        all_codes.extend(hcpcs_codes)
    except Exception as e:
        print(f"Error parsing HCPCS: {e}")
    
    print(f"Total codes parsed: {len(all_codes)}")
    return all_codes

def save_parsed_data(codes, output_dir):
    """Save parsed data to JSON"""
    output_path = output_dir / "parsed_codes.json"
    with open(output_path, 'w') as f:
        json.dump(codes, f, indent=2)
    print(f"Saved parsed data to {output_path}")

def main():
    """Main processing function"""
    if len(sys.argv) != 2:
        print("Usage: python process_medical_data.py <OPENAI_API_KEY>")
        sys.exit(1)
    
    api_key = sys.argv[1]
    
    try:
        # Parse data
        all_codes = parse_all_data()
        
        if not all_codes:
            print("No codes parsed. Check data paths.")
            return
        
        # Save parsed data
        save_parsed_data(all_codes, OUTPUT_DIR)
        
        print("\n=== BUILDING VECTOR DATABASE ===")
        # Build FAISS vector database
        vectorizer = MedicalVectorizer(api_key)
        vectorizer.build_vector_database(all_codes, OUTPUT_DIR)
        
        print("\n=== BUILDING LOOKUP TABLE ===")
        # Build lookup table
        lookup_builder = LookupTableBuilder()
        lookup_builder.build_lookup_table(all_codes, OUTPUT_DIR)
        
        print(f"\n=== PROCESSING COMPLETE ===")
        print(f"Total codes processed: {len(all_codes)}")
        print(f"Output directory: {OUTPUT_DIR}")
        print("Files created:")
        print("  - parsed_codes.json")
        print("  - medical_codes.faiss")
        print("  - metadata.json") 
        print("  - lookup_table.json")
        
    except Exception as e:
        print(f"Processing failed: {e}")

if __name__ == "__main__":
    main() 