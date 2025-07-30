.PHONY: format format-python format-rust format-check setup-hooks clean help

# Default target
help: ## Show this help message
	@echo "🔧 Circuit-Synth Formatting Commands"
	@echo "=================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "%-20s %s\n", $$1, $$2}'

format: ## Format all code (Python + Rust) - One command does it all!
	@./scripts/format_all.sh

format-python: ## Format Python code with Black and isort
	@echo "🐍 Formatting Python code..."
	@uv run black src/
	@uv run isort src/
	@echo "✅ Python formatting complete"

format-rust: ## Format all Rust code
	@echo "🦀 Formatting Rust code..."
	@for dir in rust_modules/*/; do \
		if [ -f "$$dir/Cargo.toml" ]; then \
			echo "  Formatting $$dir"; \
			cd "$$dir" && cargo fmt && cd - > /dev/null; \
		fi \
	done
	@echo "✅ Rust formatting complete"

format-check: ## Check if code is properly formatted (CI-friendly)
	@echo "🔍 Checking Python formatting..."
	@uv run black --check src/
	@uv run isort --check-only src/
	@echo "🔍 Checking Rust formatting..."
	@for dir in rust_modules/*/; do \
		if [ -f "$$dir/Cargo.toml" ]; then \
			echo "  Checking $$dir"; \
			cd "$$dir" && cargo fmt --check && cd - > /dev/null; \
		fi \
	done
	@echo "✅ All formatting checks passed\!"

setup-hooks: ## Install pre-commit hooks for automatic formatting
	@./scripts/setup_formatting.sh

install-git-hooks: ## Install git hooks for auto-formatting on commit  
	@./scripts/install_git_hooks.sh

lint: ## Run all linting checks
	@echo "🔍 Running Python lints..."
	@uv run flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics --extend-ignore=F821
	@echo "✅ Linting complete"

test: ## Run test suite
	@echo "🧪 Running test suite..."
	@uv run pytest --cov=circuit_synth --cov-report=term-missing -v
	@echo "✅ Tests complete"

clean: ## Clean up temporary files
	@echo "🧹 Cleaning up..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type f -name ".coverage" -delete
	@echo "✅ Cleanup complete"

ci-check: format-check lint ## Run all CI checks locally
	@echo "🚀 All CI checks passed\! Ready to push."
EOF < /dev/null