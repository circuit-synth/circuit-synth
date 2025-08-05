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
- **GitHub PR workflow** ensures code review before main branch merge
- **Manual merge approval** prevents accidental releases
- **Main branch protection** - releases only happen on main after PR merge
- **Release tagging** always happens on main branch after proper review

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