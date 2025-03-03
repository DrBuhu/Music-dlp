"""Terminal User Interface for Music-dlp using Textual."""
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Generator, Iterable
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Button, Static, Input, DirectoryTree
from textual.widgets import DataTable, Label
from textual import events
from textual.reactive import reactive
from rich import print as rprint

from .core.file_scanner import FileScanner
from .core.metadata_manager import MetadataManager

# Recent directories storage file
CONFIG_DIR = os.path.expanduser("~/.config/music-dlp")
RECENT_PATHS_FILE = os.path.join(CONFIG_DIR, "recent_paths.txt")

class MusicMetadataManagerApp(App):
    """Textual TUI app for Music-dlp."""
    
    TITLE = "Music Metadata Manager"
    CSS_PATH = "styles/tui.css"
    BINDINGS = [
        Binding(key="q", action="quit", description="Quit"),
        Binding(key="s", action="search", description="Search Metadata"),
        Binding(key="o", action="open_folder", description="Open Folder"),
        Binding(key="r", action="refresh", description="Refresh"),
        Binding(key="/", action="toggle_search", description="Search"),
    ]
    
    # Reactive properties
    current_directory = reactive("")
    selected_files = reactive([])
    search_results = reactive([])
    
    def __init__(self):
        super().__init__()
        self.file_scanner = FileScanner()
        self.metadata_manager = MetadataManager()
        self.recent_paths = self._load_recent_paths()
        self.last_searched_directory = None
        self.recursive_search = False
        
    def _load_recent_paths(self) -> List[str]:
        """Load recent paths from file."""
        try:
            if not os.path.exists(CONFIG_DIR):
                os.makedirs(CONFIG_DIR)
                
            if os.path.exists(RECENT_PATHS_FILE):
                with open(RECENT_PATHS_FILE, "r") as f:
                    paths = [line.strip() for line in f.readlines() if line.strip()]
                    return paths[-5:]  # Keep only the 5 most recent
        except Exception as e:
            rprint(f"Error loading recent paths: {e}")
        return []
    
    def _save_recent_path(self, path: str):
        """Save path to recent paths file."""
        if not path or not os.path.isdir(path):
            return
            
        # Add to memory list
        if path in self.recent_paths:
            self.recent_paths.remove(path)
        self.recent_paths.insert(0, path)  # Add to front
        self.recent_paths = self.recent_paths[:5]  # Keep only last 5
        
        # Save to file
        try:
            if not os.path.exists(CONFIG_DIR):
                os.makedirs(CONFIG_DIR)
                
            with open(RECENT_PATHS_FILE, "w") as f:
                f.write("\n".join(self.recent_paths))
        except Exception as e:
            rprint(f"Error saving recent paths: {e}")
    
    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield Header()
        
        with Container():
            # Left sidebar with directory navigation
            with Container(id="sidebar"):
                yield Label("Navigation", classes="sidebar-header")
                with Container(id="directory_buttons"):
                    yield Button("Open Directory", id="open_dir", variant="primary")
                    yield Button("Home", id="home_dir")
                    yield Button("Music", id="music_dir")
                    yield Button("Downloads", id="downloads_dir")
                
                yield Label("Recent Directories", classes="sidebar-header")
                with Vertical(id="recent_paths"):
                    # Recent paths will be populated dynamically
                    pass
                
                # Search controls moved to sidebar
                with Container(id="search_controls"):
                    yield Label("Search Options", classes="sidebar-header")
                    with Horizontal():
                        yield Button("Search Now", id="search_button", variant="primary")
                    with Horizontal():
                        yield Button("Recursive", id="recursive", variant="default")
                
            # Main content area
            with Container(id="main_content"):
                # Current directory display
                yield Static(id="current_dir", classes="path-display")
                
                # File display
                yield Label("Music Files", classes="section-header")
                yield DataTable(id="file_table")
                
                # Search results 
                yield Label("Search Results", id="results_label", classes="section-header")
                yield DataTable(id="results_table")
                
                # Track details display will appear when a search result is selected
                with Container(id="track_details"):
                    yield Label("Track Details", classes="track-details-header")
                    yield Static(id="track_listing", classes="track-listing")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the app on mount."""
        # Set up the tables
        file_table = self.query_one("#file_table", DataTable)
        file_table.cursor_type = "row"
        file_table.add_columns("Track", "Title", "Artist", "Album", "Year")
        
        results_table = self.query_one("#results_table", DataTable)
        results_table.cursor_type = "row"
        results_table.add_columns("Provider", "Title", "Artist", "Year", "Score")
        
        # Update the current directory display
        self.query_one("#current_dir", Static).update("No directory selected")
        
        # Clear the track listing
        self.query_one("#track_listing", Static).update("")
        
        # Add the recent paths
        self._update_recent_paths()
        
        # Show default directory if available
        if self.recent_paths:
            self._change_directory(self.recent_paths[0])
    
    def _update_recent_paths(self) -> None:
        """Update the recent paths buttons."""
        recent_paths_container = self.query_one("#recent_paths", Vertical)
        recent_paths_container.remove_children()
        
        for path in self.recent_paths:
            path_short = os.path.basename(path) or path
            button = Button(f"📁 {path_short}", classes="recent-button")
            button.path = path  # Store the full path as attribute
            recent_paths_container.mount(button)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        # Directory navigation buttons
        if event.button.id == "open_dir":
            self.action_open_folder()
        elif event.button.id == "home_dir":
            home_dir = os.path.expanduser("~")
            self._change_directory(home_dir)
        elif event.button.id == "music_dir":
            music_dir = os.path.join(os.path.expanduser("~"), "Music")
            if os.path.isdir(music_dir):
                self._change_directory(music_dir)
        elif event.button.id == "downloads_dir":
            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            if os.path.isdir(downloads_dir):
                self._change_directory(downloads_dir)
        elif event.button.id == "search_button":
            self.action_search()
        elif event.button.id == "recursive":
            # Toggle recursive mode
            self.recursive_search = not self.recursive_search
            if self.recursive_search:
                event.button.variant = "success"
            else:
                event.button.variant = "default"
        
        # Recent path buttons
        if hasattr(event.button, "path"):
            self._change_directory(event.button.path)
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle table row selection."""
        table_id = event.data_table.id
        
        if table_id == "file_table":
            # Store selected files for metadata search
            row = event.data_table.get_row(event.row_key)
            self.selected_files = [{"row": event.row_key, "data": row}]
            
        elif table_id == "results_table":
            # Display track details when a result is selected
            if event.row_key < len(self.search_results):
                result = self.search_results[event.row_key]
                self._display_result_details(result)
    
    def _display_result_details(self, result: Dict) -> None:
        """Display detailed information about a search result."""
        track_listing = self.query_one("#track_listing", Static)
        
        # Format details
        title = result.get("title", "Unknown Title")
        artist = result.get("artist", "Unknown Artist")
        album = result.get("album", title)  # Use title as fallback for album
        year = result.get("year", "")
        provider = result.get("provider", "unknown")
        
        # Create header
        details = f"[b]{title}[/b] by [b]{artist}[/b]"
        if year:
            details += f" ({year})"
        details += f"\nSource: {provider.title()}"
        
        # Add tracks if available
        tracks = result.get("tracks", [])
        if tracks:
            details += "\n\n[b]Track listing:[/b]\n"
            for track in tracks:
                track_num = track.get("position", "?")
                track_title = track.get("title", "Unknown")
                track_artist = track.get("artist", artist)  # Default to album artist
                
                # Only show artist if different from album artist
                if track_artist != artist:
                    details += f"{track_num}. {track_title} - {track_artist}\n"
                else:
                    details += f"{track_num}. {track_title}\n"
        
        track_listing.update(details)
    
    def _change_directory(self, path: str) -> None:
        """Change the current directory and scan for music files."""
        if not os.path.isdir(path):
            self.notify(f"Invalid directory: {path}", severity="error")
            return
        
        try:
            # Update the display
            path_display = self.query_one("#current_dir", Static)
            path_display.update(f"📁 {path}")
            
            # Scan for music files
            files = self.file_scanner.scan_directory(path, recursive=False)
            
            # Update the file table
            file_table = self.query_one("#file_table", DataTable)
            file_table.clear()
            
            if files:
                for file in files:
                    metadata = file["metadata"]
                    track = metadata.get("track", [""])[0]
                    title = metadata.get("title", [""])[0] or os.path.basename(file["path"])
                    artist = metadata.get("artist", [""])[0]
                    album = metadata.get("album", [""])[0]
                    year = metadata.get("date", [""])[0]
                    
                    file_table.add_row(track, title, artist, album, year)
            
            # Clear search results and track details
            results_table = self.query_one("#results_table", DataTable)
            results_table.clear()
            self.query_one("#track_listing", Static).update("")
            
            # Save to recent paths
            self.current_directory = path
            self._save_recent_path(path)
            self._update_recent_paths()
            
            # Store for searching
            self.last_searched_directory = path
            
        except Exception as e:
            self.notify(f"Error: {str(e)}", severity="error")
    
    def action_open_folder(self) -> None:
        """Open a folder dialog."""
        # This is a placeholder - Textual doesn't have a built-in folder picker
        # We'll use a simple workaround
        self.notify("Enter directory path in prompt", severity="information")
        
        # In a real application, you'd use a proper directory picker dialog
        path = os.getcwd()  # Default to current directory
        
        # Ask for user input using an overlay
        def get_directory_path() -> None:
            def submit_path(path: str) -> None:
                # Expand home directory and make absolute
                expanded_path = os.path.abspath(os.path.expanduser(path))
                if os.path.isdir(expanded_path):
                    self._change_directory(expanded_path)
                else:
                    self.notify(f"Invalid directory: {expanded_path}", severity="error")
            
            # This is a simplified version - a real app would use a modal dialog
            self.notify(f"Enter path (e.g. ~/Music):", severity="information")
            path = input("Directory path: ")  # This will break the TUI temporarily
            submit_path(path)
            
        # This is not ideal but works for demo purposes
        # In a real app, use a proper TUI dialog or modal
        self.set_timer(0.1, get_directory_path)
    
    def action_search(self) -> None:
        """Search for metadata for the selected files."""
        if not self.current_directory:
            self.notify("No directory selected", severity="warning")
            return
        
        if not self.selected_files:
            self.notify("No files selected", severity="warning")
            return
        
        try:
            # Get the selected files
            files = []
            for file_info in self.selected_files:
                # In a real app, you'd look up the actual file data
                # For demo, we'll reconstruct from the table
                row_index = file_info["row"]
                data = file_info["data"]
                
                # Extract metadata from the row
                track = data[0]
                title = data[1]
                artist = data[2]
                album = data[3]
                year = data[4]
                
                files.append({
                    "metadata": {
                        "track": [track],
                        "title": [title],
                        "artist": [artist],
                        "album": [album],
                        "date": [year]
                    }
                })
            
            # Perform search
            self.notify("Searching for metadata...", severity="information")
            
            # This would normally happen in a background task
            # but for demo purposes we'll do it synchronously
            all_results = self.metadata_manager.search_all(files)
            
            # Clear existing results
            results_table = self.query_one("#results_table", DataTable)
            results_table.clear()
            self.search_results = []
            
            # Flatten and process results
            for provider, results in all_results.items():
                for result in results:
                    provider_name = result.get("provider", provider)
                    title = result.get("title", "Unknown")
                    artist = result.get("artist", "Unknown")
                    year = result.get("year", "")
                    score = result.get("score", 0)
                    
                    # Add to UI table
                    score_str = f"{score:.1f}" if isinstance(score, float) else str(score)
                    results_table.add_row(provider_name, title, artist, year, score_str)
                    
                    # Store for later reference
                    self.search_results.append(result)
            
            # Show message if no results
            if not self.search_results:
                self.notify("No metadata found", severity="warning")
        
        except Exception as e:
            self.notify(f"Error: {str(e)}", severity="error")
    
    def action_refresh(self) -> None:
        """Refresh the current directory."""
        if self.current_directory:
            self._change_directory(self.current_directory)
    
    def action_toggle_search(self) -> None:
        """Toggle search mode."""
        self.notify("Search mode not implemented yet", severity="information")
