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
- **Sync with remote** - Fetch latest changes from origin
- **Verify main branch is up-to-date** - Ensure main is current with develop

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

### 5. Git Operations and Release Management
- **Merge to main** - Switch to main and merge develop (if releasing from develop)
- **Create release tag** - Tag main branch with version number
- **Push main branch** - Push updated main to origin
- **Push release tag** - Push tag to origin
- **Create GitHub release** - Generate release notes and publish

### 6. PyPI Publication
- **Build distributions** - Create wheel and sdist
- **Upload to PyPI** - Publish to registry
- **Verify upload** - Check package is available

## Implementation

The command runs these steps automatically:

### Pre-Release Checks and Branch Management
```bash
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
    exit 1
fi

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

### Git Merge, Tagging, and Release Management
```bash
# Merge to main branch (if releasing from develop)
if [[ "$current_branch" == "develop" ]]; then
    echo "🔄 Merging develop to main..."
    git checkout main
    git merge develop --no-ff -m "🚀 Release $version: Merge develop to main"
    
    echo "✅ Merged develop to main"
elif [[ "$current_branch" != "main" ]]; then
    echo "⚠️  Warning: Not on main or develop branch"
    echo "🔄 Switching to main for tagging..."
    git checkout main
fi

# Ensure we're on main for tagging
current_branch_for_tag=$(git branch --show-current)
if [[ "$current_branch_for_tag" != "main" ]]; then
    echo "❌ Must be on main branch for release tagging"
    exit 1
fi

# Create release tag on main
echo "🏷️  Creating release tag v$version on main..."
git tag -a "v$version" -m "🚀 Release version $version

Features and changes in this release:
- [Auto-generated from commits - update manually if needed]

Full changelog: https://github.com/circuit-synth/circuit-synth/compare/v$(git describe --tags --abbrev=0 HEAD~1 2>/dev/null || echo '0.0.0')...v$version"

# Push main branch and tags
echo "📤 Pushing main branch and tags to origin..."
git push origin main
git push origin "v$version"

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
3. **GitHub CLI (gh)** installed and authenticated
4. **Clean working directory** (no uncommitted changes)
5. **KiCad installed** (for integration tests)
6. **Rust toolchain** (if Rust modules present)
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
- **Confirmation prompts** for non-standard branches
- **Main branch synchronization** ensures proper Git workflow
- **Automatic branch merging** from develop to main
- **Release tagging** always happens on main branch

## What Gets Released

The release includes:
- **Python package** with all source code
- **Rust binaries** (if present and built)
- **Documentation** and examples
- **Git tag** marking the release on main branch
- **GitHub release** with auto-generated release notes
- **PyPI package** published and available for installation
- **Main branch** updated with latest changes from develop

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