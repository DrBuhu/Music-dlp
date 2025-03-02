# Music Metadata Manager

A flexible system for managing music metadata from multiple sources.

## Features

✅ **Multiple Metadata Sources:**
  - MusicBrainz (primary source)
  - YouTube Music 
  - iTunes
  - Deezer
  - Spotify (coming soon)

✅ **Two Interface Options:**
  - CLI with rich formatting
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
   git clone <repository-url>
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

### GUI Interface:
```bash
poetry run metadata-manager-gui
```

## Metadata Sources Priority

1. MusicBrainz - Most reliable metadata
2. YouTube Music - Good metadata + artwork
3. iTunes - Reliable metadata
4. Deezer - High quality artwork
5. Spotify - Coming soon

## Development Status

🚧 Currently in active development:
- [x] Multiple source metadata search
- [x] CLI interface with rich formatting
- [x] Basic GUI with artwork preview
- [ ] Metadata application to files
- [ ] Batch processing
- [ ] Configuration system

