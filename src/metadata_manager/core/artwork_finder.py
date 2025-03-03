"""Utility to find artwork from various sources."""
import requests
from urllib.parse import quote

def find_artwork(artist: str = "", album: str = "", title: str = "", size: str = "large") -> str:
    """Find artwork URL from various sources.
    
    Args:
        artist: Artist name
        album: Album name 
        title: Track title
        size: Size of artwork (small, medium, large, extralarge)
        
    Returns:
        URL to artwork if found, otherwise empty string
    """
    # Try Last.fm API (no authentication needed for basic search)
    lastfm_url = find_lastfm_artwork(artist, album, size)
    if lastfm_url:
        return lastfm_url
        
    # Try MusicBrainz Cover Art Archive
    mb_url = find_musicbrainz_artwork(artist, album)
    if mb_url:
        return mb_url
        
    # Try iTunes/Apple Music API
    itunes_url = find_itunes_artwork(artist, album)
    if itunes_url:
        return itunes_url
    
    return ""

def find_lastfm_artwork(artist: str, album: str, size: str = "large") -> str:
    """Find album artwork from Last.fm."""
    if not artist or not album:
        return ""
        
    try:
        # Last.fm API allows simple requests without authentication
        params = {
            "method": "album.getinfo",
            "api_key": "12dec50b355d804c7d37dff8c8ea2c14",  # Public API key
            "artist": artist,
            "album": album,
            "format": "json"
        }
        
        response = requests.get("http://ws.audioscrobbler.com/2.0/", params=params)
        if response.status_code == 200:
            data = response.json()
            if "album" in data and "image" in data["album"]:
                for image in data["album"]["image"]:
                    if image["size"] == size and image["#text"]:
                        return image["#text"]
    except Exception as e:
        print(f"Last.fm artwork error: {e}")
        
    return ""

def find_musicbrainz_artwork(artist: str, album: str) -> str:
    """Find artwork from MusicBrainz Cover Art Archive."""
    if not artist or not album:
        return ""
        
    try:
        # First search for the release
        query = f"release:{album} AND artist:{artist}"
        url = f"https://musicbrainz.org/ws/2/release?query={quote(query)}&fmt=json&limit=1"
        
        response = requests.get(url, headers={"User-Agent": "MusicDLP/1.0"})
        if response.status_code == 200:
            data = response.json()
            if data["releases"] and data["releases"][0].get("id"):
                # Get artwork from Cover Art Archive
                mbid = data["releases"][0]["id"]
                caa_url = f"https://coverartarchive.org/release/{mbid}/front"
                # Just return the URL - no need to check, CAA will redirect if image exists
                return caa_url
    except Exception as e:
        print(f"MusicBrainz artwork error: {e}")
        
    return ""

def find_itunes_artwork(artist: str, album: str) -> str:
    """Find artwork from iTunes."""
    if not artist and not album:
        return ""
        
    try:
        # iTunes search API
        term = f"{artist} {album}".strip()
        params = {
            "term": term,
            "media": "music",
            "entity": "album",
            "limit": 1
        }
        
        response = requests.get("https://itunes.apple.com/search", params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get("resultCount", 0) > 0:
                # Get artwork URL and convert to higher resolution
                artwork_url = data["results"][0].get("artworkUrl100", "")
                if artwork_url:
                    # Convert to larger size (e.g. 600x600)
                    return artwork_url.replace("100x100", "600x600")
    except Exception as e:
        print(f"iTunes artwork error: {e}")
        
    return ""
