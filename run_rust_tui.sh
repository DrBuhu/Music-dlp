#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Music-dlp Rust TUI Runner ===${NC}"

# Get project root directory
PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# Check if cargo is installed
if ! command -v cargo &> /dev/null; then
    echo -e "${RED}Cargo not found. Please install Rust and Cargo:${NC}"
    echo "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    exit 1
fi

# Build and run the TUI
cd "$PROJECT_DIR/src/tui" || exit 1

echo -e "${YELLOW}Building Rust TUI...${NC}"
cargo build --release

if [ $? -ne 0 ]; then
    echo -e "${RED}Build failed${NC}"
    exit 1
fi

echo -e "${GREEN}Running TUI interface...${NC}"
PYTHONPATH="$PROJECT_DIR:$PROJECT_DIR/src" cargo run --release

echo -e "${GREEN}TUI session completed.${NC}"
