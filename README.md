### CPC Project — Quick Overview

This repo contains a **lean, end-to-end pipeline** to:

1. **Parse** CPC-practice PDF file `./data/raw/cpc_test.pdf` into clean `dataset.jsonl`
   *each record has* **stem + options + answer + explanation**

2. **Benchmark** three frontier models
   *GPT-4o, Claude 3.6 Sonnet, Gemini 1.5*
   → generates a scoreboard of raw accuracies & error sets

3. **Fine-tune** an OpenAI chat model (GPT-3.5-turbo or GPT-4o-mini) on the same data
   → re-evaluate to show cost-efficient gains or parity with GPT-4-class baselines

Directory highlights

```
cpc_parser/     # PDF → JSONL
cpc_benchmark/  # prompt builder, evaluation harness, metrics
cpc_finetune/   # build fine-tune files, launch FT job, re-run eval
scripts/        # one-command wrappers (parse, benchmark, fine-tune, report)
tests/          # pytest for parser & metrics
data/processed/ # auto-generated JSONL & prediction CSVs (git-ignored)
```

Run it top-to-bottom:

```bash
# 1) parse PDFs
./scripts/parse_all.sh

# 2) benchmark gpt-4o / claude / gemini
./scripts/benchmark_all.sh

# 3) fine-tune + re-evaluate
./scripts/finetune_and_eval.sh

# 4) render final scoreboard
./scripts/make_report.sh
```

The goal: **beat the 70 % pass mark and ideally edge past GPT-4o raw performance while spending a fraction of the tokens.**
