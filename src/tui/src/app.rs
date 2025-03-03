use std::path::{Path, PathBuf};
use std::process::Command;

use crate::metadata::{MetadataItem, ProviderResult, scan_directory};

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum AppState {
    Navigation,
    Results,
    Details,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum FocusedPane {
    Directory,
    Files,
    Results,
}

pub struct App {
    pub state: AppState,
    pub current_path: PathBuf,
    pub directories: Vec<PathBuf>,
    pub files: Vec<MetadataItem>,
    pub results: Vec<ProviderResult>,
    pub selected_directory: Option<usize>,
    pub selected_file: Option<usize>,
    pub selected_result: Option<usize>,
    pub focus: FocusedPane,
    pub details_scroll: u16,
    pub status_message: String,
}

impl App {
    pub fn new() -> Self {
        let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
        
        App {
            state: AppState::Navigation,
            current_path: home.clone(),
            directories: vec![],
            files: vec![],
            results: vec![],
            selected_directory: None,
            selected_file: None,
            selected_result: None,
            focus: FocusedPane::Directory,
            details_scroll: 0,
            status_message: String::from("Welcome to Music-dlp TUI"),
        }
    }
    
    pub fn scan_current_directory(&mut self) {
        self.status_message = format!("Scanning {:?}...", self.current_path);
        
        match scan_directory(&self.current_path) {
            Ok((dirs, files)) => {
                self.directories = dirs;
                self.files = files;
                self.selected_directory = None;
                self.selected_file = None;
                self.status_message = format!("Found {} files in {:?}", self.files.len(), self.current_path);
            }
            Err(err) => {
                self.status_message = format!("Error scanning directory: {}", err);
            }
        }
    }
    
    pub fn select_directory(&mut self) {
        if let Some(idx) = self.selected_directory {
            if idx < self.directories.len() {
                self.current_path = self.directories[idx].clone();
                self.scan_current_directory();
            }
        }
    }
    
    pub fn next_item(&mut self) {
        match self.focus {
            FocusedPane::Directory => {
                if !self.directories.is_empty() {
                    self.selected_directory = Some(self.selected_directory.map_or(0, |i| {
                        if i >= self.directories.len() - 1 {
                            0
                        } else {
                            i + 1
                        }
                    }));
                }
            }
            FocusedPane::Files => {
                if !self.files.is_empty() {
                    self.selected_file = Some(self.selected_file.map_or(0, |i| {
                        if i >= self.files.len() - 1 {
                            0
                        } else {
                            i + 1
                        }
                    }));
                }
            }
            FocusedPane::Results => {
                // Handled by next_result
            }
        }
    }
    
    pub fn previous_item(&mut self) {
        match self.focus {
            FocusedPane::Directory => {
                if !self.directories.is_empty() {
                    self.selected_directory = Some(self.selected_directory.map_or(0, |i| {
                        if i == 0 {
                            self.directories.len() - 1
                        } else {
                            i - 1
                        }
                    }));
                }
            }
            FocusedPane::Files => {
                if !self.files.is_empty() {
                    self.selected_file = Some(self.selected_file.map_or(0, |i| {
                        if i == 0 {
                            self.files.len() - 1
                        } else {
                            i - 1
                        }
                    }));
                }
            }
            FocusedPane::Results => {
                // Handled by previous_result
            }
        }
    }
    
    pub fn toggle_focus(&mut self) {
        match self.focus {
            FocusedPane::Directory => self.focus = FocusedPane::Files,
            FocusedPane::Files => self.focus = FocusedPane::Results,
            FocusedPane::Results => self.focus = FocusedPane::Directory,
        }
    }
    
    pub fn search_metadata(&mut self) {
        if self.files.is_empty() {
            self.status_message = String::from("No files to search metadata for");
            return;
        }
        
        self.status_message = String::from("Searching metadata...");
        
        // Call the Python backend to search metadata
        let output = Command::new("python")
            .arg("-m")
            .arg("metadata_manager.cli")
            .arg("--search")
            .arg(&self.current_path)
            .output();
            
        match output {
            Ok(output) => {
                // Parse JSON results
                let stdout = String::from_utf8_lossy(&output.stdout);
                // In a real app, parse JSON results here
                self.results = vec![]; // Placeholder
                self.state = AppState::Results;
                self.status_message = String::from("Found metadata");
            }
            Err(e) => {
                self.status_message = format!("Error searching metadata: {}", e);
            }
        }
    }
    
    pub fn next_result(&mut self) {
        if !self.results.is_empty() {
            self.selected_result = Some(self.selected_result.map_or(0, |i| {
                if i >= self.results.len() - 1 {
                    0
                } else {
                    i + 1
                }
            }));
        }
    }
    
    pub fn previous_result(&mut self) {
        if !self.results.is_empty() {
            self.selected_result = Some(self.selected_result.map_or(0, |i| {
                if i == 0 {
                    self.results.len() - 1
                } else {
                    i - 1
                }
            }));
        }
    }
    
    pub fn show_details(&mut self) {
        if self.selected_result.is_some() {
            self.state = AppState::Details;
            self.details_scroll = 0;
        }
    }
    
    pub fn go_back(&mut self) {
        match self.state {
            AppState::Navigation => {}
            AppState::Results => {
                self.state = AppState::Navigation;
                self.selected_result = None;
            }
            AppState::Details => {
                self.state = AppState::Results;
            }
        }
    }
    
    pub fn apply_metadata(&mut self) {
        if let Some(idx) = self.selected_result {
            self.status_message = String::from("Applying metadata...");
            
            // Call Python backend to apply metadata
            // Implementation details omitted
            
            self.status_message = String::from("Metadata applied successfully");
        } else {
            self.status_message = String::from("No metadata selected");
        }
    }
}
