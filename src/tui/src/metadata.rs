use std::path::{Path, PathBuf};
use std::io;
use std::fs;

use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetadataItem {
    pub path: PathBuf,
    pub title: String,
    pub artist: String,
    pub album: String,
    pub track: String,
    pub year: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrackInfo {
    pub position: String,
    pub title: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProviderResult {
    pub provider: String,
    pub title: String,
    pub artist: String,
    pub album: String,
    pub year: String,
    pub score: f64,
    pub tracks: Vec<TrackInfo>,
}

pub fn scan_directory(path: &Path) -> io::Result<(Vec<PathBuf>, Vec<MetadataItem>)> {
    let mut directories = Vec::new();
    let mut files = Vec::new();
    
    for entry in fs::read_dir(path)? {
        let entry = entry?;
        let path = entry.path();
        
        if path.is_dir() {
            directories.push(path);
        } else if let Some(ext) = path.extension() {
            let ext_str = ext.to_string_lossy().to_lowercase();
            
            // Only add music files
            if ["mp3", "flac", "m4a", "ogg", "wav"].contains(&ext_str.as_str()) {
                let filename = path.file_name().unwrap_or_default().to_string_lossy().to_string();
                
                // In a real app, we'd extract metadata here
                files.push(MetadataItem {
                    path: path.clone(),
                    title: filename,
                    artist: String::new(),
                    album: String::new(),
                    track: String::new(),
                    year: String::new(),
                });
            }
        }
    }
    
    // Sort directories and files
    directories.sort();
    
    Ok((directories, files))
}
