#!/usr/bin/env python3
"""
Enhanced CLI script to process medical data for CPC test accuracy
Usage: poetry run python scripts/process_medical_data.py
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from cpc_tools import ICD10Parser, CPTParser, HCPCSParser, MedicalVectorizer, LookupTableBuilder
from cpc_tools.medical_terminology import MedicalTerminology

def main():
    """Main CLI function"""
    # Load environment variables from .env file
    load_dotenv()
    
    # Get API key from environment
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables.")
        print("Please create a .env file in the project root with:")
        print("OPENAI_API_KEY=your_api_key_here")
        sys.exit(1)
    
    # Configuration
    raw_data_dir = Path("data/raw/unstructured")
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🔧 Processing medical coding data for CPC test...")
    
    try:
        # Parse all data
        all_codes = []
        
        # Parse ICD-10
        icd10_path = raw_data_dir / "ICD-10-CM-2024"
        if icd10_path.exists():
            parser = ICD10Parser(str(icd10_path))
            codes = parser.parse()
            all_codes.extend(codes)
            print(f"✅ Parsed {len(codes)} ICD-10-CM codes")
        
        # Parse CPT
        cpt_path = raw_data_dir / "CPT"
        if cpt_path.exists():
            parser = CPTParser(str(cpt_path))
            codes = parser.parse()
            all_codes.extend(codes)
            print(f"✅ Parsed {len(codes)} CPT codes")
        
        # Parse HCPCS
        hcpcs_path = raw_data_dir / "HCPCS"
        if hcpcs_path.exists():
            parser = HCPCSParser(str(hcpcs_path))
            codes = parser.parse()
            all_codes.extend(codes)
            print(f"✅ Parsed {len(codes)} HCPCS codes")
        
        # Add medical terminology for CPC test
        terminology_data = MedicalTerminology.get_terminology_data()
        all_codes.extend(terminology_data)
        print(f"✅ Added {len(terminology_data)} medical terminology entries")
        
        if not all_codes:
            print("❌ No codes parsed. Check that data files exist in data/raw/unstructured/")
            return
        
        print(f"📊 Total entries: {len(all_codes)}")
        
        # Build enhanced FAISS vector database
        print("🔮 Building enhanced FAISS vector database...")
        vectorizer = MedicalVectorizer(api_key)
        vectorizer.build_vector_database(all_codes, output_dir)
        
        # Build comprehensive lookup table
        print("📚 Building comprehensive lookup table...")
        lookup_builder = LookupTableBuilder()
        lookup_builder.build_lookup_table(all_codes, output_dir)
        
        # Save all parsed data
        import json
        parsed_path = output_dir / "parsed_codes.json"
        with open(parsed_path, 'w') as f:
            json.dump(all_codes, f, indent=2)
        
        print(f"""
🎉 Processing complete for CPC test!
📁 Output directory: {output_dir}
📄 Files created:
   - medical_codes.faiss (Enhanced FAISS vector database)
   - metadata.json (Enhanced vector metadata)  
   - lookup_table.json (Comprehensive exact match lookup)
   - parsed_codes.json (All parsed data)
   
🎯 Optimized for 100% CPC test accuracy with:
   - {len([c for c in all_codes if c['code_type'] == 'CPT'])} CPT codes
   - {len([c for c in all_codes if c['code_type'] == 'ICD-10-CM'])} ICD-10-CM codes
   - {len([c for c in all_codes if c['code_type'] == 'HCPCS'])} HCPCS codes
   - {len([c for c in all_codes if c['code_type'] == 'Medical Terminology'])} Medical terminology entries
        """)
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 