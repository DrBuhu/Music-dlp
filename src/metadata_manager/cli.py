"""Command line interface for Music-dlp."""
import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from rich import print as rprint
from rich.table import Table
from rich.prompt import Confirm

# Importaciones relativas simples
from .core.file_scanner import FileScanner
from .core.metadata_manager import MetadataManager

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Music metadata manager CLI")
    parser.add_argument("directory", help="Directory to scan")
    parser.add_argument("-r", "--recursive", action="store_true", help="Scan recursively")
    parser.add_argument("-d", "--details", action="store_true", help="Show detailed metadata and search")
    parser.add_argument("-a", "--auto", action="store_true", help="Auto mode (no prompts)")
    parser.add_argument("-p", "--providers", help="Comma-separated list of providers")
    parser.add_argument("--no-search", action="store_true", help="Skip metadata search")
    return parser.parse_args()

def display_metadata(files: List[Dict], compact: bool = True):
    """Display metadata for files in a table."""
    # Create results table
    table = Table(title="\nMusic Files")
    table.add_column("Track")
    table.add_column("Title")
    table.add_column("Artist")
    table.add_column("Album")
    table.add_column("Year")
    
    # Process files
    for file in files:
        metadata = file["metadata"]
        track = metadata.get("track", [""])[0]
        title = metadata.get("title", [""])[0] or os.path.basename(file["path"])
        artist = metadata.get("artist", [""])[0]
        album = metadata.get("album", [""])[0]
        year = metadata.get("date", [""])[0]
        
        table.add_row(track, title, artist, album, year)
    
    # Display table
    rprint(table)
    
    # Show summary
    if files:
        first_file = files[0]
        artist = first_file["metadata"].get("artist", [""])[0]
        album = first_file["metadata"].get("album", [""])[0]
        date = first_file["metadata"].get("date", [""])[0]
        
        if artist or album:
            rprint(f"\nTracks: {len(files)} • Artist: {artist} • Album: {album} • Year: {date}")

def display_results_table(results: List[Dict]):
    """Display search results in a table."""
    if not results:
        return
        
    table = Table(title="\nSearch Results")
    table.add_column("Source")
    table.add_column("Title")
    table.add_column("Artist")
    table.add_column("Album")
    table.add_column("Year")
    table.add_column("Score")
    table.add_column("Tracks")  # Nueva columna
    
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

def search_metadata(files: List[Dict], args) -> None:
    """Search for metadata and display results."""
    if not files:
        return
        
    enabled_providers = args.providers.split(",") if args.providers else None
    manager = MetadataManager(enabled_providers)
    
    processed = 0
    for file in files:
        metadata = file["metadata"]
        title = metadata.get("title", [""])[0]
        artist = metadata.get("artist", [""])[0]
        
        if not title:
            continue
            
        results = manager.search_all([{
            'metadata': {
                'title': [title],
                'artist': [artist]
            }
        }])
        
        if results:
            rprint(f"\n[cyan]Results for: {title}[/cyan]")
            display_results_table([item for sublist in results.values() for item in sublist])
            
            match = manager.select_metadata(results, [file])
            if match:
                rprint(f"Selected: {match['title']} by {match['artist']}")
                processed += 1
            elif not args.auto:  # Solo salimos si no estamos en modo auto
                # Usuario eligió salir (0)
                if Confirm.ask("\nExit metadata search?", default=True):
                    break
                
    if processed > 0:
        rprint(f"\n[green]Processed {processed} of {len(files)} files[/green]")

def main():
    """Main entry point."""
    args = parse_args()
    
    # Initialize scanner
    scanner = FileScanner()
    
    # Scan directory
    rprint(f"[cyan]Scanning directory: {args.directory}[/cyan]")
    files = scanner.scan_directory(args.directory, recursive=args.recursive)
    
    if files:
        # Display current metadata
        display_metadata(files, compact=not args.details)
        
        # Search for metadata if requested
        if args.details and not args.no_search:
            rprint('\n[cyan]Searching metadata...[/cyan]')
            search_metadata(files, args)
    else:
        rprint("[yellow]No music files found[/yellow]")

if __name__ == "__main__":
    main()
