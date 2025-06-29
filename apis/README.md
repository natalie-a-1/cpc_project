# Medical Coding APIs

A comprehensive collection of API wrappers for medical coding systems, providing access to standardized medical codes and classifications through the Clinical Tables NLM (National Library of Medicine) databases.

## Overview

This package provides Python interfaces to essential medical coding systems used in healthcare billing, documentation, and clinical workflows. All APIs are built on top of the Clinical Tables NLM web services and include robust error handling, classification, and validation features.

## Available APIs

### 🏥 ConditionsApi
**Medical Conditions and Diagnoses**

Provides access to over 2,400 medical conditions with comprehensive coding information.

- **Data Source**: [Clinical Tables NLM Conditions Database](https://clinicaltables.nlm.nih.gov/apidoc/conditions/v3/doc.html)
- **Coverage**: Medical conditions with ICD-10-CM codes, ICD-9-CM codes, and extensive synonyms
- **Key Features**: 
  - Search by condition name or keywords
  - Automatic categorization (Cardiovascular, Respiratory, Endocrine, etc.)
  - Synonym matching and consumer-friendly names
  - Direct condition lookup by key ID

### 🔬 ProceduresApi
**Medical Procedures and Surgeries**

Access to major surgical procedures and medical implants.

- **Data Source**: [Clinical Tables NLM Procedures Database](https://clinicaltables.nlm.nih.gov/apidoc/procedures/v3/doc.html)
- **Coverage**: ~280 major surgeries and implant procedures
- **Key Features**:
  - Search by procedure name or keywords
  - Procedure categorization (Cardiac, Orthopedic, Neurological, etc.)
  - ICD-9 procedure codes included
  - Comprehensive synonym support

### 📋 ICD10CMApi
**ICD-10-CM Diagnostic Codes**

International Classification of Diseases, 10th Revision, Clinical Modification codes.

- **Data Source**: [Clinical Tables NLM ICD-10-CM Database](https://clinicaltables.nlm.nih.gov/apidoc/icd10cm/v3/doc.html)
- **Coverage**: Complete ICD-10-CM diagnostic code set
- **Key Features**:
  - Search by code or description
  - Automatic categorization by code prefix
  - Code format validation
  - Category-based searching with smart prefix mapping

### 🏥 HCPCSApi  
**HCPCS Level II Codes**

Healthcare Common Procedure Coding System Level II codes for supplies and services.

- **Data Source**: [Clinical Tables NLM HCPCS Database](https://clinicaltables.nlm.nih.gov/apidoc/hcpcs/v3/doc.html)
- **Coverage**: Medical equipment, supplies, and non-physician services
- **Key Features**:
  - Search by code or equipment/supply description
  - Category classification (DME, Prosthetics, Drugs, etc.)
  - Temporal data (add/term dates, obsolete status)
  - NOC (Not Otherwise Classified) identification

## Quick Start

```python
from apis import ConditionsApi, ProceduresApi, ICD10CMApi, HCPCSApi

# Search for medical conditions
conditions = ConditionsApi()
results = conditions.search_conditions("diabetes", max_results=5)

# Look up procedures
procedures = ProceduresApi()
cardiac_procedures = procedures.search_by_category("cardiac", max_results=10)

# Find ICD-10-CM codes
icd10 = ICD10CMApi()
codes = icd10.search_codes("hypertension", max_results=5)

# Search HCPCS codes
hcpcs = HCPCSApi()
equipment = hcpcs.search_by_category("wheelchair", max_results=5)
```

## Common Response Format

All APIs return consistent response structures:

```python
{
    "success": True,
    "total_results": 25,
    "returned_count": 5,
    "search_terms": "diabetes",
    "results": [
        {
            "code": "E11.9",
            "display": "Type 2 diabetes mellitus without complications",
            "category": "Endocrine/Metabolic",
            # ... additional fields specific to each API
        }
    ]
}
```

## Dependencies

- `requests`: HTTP client library
- `typing`: Type hints support
- Standard library modules: `logging`
