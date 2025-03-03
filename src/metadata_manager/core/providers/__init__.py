"""Metadata providers package."""
from typing import List, Type

__all__ = [
    'provider_base',
    'musicbrainz_provider',
    'spotify_provider',
    'youtube_provider',
    'itunes_provider',
    'deezer_provider'
]

from .provider_base import MetadataProvider
from .musicbrainz_provider import MusicBrainzProvider
from .youtube_provider import YouTubeMusicProvider
from .spotify_provider import SpotifyProvider
from .itunes_provider import ITunesProvider
from .deezer_provider import DeezerProvider

# Export all providers
__providers__ = [
    MusicBrainzProvider,
    YouTubeMusicProvider,
    SpotifyProvider,
    ITunesProvider,
    DeezerProvider
]

def get_available_providers() -> List[Type[MetadataProvider]]:
    """Get list of available metadata providers."""
    providers = []
    
    # Always include MusicBrainz
    providers.append(MusicBrainzProvider)
    
    return providers
