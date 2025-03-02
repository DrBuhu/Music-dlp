from typing import Dict, List
import requests
from rich import print as rprint
from ...core.metadata_manager import MetadataProvider
from ...core.utils import string_similarity

class ITunesProvider(MetadataProvider):
    """iTunes/Apple Music metadata provider."""
    
    def __init__(self):
        self.session = requests.Session()
        self.lookup_url = "https://itunes.apple.com/lookup"
        self.search_url = "https://itunes.apple.com/search"
        rprint("[cyan]iTunes provider initialized[/cyan]")
    
    @property
    def name(self) -> str:
        return "itunes"
    
    def search_track(self, title: str, artist: str = None) -> List[Dict]:
        try:
            query = f"{artist} {title}" if artist else title
            params = {
                'term': query,
                'media': 'music',
                'entity': 'song',
                'limit': 5
            }
            
            response = self.session.get(self.search_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            parsed = []
            for result in results:
                title_score = string_similarity(title, result.get('trackName', ''))
                artist_score = string_similarity(artist, result.get('artistName', '')) if artist else 100
                
                if title_score > 60 and artist_score > 60:
                    parsed.append(self.format_result({
                        'title': result.get('trackName', ''),
                        'artist': result.get('artistName', ''),
                        'album': result.get('collectionName', ''),
                        'year': str(result.get('releaseDate', ''))[:4],
                        'tracks': [],
                        'score': (title_score + artist_score) / 2,
                        'artwork_url': result.get('artworkUrl100', '').replace('100x100', '600x600')
                    }))
            
            return sorted(parsed, key=lambda x: x.get('score', 0), reverse=True)
        
        except Exception as e:
            rprint(f"[red]iTunes error: {str(e)}[/red]")
            return []
    
    def search_album(self, album: str, artist: str = None) -> List[Dict]:
        try:
            # First search for the album
            query = f"{artist} {album}" if artist else album
            params = {
                'term': query,
                'media': 'music',
                'entity': 'album',
                'limit': 5
            }
            
            response = self.session.get(self.search_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for album_data in data.get('results', []):
                album_score = string_similarity(album, album_data.get('collectionName', ''))
                artist_score = string_similarity(artist, album_data.get('artistName', '')) if artist else 100
                
                if album_score > 60 and artist_score > 60:
                    # Get tracks for this album
                    tracks = self._get_tracks_for_album(album_data.get('collectionId'))
                    
                    if tracks:  # Only include albums with tracks
                        results.append(self.format_result({
                            'title': album_data.get('collectionName', ''),
                            'artist': album_data.get('artistName', ''),
                            'year': str(album_data.get('releaseDate', ''))[:4],
                            'tracks': tracks,
                            'score': (album_score + artist_score) / 2,
                            'artwork_url': album_data.get('artworkUrl100', '').replace('100x100', '600x600')
                        }, "album"))
            
            return sorted(results, key=lambda x: x.get('score', 0), reverse=True)
            
        except Exception as e:
            rprint(f"[red]iTunes error: {str(e)}[/red]")
            return []
    
    def _get_tracks_for_album(self, album_id: str) -> List[Dict]:
        """Get all tracks for a specific album ID."""
        try:
            # Lookup album tracks
            params = {
                'id': album_id,
                'entity': 'song',
                'limit': 200  # Get all tracks
            }
            
            response = self.session.get(self.lookup_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            tracks = []
            for track in data.get('results', [])[1:]:  # Skip first result (album)
                if track.get('kind') == 'song':  # Ensure it's a song
                    tracks.append({
                        'title': track.get('trackName', ''),
                        'position': str(track.get('trackNumber', '')),
                        'duration': str(track.get('trackTimeMillis', '') // 1000)
                    })
            
            # Sort tracks by position
            tracks.sort(key=lambda x: int(x['position']) if x['position'].isdigit() else 999)
            return tracks
            
        except Exception as e:
            rprint(f"[red]Error getting album tracks: {str(e)}[/red]")
            return []
