import argparse
from pathlib import Path
from rich import print as rprint
from rich.console import Console
from rich.table import Table
from rich.theme import Theme
from .core.scanner import MusicScanner
from .core.metadata_manager import MetadataManager

# Initialize rich with a custom theme
console = Console(theme=Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "success": "green bold"
}))

def display_metadata(files: list) -> None:
    """Display metadata in the best available format."""
    try:
        display_metadata_rich(files)
    except Exception as e:
        print(f"Warning: Rich display failed ({str(e)}), falling back to simple display")
        display_metadata_simple(files)

def truncate_text(text: str, max_length: int) -> str:
    """Truncate text to max_length, adding ellipsis if needed."""
    return text if len(text) <= max_length else text[:max_length-3] + "..."

def clean_date(date_str: str) -> str:
    """Extract year from date string."""
    if not date_str or date_str == '—':
        return '—'
    # Handle common date formats
    return date_str.split('-')[0].strip()

def get_terminal_width():
    """Get terminal width or default to 80."""
    try:
        return console.width if console else 80
    except:
        return 80

def get_optimal_widths(files: list, term_width: int) -> dict:
    """Calculate optimal column widths based on content."""
    widths = {
        'track': 4,  # Increased from 3 to 4 to fit "Track"
        'title': 0,
        'artist': 0,
        'album': 0,
        'year': 4
    }
    
    # Get max lengths for each column
    for file in files:
        metadata = file['metadata']
        # Track (always 2-3 chars)
        track_num = metadata.get('tracknumber', [''])[0].split('/')[0] if 'tracknumber' in metadata else ''
        if not track_num and Path(file['filename']).stem[:2].isdigit():
            track_num = Path(file['filename']).stem[:2]
        widths['track'] = max(widths['track'], len(str(track_num)))
        
        # Other fields
        title = metadata.get('title', ['—'])[0] if 'title' in metadata else '—'
        artist = metadata.get('artist', ['—'])[0] if 'artist' in metadata else '—'
        album = metadata.get('album', ['—'])[0] if 'album' in metadata else '—'
        
        widths['title'] = max(widths['title'], len(title))
        widths['artist'] = max(widths['artist'], len(artist))
        widths['album'] = max(widths['album'], len(album))
    
    # Add padding and calculate total
    total_fixed = 13  # Borders and padding
    total = sum(widths.values()) + total_fixed
    
    # If total width exceeds terminal, reduce proportionally
    if total > term_width:
        # Calculate how much we need to reduce
        excess = total - term_width
        # Calculate proportion for each flexible column
        flex_total = widths['title'] + widths['artist'] + widths['album']
        for field in ['title', 'artist', 'album']:
            proportion = widths[field] / flex_total
            reduction = int(excess * proportion)
            widths[field] = max(10, widths[field] - reduction)
    
    return widths

def display_metadata_rich(files: list) -> None:
    """Display metadata using rich formatting."""
    term_width = get_terminal_width()
    widths = get_optimal_widths(files, term_width)
    compact_mode = term_width < 100
    
    table = Table(
        show_header=True,
        header_style="bold magenta",
        border_style="blue",
        title="Music Files",
        title_style="bold cyan",
        show_lines=False,
        padding=(0, 1),
        min_width=80
    )
    
    # Updated column definitions with no_wrap for headers
    table.add_column("Track", justify="right", width=widths['track'], style="cyan", no_wrap=True)
    table.add_column("Title", width=widths['title'], style="green", no_wrap=True)
    table.add_column("Artist", width=widths['artist'], style="yellow", no_wrap=True)
    if not compact_mode:
        table.add_column("Album", width=widths['album'], style="blue", no_wrap=True)
    table.add_column("Year", width=widths['year'], justify="right", style="magenta", no_wrap=True)
    
    for i, file in enumerate(files, 1):
        metadata = file['metadata']
        
        # Get clean year and track number
        year = clean_date(metadata.get('date', ['—'])[0] if 'date' in metadata else '—')
        track_num = metadata.get('tracknumber', [''])[0].split('/')[0] if 'tracknumber' in metadata else ''
        if not track_num and Path(file['filename']).stem[:2].isdigit():
            track_num = Path(file['filename']).stem[:2]
        
        # Build row data with single track number
        row_data = [
            track_num,
            truncate_text(metadata.get('title', ['—'])[0] if 'title' in metadata else '—', 40),
            truncate_text(metadata.get('artist', ['—'])[0] if 'artist' in metadata else '—', 25),
        ]
        if not compact_mode:
            row_data.append(truncate_text(metadata.get('album', ['—'])[0] if 'album' in metadata else '—', 35))
        row_data.append(year)
        
        table.add_row(*row_data)
    
    console.print("\n")
    console.print(table)
    
    # Show summary
    album = metadata.get('album', ['Unknown'])[0] if metadata else 'Unknown'
    artist = metadata.get('artist', ['Unknown'])[0] if metadata else 'Unknown'
    summary = f"\nTracks: {len(files)} • Artist: {artist} • Album: {album} • Year: {year}"
    rprint(f"[bold cyan]{summary}[/bold cyan]")

def display_metadata_simple(files: list) -> None:
    """Fallback display method without rich."""
    for file in files:
        metadata = file['metadata']
        print("\nFile:", file['filename'])
        print("Title:", metadata.get('title', ['—'])[0] if 'title' in metadata else '—')
        print("Artist:", metadata.get('artist', ['—'])[0] if 'artist' in metadata else '—')
        print("Album:", metadata.get('album', ['—'])[0] if 'album' in metadata else '—')
        print("Year:", metadata.get('date', ['—'])[0] if 'date' in metadata else '—')
        print("-" * 50)

def format_message(msg: str, style: str = None) -> str:
    """Format message with optional rich styling."""
    if style:
        return f"[{style}]{msg}[/{style}]"
    return msg

def display_matches(matches: list, query_type: str = "track") -> None:
    """Display metadata matches in a table."""
    if not matches:
        rprint("[yellow]No matches found[/yellow]")
        return

    table = Table(
        show_header=True,
        header_style="bold green",
        title=f"Found {len(matches)} matches",
        title_style="bold cyan",
        show_lines=False,
        padding=(0, 1)
    )
    
    # Columns depend on query type
    if query_type == "track":
        table.add_column("Title", style="green")
        table.add_column("Artist", style="yellow")
        table.add_column("Album", style="blue")
        table.add_column("Year", style="magenta", justify="right")
        
        for match in matches:
            table.add_row(
                match['title'],
                match['artist'],
                match['album'],
                match['year']
            )
    else:  # album
        table.add_column("Album", style="blue")
        table.add_column("Artist", style="yellow")
        table.add_column("Year", style="magenta", justify="right")
        table.add_column("Tracks", style="cyan", justify="right")
        
        for match in matches:
            table.add_row(
                match['title'],
                match['artist'],
                match['year'],
                str(len(match['tracks']))
            )
    
    console.print(table)

def search_metadata(files: list, args) -> None:
    """Search for metadata matches."""
    manager = MetadataManager()
    
    # Search all providers
    results = manager.search_all(files, "album" if len(files) > 1 else "track")
    
    # Let user select from results
    selection = manager.select_metadata(results, files)
    
    if selection:
        if Confirm.ask("Apply selected metadata?"):
            # TODO: Implement metadata application
            rprint("[yellow]Metadata application not yet implemented[/yellow]")

def main():
    parser = argparse.ArgumentParser(
        description="Music Metadata Manager - Organize and update your music metadata"
    )
    parser.add_argument(
        "directory",
        help="Directory containing music files to process"
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Enable automatic metadata correction"
    )
    parser.add_argument(
        "--format",
        default="{artist} - {title}",
        help="Format string for renaming files (e.g. '{artist} - {title}')"
    )
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Scan directory recursively"
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Use compact display mode"
    )
    parser.add_argument(
        "--search",
        action="store_true",
        help="Search for metadata matches"
    )
    parser.add_argument(
        "--no-search",
        action="store_true",
        help="Disable automatic metadata search"
    )
    parser.add_argument(
        "--tracks",
        action="store_true",
        help="Search for individual tracks even in album context"
    )
    
    args = parser.parse_args()
    
    if not Path(args.directory).exists():
        rprint(format_message(f"Error: Directory '{args.directory}' does not exist", "error"))
        return
    
    print(f"\nScanning directory: {args.directory}")
    scanner = MusicScanner(args.directory)
    
    try:
        files = scanner.scan_directory()
        
        if not files:
            rprint(format_message("\nNo music files found!", "warning"))
            return
            
        msg = f"\nFound {len(files)} music files"
        rprint(format_message(msg, "success"))
        display_metadata(files)
        
        # Search by default unless explicitly disabled
        if args.search or not args.no_search:
            search_metadata(files, args)
        
        if args.auto:
            rprint(format_message("\nAuto-correction mode is still under development", "warning"))
        
    except Exception as e:
        rprint(format_message(f"\nError during scanning: {str(e)}", "error"))

if __name__ == "__main__":
    main()
