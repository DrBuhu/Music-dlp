#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Music-dlp GUI Runner ===${NC}"

# Get project root directory
PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# Create temporary venv
TEMP_VENV="/tmp/music-dlp-gui-venv-$$"
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
echo -e "${YELLOW}Installing GUI dependencies...${NC}"
pip install --quiet rich mutagen musicbrainzngs requests Pillow ytmusicapi spotipy tk

# Run the GUI
echo -e "${GREEN}Starting GUI interface...${NC}"
python -m src.metadata_manager.gui

# Cleanup
deactivate
rm -rf "$TEMP_VENV"

echo -e "\n${GREEN}GUI session completed. Temporary venv removed.${NC}"
