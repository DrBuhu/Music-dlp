from typing import Dict, List, Optional
from abc import ABC, abstractmethod
import musicbrainzngs as mb
from rich import print as rprint
from rich.prompt import Prompt, Confirm

try:
    from ..rust.metadata_core import MetadataMatcher
    HAS_RUST = True
except ImportError:
    HAS_RUST = False
    print("Warning: Rust optimizations not available")

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
        return {
            'title': data.get('title', ''),
            'artist': data.get('artist', ''),
            'album': data.get('album', ''),
            'year': data.get('year', ''),
            'tracks': data.get('tracks', []),
            'source': self.name,
            'raw_data': data
        }

class MusicBrainzProvider(MetadataProvider):
    """MusicBrainz metadata provider."""
    
    def __init__(self, app_name: str = "MetadataManager", version: str = "0.1.0"):
        mb.set_useragent(app_name, version)
    
    @property
    def name(self) -> str:
        return "musicbrainz"
    
    def search_track(self, title: str, artist: str = None) -> List[Dict]:
        """Search for a track in MusicBrainz."""
        query = f'recording:"{title}"'
        if artist:
            query += f' AND artist:"{artist}"'
            
        try:
            result = mb.search_recordings(query=query, limit=5)
            return self._parse_track_results(result['recording-list'])
        except Exception as e:
            print(f"Error searching MusicBrainz: {str(e)}")
            return []
    
    def search_album(self, album: str, artist: str = None) -> List[Dict]:
        """Search for an album in MusicBrainz."""
        query = f'release:"{album}"'
        if artist:
            query += f' AND artist:"{artist}"'
            
        try:
            result = mb.search_releases(query=query, limit=5)
            return self._parse_album_results(result['release-list'])
        except Exception as e:
            print(f"Error searching MusicBrainz: {str(e)}")
            return []
    
    def _parse_track_results(self, tracks: List[Dict]) -> List[Dict]:
        """Parse track search results."""
        results = []
        for track in tracks:
            results.append(self.format_result({
                'title': track.get('title', ''),
                'artist': track['artist-credit'][0].get('name', '') if 'artist-credit' in track else '',
                'album': track['release-list'][0].get('title', '') if 'release-list' in track else '',
                'year': track['release-list'][0].get('date', '')[:4] if 'release-list' in track else '',
                'id': track.get('id', '')
            }))
        return results
    
    def _parse_album_results(self, albums: List[Dict]) -> List[Dict]:
        """Parse album search results."""
        results = []
        for album in albums:
            results.append(self.format_result({
                'title': album.get('title', ''),
                'artist': album['artist-credit'][0].get('name', '') if 'artist-credit' in album else '',
                'year': album.get('date', '')[:4] if 'date' in album else '',
                'id': album.get('id', ''),
                'tracks': self._get_album_tracks(album.get('id', ''))
            }, "album"))
        return results
    
    def _get_album_tracks(self, album_id: str) -> List[Dict]:
        """Get tracks for an album."""
        try:
            release = mb.get_release_by_id(album_id, includes=['recordings'])
            tracks = []
            for medium in release['release']['medium-list']:
                for track in medium['track-list']:
                    tracks.append({
                        'title': track['recording']['title'],
                        'position': track['position'],
                        'id': track['recording']['id']
                    })
            return tracks
        except:
            return []

class MetadataManager:
    """Manages metadata search and updates across multiple providers."""
    
    def __init__(self):
        self.providers = []
        rprint("[cyan]Initializing metadata providers...[/cyan]")
        
        # 1. MusicBrainz (primary source)
        self.providers.append(MusicBrainzProvider())
        rprint("[green]MusicBrainz provider loaded[/green]")
        
        # 2. YouTube Music (good metadata + artwork)
        try:
            from .providers.youtube_provider import YouTubeMusicProvider
            youtube = YouTubeMusicProvider()
            self.providers.append(youtube)
            rprint("[green]YouTube Music provider loaded successfully[/green]")
        except Exception as e:
            rprint(f"[yellow]Warning: YouTube Music support not available - {str(e)}[/yellow]")
        
        # 3. iTunes (reliable metadata)
        try:
            from .providers.itunes_provider import ITunesProvider
            itunes = ITunesProvider()
            self.providers.append(itunes)
            rprint("[green]iTunes provider loaded successfully[/green]")
        except Exception as e:
            rprint(f"[yellow]Warning: iTunes support not available - {str(e)}[/yellow]")
        
        # 4. Deezer (high quality artwork)
        try:
            from .providers.deezer_provider import DeezerProvider
            deezer = DeezerProvider()
            self.providers.append(deezer)
            rprint("[green]Deezer provider loaded successfully[/green]")
        except Exception as e:
            rprint(f"[yellow]Warning: Deezer support not available - {str(e)}[/yellow]")

        # 5. Spotify (backup source)
        try:
            from .providers.spotify_provider import SpotifyProvider
            spotify = SpotifyProvider()
            self.providers.append(spotify)
            rprint("[green]Spotify provider loaded successfully[/green]")
        except Exception as e:
            rprint(f"[yellow]Warning: Spotify support not available - {str(e)}[/yellow]")

        rprint(f"[cyan]Active providers: {[p.name for p in self.providers]}[/cyan]")
        
        # Initialize matcher
        try:
            from ..rust.metadata_core import MetadataMatcher
            self.matcher = MetadataMatcher()
        except ImportError:
            self.matcher = None
    
    def download_and_tag(self, url: str, output_dir: str) -> Dict:
        """Download music and get metadata."""
        import yt_dlp
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
            'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Use extracted info to search for better metadata
            title = info.get('title', '')
            artist = info.get('artist', '')
            
            results = self.search_all([{
                'metadata': {
                    'title': [title],
                    'artist': [artist]
                }
            }])
            
            return results

    def search_all(self, files: List[Dict], search_type: str = "album") -> Dict[str, List]:
        """Search across all providers."""
        results = {}
        print(f"\nSearching with providers: {[p.name for p in self.providers]}")  # Debug
        
        for provider in self.providers:
            try:
                print(f"\nTrying provider: {provider.name}")  # Debug
                if search_type == "album" and len(files) > 1:
                    album = files[0]['metadata'].get('album', [''])[0]
                    artist = files[0]['metadata'].get('artist', [''])[0]
                    if album and artist:
                        matches = provider.search_album(album, artist)
                        if matches:
                            results[provider.name] = matches
                else:
                    for file in files:
                        metadata = file['metadata']
                        title = metadata.get('title', [''])[0]
                        artist = metadata.get('artist', [''])[0]
                        if title and artist:
                            matches = provider.search_track(title, artist)
                            if matches:
                                results.setdefault(provider.name, []).extend(matches)
            except Exception as e:
                print(f"Error with {provider.name}: {str(e)}")
        
        return results
    
    def _format_display_title(self, match: Dict) -> str:
        """Format title with year for display."""
        title = match['title'] or match['album'] or '(No title)'
        year = match['year']
        year_str = f" ({year})" if year else ""
        return f"{match['artist']} - {title}{year_str}"

    def select_metadata(self, results: Dict[str, List], files: List[Dict]) -> Optional[Dict]:
        """Interactive menu to select metadata source."""
        if not results:
            rprint("[yellow]No matches found in any source[/yellow]")
            return None

        while True:  # Main selection loop
            # Show all results from all sources
            rprint("\n[bold cyan]Search Results:[/bold cyan]")
            all_matches = []
            match_index = 1

            for source, matches in results.items():
                if matches:
                    rprint(f"\n[bold]{source.upper()}[/bold] ({len(matches)} matches):")
                    
                    for match in matches:
                        all_matches.append((source, match))
                        tracks_info = f"{len(match['tracks'])} tracks" if 'tracks' in match and match['tracks'] else "no track info"
                        display_title = self._format_display_title(match)
                        rprint(f"  [green]{match_index}.[/green] {display_title} • {tracks_info}")
                        match_index += 1

            # Show options
            rprint("\n[bold cyan]Options:[/bold cyan]")
            rprint("  [green]1-{:d}[/green] Select a match".format(len(all_matches)))
            rprint("  [yellow]s[/yellow] Manual search")
            rprint("  [red]0[/red] Skip/Exit")

            # Get user choice
            choice = Prompt.ask("\nEnter your choice", default="0")
            
            if choice.lower() == 's':
                query = Prompt.ask("Enter search term")
                return self.manual_search(query, files)
            
            try:
                choice_num = int(choice)
                if choice_num == 0:
                    return None
                elif 1 <= choice_num <= len(all_matches):
                    source, match = all_matches[choice_num - 1]
                    
                    # Show detailed info
                    rprint("\n[bold]Selected match details:[/bold]")
                    rprint(f"Source: [cyan]{source}[/cyan]")
                    rprint(f"Artist: [yellow]{match['artist']}[/yellow]")
                    rprint(f"Album: [blue]{match['title'] or match['album']}[/blue]")
                    if match['year']:
                        rprint(f"Year: [magenta]{match['year']}[/magenta]")
                    
                    if 'tracks' in match and match['tracks']:
                        rprint("\n[bold]Track listing:[/bold]")
                        for track in match['tracks']:
                            rprint(f"  {track['position']}. {track['title']}")
                    
                    if Confirm.ask("\nUse this match?", default=True):
                        return match
                    # No else needed - loop will continue automatically
            except ValueError:
                rprint("[yellow]Invalid choice, try again[/yellow]")

    def _normalize_query(self, query: str) -> List[Dict[str, str]]:
        """Generate multiple query variations for better matching."""
        query = query.strip()
        variations = []
        
        # Clean query first
        query = query.replace('_', ' ').strip()
        
        # Try the full query as both album and artist
        variations.append({'title': query})
        
        # Split by common separators and try different combinations
        separators = [' - ', ' – ', ' / ', ' : ', ' by ', '-', '–', '/', ':']
        for separator in separators:
            if separator in query:
                parts = [p.strip() for p in query.split(separator, 1)]
                if len(parts) == 2:
                    # Both orders with original parts
                    variations.extend([
                        {'artist': parts[0], 'title': parts[1]},
                        {'artist': parts[1], 'title': parts[0]}
                    ])
                    
                    # Clean and normalize parts
                    clean_parts = [self._clean_term(p) for p in parts]
                    if clean_parts != parts:
                        variations.extend([
                            {'artist': clean_parts[0], 'title': clean_parts[1]},
                            {'artist': clean_parts[1], 'title': clean_parts[0]}
                        ])
                break  # Stop after first matching separator
        
        # If no separator found, try smart splitting
        if not any(sep in query for sep in separators):
            words = query.split()
            if len(words) > 2:
                # Try first half as title, second half as artist and vice versa
                mid = len(words) // 2
                variations.extend([
                    {
                        'title': ' '.join(words[:mid]),
                        'artist': ' '.join(words[mid:])
                    },
                    {
                        'artist': ' '.join(words[:mid]),
                        'title': ' '.join(words[mid:])
                    }
                ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variations = []
        for var in variations:
            key = f"{var.get('artist', '')}-{var.get('title', '')}"
            if key not in seen:
                seen.add(key)
                unique_variations.append(var)
        
        return unique_variations
    
    def _clean_term(self, term: str) -> str:
        """Clean and normalize search terms."""
        # Remove common noise words
        noise_words = ['the', 'a', 'an', 'by']
        words = term.lower().split()
        cleaned = ' '.join(w for w in words if w not in noise_words)
        
        # Remove special characters but keep spaces
        import re
        cleaned = re.sub(r'[^\w\s]', '', cleaned)
        
        return cleaned.strip()

    def manual_search(self, query: str, files: List[Dict]) -> Optional[Dict]:
        """Perform manual search across all providers."""
        rprint(f"\n[cyan]Searching all sources for:[/cyan] {query}")
        results = {}
        
        # Generate query variations
        variations = self._normalize_query(query)
        rprint("\n[dim]Trying different query variations...[/dim]")
        
        for provider in self.providers:
            matches = []
            try:
                for variation in variations:
                    if not matches:  # Only try next variation if no matches yet
                        artist = variation.get('artist')
                        title = variation.get('title')
                        
                        if len(files) > 1:
                            # Album search
                            if artist:
                                matches = provider.search_album(title, artist)
                            if not matches:
                                matches = provider.search_album(title)
                        else:
                            # Track search with fallback to album
                            if artist:
                                matches = provider.search_track(title, artist)
                                if not matches:
                                    matches = provider.search_album(title, artist)
                            if not matches:
                                matches = provider.search_track(title)
                                if not matches:
                                    matches = provider.search_album(title)
                        
                        if matches:
                            rprint(f"[green]Found matches using: {variation}[/green]")
                            results[provider.name] = matches
                            break
            except Exception as e:
                rprint(f"[red]Error with {provider.name}: {str(e)}[/red]")
        
        if not results:
            rprint("[yellow]No matches found with any variation[/yellow]")
            if Confirm.ask("\nTry another search?", default=True):
                query = Prompt.ask("Enter search term")
                return self.manual_search(query, files)
            return None
        
        return self.select_metadata(results, files)
    
    def _sort_matches(self, matches: List[Dict], reference: Dict) -> List[Dict]:
        """Sort matches by similarity score."""
        if not self.matcher:
            # Simple Python fallback
            return sorted(matches, 
                key=lambda x: (
                    x.get('year', '') == reference.get('year', ''),
                    len(x.get('tracks', [])) > 0,
                    x.get('title', '').lower() == reference.get('title', '').lower()
                ), 
                reverse=True
            )
        
        # Use Rust if available    
        scored_matches = []
        for match in matches:
            score = self.matcher.score_match(reference, match)
            scored_matches.append((score, match))
        
        return [m for s, m in sorted(scored_matches, key=lambda x: x[0], reverse=True)]
