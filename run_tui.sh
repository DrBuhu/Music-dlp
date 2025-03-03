#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Music-dlp TUI Runner ===${NC}"

# Get project root directory
PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# Create temporary venv
TEMP_VENV="/tmp/music-dlp-tui-venv-$$"
echo -e "${YELLOW}Creating temporary virtual environment at ${TEMP_VENV}...${NC}"

python -m venv "$TEMP_VENV"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to create virtual environment. Install python-venv:${NC}"
    echo "sudo pacman -S python-virtualenv"
    exit 1
fi

# Activate venv
source "$TEMP_VENV/bin/activate"

# Make sure we're in the project root
cd "$PROJECT_DIR"

# Ensure styles directory exists
mkdir -p "$PROJECT_DIR/src/metadata_manager/styles"

# Check if CSS file exists, create if missing
CSS_FILE="$PROJECT_DIR/src/metadata_manager/styles/tui.css"
if [ ! -f "$CSS_FILE" ]; then
    echo -e "${YELLOW}CSS file not found. Creating it...${NC}"
    # Use the CSS content from the repository or create a minimal version
    cat > "$CSS_FILE" << 'EOL'
/* Music-dlp Textual TUI CSS */
App { background: #1f1f1f; color: #ffffff; }
Header { background: #333333; color: #00ff00; dock: top; height: 1; }
Footer { background: #333333; color: #00ff00; dock: bottom; height: 1; }
#sidebar { width: 25%; background: #252525; padding: 1; dock: left; }
#main_content { padding: 1; }
EOL
fi

# Set up Python path
export PYTHONPATH="${PROJECT_DIR}:${PROJECT_DIR}/src:$PYTHONPATH"

# Install required packages in venv
echo -e "${YELLOW}Installing TUI dependencies...${NC}"
pip install --quiet textual rich mutagen musicbrainzngs requests Pillow ytmusicapi spotipy

# Run the TUI
echo -e "${GREEN}Starting TUI interface...${NC}"
python -m src.metadata_manager.tui

# Cleanup
deactivate
rm -rf "$TEMP_VENV"

echo -e "\n${GREEN}TUI session completed. Temporary venv removed.${NC}"
