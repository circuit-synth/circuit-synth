# Circuit-Synth development Makefile
# (No release/PyPI targets: this fork is not published to PyPI.)

.PHONY: help clean test format dev-install

help:
	@echo "Circuit-Synth development"
	@echo "========================="
	@echo "  make dev-install  - Editable install with dev extras (uv)"
	@echo "  make test         - Run the test suite (pytest)"
	@echo "  make format       - Format with black + isort"
	@echo "  make clean        - Remove build/test artifacts"

dev-install:
	uv pip install -e ".[dev]"

test:
	uv run pytest

format:
	black src/ tests/
	isort src/ tests/

clean:
	rm -rf dist/ build/ *.egg-info src/*.egg-info
	rm -rf .pytest_cache/ .coverage htmlcov/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
