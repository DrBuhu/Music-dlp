"""Textual TUI for Music-dlp."""
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DirectoryTree, DataTable, Button
from textual.containers import Container, Horizontal
from textual.binding import Binding
from textual import work
from pathlib import Path
import os

from .core.file_scanner import FileScanner
from .core.metadata_manager import MetadataManager

class MusicDLPApp(App):
    """Main TUI application."""
    
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("s", "search", "Search", show=True)
    ]
    
    def __init__(self):
        super().__init__()
        self.scanner = FileScanner()
        self.manager = MetadataManager()
        self.current_files = []
        self.current_path = Path.home()
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Container():
            with Horizontal():
                # Left sidebar with directory tree
                with Container(id="sidebar"):
                    yield Button("Home", id="home", variant="primary")
                    yield Button("Parent", id="parent", variant="primary")
                    yield DirectoryTree(str(self.current_path), id="files")
                
                # Main content area with results
                with Container(id="main"):
                    yield DataTable(id="files_table")  # Files en la carpeta actual
                    yield DataTable(id="preview_table")  # Preview de servicios
                    yield DataTable(id="results_table")  # Resultados detallados
        yield Footer()
    
    def on_mount(self) -> None:
        """Setup on app start."""
        # Configure files table
        files_table = self.query_one("#files_table", DataTable)
        files_table.add_columns("Track", "Title", "Artist", "Album", "Year")
        
        # Configure preview table
        preview_table = self.query_one("#preview_table", DataTable)
        preview_table.add_columns("Service", "Album Info", "Tracks", "Year", "Score")
        
        # Configure results table
        results_table = self.query_one("#results_table", DataTable)
        results_table.add_columns("Source", "Title", "Artist", "Album", "Year", "Score", "Tracks")
        
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

        # Clear tables
        self.call_from_thread(self.clear_tables)
        
        # Get album info from first file
        first_file = self.current_files[0]
        metadata = first_file["metadata"]
        album = metadata.get("album", [""])[0]
        artist = metadata.get("artist", [""])[0]
        
        # Search album first for preview
        if album and artist:
            preview_results = {}
            for provider in self.manager.providers:
                try:
                    matches = provider.search_album(album, artist)
                    if matches:
                        best_match = matches[0]
                        # Add to preview table
                        self.call_from_thread(
                            self.query_one("#preview_table", DataTable).add_row,
                            provider.name.upper(),
                            f"{best_match.get('artist', '')} - {best_match.get('title', '')}",
                            str(len(best_match.get('tracks', []))),
                            best_match.get('year', ''),
                            f"{best_match.get('score', 0):.1f}"
                        )
                        preview_results[provider.name] = matches
                except Exception as e:
                    continue

        # Then search individual tracks
        for file in self.current_files:
            metadata = file["metadata"]
            title = metadata.get("title", [""])[0]
            artist = metadata.get("artist", [""])[0]
            
            if not title:
                continue
                
            results = self.manager.search_all([{
                'metadata': {
                    'title': [title],
                    'artist': [artist]
                }
            }])
            
            if results:
                # Show matches in results table
                for provider, matches in results.items():
                    for match in matches:
                        self.call_from_thread(
                            self.query_one("#results_table", DataTable).add_row,
                            provider,
                            match.get("title", ""),
                            match.get("artist", ""),
                            match.get("album", ""),
                            match.get("year", ""),
                            f"{match.get('score', 0):.1f}",
                            str(len(match.get('tracks', [])))
                        )
    
    def clear_tables(self) -> None:
        """Clear all tables."""
        self.query_one("#files_table", DataTable).clear()
        self.query_one("#results_table", DataTable).clear()
        self.query_one("#preview_table", DataTable).clear()
    
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

def main():
    """Run the application."""
    app = MusicDLPApp()
    app.run()

if __name__ == "__main__":
    main()
