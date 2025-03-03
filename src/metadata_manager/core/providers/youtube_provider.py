from typing import Dict, List
import ytmusicapi
from rich import print as rprint

from .provider_base import MetadataProvider
from ...core.utils import string_similarity  # Añadir import faltante

class YouTubeMusicProvider(MetadataProvider):
    """YouTube Music metadata provider."""
    
    def __init__(self):
        """Initialize YouTube Music client."""
        try:
            self.client = ytmusicapi.YTMusic()
            rprint("[cyan]YouTube Music provider initialized[/cyan]")
        except Exception as e:
            rprint(f"[yellow]Error initializing YouTube Music: {str(e)}[/yellow]")
            self.client = None
    
    @property
    def name(self) -> str:
        return "youtube"
    
    def search_track(self, title: str, artist: str = None) -> List[Dict]:
        """Search for a track."""
        if not self.client:
            return []
            
        try:
            query = f"{artist} - {title}" if artist else title
            results = self.client.search(query, filter="songs", limit=10)
            
            parsed = []
            for result in results:
                if result['resultType'] == 'song':
                    # Get artist name and score
                    artist_name = result['artists'][0]['name'] if result.get('artists') else ''
                    title_score = string_similarity(title, result.get('title', ''))
                    artist_score = string_similarity(artist, artist_name) if artist else 100
                    
                    # Get album info with tracks
                    year = ''
                    tracks = []
                    if result.get('album', {}).get('id'):
                        try:
                            album_data = self.client.get_album(result['album']['id'])
                            year = album_data.get('year', '')
                            tracks = [{
                                'title': t['title'],
                                'position': str(i + 1)
                            } for i, t in enumerate(album_data.get('tracks', []))]
                        except:
                            pass
                    
                    if title_score > 60 and artist_score > 60:
                        parsed.append(self.format_result({
                            'title': result.get('title', ''),
                            'artist': artist_name,
                            'album': result.get('album', {}).get('name', ''),
                            'year': year,
                            'tracks': tracks,  # Include tracks here
                            'score': min(100, ((title_score + artist_score) / 2)),
                            'provider': 'youtube',
                            'id': result.get('videoId')
                        }))
            
            return sorted(parsed, key=lambda x: x.get('score', 0), reverse=True)[:5]
            
        except Exception as e:
            rprint(f"[yellow]YouTube Music search error: {str(e)}[/yellow]")
            return []
    
    def search_album(self, album: str, artist: str = None) -> List[Dict]:
        """Search for an album."""
        if not self.client:
            return []
            
        try:
            query = f"{artist} {album}" if artist else album
            results = self.client.search(query, filter="albums", limit=5)
            
            parsed = []
            for result in results:
                if result['resultType'] == 'album':
                    # Get artist name
                    artist_name = result['artists'][0]['name'] if result.get('artists') else ''
                    
                    # Get album tracks y año
                    tracks = []
                    year = ''
                    try:
                        album_id = result.get('browseId')
                        if album_id:
                            album_data = self.client.get_album(album_id)
                            year = album_data.get('year', '')
                            tracks = [{
                                'title': track['title'],
                                'position': str(i + 1),
                                'duration': track.get('duration', ''),
                                'id': track.get('videoId', '')
                            } for i, track in enumerate(album_data.get('tracks', []))]
                    except:
                        pass
                    
                    parsed.append(self.format_result({
                        'title': result.get('title', ''),
                        'artist': artist_name,
                        'year': year,
                        'tracks': tracks,
                        'score': self._calculate_score(album, result.get('title', ''),
                                                     artist, artist_name),
                        'provider': 'youtube',
                        'id': result.get('browseId')
                    }, "album"))
            
            return sorted(parsed, key=lambda x: x.get('score', 0), reverse=True)
            
        except Exception as e:
            rprint(f"[yellow]YouTube Music search error: {str(e)}[/yellow]")
            return []
    
    def _calculate_score(self, query_title: str, result_title: str,
                        query_artist: str = None, result_artist: str = None) -> float:
        """Calculate match score."""
        from difflib import SequenceMatcher
        
        # Title similarity (60%)
        title_score = (SequenceMatcher(None, query_title.lower(), 
                                     result_title.lower()).ratio() * 60)
        
        # Artist similarity if provided (40%)
        artist_score = 0
        if query_artist and result_artist:
            artist_score = (SequenceMatcher(None, query_artist.lower(),
                                          result_artist.lower()).ratio() * 40)
        
        return title_score + artist_score
