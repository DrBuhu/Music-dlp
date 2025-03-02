from typing import Dict, List
from ytmusicapi import YTMusic
from rich import print as rprint
from ...core.metadata_manager import MetadataProvider
from ...core.utils import string_similarity

class YouTubeMusicProvider(MetadataProvider):
    """YouTube Music metadata provider using ytmusicapi."""
    
    def __init__(self):
        try:
            self.ytmusic = YTMusic()  # No auth needed for search
            rprint("[green]YouTube Music provider initialized[/green]")
        except Exception as e:
            rprint(f"[red]Error initializing YouTube Music: {str(e)}[/red]")
            raise
    
    @property
    def name(self) -> str:
        return "youtube"
    
    def search_track(self, title: str, artist: str = None) -> List[Dict]:
        try:
            query = f"{artist} {title}" if artist else title
            results = self.ytmusic.search(query, filter="songs", limit=5)
            
            parsed = []
            for result in results:
                if result['resultType'] == 'song':
                    title_score = string_similarity(title, result['title'])
                    artist_score = string_similarity(artist, result['artists'][0]['name']) if artist else 100
                    
                    if title_score > 60 and artist_score > 60:
                        parsed.append(self.format_result({
                            'title': result['title'],
                            'artist': result['artists'][0]['name'],
                            'album': result['album']['name'] if 'album' in result else '',
                            'year': result.get('year', ''),
                            'tracks': [],
                            'score': (title_score + artist_score) / 2,
                            'artwork_url': result.get('thumbnails', [{}])[-1].get('url')
                        }))
            
            return sorted(parsed, key=lambda x: x.get('score', 0), reverse=True)
            
        except Exception as e:
            rprint(f"[red]YouTube Music track search error: {str(e)}[/red]")
            return []
    
    def search_album(self, album: str, artist: str = None) -> List[Dict]:
        try:
            query = f"{artist} {album}" if artist else album
            results = self.ytmusic.search(query, filter="albums", limit=5)
            
            parsed = []
            for result in results:
                if result['resultType'] == 'album':
                    album_score = string_similarity(album, result['title'])
                    artist_score = string_similarity(artist, result['artists'][0]['name']) if artist else 100
                    
                    if album_score > 60 and artist_score > 60:
                        # Get album details including tracks
                        browse_id = result.get('browseId')
                        if browse_id:
                            album_data = self.ytmusic.get_album(browse_id)
                            tracks = []
                            
                            for i, track in enumerate(album_data.get('tracks', []), 1):
                                tracks.append({
                                    'title': track['title'],
                                    'position': str(i),
                                    'duration': str(int(track.get('duration_seconds', 0)))
                                })
                            
                            parsed.append(self.format_result({
                                'title': result['title'],
                                'artist': result['artists'][0]['name'],
                                'year': result.get('year', ''),
                                'tracks': tracks,
                                'score': (album_score + artist_score) / 2,
                                'artwork_url': result.get('thumbnails', [{}])[-1].get('url')
                            }, "album"))
            
            return sorted(parsed, key=lambda x: x.get('score', 0), reverse=True)
            
        except Exception as e:
            rprint(f"[red]YouTube Music album search error: {str(e)}[/red]")
            return []
