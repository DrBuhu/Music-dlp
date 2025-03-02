from typing import Dict, List
import spotipy
from rich import print as rprint
from ...core.metadata_manager import MetadataProvider
from ...core.utils import string_similarity

class SpotifyProvider(MetadataProvider):
    """Spotify metadata provider without auth."""
    
    def __init__(self):
        # Initialize without credentials
        self.sp = spotipy.Spotify(auth=None, requests_session=True)
        self.sp.auth_manager = None  # Disable auth for search
        rprint("[cyan]Spotify provider initialized[/cyan]")
    
    @property
    def name(self) -> str:
        return "spotify"
    
    def search_track(self, title: str, artist: str = None) -> List[Dict]:
        try:
            query = f"track:{title}"
            if artist:
                query += f" artist:{artist}"
                
            results = self.sp.search(q=query, type='track', limit=5, market='US')
            tracks = results['tracks']['items']
            
            parsed = []
            for track in tracks:
                title_score = string_similarity(title, track['name'])
                artist_score = string_similarity(artist, track['artists'][0]['name']) if artist else 100
                
                if title_score > 60 and artist_score > 60:
                    # Get highest quality image
                    images = track['album']['images']
                    artwork_url = max(images, key=lambda x: x['height'])['url'] if images else None
                    
                    parsed.append(self.format_result({
                        'title': track['name'],
                        'artist': track['artists'][0]['name'],
                        'album': track['album']['name'],
                        'year': track['album']['release_date'][:4],
                        'tracks': [],
                        'score': (title_score + artist_score) / 2,
                        'artwork_url': artwork_url
                    }))
            
            return sorted(parsed, key=lambda x: x.get('score', 0), reverse=True)
            
        except Exception as e:
            rprint(f"[yellow]Spotify track search error: {str(e)}[/yellow]")
            return []
    
    def search_album(self, album: str, artist: str = None) -> List[Dict]:
        try:
            query = f"album:{album}"
            if artist:
                query += f" artist:{artist}"
                
            results = self.sp.search(q=query, type='album', limit=5, market='US')
            albums = results['albums']['items']
            
            parsed = []
            for album_data in albums:
                album_score = string_similarity(album, album_data['name'])
                artist_score = string_similarity(artist, album_data['artists'][0]['name']) if artist else 100
                
                if album_score > 60 and artist_score > 60:
                    try:
                        # Get full album data including tracks
                        full_album = self.sp.album(album_data['id'])
                        tracks = []
                        
                        for i, track in enumerate(full_album['tracks']['items'], 1):
                            tracks.append({
                                'title': track['name'],
                                'position': str(i),
                                'duration': str(track['duration_ms'] // 1000)
                            })
                            
                        # Get highest quality image
                        images = album_data['images']
                        artwork_url = max(images, key=lambda x: x['height'])['url'] if images else None
                        
                        parsed.append(self.format_result({
                            'title': album_data['name'],
                            'artist': album_data['artists'][0]['name'],
                            'year': album_data['release_date'][:4],
                            'tracks': tracks,
                            'score': (album_score + artist_score) / 2,
                            'artwork_url': artwork_url
                        }, "album"))
                        
                    except Exception as e:
                        rprint(f"[yellow]Error getting album details: {str(e)}[/yellow]")
                        continue
                        
            return sorted(parsed, key=lambda x: x.get('score', 0), reverse=True)
            
        except Exception as e:
            rprint(f"[yellow]Spotify album search error: {str(e)}[/yellow]")
            return []
