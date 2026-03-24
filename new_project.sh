#!/usr/bin/env bash
# Create a new circuit-synth project using the local fork.
# Usage: ./new_project.sh <project-name>

set -euo pipefail

CIRCUIT_SYNTH_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ $# -lt 1 ]; then
    echo "Usage: $(basename "$0") <project-name>"
    exit 1
fi

PROJECT_NAME="$1"

if [ -d "$PROJECT_NAME" ]; then
    echo "Error: directory '$PROJECT_NAME' already exists"
    exit 1
fi

uv init "$PROJECT_NAME"
cd "$PROJECT_NAME"
uv add circuit-synth

# Point circuit-synth to the local fork (editable)
# Insert [tool.uv.sources] before the first [tool.*] section or at end of file
python3 -c "
import re
from pathlib import Path

pyproject = Path('pyproject.toml')
content = pyproject.read_text()

sources_block = '''
[tool.uv.sources]
circuit-synth = { path = \"$CIRCUIT_SYNTH_DIR\", editable = true }
'''

# Insert before existing [tool.*] section if present, otherwise append
match = re.search(r'^\[tool\.', content, re.MULTILINE)
if match:
    content = content[:match.start()] + sources_block.strip() + '\n\n' + content[match.start():]
else:
    content = content.rstrip() + '\n' + sources_block.strip() + '\n'

pyproject.write_text(content)
"

uv sync
uv run cs-new-project
