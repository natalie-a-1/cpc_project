# CPC Parser

A Python package for extracting structured question data from CPC (Certified Professional Coder) practice test PDF files.

## Features

- **PDF Parsing**: Extract questions, answer choices, and explanations from CPC test PDFs
- **Data Validation**: Pydantic models ensure data integrity and consistency  
- **Structured Output**: Export to JSON/JSONL format for analysis and ML applications
- **Comprehensive Coverage**: Handles questions, answer keys, and detailed explanations

## Installation

This package is part of the CPC project. Install dependencies using Poetry:

```bash
poetry install
```

## Quick Start

### Basic Usage

```python
from cpc_parser import parse_cpc_test

# Parse PDF and save to JSONL
dataset = parse_cpc_test("cpc_test.pdf", "output.jsonl")

# Access parsed questions
for question in dataset.questions:
    print(f"Q{question.id}: {question.stem}")
    print(f"Answer: {question.correct_answer_letter}")
```

### Advanced Usage

```python
from cpc_parser import CPCTestParser

# Initialize parser with detailed control
parser = CPCTestParser("cpc_test.pdf")
dataset = parser.parse()

# Get statistics
stats = dataset.get_statistics()
print(f"Total questions: {stats['total_questions']}")

# Export to JSONL
dataset.to_jsonl("questions.jsonl")
```

## Data Structure

Each question contains:
- **ID**: Question number (1-100)
- **Stem**: Question text
- **Options**: Four answer choices (A-D)
- **Correct Answer**: Letter and corresponding text
- **Explanation**: Detailed explanation

## Processing Flow

1. **Parse Questions** → Extract from pages 4-35
2. **Parse Answer Key** → Extract correct answers
3. **Parse Explanations** → Extract detailed explanations
4. **Validate Data** → Pydantic model validation
5. **Export** → JSONL format for downstream use

## Dependencies

- `pdfplumber`: PDF text extraction
- `pydantic`: Data validation and serialization
- Python 3.10+

## Package Structure

```
cpc_parser/
├── __init__.py          # Package exports
├── schema.py            # Pydantic models
└── parse_pdf.py         # Main parsing logic
```