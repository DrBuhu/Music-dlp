"""Music file scanning and matching module."""
import os
import pathlib
from typing import Dict, List, Optional, Union
from rich import print as rprint

# Importaciones opcionales
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    rprint("[yellow]Warning: PIL/Pillow not installed. Image processing disabled.[/yellow]")

try:
    from fuzzywuzzy import fuzz
    HAS_FUZZY = True
except ImportError:
    HAS_FUZZY = False
    rprint("[yellow]Warning: Enhanced string matching disabled. Install fuzzywuzzy for better results.[/yellow]")

class MusicScanner:
    """Music file scanning and matching."""
    
    def __init__(self):
        """Initialize scanner."""
        self.supported_extensions = {'.mp3', '.flac', '.m4a', '.ogg', '.opus'}
        self.image_extensions = {'.jpg', '.jpeg', '.png'} if HAS_PIL else set()
        self.ignored_patterns = {'.*', 'Thumbs.db', 'desktop.ini', '.DS_Store'}
    
    def scan_directory(self, directory: Union[str, pathlib.Path], recursive: bool = False) -> Dict:
        """
        Scan directory for music files and artwork.
        
        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories
            
        Returns:
            Dict with music files and artwork info
        """
        directory = pathlib.Path(directory)
        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory}")
            
        result = {
            'music_files': [],
            'artwork': [] if HAS_PIL else None,
            'path': str(directory)
        }
        
        for entry in directory.iterdir():
            # Skip ignored files
            if any(entry.match(pattern) for pattern in self.ignored_patterns):
                continue
                
            if entry.is_file():
                ext = entry.suffix.lower()
                if ext in self.supported_extensions:
                    result['music_files'].append(str(entry))
                elif HAS_PIL and ext in self.image_extensions:
                    try:
                        with Image.open(entry) as img:
                            result['artwork'].append({
                                'path': str(entry),
                                'size': img.size
                            })
                    except Exception as e:
                        rprint(f"[yellow]Error reading image {entry}: {e}[/yellow]")
            
            elif recursive and entry.is_dir():
                try:
                    subdir_result = self.scan_directory(entry, recursive=True)
                    result['music_files'].extend(subdir_result['music_files'])
                    if HAS_PIL and subdir_result['artwork']:
                        result['artwork'].extend(subdir_result['artwork'])
                except Exception as e:
                    rprint(f"[yellow]Error scanning subdirectory {entry}: {e}[/yellow]")
        
        return result
    
    def find_best_artwork(self, artwork_list: List[Dict]) -> Optional[str]:
        """Find the best artwork file from a list based on common naming and size."""
        if not HAS_PIL or not artwork_list:
            return None
            
        # Score each artwork file
        scored_artwork = []
        for art in artwork_list:
            score = 0
            name = pathlib.Path(art['path']).stem.lower()
            
            # Prefer common artwork names
            common_names = {'cover', 'folder', 'album', 'artwork', 'front'}
            if any(common in name for common in common_names):
                score += 50
            
            # Prefer larger images (up to 1500x1500)
            width, height = art['size']
            if 500 <= width <= 1500 and 500 <= height <= 1500:
                score += 30
            elif width > 1500 or height > 1500:
                score += 10
            
            scored_artwork.append((score, art['path']))
        
        # Return highest scoring artwork
        return max(scored_artwork, key=lambda x: x[0])[1] if scored_artwork else None
    
    def get_matching_score(self, str1: str, str2: str) -> int:
        """Get string matching score using fuzzywuzzy if available."""
        if not str1 or not str2:
            return 0
            
        if HAS_FUZZY:
            return fuzz.ratio(str1.lower(), str2.lower())
        else:
            # Simple fallback
            return 100 if str1.lower() == str2.lower() else 0
