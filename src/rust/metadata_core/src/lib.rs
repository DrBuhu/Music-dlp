use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::collections::HashMap;

#[pyclass]
struct MetadataMatcher {
    #[pyo3(get)]
    threshold: f32,
}

#[pymethods]
impl MetadataMatcher {
    #[new]
    fn new(threshold: Option<f32>) -> Self {
        MetadataMatcher {
            threshold: threshold.unwrap_or(0.85),
        }
    }

    /// Score similarity between metadata
    fn score_match(&self, source: &PyDict, target: &PyDict) -> PyResult<f32> {
        let mut total_score = 0.0;
        let mut fields = 0.0;
        
        // Compare title
        if let (Ok(s_title), Ok(t_title)) = (
            source.get_item("title").and_then(|t| t.extract::<String>()),
            target.get_item("title").and_then(|t| t.extract::<String>())
        ) {
            total_score += self.string_similarity(&s_title, &t_title);
            fields += 1.0;
        }
        
        // Compare artist
        if let (Ok(s_artist), Ok(t_artist)) = (
            source.get_item("artist").and_then(|t| t.extract::<String>()),
            target.get_item("artist").and_then(|t| t.extract::<String>())
        ) {
            total_score += self.string_similarity(&s_artist, &t_artist);
            fields += 1.0;
        }
        
        // Return average score
        Ok(if fields > 0.0 { total_score / fields } else { 0.0 })
    }

    /// Compare track listings
    fn compare_track_lists(&self, source: &PyList, target: &PyList) -> PyResult<f32> {
        let mut total_score = 0.0;
        let s_len = source.len() as f32;
        let t_len = target.len() as f32;
        
        // Quick length comparison
        if (s_len - t_len).abs() / s_len > 0.2 {
            return Ok(0.0);
        }
        
        // Compare each track
        for (i, s_track) in source.iter().enumerate() {
            if let Ok(s_dict) = s_track.downcast::<PyDict>() {
                if let Some(t_track) = target.get_item(i) {
                    if let Ok(t_dict) = t_track.downcast::<PyDict>() {
                        total_score += self.score_match(s_dict, t_dict)?;
                    }
                }
            }
        }
        
        Ok(total_score / s_len)
    }

    fn string_similarity(&self, a: &str, b: &str) -> f32 {
        // Implement Levenshtein or similar algorithm
        // For now just a simple comparison
        if a.to_lowercase() == b.to_lowercase() {
            1.0
        } else {
            0.0
        }
    }
}

#[pymodule]
fn metadata_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<MetadataMatcher>()?;
    Ok(())
}
