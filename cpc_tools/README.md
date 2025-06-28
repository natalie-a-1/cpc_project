# CPC Tools - Enhanced for CPC Test Accuracy

Enhanced medical data processor optimized for 100% accuracy on the 2023 CPC (Certified Professional Coder) test. Parses medical coding data and creates:

1. **Enhanced FAISS vector database** - Semantic search with context-aware embeddings
2. **Comprehensive JSON lookup table** - Fast exact code matching
3. **Medical terminology knowledge base** - Anatomy and medical terms for test questions

## 🎯 CPC Test Optimization

This package is specifically enhanced to handle all question types from the CPC test:

- **CPT Codes**: Complete procedure descriptions with section context
- **ICD-10-CM Codes**: Full diagnostic code descriptions with category information
- **HCPCS Codes**: Level I (CPT) and Level II codes with equipment/supply details
- **Medical Terminology**: Anatomy terms, medical prefixes/suffixes, and definitions
- **Coding Guidelines**: HIPAA, NCCI, modifiers, and Medicare rules

## Components

- `parsers/` - Enhanced data parsers for ICD-10, CPT, and HCPCS codes
  - Handles multiple file formats (text, Excel, fixed-width)
  - Extracts complete code descriptions
  - Preserves section and category information
- `vectorizer/` - Advanced OpenAI embeddings + FAISS vector database
  - Context-aware embeddings with medical domain enhancements
  - Optimized for CPC test question patterns
- `medical_terminology.py` - Medical terminology knowledge base
- `lookup_table.py` - Comprehensive JSON lookup table builder

## Setup

From project root:

```bash
# Install dependencies
poetry install

# Create .env file with your OpenAI API key
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

## Usage

```bash
# Process medical data for CPC test
poetry run python scripts/process_medical_data.py
```

## Data Sources Configuration

The package expects medical coding data in these locations:
- `data/raw/unstructured/ICD-10-CM-2024/` - ICD-10 diagnostic codes
- `data/raw/unstructured/CPT/` - CPT procedure codes
- `data/raw/unstructured/HCPCS/` - HCPCS supply/equipment codes

## Enhanced Features for CPC Test

1. **Context-Aware Embeddings**: Each code includes enhanced context for better semantic matching
2. **Medical Domain Knowledge**: Built-in understanding of medical terminology and anatomy
3. **Comprehensive Coverage**: Includes all code types and guidelines tested in CPC exam
4. **Optimized Retrieval**: FAISS IndexFlatIP for exact similarity search

## Output Files

- `medical_codes.faiss` - Enhanced FAISS vector database
- `metadata.json` - Rich metadata including sections and categories
- `lookup_table.json` - Complete code-to-description mappings
- `parsed_codes.json` - All parsed data for verification

## Technical Details

Based on [FAISS best practices](https://www.pingcap.com/article/mastering-faiss-vector-database-a-beginners-handbook/), this system uses:

- **FAISS IndexFlatIP**: Exact cosine similarity search with L2 normalized vectors
- **OpenAI text-embedding-3-large**: 1536-dimension embeddings for semantic accuracy
- **Enhanced Text Representations**: Multiple views of each code for better matching
- **Medical Domain Enhancements**: Procedure types, body systems, and equipment categories

## Validation

After processing, validate CPC test coverage:

```python
from tests.validate_data import validate_cpc_coverage
validate_cpc_coverage("data/processed/parsed_codes.json")
```

This will show coverage statistics for actual CPC test codes to ensure 100% accuracy. 