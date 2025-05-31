.PHONY: build up down logs restart clean local test

## Run API locally without Docker (uses host Python env)
local:
	uv run uvicorn bitget_trader.receiver:app --reload

## Activate the virtual environment
activate_env:
	source .venv/Scripts/activate

## Install dependencies in the virtual environment
install_deps:
	source .venv/Scripts/activate && uv pip install -r requirements.txt