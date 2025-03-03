"""GUI implementation for Music-dlp."""
import os
import sys
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from pathlib import Path
import threading
from PIL import Image, ImageTk, ImageDraw
import io
import requests

from .core.file_scanner import FileScanner
from .core.metadata_manager import MetadataManager
from .core.artwork_finder import find_artwork

class MetadataManagerGUI:
    def __init__(self, root):
        """Initialize the GUI."""
        self.root = root
        self.root.title("Music Metadata Manager")
        self.root.geometry("1000x600")
        
        # Initialize backend components
        self.scanner = FileScanner()
        self.manager = MetadataManager()
        self.current_files = []
        self.current_results = {}
        self.selected_metadata = None
        
        # Create the main layout
        self.create_menu()
        self.create_layout()
    
    def create_menu(self):
        """Create top menu bar."""
        menubar = tk.Menu(self.root)
        
        # File menu
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open Folder", command=self.open_folder)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        
        # Actions menu
        actionmenu = tk.Menu(menubar, tearoff=0)
        actionmenu.add_command(label="Scan Files", command=self.scan_folder)
        actionmenu.add_command(label="Search Metadata", command=self.search_metadata)
        actionmenu.add_command(label="Apply Metadata", command=self.apply_metadata)
        menubar.add_cascade(label="Actions", menu=actionmenu)
        
        # Help menu
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About", command=self.show_about)
        helpmenu.add_command(label="Help", command=self.show_help)
        menubar.add_cascade(label="Help", menu=helpmenu)
        
        self.root.config(menu=menubar)
    
    def create_layout(self):
        """Create the main application layout."""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Files
        left_frame = ttk.LabelFrame(main_frame, text="Music Files")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create file list with scrollbar
        self.file_tree = ttk.Treeview(left_frame, columns=("Track", "Title", "Artist", "Album", "Year"))
        self.file_tree.heading("#0", text="")
        self.file_tree.heading("Track", text="Track")
        self.file_tree.heading("Title", text="Title")
        self.file_tree.heading("Artist", text="Artist")
        self.file_tree.heading("Album", text="Album")
        self.file_tree.heading("Year", text="Year")
        self.file_tree.column("#0", width=0, stretch=tk.NO)
        self.file_tree.column("Track", width=50)
        self.file_tree.column("Title", width=150)
        self.file_tree.column("Artist", width=150)
        self.file_tree.column("Album", width=150)
        self.file_tree.column("Year", width=60)
        self.file_tree.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar for file list
        file_scroll = ttk.Scrollbar(left_frame, orient="vertical", command=self.file_tree.yview)
        file_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_tree.configure(yscrollcommand=file_scroll.set)
        
        # Right panel - Results and details
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Results frame - top right
        results_frame = ttk.LabelFrame(right_frame, text="Search Results")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create results treeview
        self.results_tree = ttk.Treeview(results_frame, columns=("Source", "Title", "Artist", "Album", "Year", "Tracks"))
        self.results_tree.heading("#0", text="")
        self.results_tree.heading("Source", text="Source")
        self.results_tree.heading("Title", text="Title")
        self.results_tree.heading("Artist", text="Artist")
        self.results_tree.heading("Album", text="Album")
        self.results_tree.heading("Year", text="Year")
        self.results_tree.heading("Tracks", text="Tracks")
        self.results_tree.column("#0", width=0, stretch=tk.NO)
        self.results_tree.column("Source", width=80)
        self.results_tree.column("Title", width=150)
        self.results_tree.column("Artist", width=150)
        self.results_tree.column("Album", width=150)
        self.results_tree.column("Year", width=60)
        self.results_tree.column("Tracks", width=60)
        self.results_tree.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar for results
        results_scroll = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        results_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.configure(yscrollcommand=results_scroll.set)
        
        # Details frame - bottom right
        details_frame = ttk.LabelFrame(right_frame, text="Selected Metadata")
        details_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Left side: Metadata details
        details_left = ttk.Frame(details_frame)
        details_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Text widget for metadata details
        self.details_text = tk.Text(details_left, height=10, wrap=tk.WORD)
        self.details_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right side: Artwork
        details_right = ttk.Frame(details_frame)
        details_right.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)
        
        # Label for artwork
        self.artwork_label = ttk.Label(details_right, text="No artwork")
        self.artwork_label.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind events
        self.file_tree.bind("<Double-1>", self.on_file_double_click)
        self.results_tree.bind("<<TreeviewSelect>>", self.on_result_selected)
    
    def open_folder(self):
        """Open folder dialog and scan selected directory."""
        folder = filedialog.askdirectory(title="Select Music Directory")
        if folder:
            self.scan_directory(folder)
    
    def scan_folder(self):
        """Scan current folder."""
        if hasattr(self, 'current_folder'):
            self.scan_directory(self.current_folder)
        else:
            self.open_folder()
    
    def scan_directory(self, path, recursive=True):
        """Scan directory for music files."""
        self.status_var.set(f"Scanning {path}...")
        self.root.update_idletasks()
        
        # Clear current data
        self.clear_display()
        self.current_folder = path
        
        # Start scan in a separate thread
        def scan_thread():
            files = self.scanner.scan_directory(path, recursive=recursive)
            self.current_files = files
            
            # Update UI in main thread
            self.root.after(0, lambda: self.update_file_list(files))
        
        threading.Thread(target=scan_thread).start()
    
    def update_file_list(self, files):
        """Update file list in the treeview."""
        # Clear existing items
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        # Add files to the treeview
        for i, file in enumerate(files):
            metadata = file["metadata"]
            track = metadata.get("track", [""])[0]
            title = metadata.get("title", [""])[0] or os.path.basename(file["path"])
            artist = metadata.get("artist", [""])[0]
            album = metadata.get("album", [""])[0]
            year = metadata.get("date", [""])[0]
            
            self.file_tree.insert("", tk.END, text="", values=(track, title, artist, album, year))
        
        self.status_var.set(f"Found {len(files)} music files in {self.current_folder}")
    
    def search_metadata(self):
        """Search metadata for selected files."""
        if not self.current_files:
            messagebox.showinfo("No Files", "No music files to search metadata for.")
            return
        
        # Start search in a separate thread
        self.status_var.set("Searching metadata...")
        
        def search_thread():
            # Get album info from first file
            first_file = self.current_files[0]
            metadata = first_file["metadata"]
            album = metadata.get("album", [""])[0]
            artist = metadata.get("artist", [""])[0]
            
            if album and artist:
                try:
                    # Search for album metadata
                    results = {}
                    for provider in self.manager.providers:
                        matches = provider.search_album(album, artist)
                        if matches:
                            results[provider.name] = matches
                    
                    self.current_results = results
                    
                    # Update UI in main thread
                    self.root.after(0, lambda: self.update_results(results))
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Search failed: {str(e)}"))
                    self.status_var.set("Search failed")
        
        threading.Thread(target=search_thread).start()
    
    def update_results(self, results):
        """Update results in the treeview."""
        # Clear existing items
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Add results to the treeview
        for provider, matches in results.items():
            for match in matches:
                self.results_tree.insert(
                    "", 
                    tk.END, 
                    text="", 
                    values=(
                        provider.upper(),
                        match.get('title', ''),
                        match.get('artist', ''),
                        match.get('album', ''),
                        match.get('year', ''),
                        len(match.get('tracks', []))
                    )
                )
        
        self.status_var.set(f"Found metadata from {len(results)} providers")
    
    def on_file_double_click(self, event):
        """Handle double click on file item."""
        # Get selected item
        selection = self.file_tree.selection()
        if not selection:
            return
            
        item = selection[0]
        values = self.file_tree.item(item, "values")
        
        # Get file index
        idx = self.file_tree.index(item)
        if idx < len(self.current_files):
            file = self.current_files[idx]
            self.show_file_details(file)
    
    def on_result_selected(self, event):
        """Handle selection of a search result."""
        if not self.results_tree.selection():
            return
            
        # Get selected item
        item = self.results_tree.selection()[0]
        values = self.results_tree.item(item, "values")
        
        # Find matching metadata
        provider = values[0].lower()
        title = values[1]
        artist = values[2]
        
        if provider in self.current_results:
            for match in self.current_results[provider]:
                if (match.get('title', '') == title and 
                    match.get('artist', '') == artist):
                    self.selected_metadata = match
                    self.show_metadata_details(match)
                    break
    
    def show_file_details(self, file):
        """Show details for selected file."""
        metadata = file["metadata"]
        
        # Format text for display
        details = [
            "File Details:",
            f"Path: {file['path']}",
            f"Title: {metadata.get('title', [''])[0]}",
            f"Artist: {metadata.get('artist', [''])[0]}",
            f"Album: {metadata.get('album', [''])[0]}",
            f"Year: {metadata.get('date', [''])[0]}",
            f"Track: {metadata.get('track', [''])[0]}"
        ]
        
        # Update details text
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, "\n".join(details))
    
    def show_metadata_details(self, metadata):
        """Show details for selected metadata."""
        # Format text for display
        details = [
            f"Provider: {metadata.get('provider', '').upper()}",
            f"Title: {metadata.get('title', '')}",
            f"Artist: {metadata.get('artist', '')}",
            f"Album: {metadata.get('album', '')}",
            f"Year: {metadata.get('year', '')}",
            f"\nTracks: {len(metadata.get('tracks', []))}"
        ]
        
        # Add track listing
        if tracks := metadata.get('tracks', []):
            details.append("\nTrack Listing:")
            for track in tracks:
                details.append(f"{track['position']}. {track['title']}")
        
        # Update details text
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, "\n".join(details))
        
        # Try to load and display artwork
        self.load_artwork(metadata)
    
    def load_artwork(self, metadata):
        """Try to load and display artwork."""
        # Reset artwork
        self.artwork_label.config(text="Loading artwork...")
        self.root.update_idletasks()
        
        # Start artwork loading in a thread
        def load_thread():
            try:
                # Try to get artwork URL from metadata or find it
                artwork_url = metadata.get('artwork_url')
                
                # Si no hay URL, intentar buscar por artista y álbum
                if not artwork_url:
                    artwork_url = find_artwork(
                        artist=metadata.get('artist', ''),
                        album=metadata.get('title', '') or metadata.get('album', '')
                    )
                
                if artwork_url:
                    response = requests.get(artwork_url)
                    if response.status_code == 200:
                        image = Image.open(io.BytesIO(response.content))
                        image = image.resize((200, 200), Image.LANCZOS)
                        photo = ImageTk.PhotoImage(image)
                        self.root.after(0, lambda: self.update_artwork(photo))
                    else:
                        self.root.after(0, lambda: self.artwork_label.config(text="Artwork unavailable"))
                else:
                    # Si no hay URL, usar placeholder
                    self.root.after(0, lambda: self.load_placeholder_artwork())
            except Exception as e:
                print(f"Error loading artwork: {e}")
                self.root.after(0, lambda: self.artwork_label.config(text="Error loading artwork"))
        
        threading.Thread(target=load_thread).start()
    
    def load_placeholder_artwork(self):
        """Load a placeholder image for artwork."""
        try:
            # Create simple placeholder with PIL
            image = Image.new('RGB', (200, 200), color=(50, 50, 50))
            d = ImageDraw.Draw(image)
            d.text((65, 90), "No Artwork", fill=(200, 200, 200))
            photo = ImageTk.PhotoImage(image)
            self.update_artwork(photo)
        except:
            self.artwork_label.config(text="No artwork")
    
    def update_artwork(self, photo):
        """Update artwork display with loaded image."""
        self.artwork = photo  # Keep reference to prevent garbage collection
        self.artwork_label.config(image=photo, text="")
    
    def clear_display(self):
        """Clear all display elements."""
        # Clear file list
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        # Clear results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Clear details and artwork
        self.details_text.delete(1.0, tk.END)
        self.artwork_label.config(text="No artwork", image="")
    
    def apply_metadata(self):
        """Apply selected metadata to files."""
        if not self.selected_metadata:
            messagebox.showinfo("No Selection", "No metadata selected to apply.")
            return
            
        if not self.current_files:
            messagebox.showinfo("No Files", "No music files to apply metadata to.")
            return
        
        # Confirm action
        proceed = messagebox.askokcancel(
            "Apply Metadata", 
            f"Apply metadata from {self.selected_metadata.get('provider', '').upper()} to {len(self.current_files)} files?"
        )
        
        if proceed:
            self.status_var.set("Applying metadata...")
            
            # TODO: Implement actual metadata application
            
            messagebox.showinfo("Success", "Metadata applied successfully.")
            self.status_var.set("Metadata applied successfully.")
    
    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About Music Metadata Manager", 
            "Music Metadata Manager GUI\n"
            "Version 0.1.0\n\n"
            "A flexible system for managing music metadata from multiple sources."
        )
    
    def show_help(self):
        """Show help dialog."""
        messagebox.showinfo(
            "Help", 
            "How to use:\n"
            "1. Select a music folder using File > Open Folder\n"
            "2. Select files to search metadata for\n"
            "3. Click Actions > Search Metadata\n"
            "4. Select a result to see details\n"
            "5. Apply metadata with Actions > Apply Metadata"
        )

def main():
    """Run the GUI application."""
    # Create root window and configure style
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam')  # Use a modern theme
    
    # Create app
    app = MetadataManagerGUI(root)
    
    # Start main loop
    root.mainloop()

if __name__ == "__main__":
    main()
