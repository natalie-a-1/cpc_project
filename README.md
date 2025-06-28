# CPC Medical Coding Agent

Simple ReAct AI agent for CPC (Certified Professional Coder) certification exam questions using OpenAI function calling and real-time medical APIs.

## Architecture

**🎯 Simple ReAct Controller**: One agent with function calling tools - no child agents or complex orchestration.

### Available Tools:
1. **HCPCS Search** - Medical equipment, supplies, prosthetics (K0001, E0100, etc.)
2. **ICD-10-CM Search** - Diagnosis codes (I10, E11.9, etc.)
3. **Procedures Search** - Medical procedures and surgeries
4. **Conditions Search** - Medical conditions with ICD mappings
5. **Medical Terminology Lookup** - Prefixes, suffixes, anatomy, coding guidelines

The model autonomously picks which tools to use based on the question content.

## Quick Start

```bash
# Add your OpenAI API key
echo "OPENAI_API_KEY=your_api_key_here" > .env

# Run interactive mode
python scripts/run_cpc_agent.py
```

## How It Works

1. **Question Analysis**: Agent analyzes the CPC question
2. **Tool Selection**: Model decides which APIs/resources to query
3. **Information Gathering**: Executes function calls to gather relevant data
4. **Answer Generation**: Synthesizes information to pick the correct answer (A, B, C, or D)

## Example Flow

```
Question: "What is the ICD-10 code for essential hypertension?"
Options: A) I10, B) I11.9, C) I12.9, D) I13.10

Agent thinks → Calls search_icd10cm("essential hypertension") → 
Gets results → Compares with options → Returns "A"
```

## Cost Estimates

- **GPT-4o-mini**: ~$0.50 per 100 questions
- **GPT-4-turbo**: ~$15 per 100 questions

CPC exam: 100 questions, 70% pass rate required.
