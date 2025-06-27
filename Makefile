.PHONY: help install test lint format clean parse benchmark finetune report

help:
	@echo "Available commands:"
	@echo "  make install    - Install project dependencies with Poetry"
	@echo "  make test       - Run test suite"
	@echo "  make lint       - Run code linters (flake8, mypy)"
	@echo "  make format     - Format code with Black"
	@echo "  make clean      - Remove generated files and caches"
	@echo "  make parse      - Parse PDF to JSONL dataset"
	@echo "  make benchmark  - Run benchmarks on all models"
	@echo "  make finetune   - Fine-tune and evaluate model"
	@echo "  make report     - Generate final report"

install:
	poetry install

test:
	poetry run pytest -v

lint:
	poetry run flake8 cpc_parser cpc_benchmark cpc_finetune
	poetry run mypy cpc_parser cpc_benchmark cpc_finetune

format:
	poetry run black cpc_parser cpc_benchmark cpc_finetune tests scripts

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf data/processed/*.jsonl
	rm -rf results/*.csv
	rm -rf results/*.json

# Project-specific commands (to be implemented)
parse:
	poetry run python scripts/parse_all.py

benchmark:
	poetry run python scripts/benchmark_all.py

finetune:
	poetry run python scripts/finetune_and_eval.py

report:
	poetry run python scripts/make_report.py

# Development helpers
shell:
	poetry shell

ipython:
	poetry run ipython

update:
	poetry update

lock:
	poetry lock 