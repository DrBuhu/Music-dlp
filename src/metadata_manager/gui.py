import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import io
import requests
from pathlib import Path
from .core.scanner import MusicScanner
from .core.metadata_manager import MetadataManager

class MetadataManagerGUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Music Metadata Manager")
        self.window.geometry("1024x768")  # Increased size for more columns
        
        # Browse frame
        self.browse_frame = ttk.Frame(self.window)
        self.browse_frame.pack(padx=10, pady=10, fill="x")
        
        # Browse button
        self.browse_btn = ttk.Button(
            self.browse_frame, 
            text="Browse Music Files/Folders",
            command=self.browse_files
        )
        self.browse_btn.pack(side="left", padx=5)
        
        # Path display
        self.path_label = ttk.Label(self.browse_frame, text="No folder selected")
        self.path_label.pack(side="left", padx=5, fill="x", expand=True)
        
        # Results frame with artwork preview
        self.results_frame = ttk.Frame(self.window)
        self.results_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Artwork preview
        self.artwork_label = ttk.Label(self.results_frame)
        self.artwork_label.pack(side="left", padx=10)
        
        # Results tree with more columns and better formatting
        self.results_tree = ttk.Treeview(
            self.results_frame, 
            columns=("Track", "Title", "Artist", "Album", "Tracks", "Year", "Source"),
            show="headings"
        )
        
        # Configure columns
        self.results_tree.heading("Track", text="#")
        self.results_tree.heading("Title", text="Title")
        self.results_tree.heading("Artist", text="Artist")
        self.results_tree.heading("Album", text="Album")
        self.results_tree.heading("Tracks", text="Tracks")
        self.results_tree.heading("Year", text="Year")
        self.results_tree.heading("Source", text="Source")
        
        # Set column widths and alignments
        self.results_tree.column("Track", width=40, anchor="e")
        self.results_tree.column("Title", width=200)
        self.results_tree.column("Artist", width=150)
        self.results_tree.column("Album", width=200)
        self.results_tree.column("Tracks", width=60, anchor="e")
        self.results_tree.column("Year", width=60, anchor="e")
        self.results_tree.column("Source", width=80)
        
        # Style the treeview
        style = ttk.Style()
        style.configure("Treeview", font=('Arial', 10))
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        
        # Add alternating row colors
        style.map('Treeview',
            background=[('selected', '#0078D7'), ('alternate', '#F0F0F0')])
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.results_frame, orient="vertical", command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack with scrollbar
        self.results_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(
            self.window, 
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(side="bottom", fill="x")
        
        # Manager instance
        self.manager = MetadataManager()
        self.set_status("Ready")
        
        # Add right-click menu
        self.context_menu = tk.Menu(self.window, tearoff=0)
        self.context_menu.add_command(label="Apply Selected Metadata", command=self.apply_metadata)
        self.context_menu.add_command(label="Show Details", command=self.show_details)
        self.results_tree.bind("<Button-3>", self.show_context_menu)
    
    def set_status(self, message: str):
        """Update status bar message."""
        self.status_var.set(message)
        self.window.update_idletasks()
    
    def browse_files(self):
        """Open file browser dialog."""
        directory = filedialog.askdirectory(
            title="Select Music Directory",
            initialdir="~"
        )
        if directory:
            self.path_label.config(text=directory)
            self.process_directory(directory)
    
    def process_directory(self, directory):
        """Process a music directory."""
        self.set_status(f"Scanning {directory}...")
        scanner = MusicScanner(directory)
        files = scanner.scan_directory()
        
        if not files:
            messagebox.showinfo("Info", "No music files found!")
            self.set_status("Ready")
            return
            
        # Search metadata
        self.set_status("Searching metadata...")
        results = self.manager.search_all(files)
        
        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Show results
        for source, matches in results.items():
            for match in matches:
                # Fix title/album confusion
                title = match.get('album', '') if match.get('type') == 'album' else match.get('title', '')
                album = match.get('album', '') if match.get('type') != 'album' else title
                track_num = match.get('position', '')
                num_tracks = len(match.get('tracks', []))
                
                self.results_tree.insert("", "end", values=(
                    track_num,
                    title,
                    match['artist'],
                    album,
                    num_tracks or '',
                    match.get('year', ''),
                    match.get('source', source).upper()
                ), tags=('alternate',))
                
                # Show artwork if available
                if 'artwork_url' in match:
                    self.show_artwork(match['artwork_url'])
        
        self.set_status(f"Found {len(files)} files")
    
    def show_artwork(self, url):
        """Download and display artwork."""
        try:
            response = requests.get(url)
            img_data = response.content
            img = Image.open(io.BytesIO(img_data))
            
            # Resize to fit
            img.thumbnail((200, 200))
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            self.artwork_label.configure(image=photo)
            self.artwork_label.image = photo  # Keep reference
            
        except Exception as e:
            print(f"Error loading artwork: {e}")
    
    def show_context_menu(self, event):
        """Show right-click menu."""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def apply_metadata(self):
        """Apply selected metadata to files."""
        selected = self.results_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a metadata entry first")
            return
        
        if messagebox.askyesno("Confirm", "Apply selected metadata to files?"):
            # TODO: Implement metadata application
            self.set_status("Applying metadata...")
    
    def show_details(self):
        """Show detailed metadata information."""
        selected = self.results_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a metadata entry first")
            return
        
        # Get selected item data
        item = self.results_tree.item(selected[0])
        values = item['values']
        
        # Create details window
        details = tk.Toplevel(self.window)
        details.title("Metadata Details")
        details.geometry("400x300")
        
        # Add details
        ttk.Label(details, text="Title:", anchor="e").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(details, text=values[1]).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(details, text="Artist:", anchor="e").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(details, text=values[2]).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(details, text="Album:", anchor="e").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(details, text=values[3]).grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(details, text="Year:", anchor="e").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(details, text=values[4]).grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(details, text="Source:", anchor="e").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(details, text=values[5]).grid(row=4, column=1, padx=5, pady=5, sticky="w")
    
    def run(self):
        """Start the GUI."""
        self.window.mainloop()

def main():
    app = MetadataManagerGUI()
    app.run()

if __name__ == "__main__":
    main()
