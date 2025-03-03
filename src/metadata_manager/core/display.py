"""Display utilities for metadata manager."""
from typing import Dict, List
from rich import print as rprint
from rich.table import Table

def display_results_table(results: List[Dict]):
    """Display search results in a table."""
    if not results:
        return
        
    # Show table first
    table = Table(title="\nSearch Results")
    table.add_column("Source")
    table.add_column("Title")
    table.add_column("Artist")
    table.add_column("Album")
    table.add_column("Year")
    table.add_column("Score")
    table.add_column("Tracks")
    
    # Group results by provider
    by_provider = {}
    for result in results:
        provider = result.get("provider", "unknown")
        by_provider.setdefault(provider, []).append(result)

    # Add to table    
    for result in results:
        source = result.get("provider", "unknown")
        title = result.get("title", "Unknown")
        artist = result.get("artist", "Unknown")
        album = result.get("album", title)
        year = result.get("year", "")
        score = f"{result.get('score', 0):.1f}"
        num_tracks = len(result.get('tracks', []))
        tracks_str = str(num_tracks) if num_tracks > 0 else ""
        
        table.add_row(source, title, artist, album, year, score, tracks_str)

    rprint(table)
    
    # Show detailed list
    rprint("\n[bold cyan]Search Results:[/bold cyan]\n")
    match_index = 1

    for provider, provider_results in by_provider.items():
        provider = provider.upper()
        rprint(f"{provider} ({len(provider_results)} matches):")
        
        for result in provider_results:
            tracks_info = f"{len(result.get('tracks', []))} tracks" if result.get('tracks') else "no track info"
            year_str = f" ({result.get('year', '')}) " if result.get('year') else " "
            display = f"{result.get('artist', '')} - {result.get('title', '')}{year_str}• {tracks_info}"
            rprint(f"  {match_index}. {display}")
            match_index += 1
        rprint()
