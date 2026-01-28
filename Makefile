.PHONY: help setup generate-env fetch-models merge-config update-config list-models claude-set claude-set-force claude-restore

help:
	@echo "Available commands:"
	@echo "  make setup           - Create venv and install dependencies"
	@echo "  make generate-env    - Generate .env file with API keys"
	@echo "  make fetch-models    - Fetch GitHub Copilot models to models.yaml"
	@echo "  make merge-config    - Merge base config + models into litellm_config.yaml"
	@echo "  make update-config   - Fetch models and merge config (fetch + merge)"
	@echo "  make list-models     - List available GitHub Copilot models"
	@echo "  make claude-set      - Configure Claude to use local proxy"
	@echo "  make claude-restore  - Remove proxy configuration from Claude"

setup:
	@echo "Setting up environment..."
	@python3 -m venv venv
	@./venv/bin/pip install -r requirements.txt
	@echo "✅ Setup complete"

generate-env:
	@python3 scripts/generate_env.py

fetch-models:
	@echo "Fetching GitHub Copilot models..."
	@python3 scripts/fetch_models.py --output models.yaml

merge-config:
	@echo "Merging config files..."
	@python3 scripts/merge_config.py

update-config: fetch-models merge-config
	@echo "✅ Config updated successfully"

list-models:
	@./scripts/list-copilot-models.sh

claude-enable:
	@python3 scripts/anthropic_endpoint.py set http://localhost:4000

claude-enable-force:
	@python3 scripts/anthropic_endpoint.py set http://localhost:4000 --force

claude-restore:
	@python3 scripts/anthropic_endpoint.py restore
