# Music Metadata Manager

A flexible system for managing music metadata from multiple sources.

## Features

✅ **Multiple Metadata Sources:**
  - MusicBrainz (primary source)
  - YouTube Music 
  - iTunes
  - Deezer
  - Spotify

✅ **Three Interface Options:**
  - CLI with rich formatting
  - TUI (Text User Interface) with interactive selection
  - GUI with artwork preview

✅ **Key Features:**
  - Album and track metadata search
  - Artwork download
  - Track listing
  - Multiple source comparison

## Installation

1. Requirements:
   - Python 3.8+
   - Poetry for dependency management

2. Installation steps:
   ```bash
   # Install Poetry if you don't have it
   curl -sSL https://install.python-poetry.org | python3 -
   
   # Clone and install
   git clone https://github.com/DrBuhu/Music-dlp.git
   cd Music-dlp
   poetry install
   ```

## Usage

### CLI Interface:
```bash
# Basic search
poetry run metadata-manager "/path/to/music/folder"

# Options
poetry run metadata-manager "/path/to/music/folder" --auto  # Automatic mode
poetry run metadata-manager "/path/to/music/folder" -r      # Recursive scan
```

### TUI Interface:
```bash
# Run the TUI (Text User Interface)
./run_tui.sh

# Keyboard shortcuts in TUI:
# q - Quit
# r - Refresh/scan current directory
# s - Search metadata for files in current directory
# a - Apply selected metadata
# Enter - Show details of selected metadata
```

### GUI Interface:
```bash
poetry run metadata-manager-gui
```

## TUI Usage Guide

1. **Navigation**: Use arrow keys to navigate directories in the left panel
2. **Selecting files**: Press 'r' to scan the current directory for music files
3. **Search metadata**: Press 's' to search for metadata from all providers
4. **Select results**: Click on any result in the tables or use arrow keys
5. **View details**: Selected metadata details will display at the bottom
6. **Apply metadata**: Press 'a' to apply the selected metadata to your files

## Metadata Sources Priority

1. MusicBrainz - Most reliable metadata
2. YouTube Music - Good metadata + artwork
3. iTunes - Reliable metadata
4. Deezer - High quality artwork
5. Spotify - Additional source

## Development Status

🚧 Currently in active development:
- [x] Multiple source metadata search
- [x] CLI interface with rich formatting
- [x] TUI with interactive navigation and selection
- [x] Basic GUI with artwork preview
- [ ] Metadata application to files
- [ ] Batch processing
- [ ] Configuration system

