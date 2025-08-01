# PyPI Release Command

**Purpose:** Complete PyPI release pipeline - from testing to tagging to publishing.

## Usage
```bash
/dev-release-pypi [version]
```

## Arguments
- `version` - Version number (e.g., "0.2.0", "1.0.0-beta.1") - required

## What This Does

This command handles the complete release process:

### 1. Pre-Release Validation
- **Test core functionality** - Run main examples
- **Check branch status** - Ensure we're on develop/main
- **Validate version format** - Semantic versioning check
- **Check for uncommitted changes** - Ensure clean working directory

### 2. Rust Build (If Needed)
- **Check for Rust modules** - Look for Cargo.toml files
- **Build Rust crates** - Compile if present
- **Run Rust tests** - Ensure Rust components work
- **Update Python bindings** - If Rust integration exists

### 3. Version Management
- **Update pyproject.toml** - Set new version number
- **Update __init__.py** - Sync version strings
- **Update CHANGELOG** - Add release notes
- **Commit version changes** - Clean commit for version bump

### 4. Testing and Validation
- **Run full test suite** - All tests must pass
- **Validate examples** - Core examples must work
- **Check imports** - Ensure package imports correctly
- **Build documentation** - Generate fresh docs

### 5. Git Operations
- **Create release tag** - Tag with version number
- **Push changes** - Push commits and tags to origin
- **Merge to main** - If releasing from develop

### 6. PyPI Publication
- **Build distributions** - Create wheel and sdist
- **Upload to PyPI** - Publish to registry
- **Verify upload** - Check package is available

## Implementation

The command runs these steps automatically:

### Pre-Release Checks
```bash
# Ensure clean working directory
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Uncommitted changes found. Commit or stash first."
    exit 1
fi

# Check current branch
current_branch=$(git branch --show-current)
if [[ "$current_branch" != "develop" && "$current_branch" != "main" ]]; then
    echo "⚠️  Warning: Releasing from branch '$current_branch'"
    read -p "Continue? (y/N): " -n 1 -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then exit 1; fi
fi

# Validate version format
if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.-]+)?$ ]]; then
    echo "❌ Invalid version format. Use semantic versioning (e.g., 1.0.0)"
    exit 1
fi
```

### Core Functionality Test
```bash
# Test main functionality
echo "🧪 Testing core functionality..."
uv run python examples/example_kicad_project.py || {
    echo "❌ Core example failed"
    exit 1
}

# Test imports
uv run python -c "from circuit_synth import Circuit, Component, Net; print('✅ Core imports OK')" || {
    echo "❌ Import test failed"
    exit 1
}

# Check KiCad integration
kicad-cli version >/dev/null 2>&1 || {
    echo "⚠️  KiCad not found - integration tests skipped"
}
```

### Rust Build Process
```bash
# Check for Rust modules
rust_modules=()
for cargo_file in $(find . -name "Cargo.toml" 2>/dev/null); do
    rust_modules+=("$(dirname "$cargo_file")")
done

if [ ${#rust_modules[@]} -gt 0 ]; then
    echo "🦀 Building Rust modules..."
    for module in "${rust_modules[@]}"; do
        echo "  Building $module..."
        cd "$module"
        cargo build --release || {
            echo "❌ Rust build failed in $module"
            exit 1
        }
        cargo test || {
            echo "❌ Rust tests failed in $module"
            exit 1
        }
        cd - >/dev/null
    done
    echo "✅ Rust modules built successfully"
else
    echo "ℹ️  No Rust modules found"
fi
```

### Version Update
```bash
# Update pyproject.toml
echo "📝 Updating version to $version..."
sed -i.bak "s/^version = .*/version = \"$version\"/" pyproject.toml

# Update __init__.py
init_file="src/circuit_synth/__init__.py"
if [ -f "$init_file" ]; then
    sed -i.bak "s/__version__ = .*/__version__ = \"$version\"/" "$init_file"
fi

# Check if changes were made
if ! git diff --quiet; then
    git add pyproject.toml "$init_file"
    git commit -m "🔖 Bump version to $version"
    echo "✅ Version updated and committed"
else
    echo "ℹ️  Version already up to date"
fi
```

### Full Test Suite
```bash
# Run comprehensive tests
echo "🧪 Running full test suite..."

# Unit tests
uv run pytest tests/unit/ -v || {
    echo "❌ Unit tests failed"
    exit 1
}

# Integration tests
uv run pytest tests/integration/ -v || {
    echo "❌ Integration tests failed"
    exit 1
}

# Test coverage
coverage_result=$(uv run pytest --cov=circuit_synth --cov-report=term-missing | grep "TOTAL")
echo "📊 $coverage_result"

echo "✅ All tests passed"
```

### Git Tagging and Push
```bash
# Create and push tag
echo "🏷️  Creating release tag v$version..."
git tag -a "v$version" -m "Release version $version"

# Push changes and tags
echo "📤 Pushing to origin..."
git push origin
git push origin "v$version"

echo "✅ Tagged and pushed v$version"
```

### PyPI Build and Upload
```bash
# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

# Build distributions
echo "🏗️  Building distributions..."
uv run python -m build || {
    echo "❌ Build failed"
    exit 1
}

# Check distributions
echo "🔍 Built distributions:"
ls -la dist/

# Upload to PyPI
echo "📦 Uploading to PyPI..."
uv run python -m twine upload dist/* || {
    echo "❌ PyPI upload failed"
    exit 1
}

echo "✅ Successfully uploaded to PyPI"
```

### Post-Release Verification
```bash
# Wait for PyPI to propagate
echo "⏳ Waiting for PyPI propagation..."
sleep 30

# Verify package is available
package_info=$(pip index versions circuit-synth 2>/dev/null || echo "not found")
if [[ "$package_info" == *"$version"* ]]; then
    echo "✅ Package verified on PyPI"
else
    echo "⚠️  Package not yet visible on PyPI (may take a few minutes)"
fi

# Test installation in clean environment
echo "🧪 Testing installation..."
temp_dir=$(mktemp -d)
cd "$temp_dir"
python -m venv test_env
source test_env/bin/activate
pip install circuit-synth==$version
python -c "import circuit_synth; print(f'✅ Installed version: {circuit_synth.__version__}')"
deactivate
cd - >/dev/null
rm -rf "$temp_dir"
```

## Example Usage

```bash
# Release patch version
/dev-release-pypi 0.1.1

# Release minor version
/dev-release-pypi 0.2.0

# Release beta version
/dev-release-pypi 1.0.0-beta.1

# Release major version
/dev-release-pypi 1.0.0
```

## Prerequisites

Before running this command, ensure you have:

1. **PyPI account** with API token configured
2. **Git credentials** set up for pushing
3. **Clean working directory** (no uncommitted changes)
4. **KiCad installed** (for integration tests)
5. **Rust toolchain** (if Rust modules present)

### Setup PyPI Credentials
```bash
# Create ~/.pypirc
[pypi]
username = __token__
password = pypi-your-api-token-here
```

Or use environment variable:
```bash
export TWINE_PASSWORD=pypi-your-api-token-here
```

## Safety Features

- **Validation checks** prevent broken releases
- **Test failures block** the release process
- **Clean working directory** required
- **Version format validation** ensures consistency
- **Confirmation prompts** for non-standard branches

## What Gets Released

The release includes:
- **Python package** with all source code
- **Rust binaries** (if present and built)
- **Documentation** and examples
- **Git tag** marking the release
- **CHANGELOG** entry for the version

## Rollback

If something goes wrong:
```bash
# Delete local tag
git tag -d v1.0.0

# Delete remote tag  
git push origin :refs/tags/v1.0.0

# Revert version commit
git reset --hard HEAD~1
```

---

**This command provides a complete, automated PyPI release pipeline with comprehensive validation and safety checks.**