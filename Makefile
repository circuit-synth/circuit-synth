# Circuit-Synth Makefile for Release Management

.PHONY: help clean build test test-release test-local test-docker upload-testpypi upload-pypi release

VERSION ?= $(shell python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")

help:
	@echo "Circuit-Synth Release Management"
	@echo "================================"
	@echo ""
	@echo "Available targets:"
	@echo "  make clean           - Clean build artifacts"
	@echo "  make build           - Build distribution files"
	@echo "  make test            - Run unit tests"
	@echo "  make test-release    - Run comprehensive release tests"
	@echo "  make test-local      - Test local wheel installation"
	@echo "  make test-docker     - Test in Docker containers"
	@echo "  make upload-testpypi - Upload to TestPyPI"
	@echo "  make upload-pypi     - Upload to PyPI (CAUTION!)"
	@echo "  make release         - Full release process"
	@echo ""
	@echo "Current version: $(VERSION)"

clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf dist/ build/ *.egg-info src/*.egg-info
	rm -rf .pytest_cache/ .coverage htmlcov/
	rm -rf test_env/ final_test/ debug_env/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "✅ Clean complete"

test:
	@echo "🧪 Running unit tests..."
	uv run pytest tests/unit/ -v
	@echo "✅ Unit tests passed"

test-local: build
	@echo "🧪 Testing local wheel installation..."
	@rm -rf test_env
	python -m venv test_env
	@echo "📦 Installing wheel..."
	test_env/bin/pip install dist/*.whl
	@echo "🔬 Testing imports..."
	test_env/bin/python -c "import circuit_synth; print('✅ circuit_synth imports successfully')"
	@echo "⚡ Testing circuit functionality..."
	test_env/bin/python -c "from circuit_synth import Component, Net, circuit; print('✅ Circuit creation works')"
	@rm -rf test_env
	@echo "✅ Local wheel test passed"

test-docker: build
	@echo "🐳 Testing in Docker containers..."
	@if command -v docker >/dev/null 2>&1; then \
		for version in 3.10 3.11 3.12; do \
			echo "Testing Python $$version..."; \
			echo "FROM python:$$version-slim" > Dockerfile.test; \
			echo "WORKDIR /test" >> Dockerfile.test; \
			echo "COPY dist/*.whl /test/" >> Dockerfile.test; \
			echo "RUN pip install /test/*.whl" >> Dockerfile.test; \
			echo "RUN python -c \"import circuit_synth; print('✅ Python $$version test passed')\"" >> Dockerfile.test; \
			docker build -f Dockerfile.test -t circuit-synth-test:py$$version . && \
			docker run --rm circuit-synth-test:py$$version && \
			docker rmi circuit-synth-test:py$$version; \
		done; \
		rm -f Dockerfile.test; \
		echo "✅ Docker tests passed"; \
	else \
		echo "⚠️  Docker not available, skipping Docker tests"; \
	fi

test-release: build
	@echo "🚀 Running comprehensive release tests..."
	@if [ -f "tools/testing/test_release.py" ]; then \
		chmod +x tools/testing/test_release.py && \
		python tools/testing/test_release.py $(VERSION) --skip-docker; \
	else \
		echo "⚠️  test_release.py not found, running basic tests..."; \
		$(MAKE) test-local; \
	fi

upload-testpypi: test-release
	@echo "📤 Uploading to TestPyPI..."
	@echo "⚠️  Make sure you have configured ~/.pypirc with TestPyPI credentials"
	uv run twine upload --repository testpypi dist/*
	@echo "✅ Uploaded to TestPyPI"
	@echo ""
	@echo "Test installation with:"
	@echo "  pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ circuit-synth==$(VERSION)"

test-from-testpypi:
	@echo "🧪 Testing installation from TestPyPI..."
	@rm -rf test_env
	python -m venv test_env
	test_env/bin/pip install --index-url https://test.pypi.org/simple/ \
		--extra-index-url https://pypi.org/simple/ \
		circuit-synth==$(VERSION)
	test_env/bin/python -c "import circuit_synth; print('✅ TestPyPI package works!')"
	@rm -rf test_env

upload-pypi: test-release
	@echo "⚠️  WARNING: About to upload to production PyPI!"
	@echo "Version: $(VERSION)"
	@echo ""
	@read -p "Are you SURE you want to upload to PyPI? (type 'yes' to confirm): " confirm && \
	if [ "$$confirm" = "yes" ]; then \
		echo "📤 Uploading to PyPI..."; \
		uv run twine upload dist/*; \
		echo "✅ Uploaded to PyPI"; \
		echo ""; \
		echo "Package available at: https://pypi.org/project/circuit-synth/$(VERSION)/"; \
	else \
		echo "❌ Upload cancelled"; \
		exit 1; \
	fi

verify-pypi:
	@echo "🔍 Verifying PyPI release..."
	@rm -rf verify_env
	python -m venv verify_env
	verify_env/bin/pip install circuit-synth==$(VERSION)
	verify_env/bin/python -c "import circuit_synth; v = circuit_synth.__version__; print(f'✅ Installed version: {v}')"
	@rm -rf verify_env
	@echo "✅ PyPI release verified"

release: clean build test-release
	@echo "🚀 Starting full release process for version $(VERSION)"
	@echo ""
	@echo "Step 1: Upload to TestPyPI"
	$(MAKE) upload-testpypi
	@echo ""
	@echo "Step 2: Test from TestPyPI"
	@sleep 30  # Wait for TestPyPI to update
	$(MAKE) test-from-testpypi
	@echo ""
	@echo "Step 3: Upload to PyPI"
	$(MAKE) upload-pypi
	@echo ""
	@echo "Step 4: Verify PyPI release"
	@sleep 30  # Wait for PyPI to update
	$(MAKE) verify-pypi
	@echo ""
	@echo "🎉 Release $(VERSION) complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Create GitHub release: gh release create v$(VERSION)"
	@echo "  2. Update CHANGELOG.md"
	@echo "  3. Announce release"

# Development helpers
dev-install:
	uv pip install -e ".[dev]"

format:
	black src/ tests/
	isort src/ tests/

lint:
	flake8 src/ tests/
	mypy src/

# CI/CD helpers
ci-test:
	@echo "Running CI tests..."
	$(MAKE) build
	$(MAKE) test
	$(MAKE) test-local

.PHONY: dev-install format lint ci-test verify-pypi test-from-testpypi