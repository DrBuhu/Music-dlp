from typing import Dict, List
import requests
from rich import print as rprint

from .provider_base import MetadataProvider
from ...core.utils import string_similarity  # Añadir import correcto

class DeezerProvider(MetadataProvider):
    """Deezer metadata provider using public API."""
    
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://api.deezer.com"
        rprint("[cyan]Deezer provider initialized[/cyan]")
    
    @property
    def name(self) -> str:
        return "deezer"
    
    def search_track(self, title: str, artist: str = None) -> List[Dict]:
        try:
            query = f"{artist} {title}" if artist else title
            response = self.session.get(
                f"{self.base_url}/search/track",
                params={'q': query, 'limit': 5}
            )
            response.raise_for_status()
            data = response.json()
            
            parsed = []
            for track in data.get('data', []):
                title_score = string_similarity(title, track.get('title', ''))
                artist_score = string_similarity(artist, track['artist']['name']) if artist else 100
                
                if title_score > 60 and artist_score > 60:
                    # Get highest quality artwork
                    artwork_url = track['album'].get('cover_xl') or track['album'].get('cover_big')
                    
                    parsed.append(self.format_result({
                        'title': track['title'],
                        'artist': track['artist']['name'],
                        'album': track['album']['title'],
                        'year': str(track.get('album', {}).get('release_date', ''))[:4],  # Extraer año
                        'tracks': self._get_album_tracks(track['album']['id']) if track.get('album') else [],  # Get tracks
                        'score': (title_score + artist_score) / 2,
                        'artwork_url': artwork_url,
                        'deezer_id': track['id']
                    }))
            
            return sorted(parsed, key=lambda x: x.get('score', 0), reverse=True)
            
        except Exception as e:
            rprint(f"[red]Deezer track search error: {str(e)}[/red]")
            return []
    
    def search_album(self, album: str, artist: str = None) -> List[Dict]:
        try:
            query = f"{artist} {album}" if artist else album
            response = self.session.get(
                f"{self.base_url}/search/album",
                params={'q': query, 'limit': 5}
            )
            response.raise_for_status()
            data = response.json()
            
            parsed = []
            for album_data in data.get('data', []):
                album_score = string_similarity(album, album_data.get('title', ''))
                artist_score = string_similarity(artist, album_data['artist']['name']) if artist else 100
                
                if album_score > 60 and artist_score > 60:
                    # Get full album info to get release date and tracks
                    album_info = self.session.get(f"{self.base_url}/album/{album_data['id']}").json()
                    tracks = self._get_album_tracks(album_data['id'])
                    release_date = album_info.get('release_date', '').split('-')[0]  # Get year
                    
                    # Get highest quality artwork
                    artwork_url = album_data.get('cover_xl') or album_data.get('cover_big')
                    
                    parsed.append(self.format_result({
                        'title': album_data['title'],
                        'artist': album_data['artist']['name'],
                        'year': release_date,  # Use extracted year
                        'tracks': tracks,
                        'score': (album_score + artist_score) / 2,
                        'artwork_url': artwork_url,
                        'deezer_id': album_data['id']
                    }, "album"))
            
            return sorted(parsed, key=lambda x: x.get('score', 0), reverse=True)
            
        except Exception as e:
            rprint(f"[red]Deezer album search error: {str(e)}[/red]")
            return []
    
    def _get_album_tracks(self, album_id: int) -> List[Dict]:
        """Get tracks for an album."""
        try:
            response = self.session.get(f"{self.base_url}/album/{album_id}/tracks")
            response.raise_for_status()
            data = response.json()
            
            tracks = []
            for i, track in enumerate(data.get('data', []), 1):
                tracks.append({
                    'title': track['title'],
                    'position': str(i),
                    'duration': str(track.get('duration', 0))
                })
            
            return tracks
            
        except Exception as e:
            rprint(f"[red]Error getting album tracks: {str(e)}[/red]")
            return []
