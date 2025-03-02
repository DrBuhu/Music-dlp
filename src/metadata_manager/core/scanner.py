import re
from pathlib import Path
from typing import List, Dict, Optional
from mutagen import File
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
import requests
from io import BytesIO
from PIL import Image

try:
    from fuzzywuzzy import fuzz
    HAS_FUZZY = True
except ImportError:
    HAS_FUZZY = False
    print("Warning: Enhanced string matching disabled. Install fuzzywuzzy for better results.")

def simple_string_compare(a: str, b: str) -> float:
    """Simple fallback string comparison."""
    a, b = a.lower(), b.lower()
    if a == b:
        return 100.0
    if a in b or b in a:
        return 75.0
    return 0.0

def string_similarity(a: str, b: str) -> float:
    """Calculate string similarity using best available method."""
    if HAS_FUZZY:
        return fuzz.ratio(a.lower(), b.lower())
    return simple_string_compare(a, b)

class MusicScanner:
    """Scans and analyzes local music files."""
    
    SUPPORTED_FORMATS = {'.mp3', '.flac', '.wav', '.m4a', '.ogg'}
    
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
    
    def scan_directory(self) -> List[Dict]:
        """Scan directory for music files and extract their metadata."""
        music_files = []
        
        for file_path in self.root_dir.rglob('*'):
            if file_path.suffix.lower() in self.SUPPORTED_FORMATS:
                metadata = self.extract_metadata(file_path)
                if metadata:
                    music_files.append(metadata)
        
        return music_files
    
    def _extract_from_filename(self, filepath: Path) -> Dict[str, list]:
        """Extract metadata from filename and path structure."""
        metadata = {'title': [''], 'artist': [''], 'album': [''], 'date': ['']}
        
        # Try to extract from directory structure first
        # Example: Artist/Year - Album/XX - Title.mp3
        try:
            parts = filepath.parts
            if len(parts) >= 3:
                # Artist is usually the first folder
                metadata['artist'] = [parts[-3]]
                
                # Album folder might contain year
                album_dir = parts[-2]
                year_match = re.search(r'(\d{4})', album_dir)
                if year_match:
                    metadata['date'] = [year_match.group(1)]
                    # Clean album name
                    album = re.sub(r'\[.*?\]|\(.*?\)|\d{4}', '', album_dir).strip(' -')
                    metadata['album'] = [album]
                
                # Extract from filename
                filename = filepath.stem
                # Remove leading numbers and separators
                title = re.sub(r'^\d+[\s.-]+', '', filename)
                metadata['title'] = [title]
        except Exception as e:
            print(f"Error extracting from filename: {e}")
        
        return metadata

    def _merge_metadata(self, file_meta: Dict, filename_meta: Dict) -> Dict:
        """Merge file metadata with filename-extracted metadata, preferring file metadata."""
        merged = {}
        
        for key in ['title', 'artist', 'album', 'date']:
            file_value = file_meta.get(key, [''])[0]
            filename_value = filename_meta.get(key, [''])[0]
            
            # Use file metadata if it exists and seems valid
            if file_value and file_value != '—':
                merged[key] = [file_value]
            # Otherwise use filename metadata
            elif filename_value:
                merged[key] = [filename_value]
            # Fallback to empty
            else:
                merged[key] = ['—']
        
        return merged

    def extract_metadata(self, file_path: Path) -> Optional[Dict]:
        """Extract metadata from file and filename."""
        try:
            # Get metadata from file first
            file_metadata = self._extract_file_metadata(file_path)
            
            # Get metadata from filename/path
            filename_metadata = self._extract_from_filename(file_path)
            
            # Extract artwork
            artwork = self._extract_artwork(file_path)
            
            # Merge both sources
            metadata = self._merge_metadata(
                file_metadata or {},
                filename_metadata
            )
            
            return {
                'path': str(file_path),
                'filename': file_path.name,
                'format': file_path.suffix[1:],
                'metadata': metadata,
                'artwork': artwork
            }
            
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            return None

    def _extract_file_metadata(self, file_path: Path) -> Optional[Dict]:
        """Extract metadata from a music file."""
        try:
            metadata = {}
            
            if file_path.suffix.lower() == '.flac':
                audio = FLAC(file_path)
                if audio:
                    metadata = {
                        'title': [audio.get('title', [''])[0]],
                        'artist': [audio.get('artist', [''])[0]],
                        'album': [audio.get('album', [''])[0]],
                        'date': [audio.get('date', [''])[0]],
                        'tracknumber': [audio.get('tracknumber', [''])[0]]
                    }
            else:
                audio = File(file_path, easy=True)
                if isinstance(audio, EasyID3):
                    metadata = dict(audio)
                elif audio:
                    # Try to get basic metadata for non-ID3 files
                    metadata = {
                        'title': [audio.tags.get('title', [''])[0] if audio.tags else ''],
                        'artist': [audio.tags.get('artist', [''])[0] if audio.tags else ''],
                        'album': [audio.tags.get('album', [''])[0] if audio.tags else ''],
                        'date': [audio.tags.get('date', [''])[0] if audio.tags else '']
                    }
            
            return metadata
            
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            return None

    def _extract_artwork(self, file_path: Path) -> Optional[Image.Image]:
        """Extract artwork from music file."""
        try:
            audio = File(file_path)
            if audio is None:
                return None
                
            # FLAC artwork
            if isinstance(audio, FLAC):
                if audio.pictures:
                    pic = audio.pictures[0]
                    return Image.open(BytesIO(pic.data))
            
            # MP3 artwork
            elif hasattr(audio, 'tags'):
                tags = audio.tags
                # ID3 APIC frame
                if hasattr(tags, 'getall'):
                    apic_frames = tags.getall('APIC')
                    if apic_frames:
                        return Image.open(BytesIO(apic_frames[0].data))
                # MP4/M4A artwork
                elif hasattr(audio, 'pictures'):
                    if audio.pictures:
                        return Image.open(BytesIO(audio.pictures[0].data))
            
            return None
            
        except Exception as e:
            print(f"Error extracting artwork: {str(e)}")
            return None
