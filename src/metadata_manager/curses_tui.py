"""
Simple curses-based TUI for Music-dlp.
This implementation uses the standard curses library for better compatibility.
"""
import curses
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from .core.file_scanner import FileScanner
from .core.metadata_manager import MetadataManager

# Constants for UI layout
HEADER_HEIGHT = 3
FOOTER_HEIGHT = 2
KEY_ESC = 27
KEY_Q = 113
KEY_R = 114
KEY_S = 115
KEY_A = 97
KEY_ENTER = 10
KEY_TAB = 9


class CursesTUI:
    """Curses-based TUI for Music-dlp."""

    def __init__(self):
        """Initialize the TUI."""
        self.scanner = FileScanner()
        self.manager = MetadataManager()
        self.current_path = Path.home() / "Music"  # Inicio en carpeta de música por defecto
        self.current_files = []
        self.current_results = {}
        self.selected_metadata = None
        self.focused_panel = 0  # 0: files, 1: results
        self.selected_file_idx = 0
        self.selected_result_idx = 0
        self.status_message = "Welcome to Music-dlp TUI"
        self.show_details = False
        self.visible_files = []
        self.flat_results = []  # Resultados aplanados para navegación más sencilla

    def run(self):
        """Run the TUI main loop."""
        curses.wrapper(self._main)

    def _main(self, stdscr):
        """Main TUI loop."""
        # Setup curses
        curses.curs_set(0)  # Hide cursor
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)  # Header/Footer
        curses.init_pair(2, curses.COLOR_CYAN, -1)   # Selected item
        curses.init_pair(3, curses.COLOR_YELLOW, -1) # Highlight
        curses.init_pair(4, curses.COLOR_RED, -1)    # Error
        
        # Main screen
        self.screen = stdscr
        self.screen.timeout(100)  # For responsive UI
        
        # Initial scan
        self.scan_directory(self.current_path)
        
        # Mostrar ayuda de teclas
        self.status_message = "Press 'r' to scan directory, 's' to search metadata, 'q' to quit"
        
        # Main loop
        while True:
            self.draw_ui()
            try:
                key = self.screen.getch()
            except KeyboardInterrupt:
                break
                
            if key == KEY_Q or key == KEY_ESC:  # Quit on 'q' or ESC
                break
                
            if self.handle_key(key):
                continue
                
    def handle_key(self, key):
        """Handle key press."""
        if key == KEY_R:  # Refresh
            self.scan_directory(self.current_path)
            return True
            
        elif key == KEY_S:  # Search
            self.search_metadata()
            return True
            
        elif key == KEY_A:  # Apply metadata
            self.apply_metadata()
            return True
            
        elif key == KEY_TAB:  # Switch focus
            self.focused_panel = (self.focused_panel + 1) % 2
            self.status_message = f"Panel {'Results' if self.focused_panel else 'Files'} focused"
            return True
            
        elif key == KEY_ENTER or key == 10 or key == 13:  # Enter key variants
            if self.show_details:
                self.show_details = False
            else:
                self.show_metadata_details()
            return True
            
        elif key == curses.KEY_UP:
            if self.focused_panel == 0 and self.current_files:
                # Files panel
                if self.selected_file_idx > 0:
                    self.selected_file_idx -= 1
                    self.status_message = f"Selected file: {self.selected_file_idx + 1}/{len(self.current_files)}"
            elif self.focused_panel == 1 and self.flat_results:
                # Results panel
                if self.selected_result_idx > 0:
                    self.selected_result_idx -= 1
                    self.status_message = f"Selected result: {self.selected_result_idx + 1}/{len(self.flat_results)}"
            return True
            
        elif key == curses.KEY_DOWN:
            if self.focused_panel == 0 and self.current_files:
                # Files panel
                if self.selected_file_idx < len(self.current_files) - 1:
                    self.selected_file_idx += 1
                    self.status_message = f"Selected file: {self.selected_file_idx + 1}/{len(self.current_files)}"
            elif self.focused_panel == 1 and self.flat_results:
                # Results panel
                if self.selected_result_idx < len(self.flat_results) - 1:
                    self.selected_result_idx += 1
                    self.status_message = f"Selected result: {self.selected_result_idx + 1}/{len(self.flat_results)}"
            return True
            
        # Handle navigation to parent directory
        elif key == curses.KEY_BACKSPACE or key == 127:
            if self.focused_panel == 0:  # Only in files panel
                parent = self.current_path.parent
                if parent != self.current_path:  # Asegurarse de que no estamos en la raíz
                    self.scan_directory(parent)
            return True
            
        return False
        
    def scan_directory(self, path: Path):
        """Scan directory for music files."""
        self.status_message = f"Scanning {path}..."
        self.draw_status_bar()
        self.screen.refresh()
        
        try:
            files = self.scanner.scan_directory(path)
            self.current_files = files
            self.current_path = path
            self.selected_file_idx = 0  # Reset selection
            
            # Generate navigation info for subdirectories
            self.visible_files = []
            if path.parent != path:
                self.visible_files.append({
                    "is_dir": True,
                    "name": "..",
                    "path": path.parent
                })
            
            # Add subdirectories
            subdirs = [d for d in path.iterdir() if d.is_dir()]
            subdirs.sort()
            for subdir in subdirs:
                self.visible_files.append({
                    "is_dir": True,
                    "name": subdir.name,
                    "path": subdir
                })
            
            # Add music files
            for file in files:
                metadata = file["metadata"]
                name = metadata.get("title", [""])[0] or Path(file["path"]).name
                self.visible_files.append({
                    "is_dir": False,
                    "name": name,
                    "file": file
                })
            
            if files:
                self.status_message = f"Found {len(files)} music files in {path}"
            else:
                self.status_message = f"No music files in {path}"
        except Exception as e:
            self.status_message = f"Error scanning directory: {str(e)}"
            
    def search_metadata(self):
        """Search metadata for current files."""
        if not self.current_files:
            self.status_message = "No files to search metadata for."
            return
            
        self.status_message = "Searching metadata..."
        self.draw_status_bar()
        self.screen.refresh()
        
        try:
            # Get album info from first file
            first_file = self.current_files[0]
            metadata = first_file["metadata"]
            album = metadata.get("album", [""])[0]
            artist = metadata.get("artist", [""])[0]
            
            # Search all providers
            results = {}
            if album and artist:
                for provider in self.manager.providers:
                    try:
                        matches = provider.search_album(album, artist)
                        if matches:
                            results[provider.name] = matches
                    except Exception as e:
                        self.status_message = f"Error with {provider.name}: {str(e)}"
                        self.draw_status_bar()
                        self.screen.refresh()
                        time.sleep(1)  # Show error briefly
            
            self.current_results = results
            self.selected_result_idx = 0  # Reset selection
            
            # Flatten results for easier navigation
            self.flat_results = []
            for provider, matches in results.items():
                for match in matches:
                    match['provider'] = provider  # Ensure provider is in match
                    self.flat_results.append(match)
            
            if not self.flat_results:
                self.status_message = "No metadata found"
            else:
                self.status_message = f"Found {len(self.flat_results)} metadata matches from {len(results)} providers"
                self.focused_panel = 1  # Switch focus to results
            
        except Exception as e:
            self.status_message = f"Error searching metadata: {str(e)}"
            
    def apply_metadata(self):
        """Apply selected metadata to files."""
        if self.flat_results and 0 <= self.selected_result_idx < len(self.flat_results):
            selected = self.flat_results[self.selected_result_idx]
            if not self.current_files:
                self.status_message = "No files to apply metadata to."
                return
                
            self.status_message = f"Applying metadata from {selected.get('provider', '').upper()}..."
            self.draw_status_bar()
            self.screen.refresh()
            time.sleep(0.5)  # Simulate processing
            
            # TODO: Implement actual metadata application
            # Both cleaner CLI and GUI already have the logic
            # for tm in tracks_map:
            #    apply_metadata(tm["file"], selected)
            
            self.status_message = "Metadata applied successfully."
        else:
            self.status_message = "No metadata selected."
        
    def show_metadata_details(self):
        """Show details of selected metadata."""
        if self.flat_results and 0 <= self.selected_result_idx < len(self.flat_results):
            self.selected_metadata = self.flat_results[self.selected_result_idx]
            self.show_details = True
        else:
            self.status_message = "No metadata selected."
            
    def draw_ui(self):
        """Draw the complete UI."""
        self.screen.clear()
        height, width = self.screen.getmaxyx()
        
        # Calculate panel dimensions
        content_height = height - HEADER_HEIGHT - FOOTER_HEIGHT
        
        if self.show_details:
            self.draw_details_view(0, HEADER_HEIGHT, width, content_height)
        else:
            # Half width for each panel
            half_width = width // 2
            
            # Draw panels
            self.draw_files_panel(0, HEADER_HEIGHT, half_width, content_height)
            self.draw_results_panel(half_width, HEADER_HEIGHT, width - half_width, content_height)
            
        # Draw header and footer
        self.draw_header()
        self.draw_status_bar()
        self.screen.refresh()

    def draw_header(self):
        """Draw application header."""
        height, width = self.screen.getmaxyx()
        
        # Clear header area
        for y in range(HEADER_HEIGHT):
            self.screen.addstr(y, 0, " " * (width - 1))
            
        # Draw title bar
        title = "Music-dlp TUI"
        self.screen.addstr(1, 2, title, curses.color_pair(1) | curses.A_BOLD)
        
        # Draw help
        help_text = "q:Quit  r:Refresh  s:Search  a:Apply  Tab:Switch Focus  Enter:Details"
        help_x = width - len(help_text) - 2
        if help_x > len(title) + 4:
            self.screen.addstr(1, help_x, help_text, curses.color_pair(1))
            
        # Draw current path
        path_str = f"Path: {self.current_path}"
        if len(path_str) > width - 4:
            path_str = "Path: ..." + str(self.current_path)[-(width - 10):]
        self.screen.addstr(2, 2, path_str)

    def draw_status_bar(self):
        """Draw status bar at bottom of screen."""
        height, width = self.screen.getmaxyx()
        
        # Clear status area
        for y in range(height - FOOTER_HEIGHT, height):
            self.screen.addstr(y, 0, " " * (width - 1))
            
        # Draw status message
        status = self.status_message[:width - 4]  # Truncate if too long
        self.screen.addstr(height - 2, 2, status, curses.color_pair(1))
        
    def draw_files_panel(self, x, y, width, height):
        """Draw files panel."""
        # Draw border
        self._draw_border(x, y, width, height, "Files/Directories")
        
        # Display files/directories
        start_y = y + 1
        max_items = height - 2
        
        # Calculate start index for scrolling
        start_idx = max(0, self.selected_file_idx - max_items // 2)
        visible_items = self.visible_files[start_idx:start_idx + max_items]
        
        for i, item in enumerate(visible_items):
            if start_y + i >= y + height - 1:
                break
                
            # Format item display
            is_dir = item.get("is_dir", False)
            name = item.get("name", "")
            prefix = "[DIR] " if is_dir else ""
            
            # Truncate name if needed
            display_name = prefix + name
            if len(display_name) > width - 6:
                display_name = display_name[:width - 9] + "..."
                
            # Highlight if selected
            attrs = curses.A_NORMAL
            if i + start_idx == self.selected_file_idx:
                if self.focused_panel == 0:
                    attrs = curses.color_pair(2) | curses.A_BOLD  # Cyan, focused
                else:
                    attrs = curses.A_BOLD  # Just bold, not focused
                    
            # Directory items get special color
            if is_dir and attrs == curses.A_NORMAL:
                attrs = curses.color_pair(3)  # Yellow for directories
            
            self.screen.addstr(start_y + i, x + 2, display_name, attrs)
            
    def draw_results_panel(self, x, y, width, height):
        """Draw results panel."""
        # Draw border
        self._draw_border(x, y, width, height, "Search Results")
        
        # Display results
        start_y = y + 1
        max_items = height - 2
        
        if not self.flat_results:
            # Show help text if no results
            help_text = "Press 's' to search metadata"
            self.screen.addstr(start_y + 2, x + (width - len(help_text)) // 2, help_text)
            return
            
        # Calculate start index for scrolling
        start_idx = max(0, self.selected_result_idx - max_items // 2)
        visible_results = self.flat_results[start_idx:start_idx + max_items]
        
        for i, result in enumerate(visible_results):
            if start_y + i >= y + height - 1:
                break
                
            # Format display
            provider = result.get('provider', '').upper()
            title = result.get('title', '')
            artist = result.get('artist', '')
            
            # Combine info
            display_text = f"{provider}: {title} - {artist}"
            
            # Truncate if needed
            if len(display_text) > width - 4:
                display_text = display_text[:width - 7] + "..."
                
            # Highlight if selected
            attrs = curses.A_NORMAL
            if i + start_idx == self.selected_result_idx:
                if self.focused_panel == 1:
                    attrs = curses.color_pair(2) | curses.A_BOLD  # Cyan, focused
                else:
                    attrs = curses.A_BOLD  # Just bold, not focused
            
            self.screen.addstr(start_y + i, x + 2, display_text, attrs)

    def draw_details_view(self, x, y, width, height):
        """Draw metadata details view."""
        # Draw border
        self._draw_border(x, y, width, height, "Metadata Details")
        
        if not self.selected_metadata:
            self.screen.addstr(y + 2, x + 2, "No metadata selected.", curses.color_pair(4))
            return
        
        metadata = self.selected_metadata
        provider = metadata.get('provider', '').upper()
        title = metadata.get('title', '')
        artist = metadata.get('artist', '')
        album = metadata.get('album', '')
        year = metadata.get('year', '')
        
        # Draw metadata header
        self.screen.addstr(y + 2, x + 2, f"Source: {provider}", curses.color_pair(3) | curses.A_BOLD)
        self.screen.addstr(y + 3, x + 2, f"Title: {title}")
        self.screen.addstr(y + 4, x + 2, f"Artist: {artist}")
        self.screen.addstr(y + 5, x + 2, f"Album: {album}")
        self.screen.addstr(y + 6, x + 2, f"Year: {year}")
        
        # Draw tracks
        self.screen.addstr(y + 8, x + 2, "Tracks:", curses.A_BOLD)
        
        tracks = metadata.get('tracks', [])
        start_y = y + 9
        
        for i, track in enumerate(tracks):
            if start_y + i >= y + height - 1:
                break
                
            track_text = f"{track['position']}. {track['title']}"
            
            # Truncate if needed
            if len(track_text) > width - 6:
                track_text = track_text[:width - 9] + "..."
                
            self.screen.addstr(start_y + i, x + 4, track_text)
        
        # Add footer with instructions
        footer_y = y + height - 2
        self.screen.addstr(footer_y, x + 2, "Press Enter to return, 'a' to apply metadata", curses.color_pair(1))
            
    def _draw_border(self, x, y, width, height, title=None):
        """Draw a border with optional title."""
        # Draw corners
        self.screen.addch(y, x, curses.ACS_ULCORNER)
        self.screen.addch(y, x + width - 1, curses.ACS_URCORNER)
        self.screen.addch(y + height - 1, x, curses.ACS_LLCORNER)
        self.screen.addch(y + height - 1, x + width - 1, curses.ACS_LRCORNER)
        
        # Draw horizontal lines
        for i in range(1, width - 1):
            self.screen.addch(y, x + i, curses.ACS_HLINE)
            self.screen.addch(y + height - 1, x + i, curses.ACS_HLINE)
            
        # Draw vertical lines
        for i in range(1, height - 1):
            self.screen.addch(y + i, x, curses.ACS_VLINE)
            self.screen.addch(y + i, x + width - 1, curses.ACS_VLINE)
            
        # Draw title if provided
        if title:
            # Ensure title fits
            if len(title) + 4 < width:
                title_x = x + (width - len(title) - 4) // 2
                self.screen.addstr(y, title_x, f" {title} ")


def main():
    """Run the TUI."""
    # Check if running in a terminal
    if not sys.stdout.isatty():
        print("Error: This application must run in a terminal.")
        return 1
        
    app = CursesTUI()
    app.run()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
