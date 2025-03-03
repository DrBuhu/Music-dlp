"""Music file scanner module."""
import os
import pathlib
from typing import Dict, List, Optional, Union
from rich import print as rprint
import mutagen

class FileScanner:
    """Scanner for music files and their metadata."""
    
    SUPPORTED_EXTENSIONS = {'.mp3', '.flac', '.m4a', '.ogg', '.opus', '.wma'}
    
    def __init__(self):
        """Initialize the scanner."""
        self.ignored_patterns = {'.*', 'Thumbs.db', 'desktop.ini', '.DS_Store'}
    
    def scan_directory(self, directory: Union[str, pathlib.Path], recursive: bool = False) -> List[Dict]:
        """
        Scan a directory for music files.
        
        Args:
            directory: Path to scan
            recursive: Whether to scan subdirectories
            
        Returns:
            List of dictionaries containing file info and metadata
        """
        try:
            directory = pathlib.Path(directory).resolve()
            if not directory.is_dir():
                rprint(f"[red]Error: {directory} is not a directory[/red]")
                return []
                
            rprint(f"[cyan]Scanning directory: {directory}[/cyan]")
            
            files = []
            for file in self._scan_path(directory, recursive):
                try:
                    metadata = self._extract_metadata(file)
                    if metadata:
                        files.append({
                            'path': str(file),
                            'filename': file.name,
                            'metadata': metadata
                        })
                except Exception as e:
                    rprint(f"[yellow]Error reading {file.name}: {str(e)}[/yellow]")
            
            rprint(f"[green]Found {len(files)} music files[/green]")
            return files
            
        except Exception as e:
            rprint(f"[red]Error scanning directory: {str(e)}[/red]")
            return []
    
    def _scan_path(self, path: pathlib.Path, recursive: bool) -> List[pathlib.Path]:
        """Yield music files from path."""
        files = []
        try:
            for entry in path.iterdir():
                # Skip hidden files and ignored patterns
                if any(entry.match(pattern) for pattern in self.ignored_patterns):
                    continue
                
                if entry.is_file() and entry.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    files.append(entry)
                elif recursive and entry.is_dir():
                    files.extend(self._scan_path(entry, recursive))
        except Exception as e:
            rprint(f"[yellow]Error accessing {path}: {str(e)}[/yellow]")
            
        return files
    
    def _extract_metadata(self, file_path: pathlib.Path) -> Dict:
        """Extract metadata from a music file."""
        try:
            audio = mutagen.File(file_path)
            if not audio:
                return {}
                
            # Extract basic metadata
            metadata = {}
            
            # Handle different tag formats
            if isinstance(audio.tags, mutagen.id3.ID3):
                # ID3 tags (MP3)
                tag_mapping = {
                    'title': ['TIT2'],
                    'artist': ['TPE1', 'TPE2'],
                    'album': ['TALB'],
                    'date': ['TDRC', 'TYER'],
                    'track': ['TRCK'],
                    'genre': ['TCON'],
                    'album_artist': ['TPE2'],
                }
                
                for key, tag_names in tag_mapping.items():
                    for tag in tag_names:
                        if tag in audio:
                            metadata[key] = audio[tag].text
                            break
                    
            elif hasattr(audio, 'tags') and audio.tags:
                # Common tag format (FLAC, OGG, etc.)
                tag_mapping = {
                    'title': ['title'],
                    'artist': ['artist'],
                    'album': ['album'],
                    'date': ['date', 'year'],
                    'track': ['tracknumber'],
                    'genre': ['genre'],
                    'album_artist': ['albumartist'],
                }
                
                for key, tag_names in tag_mapping.items():
                    for tag in tag_names:
                        if tag in audio.tags:
                            metadata[key] = audio.tags[tag]
                            break
            
            # Add file info
            metadata['duration'] = str(int(audio.info.length)) if hasattr(audio.info, 'length') else '0'
            metadata['bitrate'] = str(getattr(audio.info, 'bitrate', 0))
            metadata['sample_rate'] = str(getattr(audio.info, 'sample_rate', 0))
            
            return metadata
            
        except Exception as e:
            rprint(f"[yellow]Error extracting metadata from {file_path.name}: {str(e)}[/yellow]")
            return {}
