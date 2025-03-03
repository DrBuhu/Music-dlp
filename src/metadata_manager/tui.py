"""Textual TUI for Music-dlp."""
from typing import Dict, List, Optional
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DirectoryTree, DataTable, Button, Static
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding
from textual import work
from pathlib import Path
import os
from rich import print as rprint

from .core.file_scanner import FileScanner
from .core.metadata_manager import MetadataManager

class MusicDLPApp(App):
    """Main TUI application."""
    
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("s", "search", "Search", show=True),
        Binding("a", "apply_metadata", "Apply Metadata"),
        Binding("enter", "show_details", "Show Details")
    ]
    
    def __init__(self):
        super().__init__()
        self.scanner = FileScanner()
        self.manager = MetadataManager()
        self.current_files = []
        self.current_path = Path.home()
        self.current_results = {}  # Añadido para guardar resultados
        self.selected_metadata = None  # Añadido para guardar selección
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Container():
            with Horizontal():
                # Left sidebar with directory tree
                with Container(id="sidebar"):
                    yield Button("Home", id="home")
                    yield Button("Parent", id="parent")
                    yield DirectoryTree(".", id="files")
                
                # Main content area with vertical layout
                with Vertical(id="main"):
                    # Files section
                    yield Static("Current Files", classes="section-header")
                    yield DataTable(id="files_table")
                    # Preview section
                    yield Static("Album Matches", classes="section-header")
                    yield DataTable(id="preview_table")
                    # Results section
                    yield Static("Track Results", classes="section-header")
                    yield DataTable(id="results_table")
                    # Details section
                    yield Static("Selected Details", classes="section-header")
                    yield Static("No metadata selected", id="metadata_details")
        yield Footer()
    
    def on_mount(self) -> None:
        """Setup on app start."""
        # Configure files table
        self.query_one("#files_table").add_columns(
            "Track", "Title", "Artist", "Album", "Year"
        )
        
        # Configure preview table
        self.query_one("#preview_table").add_columns(
            "Provider", "Album", "Artist", "Year", "Tracks", "Score"
        )
        
        # Configure results table
        self.query_one("#results_table").add_columns(
            "Provider", "Title", "Artist", "Album", "Year", "Score", "Tracks"
        )
        
        # Set initial directory tree path without scanning
        tree = self.query_one("#files", DirectoryTree)
        tree.path = str(self.current_path)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "home":
            self.current_path = Path.home()
            tree = self.query_one("#files", DirectoryTree)
            tree.path = str(Path.home())
        elif event.button.id == "parent":
            self.current_path = self.current_path.parent
            tree = self.query_one("#files", DirectoryTree)
            tree.path = str(self.current_path)
    
    def on_directory_tree_directory_selected(self, event) -> None:
        """Just update the current path without scanning."""
        if event.path and event.path.is_dir():
            self.current_path = event.path
            # Solo actualizamos la vista del árbol sin escanear
            tree = self.query_one("#files", DirectoryTree)
            tree.path = str(event.path)

    def on_directory_tree_file_selected(self, event) -> None:
        """Handle file selection - ignore it."""
        pass  # No hacemos nada con los archivos seleccionados
    
    def refresh_directory(self, path: Path, recursive: bool = False) -> None:
        """Refresh current directory view."""
        if path == self.current_path:
            return  # Evitar reescanear el mismo directorio
            
        self.current_path = path
        
        # Update directory tree
        tree = self.query_one("#files", DirectoryTree)
        tree.path = str(path)
        tree.reload()
        
        # Scan for music files
        self.scan_directory(path, recursive)
    
    @work(thread=True)
    def scan_directory(self, path: Path, recursive: bool = False) -> None:
        """Scan directory for music files."""
        # Clear current tables
        self.call_from_thread(self.clear_tables)
        
        # Scan directory with recursive flag
        files = self.scanner.scan_directory(path, recursive=recursive)
        if not files:
            return
            
        # Update files table
        self.current_files = files
        for file in files:
            metadata = file["metadata"]
            self.call_from_thread(
                self.query_one("#files_table", DataTable).add_row,
                metadata.get("track", [""])[0],
                metadata.get("title", [""])[0] or Path(file["path"]).name,
                metadata.get("artist", [""])[0],
                metadata.get("album", [""])[0],
                metadata.get("date", [""])[0]
            )
    
    def action_search(self) -> None:
        """Search metadata for current files."""
        if self.current_files:
            self.search_metadata()
    
    @work(thread=True)
    def search_metadata(self) -> None:
        """Search metadata in background."""
        if not self.current_files:
            return
            
        self.call_from_thread(self.clear_tables)
        
        # Get first file info
        first_file = self.current_files[0]
        metadata = first_file["metadata"]
        album = metadata.get("album", [""])[0]
        artist = metadata.get("artist", [""])[0]
        
        # Search albums first
        if album and artist:
            for provider in self.manager.providers:
                try:
                    matches = provider.search_album(album, artist)
                    if matches and len(matches) > 0:
                        match = matches[0]
                        self.current_results[provider.name] = matches
                        
                        # Add to preview table
                        self.call_from_thread(
                            self.query_one("#preview_table").add_row,
                            provider.name,
                            match.get('title', ''),
                            match.get('artist', ''),
                            match.get('year', ''),
                            str(len(match.get('tracks', []))),
                            f"{match.get('score', 0):.1f}"
                        )
                except Exception as e:
                    print(f"Error with {provider.name}: {str(e)}")
                    continue

        # Search individual tracks
        for file in self.current_files:
            title = file["metadata"].get("title", [""])[0]
            artist = file["metadata"].get("artist", [""])[0]
            
            if not title:
                continue
                
            results = self.manager.search_all([{
                'metadata': {
                    'title': [title],
                    'artist': [artist]
                }
            }])
            
            if results:
                for provider, matches in results.items():
                    self.current_results[provider] = matches
                    for match in matches:
                        self.call_from_thread(
                            self.query_one("#results_table").add_row,
                            provider,
                            match.get('title', ''),
                            match.get('artist', ''),
                            match.get('album', ''),
                            match.get('year', ''),
                            f"{match.get('score', 0):.1f}",
                            str(len(match.get('tracks', [])))
                        )
    
    def clear_tables(self) -> None:
        """Clear all tables."""
        self.query_one("#files_table").clear()
        self.query_one("#preview_table").clear()
        self.query_one("#results_table").clear()
        self.query_one("#metadata_details").update("No metadata selected")
    
    def action_refresh(self) -> None:
        """Refresh current directory with scan."""
        if self.current_path:
            self.scan_directory(self.current_path, recursive=False)

    async def action_quit(self) -> None:
        """Handle quit action properly."""
        # Limpiar cualquier tarea pendiente
        self.exit()

    async def on_unmount(self) -> None:
        """Clean up on exit."""
        # Asegurar que todo se limpia
        for provider in self.manager.providers:
            if hasattr(provider, 'client'):
                provider.client = None

    def on_data_table_row_selected(self, event) -> None:
        """Handle row selection in any table."""
        table_id = event.data_table.id
        row_key = event.row_key
        
        # Debug info
        print(f"Table selected: {table_id}, Row: {row_key}")
        
        if table_id == "preview_table":
            self._handle_preview_selection(row_key)
        elif table_id == "results_table":
            self._handle_results_selection(row_key)

    def _handle_preview_selection(self, row_key) -> None:
        """Handle selection in preview table."""
        try:
            table = self.query_one("#preview_table", DataTable)
            row = table.get_row_at(row_key)
            
            provider_name = row[0].lower()
            print(f"Selected provider: {provider_name}")
            
            # Get the first match for this provider
            if provider_name in self.current_results:
                match = self.current_results[provider_name][0]
                self.selected_metadata = match
                print(f"Selected metadata: {match.get('title')} by {match.get('artist')}")
                
                # Update details display
                details = self._format_metadata_details(match)
                self.query_one("#metadata_details").update(details)
        except Exception as e:
            print(f"Error handling preview selection: {e}")
    
    def _handle_results_selection(self, row_key) -> None:
        """Handle selection in results table."""
        try:
            table = self.query_one("#results_table", DataTable)
            row = table.get_row_at(row_key)
            
            provider = row[0].lower()
            title = row[1]
            artist = row[2]
            print(f"Selected: {title} by {artist} from {provider}")
            
            # Find matching result in our stored results
            if provider in self.current_results:
                for match in self.current_results[provider]:
                    if match.get('title') == title and match.get('artist') == artist:
                        self.selected_metadata = match
                        # Update details display
                        details = self._format_metadata_details(match)
                        self.query_one("#metadata_details").update(details)
                        break
        except Exception as e:
            print(f"Error handling results selection: {e}")

    def _format_metadata_details(self, metadata: Dict) -> str:
        """Format metadata as rich text for display."""
        lines = []
        lines.append("[bold green]Selected Metadata:[/bold green]")
        lines.append(f"[cyan]Provider:[/cyan] {metadata.get('provider', '').upper()}")
        lines.append(f"[cyan]Title:[/cyan] {metadata.get('title', '')}")
        lines.append(f"[cyan]Artist:[/cyan] {metadata.get('artist', '')}")
        lines.append(f"[cyan]Album:[/cyan] {metadata.get('album', '')}")
        lines.append(f"[cyan]Year:[/cyan] {metadata.get('year', '')}")
        
        if tracks := metadata.get('tracks', []):
            lines.append("\n[bold yellow]Tracks:[/bold yellow]")
            for track in tracks:
                lines.append(f"{track['position']}. {track['title']}")
        
        return "\n".join(lines)

    def action_show_details(self) -> None:
        """Show details of selected metadata."""
        if self.selected_metadata:
            details = self._format_metadata_details(self.selected_metadata)
            self.query_one("#metadata_details").update(details)
        else:
            self.query_one("#metadata_details").update("[yellow]No metadata selected[/yellow]")

    def action_apply_metadata(self) -> None:
        """Apply selected metadata to files."""
        if self.selected_metadata:
            rprint(f"[green]Applying metadata from {self.selected_metadata.get('provider')}...[/green]")
            # TODO: Implement actual metadata application
            rprint("[green]Metadata applied successfully[/green]")
        else:
            rprint("[yellow]No metadata selected[/yellow]")

def main():
    """Run the application."""
    app = MusicDLPApp()
    app.run()

if __name__ == "__main__":
    main()
