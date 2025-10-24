---
name: release-testpypi
description: Test release on TestPyPI (staging)
---

# TestPyPI Release Command

**Purpose:** Test releases on TestPyPI before publishing to production PyPI.

## Usage
```bash
/dev-release-testpypi <version>
```

**⚠️ CRITICAL: Version number is MANDATORY - command will fail if not provided!**

## What This Does

This command performs a **complete release simulation** using TestPyPI:

### 1. Pre-Release Validation
- Test core functionality
- Check branch status
- Validate version format
- Check for uncommitted changes
- Sync with remote

### 2. Version Management
- Update pyproject.toml with version number
- Update __init__.py version strings
- Commit version changes

### 3. Testing and Validation
- Run full regression test suite
- Validate examples work
- Check imports
- **CRITICAL: Comprehensive testing to prevent broken releases**

### 4. Build and Upload to TestPyPI
- Clean previous builds
- Build wheel and sdist
- **Upload ONLY to TestPyPI (not production PyPI)**
- Wait for propagation
- Test installation from TestPyPI

### 5. Verification
- Install package from TestPyPI in clean environment
- Run functionality tests
- Verify imports work

## Key Differences from Production Release

| Feature | TestPyPI (`/dev-release-testpypi`) | Production PyPI (`/dev-release-pypi`) |
|---------|-----------------------------------|--------------------------------------|
| **Upload Target** | test.pypi.org | pypi.org |
| **Git Tagging** | ❌ No tags created | ✅ Creates release tags |
| **GitHub Release** | ❌ No GitHub release | ✅ Creates GitHub release |
| **Branch Protection** | ⚠️ Works on any branch | ✅ Requires develop/main |
| **Purpose** | Testing & validation | Production release |
| **Rollback** | Easy (just test again) | Harder (need to yank) |

## Implementation

Run the TestPyPI release script:

```bash
#!/bin/bash
set -e

VERSION=$1

# Validate version parameter
if [ -z "$VERSION" ]; then
    echo "❌ ERROR: Version number is required!"
    echo "Usage: /dev-release-testpypi <version>"
    echo "Example: /dev-release-testpypi 0.6.2-test.1"
    echo "Example: /dev-release-testpypi 0.7.0-alpha.3"
    exit 1
fi

echo "🧪 Starting TestPyPI release process for version: $VERSION"
echo "📋 This will upload to test.pypi.org (NOT production PyPI)"
echo ""

# Fetch latest changes
echo "🔄 Fetching latest changes from origin..."
git fetch origin

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Uncommitted changes found. Commit or stash first."
    exit 1
fi

# Show current branch
current_branch=$(git branch --show-current)
echo "📍 Current branch: $current_branch"
echo "💡 TestPyPI testing works from any branch"
echo ""

# Validate version format
if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.-]+)?$ ]]; then
    echo "❌ Invalid version format. Use semantic versioning"
    echo "Examples: 0.7.0, 1.0.0-beta.1, 0.6.2-test.3"
    exit 1
fi

# Show current version
current_version=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
echo "📊 Current version: $current_version"
echo "📊 Test version: $VERSION"
echo ""

read -p "🤔 Confirm TestPyPI release for $VERSION? (y/N): " -n 1 -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "❌ TestPyPI release cancelled"
    exit 1
fi
echo ""

# CRITICAL: Sync project template with latest agents
echo "🔄 Syncing project template with latest .claude agents..."
if [ -f "./tools/packaging/sync_example_to_template.sh" ]; then
    ./tools/packaging/sync_example_to_template.sh || {
        echo "❌ Failed to sync project template"
        exit 1
    }
    echo "✅ Project template synced"
else
    echo "⚠️  Template sync script not found - skipping"
fi

# Test core functionality
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

# Update version in files
echo "📝 Updating version to $VERSION..."
sed -i.bak "s/^version = .*/version = \"$VERSION\"/" pyproject.toml
rm -f pyproject.toml.bak

init_file="src/circuit_synth/__init__.py"
if [ -f "$init_file" ]; then
    sed -i.bak "s/__version__ = .*/__version__ = \"$VERSION\"/" "$init_file"
    rm -f "${init_file}.bak"
fi

# Check if changes were made
if ! git diff --quiet; then
    git add pyproject.toml "$init_file"
    git commit -m "🧪 Bump version to $VERSION for TestPyPI"
    echo "✅ Version updated and committed"
else
    echo "ℹ️  Version already up to date"
fi

# CRITICAL: Run regression tests
echo "🔥 Running comprehensive regression tests..."
echo "⏱️  This may take 15-20 minutes..."

if [ -f "./tools/testing/run_full_regression_tests.py" ]; then
    ./tools/testing/run_full_regression_tests.py || {
        echo "❌ REGRESSION TESTS FAILED - DO NOT RELEASE!"
        echo "Fix all issues before proceeding to TestPyPI"
        exit 1
    }
    echo "✅ All regression tests passed"
else
    echo "⚠️  Full regression tests not found - running quick tests"
    uv run pytest tests/ -v || {
        echo "❌ Tests failed"
        exit 1
    }
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/ src/*.egg-info/

# Build distributions
echo "🏗️  Building distributions..."
uv build || {
    echo "❌ Build failed"
    exit 1
}

# Show built distributions
echo "🔍 Built distributions:"
ls -lh dist/

# Upload to TestPyPI
echo ""
echo "📤 Uploading to TestPyPI..."
echo "🌐 Target: https://test.pypi.org"
echo ""

uv run twine upload --repository testpypi dist/* || {
    echo "❌ TestPyPI upload failed"
    echo ""
    echo "Common issues:"
    echo "  - Version already exists on TestPyPI (try incrementing: $VERSION-test.2)"
    echo "  - Missing TestPyPI credentials in ~/.pypirc"
    echo "  - Network connectivity issues"
    exit 1
}

echo "✅ Successfully uploaded to TestPyPI"
echo ""

# Wait for TestPyPI propagation
echo "⏳ Waiting 60 seconds for TestPyPI to propagate..."
sleep 60

# Test installation from TestPyPI
echo "🧪 Testing installation from TestPyPI..."
temp_dir=$(mktemp -d)
cd "$temp_dir"

python3 -m venv testpypi_env
source testpypi_env/bin/activate

echo "📥 Installing from TestPyPI..."
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            circuit-synth==$VERSION || {
    echo "❌ Installation from TestPyPI failed"
    echo "💡 The package may still be propagating (try again in 2-3 minutes)"
    deactivate
    cd - >/dev/null
    rm -rf "$temp_dir"
    exit 1
}

# Test functionality
echo "🧪 Testing circuit creation from TestPyPI package..."
python3 -c "
from circuit_synth import Component, Net, circuit

@circuit
def test():
    r1 = Component('Device:R', 'R', value='10k')
    c1 = Component('Device:C', 'C', value='100nF')
    vcc = Net('VCC')
    gnd = Net('GND')
    r1[1] += vcc
    r1[2] += gnd
    c1[1] += vcc
    c1[2] += gnd

try:
    circuit_obj = test()
    json_data = circuit_obj.to_dict()
    assert 'components' in json_data
    assert 'nets' in json_data
    print('✅ Circuit creation works!')
except Exception as e:
    print(f'❌ Circuit creation failed: {e}')
    exit(1)
" || {
    echo "❌ Functionality test failed"
    deactivate
    cd - >/dev/null
    rm -rf "$temp_dir"
    exit 1
}

deactivate
cd - >/dev/null
rm -rf "$temp_dir"

# Success summary
echo ""
echo "═══════════════════════════════════════════════"
echo "✅ TestPyPI Release Complete!"
echo "═══════════════════════════════════════════════"
echo ""
echo "📦 Package: circuit-synth==$VERSION"
echo "🌐 TestPyPI: https://test.pypi.org/project/circuit-synth/$VERSION/"
echo ""
echo "🧪 Test installation with:"
echo "   pip install --index-url https://test.pypi.org/simple/ \\"
echo "               --extra-index-url https://pypi.org/simple/ \\"
echo "               circuit-synth==$VERSION"
echo ""
echo "✅ All tests passed - package works on TestPyPI"
echo ""
echo "📋 Next Steps:"
echo "   1. Verify the package on TestPyPI: https://test.pypi.org/project/circuit-synth/"
echo "   2. Test installation in a fresh environment"
echo "   3. If everything looks good, release to production with:"
echo "      /dev-release-pypi $VERSION"
echo ""
```

## Example Usage

### Test a Pre-Release Version
```bash
# Upload a test/alpha/beta version to TestPyPI
/dev-release-testpypi 0.7.0-test.1
/dev-release-testpypi 0.7.0-alpha.2
/dev-release-testpypi 1.0.0-beta.3
```

### Test Before Production Release
```bash
# Test on TestPyPI first
/dev-release-testpypi 0.7.0

# If tests pass, release to production
/dev-release-pypi 0.7.0
```

### Iterate on TestPyPI
```bash
# Try different versions until it works
/dev-release-testpypi 0.7.0-test.1  # First attempt
/dev-release-testpypi 0.7.0-test.2  # Fixed an issue
/dev-release-testpypi 0.7.0-test.3  # Final test before release
/dev-release-pypi 0.7.0             # Production release
```

## Manual Testing from TestPyPI

After the command completes, manually verify:

```bash
# Create fresh test environment
python3 -m venv test_env
source test_env/bin/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            circuit-synth==VERSION

# Test your typical workflow
python3 -c "
from circuit_synth import Component, Net, circuit

@circuit(name='test')
def my_circuit():
    # Your circuit code here
    pass

circuit_obj = my_circuit()
print('✅ Everything works!')
"

# Clean up
deactivate
rm -rf test_env
```

## Prerequisites

1. **TestPyPI account** - Register at https://test.pypi.org
2. **TestPyPI API token** - Generate at https://test.pypi.org/manage/account/
3. **Configure credentials** in `~/.pypirc`:

```ini
[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TESTPYPI-TOKEN-HERE

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-YOUR-REAL-PYPI-TOKEN-HERE
```

## Advantages of TestPyPI

- ✅ **Safe testing** - Won't affect production PyPI
- ✅ **No version conflicts** - Can test same version multiple times with suffixes
- ✅ **Fast iteration** - Upload, test, fix, repeat
- ✅ **Real environment** - Tests actual package installation flow
- ✅ **No rollback needed** - TestPyPI packages don't matter long-term

## Common Issues

### "Version already exists on TestPyPI"
```bash
# Solution: Add a test suffix
/dev-release-testpypi 0.7.0-test.2  # Instead of 0.7.0-test.1
```

### "Package not found after upload"
```bash
# Solution: Wait longer (TestPyPI can be slow)
sleep 120  # Wait 2 minutes
# Then try installing again
```

### "Installation fails with dependency errors"
```bash
# Solution: Use --extra-index-url to get dependencies from real PyPI
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            circuit-synth==VERSION
```

## Workflow Recommendation

**Always test on TestPyPI before releasing to production:**

```bash
# 1. Develop your changes
git checkout -b feature/my-feature

# 2. Test locally
./tools/testing/run_full_regression_tests.py

# 3. Test on TestPyPI
/dev-release-testpypi 0.7.0-test.1

# 4. Fix any issues found, then test again
/dev-release-testpypi 0.7.0-test.2

# 5. When everything works, merge to main and release
git checkout main
git merge feature/my-feature
/dev-release-pypi 0.7.0
```

---

**This command provides safe, fast testing of releases before publishing to production PyPI.**
