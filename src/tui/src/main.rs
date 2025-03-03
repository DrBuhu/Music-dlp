use std::time::Duration;
use std::{io, process::Command};
use anyhow::Result;

use ratatui::{
    backend::CrosstermBackend,
    layout::{Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Span, Spans, Text},
    widgets::{Block, Borders, List, ListItem, Paragraph, Table, Tabs},
    Terminal,
};

use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};

mod app;
mod metadata;
mod ui;

use app::{App, AppState};
use metadata::{MetadataItem, scan_directory};

fn main() -> Result<()> {
    // Setup terminal
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    // Create app state
    let mut app = App::new();
    let res = run_app(&mut terminal, &mut app);

    // Cleanup terminal
    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;

    // Print any errors that occurred during the app
    if let Err(err) = res {
        println!("Error: {}", err);
    }

    Ok(())
}

fn run_app<B: ratatui::backend::Backend>(terminal: &mut Terminal<B>, app: &mut App) -> Result<()> {
    loop {
        // Draw the current UI
        terminal.draw(|f| ui::draw_ui(f, app))?;

        // Handle key events
        if let Event::Key(key) = event::read()? {
            match app.state {
                AppState::Navigation => match key.code {
                    KeyCode::Char('q') => return Ok(()),
                    KeyCode::Char('r') => app.scan_current_directory(),
                    KeyCode::Char('s') => app.search_metadata(),
                    KeyCode::Down => app.next_item(),
                    KeyCode::Up => app.previous_item(),
                    KeyCode::Enter => app.select_directory(),
                    KeyCode::Tab => app.toggle_focus(),
                    _ => {}
                },
                AppState::Results => match key.code {
                    KeyCode::Char('q') => return Ok(()),
                    KeyCode::Char('a') => app.apply_metadata(),
                    KeyCode::Esc => app.go_back(),
                    KeyCode::Down => app.next_result(),
                    KeyCode::Up => app.previous_result(),
                    KeyCode::Enter => app.show_details(),
                    KeyCode::Tab => app.toggle_focus(),
                    _ => {}
                },
                AppState::Details => match key.code {
                    KeyCode::Char('q') => return Ok(()),
                    KeyCode::Char('a') => app.apply_metadata(),
                    KeyCode::Esc => app.go_back(),
                    _ => {}
                },
            }
        }
    }
}
