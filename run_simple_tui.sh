#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Music-dlp Simple TUI Runner ===${NC}"

# Get project root directory
PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# Create temporary venv
TEMP_VENV="/tmp/music-dlp-simple-tui-venv-$$"
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

# Set up Python path
export PYTHONPATH="${PROJECT_DIR}:${PROJECT_DIR}/src:$PYTHONPATH"

# Install required packages in venv
echo -e "${YELLOW}Installing TUI dependencies...${NC}"
pip install --quiet rich mutagen musicbrainzngs requests spotipy ytmusicapi

# Run the TUI
echo -e "${GREEN}Starting Simple TUI interface...${NC}"
python -m src.metadata_manager.simple_tui

# Cleanup
deactivate
rm -rf "$TEMP_VENV"

echo -e "\n${GREEN}TUI session completed. Temporary venv removed.${NC}"
