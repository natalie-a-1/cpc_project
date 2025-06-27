#!/usr/bin/env python
"""
Parse all CPC practice test PDFs in the data/raw directory.

This script finds all PDF files in data/raw and parses them into JSONL format
in data/processed, maintaining the same filename with .jsonl extension.
"""

import os
from pathlib import Path
import sys
from cpc_parser import parse_cpc_test


def main():
    """Parse all PDFs in data/raw directory."""
    # Set up paths
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    
    # Ensure directories exist
    if not raw_dir.exists():
        print(f"Error: {raw_dir} does not exist")
        sys.exit(1)
    
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all PDF files
    pdf_files = list(raw_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {raw_dir}")
        sys.exit(1)
    
    print(f"Found {len(pdf_files)} PDF file(s) to process")
    
    # Process each PDF
    for pdf_path in pdf_files:
        output_path = processed_dir / f"{pdf_path.stem}.jsonl"
        print(f"\nProcessing {pdf_path.name}...")
        
        try:
            dataset = parse_cpc_test(str(pdf_path), str(output_path))
            print(f"✓ Successfully parsed {len(dataset.questions)} questions")
            
            # Show statistics
            stats = dataset.get_statistics()
            print(f"  - Answer distribution: {stats['answer_distribution']}")
            print(f"  - Questions with explanations: {stats['questions_with_explanations']}")
            
        except Exception as e:
            print(f"✗ Error processing {pdf_path.name}: {e}")
            continue
    
    print("\nParsing complete!")


if __name__ == "__main__":
    main() 