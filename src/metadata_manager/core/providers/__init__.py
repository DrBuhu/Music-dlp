"""Metadata providers package."""

from typing import List, Type
from ..metadata_manager import MetadataProvider

def get_available_providers() -> List[Type[MetadataProvider]]:
    """Get list of available metadata providers."""
    providers = []
    
    # Always include MusicBrainz
    from ..metadata_manager import MusicBrainzProvider
    providers.append(MusicBrainzProvider)
    
    # Try to load optional providers
    try:
        from .discogs_provider import DiscogsProvider
        providers.append(DiscogsProvider)
    except ImportError:
        print("Warning: Discogs provider not available")
    
    # Add web provider as fallback
    from ..web import WebMetadataProvider
    providers.append(WebMetadataProvider)
    
    return providers
