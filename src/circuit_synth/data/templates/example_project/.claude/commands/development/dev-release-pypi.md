# PyPI Release Command

**Purpose:** Complete PyPI release pipeline - from testing to tagging to publishing.

## Usage
```bash
/dev-release-pypi [version]
```

## Arguments
- `version` - Version number - **REQUIRED** - Must follow strict semantic versioning rules (see Version Validation below)

## 🔒 Version Validation Rules

**CRITICAL: The command MUST validate version numbers before proceeding with any release steps.**

### Required Format
- **Semantic Versioning**: `MAJOR.MINOR.PATCH` (e.g., "1.2.3")
- **Pre-release**: `MAJOR.MINOR.PATCH-LABEL` (e.g., "1.2.3-beta.1", "2.0.0-rc.1")
- **No 'v' prefix**: Use "1.2.3" NOT "v1.2.3"

### Version Type Guidelines

**🔴 MAJOR (X.0.0) - Breaking Changes**
- Breaking API changes
- Incompatible functionality changes
- Major architecture overhauls
- **Examples**: 1.0.0 → 2.0.0

**🟡 MINOR (0.X.0) - New Features**
- New functionality added
- New commands or major features
- Backwards-compatible changes
- **Examples**: 0.4.2 → 0.5.0

**🟢 PATCH (0.0.X) - Bug Fixes**
- Bug fixes and small improvements
- Documentation updates
- Template improvements (like .claude directory fixes)
- Backwards-compatible bug fixes
- **Examples**: 0.4.2 → 0.4.3

### Validation Requirements

The command MUST check:

1. **Current Version**: Get current version from pyproject.toml
2. **Version Format**: Validate semantic versioning format
3. **Version Increment**: Ensure proper increment (no skipping versions)
4. **Change Type Assessment**: Require explicit confirmation of change type

### Interactive Validation Process

```bash
# Example validation flow
current_version=$(grep "version" pyproject.toml | cut -d'"' -f2)
echo "Current version: $current_version"
echo "Requested version: $version"

# Validate format
if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.-]+)?$ ]]; then
    echo "❌ Invalid version format. Use semantic versioning (e.g., 1.2.3)"
    exit 1
fi

# Parse versions
IFS='.' read -ra CURRENT <<< "$current_version"
IFS='.' read -ra NEW <<< "${version%%-*}"  # Remove pre-release suffix

current_major=${CURRENT[0]}
current_minor=${CURRENT[1]}
current_patch=${CURRENT[2]}
new_major=${NEW[0]}
new_minor=${NEW[1]}
new_patch=${NEW[2]}

# Determine change type and validate
if [[ $new_major -gt $current_major ]]; then
    change_type="MAJOR"
elif [[ $new_major -eq $current_major && $new_minor -gt $current_minor ]]; then
    change_type="MINOR"
elif [[ $new_major -eq $current_major && $new_minor -eq $current_minor && $new_patch -gt $current_patch ]]; then
    change_type="PATCH"
else
    echo "❌ Invalid version increment. Version must be greater than current."
    echo "   Current: $current_version"
    echo "   Requested: $version"
    exit 1
fi

# Require explicit confirmation
echo ""
echo "🔍 CHANGE TYPE: $change_type"
case $change_type in
    "MAJOR")
        echo "⚠️  MAJOR release - Breaking changes"
        echo "   - API compatibility broken"
        echo "   - Users may need code changes"
        ;;
    "MINOR")
        echo "✨ MINOR release - New features"
        echo "   - New functionality added"
        echo "   - Backwards compatible"
        ;;
    "PATCH")
        echo "🔧 PATCH release - Bug fixes"
        echo "   - Bug fixes and improvements"
        echo "   - No new features"
        ;;
esac

echo ""
read -p "Is this the correct change type for your release? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Release cancelled. Please choose the correct version number:"
    echo "   - PATCH: $current_major.$current_minor.$((current_patch + 1))"
    echo "   - MINOR: $current_major.$((current_minor + 1)).0"
    echo "   - MAJOR: $((current_major + 1)).0.0"
    exit 1
fi
```

### Common Version Mistakes

**❌ Wrong:**
- Skipping versions: 0.4.2 → 0.6.0
- Wrong format: v1.2.3, 1.2, 1.2.3.4
- Wrong type: Bug fix as MINOR (0.4.2 → 0.5.0)
- Wrong type: New feature as PATCH (0.4.2 → 0.4.3)

**✅ Correct:**
- Sequential: 0.4.2 → 0.4.3 (patch)
- Sequential: 0.4.3 → 0.5.0 (minor)
- Sequential: 0.5.0 → 1.0.0 (major)

## What This Does

This command handles the complete release process:

### 1. Pre-Release Validation
- **Test core functionality** - Run main examples
- **Check branch status** - Ensure we're on develop/main
- **Validate version format** - Strict semantic versioning validation with interactive confirmation
- **Check for uncommitted changes** - Ensure clean working directory


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

# STRICT VERSION VALIDATION (see Version Validation Rules above)
current_version=$(grep "version = " pyproject.toml | cut -d'"' -f2)
echo "Current version: $current_version"
echo "Requested version: $version"

# Validate format
if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.-]+)?$ ]]; then
    echo "❌ Invalid version format. Use semantic versioning (e.g., 1.2.3)"
    exit 1
fi

# Parse and validate increment
IFS='.' read -ra CURRENT <<< "$current_version"
IFS='.' read -ra NEW <<< "${version%%-*}"

current_major=${CURRENT[0]}
current_minor=${CURRENT[1]}
current_patch=${CURRENT[2]}
new_major=${NEW[0]}
new_minor=${NEW[1]}
new_patch=${NEW[2]}

# Determine change type and validate increment
if [[ $new_major -gt $current_major ]]; then
    change_type="MAJOR"
elif [[ $new_major -eq $current_major && $new_minor -gt $current_minor ]]; then
    change_type="MINOR"
elif [[ $new_major -eq $current_major && $new_minor -eq $current_minor && $new_patch -gt $current_patch ]]; then
    change_type="PATCH"
else
    echo "❌ Invalid version increment. Version must be greater than current."
    echo "   Current: $current_version → Requested: $version"
    echo "   Valid options:"
    echo "   - PATCH: $current_major.$current_minor.$((current_patch + 1))"
    echo "   - MINOR: $current_major.$((current_minor + 1)).0"
    echo "   - MAJOR: $((current_major + 1)).0.0"
    exit 1
fi

# Interactive confirmation
echo ""
echo "🔍 CHANGE TYPE: $change_type"
case $change_type in
    "MAJOR") echo "⚠️  MAJOR - Breaking changes, API incompatibility" ;;
    "MINOR") echo "✨ MINOR - New features, backwards compatible" ;;
    "PATCH") echo "🔧 PATCH - Bug fixes, improvements, templates" ;;
esac

read -p "Is this the correct change type? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Release cancelled. Choose correct version:"
    echo "   - PATCH: $current_major.$current_minor.$((current_patch + 1))"
    echo "   - MINOR: $current_major.$((current_minor + 1)).0"
    echo "   - MAJOR: $((current_major + 1)).0.0"
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