from typing import Dict, List
import requests
from bs4 import BeautifulSoup
from rich import print as rprint
from .metadata_manager import MetadataProvider
from .utils import string_similarity

class WebMetadataProvider(MetadataProvider):
    """Web scraping fallback provider."""
    
    def __init__(self):
        self.session = requests.Session()
        rprint("[cyan]Web provider initialized[/cyan]")
    
    @property
    def name(self) -> str:
        return "web"
    
    def search_track(self, title: str, artist: str = None) -> List[Dict]:
        """Basic web search for track info."""
        try:
            # For now, return empty since we're using other providers
            return []
        except Exception as e:
            rprint(f"[red]Web search error: {str(e)}[/red]")
            return []
    
    def search_album(self, album: str, artist: str = None) -> List[Dict]:
        """Basic web search for album info."""
        try:
            # For now, return empty since we're using other providers
            return []
        except Exception as e:
            rprint(f"[red]Web search error: {str(e)}[/red]")
            return []
