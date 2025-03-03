"""Spotify metadata provider."""
from typing import Dict, List
import requests
from rich import print as rprint

from .provider_base import MetadataProvider
from ...core.utils import string_similarity

class SpotifyProvider(MetadataProvider):
    """Spotify metadata provider."""
    
    def __init__(self):
        """Initialize provider."""
        self.session = requests.Session()
        self.base_url = "https://api.spotify.com/v1"
        self.headers = {
            'Authorization': 'Bearer BQB5veg3Vc4XjEzSCc3t1LJFkdH-PVNpSbBMRQM7VU1PL9nIaO2TKKDFu6z0Qj9uMmbhZhlewWCuZ3qvpGRLNEFM0YWwVPChS3frMbv2zM4rRyF0p7fEspRNOnxlLqpt4-DOHJSRDRIj',
            'Accept': 'application/json'
        }
        rprint("[cyan]Spotify provider initialized[/cyan]")
    
    @property
    def name(self) -> str:
        return "spotify"
    
    def _get_token(self) -> None:
        """Get a new token if needed."""
        try:
            response = requests.get("https://open.spotify.com")
            if 'accessToken' in response.text:
                import re
                token = re.search(r'accessToken":"(.*?)"', response.text)
                if token:
                    self.headers['Authorization'] = f'Bearer {token.group(1)}'
        except:
            pass
    
    def search_track(self, title: str, artist: str = None) -> List[Dict]:
        """Search for a track."""
        try:
            self._get_token()  # Refresh token if needed
            
            query = f"{title}"
            if artist:
                query = f"track:{title} artist:{artist}"
                
            response = self.session.get(
                f"{self.base_url}/search",
                params={'q': query, 'type': 'track', 'limit': 5},
                headers=self.headers
            )
            
            if response.status_code == 401:
                self._get_token()  # Try refresh token
                response = self.session.get(
                    f"{self.base_url}/search",
                    params={'q': query, 'type': 'track', 'limit': 5},
                    headers=self.headers
                )
            
            data = response.json()
            tracks = data.get('tracks', {}).get('items', [])
            
            parsed = []
            for track in tracks:
                title_score = string_similarity(title, track['name'])
                artist_score = string_similarity(artist, track['artists'][0]['name']) if artist else 100
                
                if title_score > 60 and artist_score > 60:
                    parsed.append(self.format_result({
                        'title': track['name'],
                        'artist': track['artists'][0]['name'],
                        'album': track['album']['name'],
                        'year': track['album']['release_date'][:4],
                        'score': (title_score + artist_score) / 2
                    }))
            
            return sorted(parsed, key=lambda x: x.get('score', 0), reverse=True)
            
        except Exception as e:
            rprint(f"[yellow]Spotify search error: {str(e)}[/yellow]")
            return []
    
    def search_album(self, album: str, artist: str = None) -> List[Dict]:
        """Search for an album."""
        try:
            query = f"{artist} {album}" if artist else album
            response = self.session.get(
                self.base_url,
                params={'q': query, 'type': 'album'},
                headers=self.headers
            )
            
            data = response.json()
            albums = data.get('albums', {}).get('items', [])
            
            parsed = []
            for album_data in albums[:5]:
                album_score = string_similarity(album, album_data.get('name', ''))
                artist_score = string_similarity(artist, album_data.get('artists', [{}])[0].get('name', '')) if artist else 100
                
                if album_score > 60 and artist_score > 60:
                    tracks = []
                    try:
                        album_tracks = album_data.get('tracks', {}).get('items', [])
                        for i, track in enumerate(album_tracks, 1):
                            tracks.append({
                                'title': track['name'],
                                'position': str(i)
                            })
                    except:
                        pass
                    
                    parsed.append(self.format_result({
                        'title': album_data['name'],
                        'artist': album_data['artists'][0]['name'],
                        'year': album_data['release_date'][:4],
                        'tracks': tracks,
                        'score': (album_score + artist_score) / 2
                    }, "album"))
            
            return sorted(parsed, key=lambda x: x.get('score', 0), reverse=True)
            
        except Exception as e:
            rprint(f"[yellow]Spotify search error: {str(e)}[/yellow]")
            return []
