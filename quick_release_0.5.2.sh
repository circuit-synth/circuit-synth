#!/bin/bash
set -e

# Commit version bump
git add -A
git commit -m "🔖 Bump version to 0.5.2"
git push origin develop

# Tag and push
git tag -a "v0.5.2" -m "Release v0.5.2 - Simplified cs-new-pcb command"
git push origin "v0.5.2"

# Build and upload
rm -rf dist/ build/
uv run python -m build
uv run python -m twine upload dist/*

# Create GitHub release
gh release create "v0.5.2" \
    --title "🚀 Release v0.5.2 - Even Simpler cs-new-pcb" \
    --notes "## What's Changed

### ✨ Major Improvement

**cs-new-pcb now works without any arguments!**

The command automatically uses your directory name as the project name:
- \`my-awesome-pcb\` → \"My Awesome Pcb\" 
- \`sensor_board\` → \"Sensor Board\"
- \`PowerSupply\` → \"PowerSupply\"

### 📋 Usage

\`\`\`bash
# Old way (still works)
cs-new-pcb \"My Project Name\"

# New way - no arguments needed!
cs-new-pcb

# Override if needed
cs-new-pcb --name \"Custom Name\"
\`\`\`

### 🔧 Complete Workflow Example

\`\`\`bash
# Create a new project
uv init my-awesome-sensor
cd my-awesome-sensor

# Install circuit-synth
uv add circuit-synth

# Transform into a PCB project (no arguments!)
uv run cs-new-pcb

# Start designing
cd circuit-synth
uv run python main.py
\`\`\`

The command automatically infers \"My Awesome Sensor\" as your project name from the directory name.

### 🐛 Also in this release

- Fixed PyPI distribution of v0.5.1

## Installation

\`\`\`bash
pip install circuit-synth==0.5.2
# or
uv add circuit-synth==0.5.2
\`\`\`

**Full Changelog**: https://github.com/circuit-synth/circuit-synth/compare/v0.5.1...v0.5.2" \
    --latest

echo "✅ Released v0.5.2!"