"""Base class for metadata providers."""
from abc import ABC, abstractmethod
from typing import Dict, List

class MetadataProvider(ABC):
    """Base class for metadata providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass
    
    @abstractmethod
    def search_track(self, title: str, artist: str = None) -> List[Dict]:
        """Search for a track."""
        pass
    
    @abstractmethod
    def search_album(self, album: str, artist: str = None) -> List[Dict]:
        """Search for an album."""
        pass
    
    def format_result(self, data: Dict, type: str = "track") -> Dict:
        """Format provider-specific data to common format."""
        formatted = {
            'title': data.get('title', ''),
            'artist': data.get('artist', ''),
            'album': data.get('album', ''),
            'year': data.get('year', ''),
            'tracks': data.get('tracks', []),
            'score': data.get('score', 0),  # Ensure score is included
            'provider': data.get('provider', self.name),  # Use provided or default name
            'raw_data': data
        }
        return formatted
