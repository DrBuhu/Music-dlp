"""MusicBrainz metadata provider."""
import time
from typing import Dict, List, Optional
import musicbrainzngs as mb
from rich import print as rprint
import socket
from urllib.error import URLError

from .provider_base import MetadataProvider

class MusicBrainzProvider(MetadataProvider):
    @property  # Añadir el decorador que faltaba
    def name(self) -> str:
        """Provider name."""
        return "musicbrainz"

    def __init__(self, app_name: str = "MetadataManager", version: str = "0.1.0"):
        """Initialize MusicBrainz client."""
        mb.set_useragent(app_name, version)
        # Configure shorter timeouts
        socket.setdefaulttimeout(3)  # 3 segundos de timeout global
        
    def _retry_request(self, func, *args, max_retries=3, **kwargs):
        """Ejecuta una request con reintentos."""
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except (URLError, socket.timeout) as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)
                continue
    
    def search_track(self, title: str, artist: str = None) -> List[Dict]:
        """Search for a track."""
        try:
            query = f'recording:"{title}"'
            if artist:
                query += f' AND artist:"{artist}"'
                
            result = self._retry_request(
                mb.search_recordings,
                query=query,
                limit=5  # Aumentado de 1 a 5
            )
            
            if not result or 'recording-list' not in result:
                return []
                
            return self._parse_track_results(result['recording-list'])
            
        except Exception as e:
            rprint(f"[yellow]MusicBrainz search error: {str(e)}[/yellow]")
            return []

    def search_album(self, album: str, artist: str = None) -> List[Dict]:
        """Search for an album."""
        try:
            query = f'release:"{album}"'
            if artist:
                query += f' AND artist:"{artist}"'
                
            result = self._retry_request(
                mb.search_releases,
                query=query,
                limit=5
            )
            
            if not result or 'release-list' not in result:
                return []
                
            return self._parse_album_results(result['release-list'])
            
        except Exception as e:
            rprint(f"[yellow]MusicBrainz search error: {str(e)}[/yellow]")
            return []

    def _parse_track_results(self, tracks: List[Dict]) -> List[Dict]:
        """Parse track search results."""
        results = []
        for track in tracks:
            try:
                artist = track['artist-credit'][0]['name'] if 'artist-credit' in track else ''
                
                # Get release info and tracks
                album = None
                year = ''
                track_list = []
                if track.get('release-list'):
                    album = track['release-list'][0]
                    # Try to get year and tracks
                    for release in track['release-list']:
                        if 'date' in release:
                            year = release['date'][:4]
                        if not track_list:  # Get tracks from first release that has them
                            track_list = self._get_album_tracks(release.get('id', ''))
                        if year and track_list:  # If we have both, stop looking
                            break
                
                result = {
                    'title': track.get('title', ''),
                    'artist': artist,
                    'album': album.get('title', '') if album else '',
                    'year': year,
                    'tracks': track_list,  # Add tracks here
                    'score': float(track.get('ext:score', 0)),
                    'id': track.get('id', ''),
                    'provider': 'musicbrainz'
                }
                results.append(self.format_result(result))
            except Exception as e:
                rprint(f"[yellow]Error parsing track: {str(e)}[/yellow]")
                continue
        return results

    def _parse_album_results(self, albums: List[Dict]) -> List[Dict]:
        """Parse album search results."""
        results = []
        for album in albums:
            try:
                artist = album['artist-credit'][0]['name'] if 'artist-credit' in album else ''
                date = album.get('date', '')[:4] if 'date' in album else ''
                score = float(album.get('ext:score', 0))
                
                tracks = self._get_album_tracks(album.get('id', ''))
                
                result = {
                    'title': album.get('title', ''),
                    'artist': artist,
                    'year': date,
                    'tracks': tracks,
                    'score': score,
                    'id': album.get('id', ''),
                    'provider': 'musicbrainz'  # Add provider name
                }
                results.append(self.format_result(result, "album"))
            except Exception as e:
                rprint(f"[yellow]Error parsing album: {str(e)}[/yellow]")
                continue
                
        return results
    
    def _get_album_tracks(self, album_id: str) -> List[Dict]:
        """Get tracks for an album with rate limiting."""
        if not album_id:
            return []
            
        try:
            for attempt in range(3):  # 3 intentos
                try:
                    release = mb.get_release_by_id(album_id, includes=['recordings'])
                    tracks = []
                    
                    if 'release' in release and 'medium-list' in release['release']:
                        for medium in release['release']['medium-list']:
                            if 'track-list' in medium:
                                for track in medium['track-list']:
                                    tracks.append({
                                        'title': track['recording']['title'],
                                        'position': track['position'],
                                        'id': track['recording']['id']
                                    })
                    return tracks
                    
                except mb.NetworkError:
                    if attempt < 2:  # Si no es el último intento
                        time.sleep(1)  # Esperar 1 segundo antes de reintentar
                        continue
                    raise
                except Exception as e:
                    rprint(f"[yellow]Error fetching tracks: {str(e)}[/yellow]")
                    return []
            
            return []  # Si todos los intentos fallan
            
        except Exception as e:
            rprint(f"[yellow]Error fetching tracks: {str(e)}[/yellow]")
            return []
