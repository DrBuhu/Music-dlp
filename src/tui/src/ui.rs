use ratatui::{
    backend::Backend,
    layout::{Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Span, Spans, Text},
    widgets::{Block, Borders, List, ListItem, Paragraph, Table, Tabs},
    Frame,
};

use crate::app::{App, AppState, FocusedPane};

pub fn draw_ui<B: Backend>(f: &mut Frame<B>, app: &App) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3), // Title bar
            Constraint::Min(0),    // Main content
            Constraint::Length(1), // Status bar
        ])
        .split(f.size());

    draw_title_bar(f, chunks[0]);
    
    match app.state {
        AppState::Navigation => draw_navigation_view(f, app, chunks[1]),
        AppState::Results => draw_results_view(f, app, chunks[1]),
        AppState::Details => draw_details_view(f, app, chunks[1]),
    }
    
    draw_status_bar(f, app, chunks[2]);
}

fn draw_title_bar<B: Backend>(f: &mut Frame<B>, area: Rect) {
    let title_block = Block::default()
        .borders(Borders::ALL)
        .style(Style::default().bg(Color::Blue));
    
    let title = Paragraph::new(Text::from(Spans::from(vec![
        Span::styled("Music-dlp TUI", Style::default().add_modifier(Modifier::BOLD)),
        Span::raw(" | "),
        Span::raw("Press 'q' to quit, 'r' to refresh, 's' to search, 'a' to apply"),
    ])))
    .block(title_block);
    
    f.render_widget(title, area);
}

fn draw_navigation_view<B: Backend>(f: &mut Frame<B>, app: &App, area: Rect) {
    // Create a layout with left panel for directories and right panel for files
    let chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Percentage(30), // Directories
            Constraint::Percentage(70), // Files
        ])
        .split(area);
    
    // Draw directory list
    let dir_block = Block::default()
        .title("Directories")
        .borders(Borders::ALL)
        .style(Style::default().bg(Color::Black).fg(Color::White));
    
    let dir_items: Vec<ListItem> = app.directories.iter()
        .map(|dir| {
            let dir_name = dir.file_name()
                .unwrap_or_default()
                .to_string_lossy()
                .to_string();
            
            ListItem::new(dir_name)
        })
        .collect();
    
    let dir_list = List::new(dir_items)
        .block(dir_block)
        .highlight_style(
            Style::default()
                .bg(if app.focus == FocusedPane::Directory {
                    Color::Blue
                } else {
                    Color::DarkGray
                })
                .fg(Color::White)
                .add_modifier(Modifier::BOLD),
        )
        .highlight_symbol("> ");
    
    let mut dir_state = ratatui::widgets::ListState::default();
    dir_state.select(app.selected_directory);
    
    f.render_stateful_widget(dir_list, chunks[0], &mut dir_state);
    
    // Draw file list as a table
    let file_block = Block::default()
        .title("Files")
        .borders(Borders::ALL)
        .style(Style::default().bg(Color::Black).fg(Color::White));
    
    let file_rows: Vec<ratatui::widgets::Row> = app.files.iter()
        .map(|file| {
            let cells = vec![
                file.track.clone(),
                file.title.clone(),
                file.artist.clone(),
                file.album.clone(),
                file.year.clone(),
            ];
            
            ratatui::widgets::Row::new(cells)
        })
        .collect();
    
    let file_table = Table::new(file_rows)
        .header(ratatui::widgets::Row::new(vec![
            "Track", "Title", "Artist", "Album", "Year"
        ]).style(Style::default().fg(Color::Yellow)))
        .block(file_block)
        .highlight_style(
            Style::default()
                .bg(if app.focus == FocusedPane::Files {
                    Color::Blue
                } else {
                    Color::DarkGray
                })
                .fg(Color::White)
                .add_modifier(Modifier::BOLD),
        )
        .widths(&[
            Constraint::Percentage(10),
            Constraint::Percentage(30),
            Constraint::Percentage(20),
            Constraint::Percentage(30),
            Constraint::Percentage(10),
        ]);
    
    let mut file_state = ratatui::widgets::TableState::default();
    file_state.select(app.selected_file);
    
    f.render_stateful_widget(file_table, chunks[1], &mut file_state);
}

fn draw_results_view<B: Backend>(f: &mut Frame<B>, app: &App, area: Rect) {
    // Create layout for results
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Percentage(70), // Results table
            Constraint::Percentage(30), // Preview
        ])
        .split(area);
    
    // Draw results table
    let results_block = Block::default()
        .title("Search Results")
        .borders(Borders::ALL)
        .style(Style::default().bg(Color::Black).fg(Color::White));
    
    let result_rows: Vec<ratatui::widgets::Row> = app.results.iter()
        .map(|result| {
            let cells = vec![
                result.provider.clone(),
                result.title.clone(),
                result.artist.clone(),
                result.album.clone(),
                result.year.clone(),
                format!("{:.1}", result.score),
                format!("{}", result.tracks.len()),
            ];
            
            ratatui::widgets::Row::new(cells)
        })
        .collect();
    
    let results_table = Table::new(result_rows)
        .header(ratatui::widgets::Row::new(vec![
            "Provider", "Title", "Artist", "Album", "Year", "Score", "Tracks"
        ]).style(Style::default().fg(Color::Yellow)))
        .block(results_block)
        .highlight_style(
            Style::default()
                .bg(Color::Blue)
                .fg(Color::White)
                .add_modifier(Modifier::BOLD),
        )
        .widths(&[
            Constraint::Percentage(10),
            Constraint::Percentage(25),
            Constraint::Percentage(20),
            Constraint::Percentage(25),
            Constraint::Percentage(10),
            Constraint::Percentage(5),
            Constraint::Percentage(5),
        ]);
    
    let mut results_state = ratatui::widgets::TableState::default();
    results_state.select(app.selected_result);
    
    f.render_stateful_widget(results_table, chunks[0], &mut results_state);
    
    // Draw preview
    let preview_block = Block::default()
        .title("Preview")
        .borders(Borders::ALL)
        .style(Style::default().bg(Color::Black).fg(Color::White));
    
    let preview_text = if let Some(idx) = app.selected_result {
        let result = &app.results[idx];
        format!(
            "Selected: {} from {}\nAlbum: {} ({})\nTracks: {}",
            result.title,
            result.provider.to_uppercase(),
            result.album,
            result.year,
            result.tracks.len()
        )
    } else {
        String::from("No result selected")
    };
    
    let preview = Paragraph::new(preview_text)
        .block(preview_block)
        .wrap(ratatui::widgets::Wrap { trim: true });
    
    f.render_widget(preview, chunks[1]);
}

fn draw_details_view<B: Backend>(f: &mut Frame<B>, app: &App, area: Rect) {
    // Create layout for details
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3),  // Header
            Constraint::Min(0),     // Details
        ])
        .split(area);
    
    // Draw details
    if let Some(idx) = app.selected_result {
        let result = &app.results[idx];
        
        // Draw header
        let header_block = Block::default()
            .borders(Borders::ALL)
            .style(Style::default().bg(Color::Black).fg(Color::White));
        
        let header_text = format!(
            "{} - {} from {}",
            result.title,
            result.artist,
            result.provider.to_uppercase()
        );
        
        let header = Paragraph::new(header_text)
            .block(header_block)
            .style(Style::default().add_modifier(Modifier::BOLD));
        
        f.render_widget(header, chunks[0]);
        
        // Draw track list
        let tracks_block = Block::default()
            .title("Track List")
            .borders(Borders::ALL)
            .style(Style::default().bg(Color::Black).fg(Color::White));
        
        let track_items: Vec<ListItem> = result.tracks.iter()
            .map(|track| {
                ListItem::new(format!("{}. {}", track.position, track.title))
            })
            .collect();
        
        let tracks_list = List::new(track_items)
            .block(tracks_block);
        
        f.render_widget(tracks_list, chunks[1]);
    } else {
        let block = Block::default()
            .title("Details")
            .borders(Borders::ALL);
        
        f.render_widget(block, area);
    }
}

fn draw_status_bar<B: Backend>(f: &mut Frame<B>, app: &App, area: Rect) {
    let status = Paragraph::new(app.status_message.clone())
        .style(Style::default().bg(Color::DarkGray).fg(Color::White));
    
    f.render_widget(status, area);
}
