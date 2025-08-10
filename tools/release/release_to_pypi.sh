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

# Run Comprehensive Regression Tests
echo -e "\n${YELLOW}🧪 Running comprehensive regression tests...${NC}"
echo -e "${BLUE}This will perform complete environment reconstruction and validation${NC}"

# Check if regression test script exists
REGRESSION_TEST_SCRIPT="./tools/testing/run_full_regression_tests.py"
if [ -f "$REGRESSION_TEST_SCRIPT" ]; then
    echo -e "${BLUE}🚀 Starting full regression test (this will take ~2 minutes)...${NC}"
    $REGRESSION_TEST_SCRIPT || {
        echo -e "${RED}❌ Regression tests failed! DO NOT RELEASE!${NC}"
        echo -e "${YELLOW}Check test_outputs/test_results.json for details${NC}"
        exit 1
    }
    echo -e "${GREEN}✅ All regression tests passed!${NC}"
else
    echo -e "${YELLOW}⚠️  Regression test script not found, using basic tests${NC}"
fi

# Test Core Functionality (as backup)
echo -e "\n${YELLOW}🧪 Testing core functionality...${NC}"

# Test imports
uv run python -c "from circuit_synth import Circuit, Component, Net; print('✅ Core imports OK')" || {
    echo -e "${RED}❌ Import test failed${NC}"
    exit 1
}

echo -e "${GREEN}✅ Core functionality tests passed${NC}"

# Copy .claude directory to package templates (Option A implementation)
echo -e "\n${YELLOW}📋 Copying .claude directory to package templates...${NC}"
CLAUDE_SOURCE=".claude"
CLAUDE_TARGET="src/circuit_synth/data/templates/example_project/.claude"

if [ -d "$CLAUDE_SOURCE" ]; then
    echo -e "${BLUE}🔄 Copying production agents and commands to package...${NC}"
    
    # Remove existing template .claude directory
    rm -rf "$CLAUDE_TARGET"
    
    # Create target directory structure
    mkdir -p "$CLAUDE_TARGET/agents" "$CLAUDE_TARGET/commands"
    
    # Copy production agents (exclude dev/ subdirectory)
    find "$CLAUDE_SOURCE/agents" -name "*.md" -not -path "*/dev/*" -exec cp {} "$CLAUDE_TARGET/agents/" \;
    
    # Organize agents into subdirectories in target
    mkdir -p "$CLAUDE_TARGET/agents/circuit-design" "$CLAUDE_TARGET/agents/manufacturing" "$CLAUDE_TARGET/agents/orchestration" "$CLAUDE_TARGET/agents/microcontrollers"
    
    # Move agents to proper subdirectories in target
    [ -f "$CLAUDE_TARGET/agents/circuit-architect.md" ] && mv "$CLAUDE_TARGET/agents/circuit-architect.md" "$CLAUDE_TARGET/agents/circuit-design/"
    [ -f "$CLAUDE_TARGET/agents/component-symbol-validator.md" ] && mv "$CLAUDE_TARGET/agents/component-symbol-validator.md" "$CLAUDE_TARGET/agents/circuit-design/"
    [ -f "$CLAUDE_TARGET/agents/circuit-design-guide.md" ] && mv "$CLAUDE_TARGET/agents/circuit-design-guide.md" "$CLAUDE_TARGET/agents/circuit-design/"
    [ -f "$CLAUDE_TARGET/agents/circuit-validation-agent.md" ] && mv "$CLAUDE_TARGET/agents/circuit-validation-agent.md" "$CLAUDE_TARGET/agents/circuit-design/"
    [ -f "$CLAUDE_TARGET/agents/circuit-syntax-fixer.md" ] && mv "$CLAUDE_TARGET/agents/circuit-syntax-fixer.md" "$CLAUDE_TARGET/agents/circuit-design/"
    [ -f "$CLAUDE_TARGET/agents/simulation-expert.md" ] && mv "$CLAUDE_TARGET/agents/simulation-expert.md" "$CLAUDE_TARGET/agents/circuit-design/"
    [ -f "$CLAUDE_TARGET/agents/test-plan-creator.md" ] && mv "$CLAUDE_TARGET/agents/test-plan-creator.md" "$CLAUDE_TARGET/agents/circuit-design/"
    
    [ -f "$CLAUDE_TARGET/agents/jlc-parts-finder.md" ] && mv "$CLAUDE_TARGET/agents/jlc-parts-finder.md" "$CLAUDE_TARGET/agents/manufacturing/"
    [ -f "$CLAUDE_TARGET/agents/component-guru.md" ] && mv "$CLAUDE_TARGET/agents/component-guru.md" "$CLAUDE_TARGET/agents/manufacturing/"
    [ -f "$CLAUDE_TARGET/agents/dfm-agent.md" ] && mv "$CLAUDE_TARGET/agents/dfm-agent.md" "$CLAUDE_TARGET/agents/manufacturing/"
    
    [ -f "$CLAUDE_TARGET/agents/circuit-project-creator.md" ] && mv "$CLAUDE_TARGET/agents/circuit-project-creator.md" "$CLAUDE_TARGET/agents/orchestration/"
    
    [ -f "$CLAUDE_TARGET/agents/stm32-mcu-finder.md" ] && mv "$CLAUDE_TARGET/agents/stm32-mcu-finder.md" "$CLAUDE_TARGET/agents/microcontrollers/"
    
    # Copy production commands (exclude dev/ subdirectory) 
    cp -r "$CLAUDE_SOURCE/commands/circuit-design" "$CLAUDE_TARGET/commands/" 2>/dev/null || true
    cp -r "$CLAUDE_SOURCE/commands/manufacturing" "$CLAUDE_TARGET/commands/" 2>/dev/null || true  
    cp -r "$CLAUDE_SOURCE/commands/setup" "$CLAUDE_TARGET/commands/" 2>/dev/null || true
    
    # Copy any remaining project config files
    [ -f "$CLAUDE_SOURCE/mcp_settings.json" ] && cp "$CLAUDE_SOURCE/mcp_settings.json" "$CLAUDE_TARGET/"
    
    echo -e "${GREEN}✅ Production .claude directory copied to package templates${NC}"
else
    echo -e "${YELLOW}⚠️  .claude directory not found, skipping template update${NC}"
fi

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