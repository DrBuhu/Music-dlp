#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Music-dlp CLI Runner ===${NC}"

# Get project root directory
PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# Create temporary venv
TEMP_VENV="/tmp/music-dlp-venv-$$"
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
cd "$(dirname "$0")"

# Set up Python path
export PYTHONPATH="$(pwd):$(pwd)/src:$PYTHONPATH"

# Install required packages in venv
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install --quiet rich mutagen spotipy ytmusicapi musicbrainzngs requests Pillow beautifulsoup4

if [ $# -eq 0 ]; then
    echo -e "${YELLOW}Usage: $0 <music_directory> [-r] [-d]${NC}"
    echo "Options:"
    echo "  -r         Recursive scan"
    echo "  -d         Show details"
    echo "  -a         Auto mode (no prompts)"
    echo "  -p <list>  Specify providers (comma-separated)"
    echo "Example:"
    echo "  $0 ~/Music/some_album -r -d"
    deactivate
    rm -rf "$TEMP_VENV"
    exit 1
fi

# Run the CLI with arguments
echo -e "${GREEN}Scanning directory: $1${NC}"
python -c "
import sys
sys.path.insert(0, '${PROJECT_DIR}')
sys.path.insert(0, '${PROJECT_DIR}/src')
from src.metadata_manager.cli import main
sys.argv = ['cli.py'] + sys.argv[1:]
main()
" "$@"

# Cleanup
deactivate
rm -rf "$TEMP_VENV"

echo -e "\n${GREEN}Test completed. Temporary venv removed.${NC}"
