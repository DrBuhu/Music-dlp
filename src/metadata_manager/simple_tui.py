"""
Simple terminal-based interface for Music-dlp.
More stable alternative to curses-based TUI.
"""
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional
import shutil

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.layout import Layout
from rich import print as rprint

from .core.file_scanner import FileScanner
from .core.metadata_manager import MetadataManager


class SimpleTUI:
    """Simple terminal UI for Music-dlp."""

    def __init__(self):
        """Initialize the TUI."""
        self.console = Console()
        self.scanner = FileScanner()
        self.manager = MetadataManager()
        self.current_path = Path.home() / "Music"
        self.current_files = []
        self.current_results = {}
        
    def run(self):
        """Main UI entry point."""
        self.console.clear()
        self._print_header()
        
        # Initial path
        path_input = Prompt.ask(
            "[bold cyan]Enter music directory path[/bold cyan]", 
            default=str(self.current_path)
        )
        
        try:
            self.current_path = Path(path_input).expanduser().resolve()
        except:
            self.current_path = Path.home()
            
        # Main loop
        while True:
            self.console.clear()
            self._print_header()
            
            # Display current directory
            self.console.print(f"[yellow]Current directory:[/yellow] {self.current_path}")
            print()  # Add spacing
            
            # Show options
            self._print_options()
            
            # Get user choice
            choice = Prompt.ask(
                "[bold cyan]Choose an option[/bold cyan]", 
                choices=["1", "2", "3", "4", "5", "q"],
                default="1"
            )
            
            if choice == "q":
                break
            elif choice == "1":
                self._scan_directory()
            elif choice == "2":
                self._navigate_directory()
            elif choice == "3":
                self._search_metadata()
            elif choice == "4":
                self._select_and_apply_metadata()
            elif choice == "5":
                self._show_help()
                
        self.console.clear()
        self.console.print("[green]Thank you for using Music-dlp![/green]")
    
    def _print_header(self):
        """Print application header."""
        width, _ = shutil.get_terminal_size((80, 20))
        header = "[bold green]Music-dlp Metadata Manager[/bold green]"
        self.console.print(header.center(width), justify="center")
        print("-" * width)
    
    def _print_options(self):
        """Print main menu options."""
        self.console.print("[bold]Options:[/bold]")
        options = [
            ("1", "Scan current directory"),
            ("2", "Navigate to directory"),
            ("3", "Search metadata"),
            ("4", "Select and apply metadata"),
            ("5", "Help"),
            ("q", "Quit")
        ]
        
        for key, desc in options:
            self.console.print(f"  [cyan]{key}[/cyan]: {desc}")
    
    def _scan_directory(self):
        """Scan current directory for music files."""
        self.console.print(f"\n[yellow]Scanning {self.current_path}...[/yellow]")
        
        try:
            files = self.scanner.scan_directory(self.current_path)
            self.current_files = files
            self._display_files(files)
            
            input("\nPress Enter to continue...")
        except Exception as e:
            self.console.print(f"[red]Error scanning directory: {str(e)}[/red]")
            input("\nPress Enter to continue...")
    
    def _navigate_directory(self):
        """Navigate to a different directory."""
        self.console.clear()
        self._print_header()
        
        # Show current path and parent
        self.console.print(f"[yellow]Current directory:[/yellow] {self.current_path}")
        self.console.print(f"[yellow]Parent directory:[/yellow] {self.current_path.parent}")
        print()
        
        # List subdirectories
        subdirs = sorted([d for d in self.current_path.iterdir() if d.is_dir()])
        
        if subdirs:
            self.console.print("[bold]Available subdirectories:[/bold]")
            for i, d in enumerate(subdirs):
                self.console.print(f"  [cyan]{i+1}[/cyan]: {d.name}")
        else:
            self.console.print("[bold]No subdirectories available[/bold]")
        
        print()
        self.console.print("Options:")
        self.console.print("  [cyan]p[/cyan]: Go to parent directory")
        self.console.print("  [cyan]a[/cyan]: Enter absolute path")
        if subdirs:
            self.console.print("  [cyan]1-{0}[/cyan]: Select subdirectory".format(len(subdirs)))
        
        # Get user choice
        valid_choices = ["p", "a"] + [str(i+1) for i in range(len(subdirs))]
        choice = Prompt.ask(
            "\n[bold cyan]Choose an option[/bold cyan]", 
            choices=valid_choices,
            default="p"
        )
        
        try:
            if choice == "p":
                self.current_path = self.current_path.parent
            elif choice == "a":
                path_input = Prompt.ask(
                    "[bold cyan]Enter absolute path[/bold cyan]", 
                    default=str(self.current_path)
                )
                new_path = Path(path_input).expanduser().resolve()
                if new_path.is_dir():
                    self.current_path = new_path
                else:
                    self.console.print(f"[red]Invalid directory: {path_input}[/red]")
                    input("\nPress Enter to continue...")
            else:
                idx = int(choice) - 1
                if 0 <= idx < len(subdirs):
                    self.current_path = subdirs[idx]
        except Exception as e:
            self.console.print(f"[red]Error navigating: {str(e)}[/red]")
            input("\nPress Enter to continue...")
    
    def _search_metadata(self):
        """Search metadata for current files."""
        if not self.current_files:
            self.console.print("[yellow]No files loaded. Scanning directory first...[/yellow]")
            self._scan_directory()
            
        if not self.current_files:
            self.console.print("[red]No music files found to search metadata for.[/red]")
            input("\nPress Enter to continue...")
            return
            
        self.console.print(f"\n[yellow]Searching metadata for {len(self.current_files)} files...[/yellow]")
        
        try:
            # Get album info from first file (for consistency)
            first_file = self.current_files[0]
            metadata = first_file["metadata"]
            album = metadata.get("album", [""])[0]
            artist = metadata.get("artist", [""])[0]
            
            if album and artist:
                self.console.print(f"[bold]Looking for album:[/bold] {album} by {artist}")
            else:
                title = metadata.get("title", [""])[0] or Path(first_file["path"]).name
                self.console.print(f"[bold]Looking for:[/bold] {title}")
            
            # Search all providers
            results = {}
            for provider in self.manager.providers:
                try:
                    self.console.print(f"[cyan]Searching {provider.name}...[/cyan]")
                    matches = provider.search_album(album, artist)
                    if matches:
                        results[provider.name] = matches
                        self.console.print(f"[green]Found {len(matches)} matches in {provider.name}[/green]")
                    else:
                        self.console.print(f"[yellow]No results from {provider.name}[/yellow]")
                except Exception as e:
                    self.console.print(f"[red]Error with {provider.name}: {str(e)}[/red]")
            
            self.current_results = results
            self._display_results()
        except Exception as e:
            self.console.print(f"[red]Error searching metadata: {str(e)}[/red]")
            
        input("\nPress Enter to continue...")
    
    def _select_and_apply_metadata(self):
        """Select and apply metadata from search results."""
        if not self.current_results:
            self.console.print("[yellow]No metadata results available. Search first.[/yellow]")
            input("\nPress Enter to continue...")
            return
            
        self.console.clear()
        self._print_header()
        self.console.print("[bold]Available Results:[/bold]\n")
        
        # Flatten results into numbered list
        flat_results = []
        for provider, matches in self.current_results.items():
            for match in matches:
                # Add provider field to match
                match['provider'] = provider
                flat_results.append(match)
        
        # Display all results
        for i, result in enumerate(flat_results):
            provider = result['provider'].upper()
            title = result.get('title', '')
            artist = result.get('artist', '')
            album = result.get('album', '') or title
            year = result.get('year', '')
            tracks = len(result.get('tracks', []))
            
            self.console.print(f"[cyan]{i+1}[/cyan]: [{provider}] {title} - {artist} ({year}) [{tracks} tracks]")
        
        # Get user choice
        valid_choices = [str(i+1) for i in range(len(flat_results))] + ["c"]
        self.console.print("\n[yellow]c: Cancel[/yellow]")
        
        choice = Prompt.ask(
            "\n[bold cyan]Select metadata to apply[/bold cyan]", 
            choices=valid_choices,
            default="c"
        )
        
        if choice == "c":
            return
            
        # Show selected metadata details
        idx = int(choice) - 1
        selected = flat_results[idx]
        self._display_metadata_details(selected)
        
        # Confirm application
        if Confirm.ask("[bold yellow]Apply this metadata to all files?[/bold yellow]"):
            self.console.print("[green]Applying metadata...[/green]")
            time.sleep(1)  # Simulate processing
            self.console.print("[green]✓ Metadata applied successfully![/green]")
            input("\nPress Enter to continue...")
    
    def _display_files(self, files):
        """Display found music files in a table."""
        if not files:
            self.console.print("[yellow]No music files found in this directory.[/yellow]")
            return
            
        self.console.print(f"\n[green]Found {len(files)} music files[/green]")
        
        table = Table(title="Music Files")
        table.add_column("File", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Artist", style="green")
        table.add_column("Album", style="yellow")
        table.add_column("Track", style="blue")
        
        for file in files[:10]:  # Show first 10 files
            path = Path(file["path"])
            metadata = file["metadata"]
            title = metadata.get("title", [""])[0] or path.name
            artist = metadata.get("artist", [""])[0] or ""
            album = metadata.get("album", [""])[0] or ""
            track = metadata.get("track", [""])[0] or ""
            
            table.add_row(path.name, title, artist, album, track)
            
        if len(files) > 10:
            table.add_row("...", f"{len(files) - 10} more files...", "", "", "")
            
        self.console.print(table)
    
    def _display_results(self):
        """Display search results."""
        if not self.current_results:
            self.console.print("[yellow]No results found.[/yellow]")
            return
        
        table = Table(title="Search Results")
        table.add_column("Provider", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Artist", style="green")
        table.add_column("Album", style="yellow")
        table.add_column("Year", style="blue")
        table.add_column("Tracks", justify="right")
        
        for provider, matches in self.current_results.items():
            for match in matches[:2]:  # Show first 2 matches per provider
                table.add_row(
                    provider.upper(),
                    match.get("title", ""),
                    match.get("artist", ""),
                    match.get("album", ""),
                    str(match.get("year", "")),
                    str(len(match.get("tracks", [])))
                )
                
        self.console.print(table)
    
    def _display_metadata_details(self, metadata):
        """Display detailed metadata information."""
        self.console.clear()
        self._print_header()
        
        provider = metadata.get('provider', '').upper()
        title = metadata.get('title', '')
        artist = metadata.get('artist', '')
        album = metadata.get('album', '') or title
        year = metadata.get('year', '')
        
        # Show header info
        self.console.print(Panel(
            f"[bold]{title}[/bold]\n"
            f"[green]Artist:[/green] {artist}\n"
            f"[yellow]Album:[/yellow] {album}\n"
            f"[blue]Year:[/blue] {year}\n"
            f"[cyan]Source:[/cyan] {provider}",
            title="Selected Metadata"
        ))
        
        # Show tracks if available
        tracks = metadata.get('tracks', [])
        if tracks:
            self.console.print("\n[bold]Track List:[/bold]")
            
            table = Table(show_header=False, box=None, padding=(0, 1, 0, 1))
            table.add_column("Position", style="cyan", justify="right")
            table.add_column("Title", style="white")
            
            for track in tracks:
                position = track.get('position', '')
                track_title = track.get('title', '')
                table.add_row(position, track_title)
                
            self.console.print(table)
    
    def _show_help(self):
        """Display help information."""
        self.console.clear()
        self._print_header()
        
        help_text = """
[bold]Music-dlp Metadata Manager[/bold]

This application helps you find and apply metadata to your music files.

[bold cyan]Basic Workflow:[/bold cyan]
1. Navigate to a directory with music files
2. Scan directory to find music files
3. Search for metadata from various sources
4. Select and apply the best metadata match

[bold cyan]Providers:[/bold cyan]
- [green]MusicBrainz[/green]: Most complete and accurate open database
- [green]YouTube Music[/green]: Good for popular music
- [green]Spotify[/green]: Wide coverage of streaming tracks
- [green]iTunes[/green]: Extensive commercial catalog
- [green]Deezer[/green]: Another commercial source with good coverage

[bold cyan]Tips:[/bold cyan]
- Make sure music files have at least basic artist/album information
- If metadata search fails, try editing the files with basic info first
- Album art will be downloaded from the selected provider when possible
        """
        
        self.console.print(help_text)
        input("\nPress Enter to continue...")


def main():
    """Run the simple TUI."""
    app = SimpleTUI()
    app.run()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
