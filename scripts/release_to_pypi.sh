#!/bin/bash
# PyPI Release Script
# Complete PyPI release pipeline - from testing to tagging to publishing

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get version from command line argument
VERSION="$1"

if [ -z "$VERSION" ]; then
    echo -e "${RED}❌ Error: Version number required${NC}"
    echo "Usage: $0 <version>"
    echo "Example: $0 0.5.1"
    exit 1
fi

echo -e "${BLUE}🚀 Starting PyPI release process for version ${VERSION}${NC}"

# Pre-Release Validation
echo -e "\n${YELLOW}📋 Pre-release validation...${NC}"

# Check for clean working directory
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${RED}❌ Uncommitted changes found. Commit or stash first.${NC}"
    exit 1
fi

# Check for test/temporary files that shouldn't be in main
echo -e "${BLUE}🔍 Checking for test/temporary files...${NC}"
UNWANTED_FILES=$(find . -maxdepth 1 \( \
    -name "*.py" -o \
    -name "*.log" -o \
    -name "*.tmp" -o \
    -name "*.md" -o \
    -name "*.txt" -o \
    -name "test_*" -o \
    -name "*_test.py" -o \
    -name "*_generated" -o \
    -name "*_reference" -o \
    -type d -name "*_Dev_Board" -o \
    -type d -name "*_generated" -o \
    -type d -name "*_reference" \
\) ! -path "./.git/*" ! -path "./.*" ! -name "README.md" ! -name "LICENSE" ! -name "CLAUDE.md" ! -name "Contributors.md" | grep -v "^\\./\\.")

if [ -n "$UNWANTED_FILES" ]; then
    echo -e "${YELLOW}⚠️  Found files/directories that may not belong in the main branch:${NC}"
    echo "$UNWANTED_FILES" | head -20
    if [ $(echo "$UNWANTED_FILES" | wc -l) -gt 20 ]; then
        echo "... and $(( $(echo "$UNWANTED_FILES" | wc -l) - 20 )) more files"
    fi
    echo
    read -p "These files appear to be test/temporary files. Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then 
        echo -e "${RED}❌ Release cancelled. Please clean up test files first.${NC}"
        echo -e "${BLUE}💡 Tip: Consider moving test files to tests/ or examples/ directories${NC}"
        exit 1
    fi
fi

# Validate version format
if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.-]+)?$ ]]; then
    echo -e "${RED}❌ Invalid version format. Use semantic versioning (e.g., 1.0.0)${NC}"
    exit 1
fi

# Fetch latest changes
echo -e "${BLUE}🔄 Fetching latest changes from origin...${NC}"
git fetch origin

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" != "develop" && "$CURRENT_BRANCH" != "main" ]]; then
    echo -e "${YELLOW}⚠️  Warning: Releasing from branch '$CURRENT_BRANCH'${NC}"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then exit 1; fi
fi

# Ensure branch is up-to-date
if [[ "$CURRENT_BRANCH" == "develop" ]]; then
    echo -e "${BLUE}🔄 Ensuring develop is up-to-date...${NC}"
    git pull origin develop || {
        echo -e "${RED}❌ Failed to pull latest develop${NC}"
        exit 1
    }
fi

# Test Core Functionality
echo -e "\n${YELLOW}🧪 Testing core functionality...${NC}"

# Test imports
uv run python -c "from circuit_synth import Circuit, Component, Net; print('✅ Core imports OK')" || {
    echo -e "${RED}❌ Import test failed${NC}"
    exit 1
}

echo -e "${GREEN}✅ Core functionality tests passed${NC}"

# Update Version
echo -e "\n${YELLOW}📝 Updating version to ${VERSION}...${NC}"

# Update pyproject.toml
sed -i.bak "s/^version = .*/version = \"$VERSION\"/" pyproject.toml

# Update __init__.py if it exists
INIT_FILE="src/circuit_synth/__init__.py"
if [ -f "$INIT_FILE" ]; then
    if grep -q "__version__" "$INIT_FILE"; then
        sed -i.bak "s/__version__ = .*/__version__ = \"$VERSION\"/" "$INIT_FILE"
    fi
fi

# Remove backup files
rm -f pyproject.toml.bak "$INIT_FILE.bak"

# Commit version changes
if ! git diff --quiet; then
    git add pyproject.toml "$INIT_FILE" 2>/dev/null || git add pyproject.toml
    git commit -m "🔖 Bump version to $VERSION"
    echo -e "${GREEN}✅ Version updated and committed${NC}"
else
    echo -e "${YELLOW}ℹ️  Version already up to date${NC}"
fi

# Run Tests
echo -e "\n${YELLOW}🧪 Running test suite...${NC}"

# Run pytest if tests exist
if [ -d "tests" ]; then
    uv run pytest tests/ -v --tb=short || {
        echo -e "${RED}❌ Tests failed${NC}"
        exit 1
    }
else
    echo -e "${YELLOW}⚠️  No tests directory found, skipping tests${NC}"
fi

echo -e "${GREEN}✅ All tests passed${NC}"

# Git Operations
echo -e "\n${YELLOW}🔀 Preparing release branches...${NC}"

# Push current branch changes
git push origin "$CURRENT_BRANCH"

# Merge to main (if on develop)
if [[ "$CURRENT_BRANCH" == "develop" ]]; then
    echo -e "${BLUE}🔄 Merging develop to main...${NC}"
    git checkout main
    git pull origin main
    git merge develop --no-ff -m "🚀 Release $VERSION: Merge develop to main"
    git push origin main
    echo -e "${GREEN}✅ Merged develop to main${NC}"
else
    git checkout main
    git pull origin main
fi

# Create and push tag
echo -e "${BLUE}🏷️  Creating release tag v${VERSION}...${NC}"
git tag -a "v$VERSION" -m "🚀 Release version $VERSION

Circuit-synth improvements and bug fixes.

Full changelog: https://github.com/circuit-synth/circuit-synth/releases"

git push origin "v$VERSION"
echo -e "${GREEN}✅ Tagged and pushed v${VERSION}${NC}"

# Build and Upload
echo -e "\n${YELLOW}📦 Building and uploading to PyPI...${NC}"

# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Additional cleanup of common temporary files
echo -e "${BLUE}🧹 Cleaning up temporary build artifacts...${NC}"
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name ".DS_Store" -delete 2>/dev/null || true

# Build distributions
echo -e "${BLUE}🏗️  Building distributions...${NC}"
uv run python -m build || {
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
}

# Check distributions
echo -e "${BLUE}📋 Built distributions:${NC}"
ls -la dist/

# Upload to PyPI
echo -e "${BLUE}📤 Uploading to PyPI...${NC}"
uv run python -m twine upload dist/* || {
    echo -e "${RED}❌ PyPI upload failed${NC}"
    exit 1
}

echo -e "${GREEN}✅ Successfully uploaded to PyPI${NC}"

# Create GitHub Release
if command -v gh >/dev/null 2>&1; then
    echo -e "\n${YELLOW}📝 Creating GitHub release...${NC}"
    
    # Get last tag for comparison
    LAST_TAG=$(git describe --tags --abbrev=0 HEAD~1 2>/dev/null || echo "")
    
    # Generate simple release notes
    if [ -n "$LAST_TAG" ]; then
        RELEASE_NOTES=$(git log --pretty=format:"- %s (%h)" "$LAST_TAG"..HEAD)
    else
        RELEASE_NOTES=$(git log --pretty=format:"- %s (%h)" --max-count=10)
    fi
    
    gh release create "v$VERSION" \
        --title "🚀 Release v$VERSION" \
        --notes "## What's Changed

$RELEASE_NOTES

## Installation

\`\`\`bash
pip install circuit-synth==$VERSION
# or
uv add circuit-synth==$VERSION
\`\`\`

**Full Changelog**: https://github.com/circuit-synth/circuit-synth/compare/$LAST_TAG...v$VERSION" \
        --latest || {
        echo -e "${YELLOW}⚠️  GitHub release creation failed (continuing)${NC}"
    }
    
    echo -e "${GREEN}✅ GitHub release created${NC}"
else
    echo -e "${YELLOW}⚠️  GitHub CLI not found - skipping GitHub release${NC}"
fi

# Return to original branch
git checkout "$CURRENT_BRANCH"

# Success!
echo -e "\n${GREEN}🎉 Release v${VERSION} completed successfully!${NC}"
echo -e "${BLUE}📦 Package available at: https://pypi.org/project/circuit-synth/${VERSION}/${NC}"
echo -e "${BLUE}🐙 GitHub release: https://github.com/circuit-synth/circuit-synth/releases/tag/v${VERSION}${NC}"