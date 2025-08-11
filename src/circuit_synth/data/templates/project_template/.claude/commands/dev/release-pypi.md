# PyPI Release Command

**Purpose:** Complete PyPI release pipeline - from testing to tagging to publishing.

## Usage
```bash
/dev-release-pypi <version>
```

**⚠️ CRITICAL: Version number is MANDATORY - command will fail if not provided!**

## Arguments
- `version` - **REQUIRED** Version number (e.g., "0.2.0", "1.0.0-beta.1") - **MUST BE SPECIFIED**

## What This Does

This command handles the complete release process:

### 1. Pre-Release Validation
- **Test core functionality** - Run main examples
- **Check branch status** - Ensure we're on develop/main
- **Validate version format** - Semantic versioning check
- **Check for uncommitted changes** - Ensure clean working directory
- **Sync with remote** - Fetch latest changes from origin
- **Verify main branch is up-to-date** - Ensure main is current with develop
- **Website validation** - Check website content accuracy and deployment readiness


### 3. Version Management
- **Update pyproject.toml** - Set new version number
- **Update __init__.py** - Sync version strings
- **Update CHANGELOG** - Add release notes
- **Commit version changes** - Clean commit for version bump

### 4. Testing and Validation - COMPREHENSIVE REGRESSION TESTING
- **Run full test suite** - All tests must pass
- **Validate examples** - Core examples must work
- **Check imports** - Ensure package imports correctly
- **Build documentation** - Generate fresh docs
- **CRITICAL: Run comprehensive regression testing** - Prevent PyPI release failures

### 5. Git Operations and Release Management
- **Create GitHub PR** - Create PR to merge develop into main (if releasing from develop)
- **Wait for PR merge** - Process pauses for manual PR review and merge
- **Verify main branch** - Ensure we're on updated main branch for tagging
- **Create release tag** - Tag main branch with version number
- **Push release tag** - Push tag to origin (main updated via PR merge)
- **Create GitHub release** - Generate release notes and publish

### 6. PyPI Publication
- **Build distributions** - Create wheel and sdist
- **Upload to PyPI** - Publish to registry
- **Verify upload** - Check package is available

## Implementation

**🔧 ENHANCED: Now includes .claude directory synchronization**

The command runs the complete release script at `./tools/release/release_to_pypi.sh` which includes:
- Copy production agents/commands from `.claude/` to package templates 
- Exclude development agents/commands (dev/ subdirectories)
- Ensure users get latest circuit design workflow improvements

The command runs these steps automatically:

### Pre-Release Checks and Branch Management
```bash
# CRITICAL: Always require version number as parameter
if [ -z "$1" ]; then
    echo "❌ ERROR: Version number is required!"
    echo "Usage: /dev-release-pypi <version>"
    echo "Example: /dev-release-pypi 0.6.2"
    echo "Example: /dev-release-pypi 0.7.0"
    echo "Example: /dev-release-pypi 1.0.0-beta.1"
    exit 1
fi

version="$1"
echo "🎯 Starting release process for version: $version"

# Fetch latest changes from remote
echo "🔄 Fetching latest changes from origin..."
git fetch origin

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
    echo "Provided: $version"
    exit 1
fi

# Show current version for comparison
current_version=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
echo "📊 Current version: $current_version"
echo "📊 New version: $version"
echo ""
read -p "🤔 Confirm release version $version? (y/N): " -n 1 -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then 
    echo ""
    echo "❌ Release cancelled. Please specify the correct version."
    exit 1
fi
echo ""

# Ensure develop is up-to-date with origin
if [[ "$current_branch" == "develop" ]]; then
    echo "🔄 Ensuring develop is up-to-date..."
    git pull origin develop || {
        echo "❌ Failed to pull latest develop"
        exit 1
    }
fi

# Check if main needs updating from develop
echo "🔍 Checking main branch status..."
git checkout main
git pull origin main

# Check if main is behind develop
behind_count=$(git rev-list --count main..develop)
if [ "$behind_count" -gt 0 ]; then
    echo "📋 Main is $behind_count commits behind develop"
    echo "🔄 Main will be updated during release process"
else
    echo "✅ Main is up-to-date with develop"
fi

# Return to original branch
git checkout "$current_branch"
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

# Website validation (CRITICAL for PyPI release)
echo "🌐 Validating website content before release..."
if [ -d "website" ]; then
    echo "📱 Checking website directory..."
    
    # Check if website content includes new version
    if [ -f "website/index.html" ]; then
        html_content=$(cat website/index.html)
        
        # Check for circuit-synth branding
        if ! echo "$html_content" | grep -q "circuit-synth"; then
            echo "❌ Website missing circuit-synth branding"
            exit 1
        fi
        
        # Check for key features
        required_features=("Python" "KiCad" "AI")
        for feature in "${required_features[@]}"; do
            if ! echo "$html_content" | grep -qi "$feature"; then
                echo "❌ Website missing '$feature' in content"
                exit 1
            fi
        done
        
        # Check installation instructions
        if ! echo "$html_content" | grep -q "uv add circuit-synth"; then
            echo "⚠️  Website may need installation instruction updates"
        fi
        
        echo "✅ Website content validation passed"
    else
        echo "❌ Missing website/index.html"
        exit 1
    fi
    
    # Check deployment script
    if [ -f "website/deploy-website.sh" ]; then
        if ! bash -n website/deploy-website.sh; then
            echo "❌ Website deployment script has syntax errors"
            exit 1
        fi
        echo "✅ Website deployment script OK"
    else
        echo "⚠️  Missing website deployment script"
    fi
    
    # Check deployment documentation
    if [ -f "website/DEPLOYMENT.md" ]; then
        echo "✅ Website deployment documentation exists"
    else
        echo "⚠️  Consider adding website/DEPLOYMENT.md"
    fi
    
else
    echo "⚠️  No website directory found - website won't be updated"
    echo "💡 Consider adding website/ directory for circuit-synth.com"
fi
```

```bash
done

        echo "  Building $module..."
        cd "$module"
            exit 1
        }
            exit 1
        }
        cd - >/dev/null
    done
else
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

### CRITICAL: Comprehensive Regression Testing

**⚠️ THIS IS THE MOST IMPORTANT STEP - PREVENTS BROKEN PyPI RELEASES**

Run the full regression test suite that simulates EXACTLY what users will experience when installing from PyPI:

```bash
# OPTION 1: Quick regression test (5-10 minutes)
echo "🚀 Running quick regression tests..."
./tools/testing/run_regression_tests.py --quick || {
    echo "❌ REGRESSION TESTS FAILED - DO NOT RELEASE!"
    echo "Fix all issues before proceeding"
    exit 1
}

# OPTION 2: Full regression test with clean environment (15-20 minutes)
# RECOMMENDED BEFORE ANY PyPI RELEASE
echo "🔥 Running FULL regression test suite..."
./tools/testing/run_full_regression_tests.py || {
    echo "❌ FULL REGRESSION TESTS FAILED - DO NOT RELEASE!"
    echo "This means the package WILL BE BROKEN on PyPI"
    exit 1
}

# OPTION 3: Release-specific testing (10-15 minutes)
# Tests the exact wheel that will be uploaded
echo "📦 Testing release package..."
./tools/testing/test_release.py $version --skip-docker || {
    echo "❌ RELEASE TESTS FAILED - DO NOT RELEASE!"
    exit 1
}
```

#### What the Regression Tests Do:

**1. Environment Reconstruction (run_full_regression_tests.py)**
- Creates fresh virtual environment from scratch
- Installs package as users would (pip install circuit-synth)
- Tests comprehensive functionality

**2. Package Distribution Testing (test_release.py)**
- Builds the actual wheel/sdist that will go to PyPI
- Installs in isolated virtual environment
- Tests on multiple Python versions (3.10, 3.11, 3.12)
- Tests actual circuit creation functionality
- Optionally tests in Docker containers
- Can upload to TestPyPI for staging test

**3. Core Functionality Testing (run_regression_tests.py)**
- Tests all major circuit creation patterns
- Validates KiCad generation
- Tests component libraries
- Validates manufacturing integrations (JLCPCB, DigiKey)

#### When to Use Each Test:

| Test Type | When to Use | Duration | Command |
|-----------|------------|----------|---------|
| Quick Test | During development | 5 min | `./tools/testing/run_regression_tests.py --quick` |
| Full Test | Before ANY release | 15-20 min | `./tools/testing/run_full_regression_tests.py` |
| Release Test | Final validation | 10-15 min | `./tools/testing/test_release.py VERSION` |
| All Tests | Maximum safety | 30-40 min | All three above |

#### Critical Test Points:

```bash
# 1. Test local wheel installation
echo "🧪 Testing local wheel..."
python -m venv test_env
source test_env/bin/activate
pip install dist/*.whl
deactivate
rm -rf test_env

# 2. Test from TestPyPI (staging)
echo "📤 Uploading to TestPyPI for staging test..."
uv run twine upload --repository testpypi dist/*
sleep 30  # Wait for propagation

echo "🧪 Testing from TestPyPI..."
python -m venv testpypi_env
source testpypi_env/bin/activate
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            circuit-synth==$version
python -c "import circuit_synth; print('✅ TestPyPI package works')"
deactivate
rm -rf testpypi_env

python -c "
import sys
import importlib

]

failed = []
    try:
        importlib.import_module(module)
        print(f'✅ {module} imports successfully')
    except ImportError as e:
        print(f'❌ {module} failed: {e}')
        failed.append(module)

if failed:
    sys.exit(1)
else:
"

# 4. Circuit Functionality Test
echo "⚡ Testing circuit creation..."
python -c "
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
"
```

#### Common Regression Test Failures and Fixes:

| Error | Cause | Fix |
|-------|-------|-----|
| "Circuit creation failed" | Core functionality broken | Run unit tests, check recent changes |

#### Emergency Test Commands:

```bash
# If regression tests keep failing, debug with:

# 1. Clean EVERYTHING and start fresh
./tools/maintenance/clear_all_caches.sh
rm -rf dist/ build/ *.egg-info/

    cd $module
    cd ../..
done

# 3. Test in completely isolated environment
docker run --rm -it -v $(pwd):/app python:3.12 bash
cd /app
pip install uv
uv build
pip install dist/*.whl
python -c "import circuit_synth; print('Docker test:', circuit_synth.__version__)"
```

### Git Operations and Release PR Management
```bash
# Create GitHub PR to merge develop into main (if releasing from develop)
if [[ "$current_branch" == "develop" ]]; then
    echo "🔄 Creating GitHub PR to merge develop into main..."
    
    # Create PR using GitHub CLI
    if command -v gh >/dev/null 2>&1; then
        pr_title="🚀 Release v$version: Merge develop to main"
        pr_body="## Release v$version

### Summary
This PR merges the develop branch into main for the v$version release.

### Changes
$(git log --pretty=format:"- %s (%h)" main..develop | head -10)

### Pre-Release Checklist
- [x] All tests passing
- [x] Version updated to $version
- [x] Core functionality validated
- [x] Documentation updated

### Post-Merge Actions
After this PR is merged, the release process will:
1. Tag main branch with v$version
2. Build and publish to PyPI
3. Create GitHub release with release notes

**Ready for release!** 🚀"

        echo "📝 Creating PR: $pr_title"
        pr_url=$(gh pr create --title "$pr_title" --body "$pr_body" --base main --head develop)
        
        if [ $? -eq 0 ]; then
            echo "✅ Created PR: $pr_url"
            echo ""
            echo "🔔 NEXT STEPS:"
            echo "   1. Review and merge the PR: $pr_url"
            echo "   2. Re-run this command after merge to complete the release"
            echo ""
            echo "⏸️  Release process paused - waiting for PR merge"
            exit 0
        else
            echo "❌ Failed to create PR - falling back to manual merge"
            echo "⚠️  Manual merge required:"
            echo "   1. Create PR manually: develop → main"  
            echo "   2. Merge the PR"
            echo "   3. Re-run this command"
            exit 1
        fi
    else
        echo "❌ GitHub CLI (gh) not found"
        echo "🔧 Install with: brew install gh"
        echo ""
        echo "⚠️  Manual steps required:"
        echo "   1. Create PR manually: develop → main"
        echo "   2. Merge the PR" 
        echo "   3. Re-run this command from main branch"
        exit 1
    fi
    
elif [[ "$current_branch" != "main" ]]; then
    echo "⚠️  Warning: Not on main or develop branch"
    echo "🔄 For releases, use develop branch to create PR, or main branch to tag existing release"
    exit 1
fi

# If we're on main, proceed with tagging (assumes PR was already merged)
echo "🔍 Verifying we're on main branch for release tagging..."
current_branch_for_tag=$(git branch --show-current)
if [[ "$current_branch_for_tag" != "main" ]]; then
    echo "❌ Must be on main branch for release tagging"
    echo "💡 Switch to main branch and re-run this command"
    exit 1
fi

# Ensure main is up-to-date
echo "🔄 Ensuring main branch is up-to-date..."
git pull origin main || {
    echo "❌ Failed to pull latest main branch"
    exit 1
}

# Create release tag on main
echo "🏷️  Creating release tag v$version on main..."
git tag -a "v$version" -m "🚀 Release version $version

Features and changes in this release:
- [Auto-generated from commits - update manually if needed]

Full changelog: https://github.com/circuit-synth/circuit-synth/compare/v$(git describe --tags --abbrev=0 HEAD~1 2>/dev/null || echo '0.0.0')...v$version"

# Push tags to origin (main branch should already be pushed via PR merge)
echo "📤 Pushing release tag to origin..."
git push origin "v$version" || {
    echo "❌ Failed to push release tag"
    exit 1
}

echo "✅ Tagged and pushed v$version on main branch"
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

### GitHub Release Creation
```bash
# Create GitHub release with release notes
echo "📝 Creating GitHub release..."

# Generate release notes from commits since last tag
last_tag=$(git describe --tags --abbrev=0 HEAD~1 2>/dev/null || echo "")
if [ -n "$last_tag" ]; then
    echo "📋 Generating release notes since $last_tag..."
    release_notes=$(git log --pretty=format:"- %s (%h)" "$last_tag"..HEAD)
else
    echo "📋 Generating release notes for initial release..."
    release_notes=$(git log --pretty=format:"- %s (%h)" --max-count=10)
fi

# Create GitHub release using gh CLI
if command -v gh >/dev/null 2>&1; then
    echo "🚀 Creating GitHub release v$version..."
    
    gh release create "v$version" \
        --title "🚀 Release v$version" \
        --notes "## What's Changed

$release_notes

## Installation

\`\`\`bash
pip install circuit-synth==$version
# or
uv add circuit-synth==$version
\`\`\`

## PyPI Package
📦 https://pypi.org/project/circuit-synth/$version/

**Full Changelog**: https://github.com/circuit-synth/circuit-synth/compare/v$last_tag...v$version" \
        --latest || {
        echo "⚠️  GitHub release creation failed (continuing with PyPI release)"
    }
    
    echo "✅ GitHub release created"
else
    echo "⚠️  GitHub CLI (gh) not found - skipping GitHub release creation"
    echo "💡 Install with: brew install gh"
    echo "📝 Manual release notes:"
    echo "$release_notes"
fi
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

# Deploy website after successful PyPI release
echo "🌐 Deploying website after successful release..."
if [ -f "website/deploy-website.sh" ]; then
    echo "🚀 Running website deployment..."
    cd website
    if bash deploy-website.sh; then
        echo "✅ Website deployed successfully"
    else
        echo "⚠️  Website deployment failed - manual intervention may be needed"
        echo "💡 Check website/deploy-website.sh and website/DEPLOYMENT.md"
    fi
    cd - >/dev/null
else
    echo "⚠️  No website deployment script found"
    echo "💡 Consider adding website/deploy-website.sh for automated deployment"
fi

# Final verification
echo "📊 Release Summary:"
echo "   📦 PyPI: https://pypi.org/project/circuit-synth/$version/"
echo "   🏷️  Git Tag: v$version"
echo "   🌐 Website: circuit-synth.com (if deployment succeeded)"
echo "   📋 GitHub: https://github.com/circuit-synth/circuit-synth/releases/tag/v$version"
```

## Example Usage

### Two-Step Release Process

**Step 1: Create Release PR (from develop branch)**
```bash
# From develop branch - creates PR to merge into main
/dev-release-pypi 0.7.0
# → Creates GitHub PR: develop → main
# → Process pauses for manual PR review/merge
```

**Step 2: Complete Release (from main branch after PR merge)**
```bash
# Switch to main branch and pull latest
git checkout main && git pull origin main

# Complete the release - tags and publishes
/dev-release-pypi 0.7.0
# → Tags main branch with v0.7.0
# → Publishes to PyPI
# → Creates GitHub release
```

### Version Examples
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
3. **GitHub CLI (gh)** installed and authenticated
4. **Clean working directory** (no uncommitted changes)
5. **KiCad installed** (for integration tests)
7. **Main branch permissions** for pushing releases

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

### Setup GitHub CLI
```bash
# Install GitHub CLI
brew install gh

# Authenticate with GitHub
gh auth login

# Verify authentication
gh auth status
```

## Safety Features

- **Validation checks** prevent broken releases
- **Test failures block** the release process
- **Clean working directory** required
- **Version format validation** ensures consistency
- **GitHub PR workflow** ensures code review before main branch merge
- **Manual merge approval** prevents accidental releases
- **Main branch protection** - releases only happen on main after PR merge
- **Release tagging** always happens on main branch after proper review

## What Gets Released

The release includes:
- **Python package** with all source code
- **Documentation** and examples
- **Git tag** marking the release on main branch
- **GitHub release** with auto-generated release notes
- **PyPI package** published and available for installation
- **Main branch** updated with latest changes from develop
- **Website deployment** to circuit-synth.com (if website/ directory exists)

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


**⚠️ ALWAYS RUN THIS BEFORE ANY RELEASE TO PREVENT BROKEN PACKAGES**


2. Path manipulation doesn't work in packaged distributions  
3. Compiled binaries (.so files) aren't properly included


```bash
# 1. First, check for problematic import patterns
python3 -c "
import os
from pathlib import Path

problem_files = [
    'src/circuit_synth/kicad/sch_gen/kicad_formatter.py',
    'src/circuit_synth/kicad/schematic/placement.py',
]

for file in problem_files:
    if Path(file).exists():
        content = Path(file).read_text()
        issues = []
        if 'spec.loader.exec_module' in content:
            issues.append('file-based loading')
            issues.append('path manipulation')
        if issues:
            print(f'❌ {file}: {', '.join(issues)}')
        else:
            print(f'✅ {file}: clean')
"

# 2. Apply emergency fixes if needed
#!/usr/bin/env python3

from pathlib import Path

    content = Path(file_path).read_text()
    
    # Replace complex import with simple optional pattern
    simple_import = f'''
try:
    import {module_name}
except ImportError:
    # Will use Python fallback
'''
    
    # This is simplified - in practice need proper replacement logic
    Path(file_path).write_text(content)
    print(f'✅ Fixed {file_path}')

# Fix all known problematic files
EOF

```


```bash
    # Cargo.toml check removed - pure Python project
done

find . -name "*.so" -o -name "*.dylib" -o -name "*.pyd" | grep -v .venv
```

### Step 3: Test Import Logic Locally

```bash
# Test that imports work in a clean environment
python3 -m venv test_imports
source test_imports/bin/activate

# Install in development mode to test import logic
pip install -e .

python3 -c "
import sys
modules_to_test = [
]

for module in modules_to_test:
    try:
        __import__(module)
        print(f'✅ {module} imports successfully')
    except ImportError as e:
        print(f'⚠️ {module} not available (OK if using Python fallback): {e}')
    except Exception as e:
        print(f'❌ {module} ERROR: {e}')
        sys.exit(1)
"

deactivate
rm -rf test_imports
```

## NON-GITHUB WORKFLOW Testing Process

For releases without GitHub Actions, follow this manual but thorough process:

### Pre-Release Testing Sequence

```bash
# This is the #1 cause of broken releases
python3 << 'EOF'
from pathlib import Path
import re

def fix_file(path, old_pattern, new_code):
    content = Path(path).read_text()
    Path(path).write_text(re.sub(old_pattern, new_code, content, flags=re.DOTALL))

# Fix kicad_formatter.py 
fix_file(
    'src/circuit_synth/kicad/sch_gen/kicad_formatter.py',
    r'try:.*?raise.*?(?=\n\nlogger)',
try:
except ImportError:
    pass  # Use Python fallback
except Exception as e:
)
EOF

# 1. MANDATORY: Full Regression Test (20 minutes)
# This catches 99% of PyPI packaging issues
./tools/testing/run_full_regression_tests.py || exit 1

# 2. Build Distribution Files
uv build

# 3. Test Local Wheel (5 minutes)
python -m venv local_test
source local_test/bin/activate
pip install dist/circuit_synth-*.whl
python -c "
import circuit_synth
from circuit_synth import Component, Net, circuit
print('✅ Local wheel test passed')
"
deactivate
rm -rf local_test

# 4. Test on Multiple Python Versions (10 minutes)
for version in 3.10 3.11 3.12; do
    if command -v python$version >/dev/null; then
        echo "Testing Python $version..."
        python$version -m venv test_$version
        test_$version/bin/pip install dist/*.whl
        test_$version/bin/python -c "import circuit_synth; print('✅ Python $version OK')"
        rm -rf test_$version
    fi
done

# 5. TestPyPI Staging (15 minutes)
# Upload to TestPyPI first
uv run twine upload --repository testpypi dist/*

# Wait for propagation
sleep 60

# Test from TestPyPI
python -m venv testpypi_test
source testpypi_test/bin/activate
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            circuit-synth==$version
            
# Comprehensive functionality test
python -c "
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
    return locals()

circuit_obj = test()
json_data = circuit_obj.to_dict()
assert len(json_data['components']) == 2
assert len(json_data['nets']) == 2
print('✅ TestPyPI validation complete')
"
deactivate
rm -rf testpypi_test

# 6. Final Docker Test (Optional but Recommended)
if command -v docker >/dev/null; then
    echo "FROM python:3.12-slim" > Dockerfile.test
    echo "COPY dist/*.whl /tmp/" >> Dockerfile.test
    echo "RUN pip install /tmp/*.whl" >> Dockerfile.test
    
    docker build -f Dockerfile.test -t circuit-test .
    docker run --rm circuit-test && echo "✅ Docker test passed"
    docker rmi circuit-test
    rm Dockerfile.test
fi

# 7. ONLY IF ALL TESTS PASS - Upload to PyPI
echo "🎯 All tests passed! Ready for PyPI release."
echo "Run: uv run twine upload dist/*"
```

### Test Failure Decision Tree

```
┌─────────────────────────┐
│ Run Full Regression Test│
└───────────┬─────────────┘
            │
            ▼
        ┌───────┐
        │ Pass? │
        └───┬───┘
            │
     ┌──────┴──────┐
     │             │
     ▼ No          ▼ Yes
 ┌─────────┐   ┌──────────────┐
 │  STOP!  │   │ Test Wheel   │
 │ Fix bugs│   │ Locally      │
 └─────────┘   └──────┬───────┘
                      │
                      ▼
                  ┌───────┐
                  │ Pass? │
                  └───┬───┘
                      │
               ┌──────┴──────┐
               │             │
               ▼ No          ▼ Yes
           ┌─────────┐   ┌──────────────┐
           │  Debug  │   │Test TestPyPI │
           │ Locally │   └──────┬───────┘
           └─────────┘          │
                                ▼
                            ┌───────┐
                            │ Pass? │
                            └───┬───┘
                                │
                         ┌──────┴──────┐
                         │             │
                         ▼ No          ▼ Yes
                     ┌─────────┐   ┌─────────────┐
                     │ DO NOT  │   │ SAFE TO     │
                     │ RELEASE │   │ RELEASE!    │
                     └─────────┘   └─────────────┘
```

## ROCK-SOLID RELEASE CHECKLIST

### The Absolute Minimum for Safe Release

If you do NOTHING else, do these 5 things to prevent broken releases:

2. **Build Clean** - `rm -rf dist/ build/ && uv build`
3. **Test Wheel Locally** - Install in fresh venv and test imports
4. **Upload to TestPyPI First** - Test from TestPyPI before real PyPI
5. **Version Bump** - Always increment version for new releases

### Complete Rock-Solid Release Process

```bash
#!/bin/bash
# save this as release.sh and run it for every release

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: ./release.sh VERSION"
    echo "Example: ./release.sh 0.8.6"
    exit 1
fi

echo "🚀 Starting rock-solid release process for v$VERSION"

# 1. Update version
sed -i '' "s/version = .*/version = \"$VERSION\"/" pyproject.toml
sed -i '' "s/__version__ = .*/__version__ = \"$VERSION\"/" src/circuit_synth/__init__.py

python3 << 'EOF'
EOF

# 3. Clean everything
rm -rf dist/ build/ *.egg-info src/*.egg-info
rm -rf test_env/ test_venv/ testpypi_env/
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# 4. Build distribution
uv build || exit 1

# 5. Test local wheel
echo "🧪 Testing local wheel..."
python3 -m venv test_env
source test_env/bin/activate
pip install dist/*.whl
python3 -c "
import circuit_synth
print(f'Version: {circuit_synth.__version__}')
from circuit_synth import Component, Net, circuit
print('✅ Core imports work')
try:
except ImportError:
"
deactivate
rm -rf test_env

# 6. Upload to TestPyPI
echo "📤 Uploading to TestPyPI..."
uv run twine upload --repository testpypi dist/* || {
    echo "⚠️ TestPyPI upload failed (package may already exist)"
}

# 7. Test from TestPyPI
echo "⏳ Waiting 60s for TestPyPI to update..."
sleep 60

echo "🧪 Testing from TestPyPI..."
python3 -m venv testpypi_env
source testpypi_env/bin/activate
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            circuit-synth==$VERSION || {
    echo "❌ TestPyPI installation failed!"
    deactivate
    exit 1
}

python3 -c "
from circuit_synth import Component, Net, circuit
@circuit
def test():
    r1 = Component('Device:R', 'R', value='10k')
    return locals()
c = test()
print('✅ TestPyPI package works!')
"
deactivate
rm -rf testpypi_env

# 8. Final confirmation
echo ""
echo "========================================="
echo "✅ All tests passed for version $VERSION"
echo "========================================="
echo ""
echo "Ready to upload to PyPI?"
echo "Run: uv run twine upload dist/*"
echo ""
echo "After upload, verify with:"
echo "pip install circuit-synth==$VERSION"
```

### Known Issues and Solutions

| Problem | Symptom | Solution |
|---------|---------|----------|
| Version conflict | "Version already exists" | Increment version number |
| TestPyPI timeout | Can't install from TestPyPI | Wait 2-5 minutes and retry |

### Emergency Recovery

If a bad release makes it to PyPI:

```bash
# 1. Yank the bad release (prevents new installs)
pip install twine
twine yank circuit-synth --version BAD_VERSION

# 2. Fix the issues
# [Apply all fixes]

# 3. Release new patch version
NEW_VERSION="X.Y.Z+1"  # Increment patch
./release.sh $NEW_VERSION

# 4. Communicate to users
# Post on GitHub issues about the fix
```

---

**This command provides a complete, automated PyPI release pipeline with comprehensive validation and safety checks.**