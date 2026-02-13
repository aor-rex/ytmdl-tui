#!/usr/bin/env python3
"""
youtube music downloader
a terminal ui for downloading music from youtube music with metadata
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Input, Button, Static, Log, Select, ProgressBar
from textual.binding import Binding
import subprocess
import threading
from pathlib import Path
import os
import re
import json

# Config file location
CONFIG_FILE = Path.home() / ".config" / "ytdl-tui" / "config.json"

# Available themes
THEMES = {
    "default": "textual-dark",
    "light": "textual-light",
    "nord": "nord",
    "gruvbox": "gruvbox",
    "catppuccin": "catppuccin-mocha",
    "dracula": "dracula",
    "tokyo-night": "tokyo-night",
    "rose-pine": "rose-pine"
}


class MusicDownloader(App):
    """A textual app to download music from youtube music."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.download_process = None
        self.is_paused = False
        self.is_downloading = False
        self.config = self.load_config()
        
    def load_config(self):
        """load configuration from file."""
        default_config = {
            "theme": "default",
            "output_dir": str(Path.home() / "Music"),
            "audio_format": "mp3",
            "audio_quality": "0"
        }
        
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return {**default_config, **config}
            except Exception as e:
                print(f"Error loading config: {e}")
                return default_config
        return default_config
    
    def save_config(self):
        """Save configuration to file."""
        try:
            # Create config directory if it doesn't exist
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # Update config with current values
            output_dir = self.query_one("#output_dir", Input)
            format_select = self.query_one("#format_select", Select)
            quality_input = self.query_one("#quality_input", Input)
            theme_select = self.query_one("#theme_select", Select)
            
            self.config["output_dir"] = output_dir.value
            self.config["audio_format"] = format_select.value
            self.config["audio_quality"] = quality_input.value
            self.config["theme"] = theme_select.value
            
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
                
            self.update_status("💾 Settings saved!")
            self.log_message(f"Configuration saved to {CONFIG_FILE}")
        except Exception as e:
            self.update_status(f"❌ Error saving settings: {str(e)}")
            self.log_message(f"ERROR: Failed to save config: {str(e)}")

    CSS = """
    Screen {
        background: $surface;
    }

    #title {
        width: 100%;
        height: 3;
        content-align: center middle;
        text-style: bold;
        background: $primary;
        color: $text;
        margin-bottom: 1;
    }

    .input-container {
        height: auto;
        margin: 1 2;
        padding: 1;
        border: solid $primary;
    }

    .input-label {
        color: $text;
        margin-bottom: 1;
    }

    Input {
        width: 100%;
        margin-bottom: 1;
    }

    .button-row {
        height: auto;
        width: 100%;
        align: center middle;
        margin-top: 1;
    }

    Button {
        margin: 0 1;
    }

    #progress-container {
        height: auto;
        margin: 0 2;
        padding: 1;
        border: solid $accent;
        background: $surface-darken-1;
    }

    #current-action {
        width: 100%;
        height: auto;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }

    #download-progress {
        width: 100%;
        margin-bottom: 1;
    }

    #playlist-info {
        width: 100%;
        height: auto;
        color: $text-muted;
    }

    #current-file {
        width: 100%;
        height: auto;
        color: $success;
        text-style: italic;
        margin-top: 1;
    }

    #log-container {
        height: 1fr;
        margin: 1 2;
        border: solid $accent;
    }

    Log {
        height: 100%;
        background: $surface-darken-1;
    }

    .status-bar {
        height: 3;
        width: 100%;
        background: $surface-lighten-1;
        content-align: center middle;
        color: $text;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("d", "download", "Download", priority=True),
        Binding("p", "pause_resume", "Pause/Resume", priority=True),
        Binding("s", "save_settings", "Save Settings", priority=True),
        Binding("c", "clear_log", "Clear Log"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Static("🎵 youtube music downloader", id="title")
        
        with Container(classes="input-container"):
            yield Static("URL (Playlist or Video):", classes="input-label")
            yield Input(
                placeholder="https://music.youtube.com/...",
                id="url_input"
            )
            
            yield Static("Output Directory:", classes="input-label")
            yield Input(
                value=str(Path.home() / "Music"),
                id="output_dir"
            )
            
            yield Static("Audio Format:", classes="input-label")
            yield Select(
                [
                    ("MP3", "mp3"),
                    ("M4A", "m4a"),
                    ("FLAC", "flac"),
                    ("WAV", "wav"),
                    ("OPUS", "opus"),
                ],
                value="mp3",
                id="format_select"
            )
            
            yield Static("Audio Quality (0=best, 9=worst):", classes="input-label")
            yield Input(value="0", id="quality_input")
            
            yield Static("Theme:", classes="input-label")
            yield Select(
                [
                    ("Default (Dark)", "default"),
                    ("Light", "light"),
                    ("Nord", "nord"),
                    ("Gruvbox", "gruvbox"),
                    ("Catppuccin Mocha", "catppuccin"),
                    ("Dracula", "dracula"),
                    ("Tokyo Night", "tokyo-night"),
                    ("Rose Pine", "rose-pine"),
                ],
                value="default",
                id="theme_select"
            )
            
            with Horizontal(classes="button-row"):
                yield Button("Download", variant="primary", id="download_btn")
                yield Button("Pause", variant="warning", id="pause_btn", disabled=True)
                yield Button("Save Settings", variant="success", id="save_btn")
                yield Button("Clear Log", variant="default", id="clear_btn")
        
        with Container(id="progress-container"):
            yield Static("Ready", id="current-action")
            yield ProgressBar(total=100, show_eta=False, id="download-progress")
            yield Static("", id="playlist-info")
            yield Static("", id="current-file")
        
        with Container(id="log-container"):
            yield Static("Download Log:", classes="input-label")
            yield Log(id="download_log")
        
        yield Static("Ready to download", classes="status-bar", id="status")
        yield Footer()

    def on_mount(self) -> None:
        """Focus the URL input on mount."""
        self.query_one("#url_input").focus()
        # Hide progress bar initially
        progress = self.query_one("#download-progress", ProgressBar)
        progress.update(total=100, progress=0)
        
        # Load saved configuration
        output_dir = self.query_one("#output_dir", Input)
        format_select = self.query_one("#format_select", Select)
        quality_input = self.query_one("#quality_input", Input)
        theme_select = self.query_one("#theme_select", Select)
        
        output_dir.value = self.config.get("output_dir", str(Path.home() / "Music"))
        format_select.value = self.config.get("audio_format", "mp3")
        quality_input.value = self.config.get("audio_quality", "0")
        theme_select.value = self.config.get("theme", "default")
        
        # Apply saved theme
        self.apply_theme(self.config.get("theme", "default"))
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle theme selection changes."""
        if event.select.id == "theme_select":
            self.apply_theme(event.value)
    
    def apply_theme(self, theme_name: str) -> None:
        """Apply the selected theme."""
        theme = THEMES.get(theme_name, "textual-dark")
        self.theme = theme

    def update_current_action(self, action: str) -> None:
        """Update the current action display."""
        current_action = self.query_one("#current-action", Static)
        current_action.update(action)

    def update_playlist_info(self, info: str) -> None:
        """Update the playlist info display."""
        playlist_info = self.query_one("#playlist-info", Static)
        playlist_info.update(info)

    def update_current_file(self, filename: str) -> None:
        """Update the current file being downloaded."""
        current_file = self.query_one("#current-file", Static)
        if filename:
            current_file.update(f"📄 {filename}")
        else:
            current_file.update("")

    def update_progress(self, current: int, total: int) -> None:
        """Update the progress bar."""
        progress = self.query_one("#download-progress", ProgressBar)
        progress.update(total=total, progress=current)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "download_btn":
            self.action_download()
        elif event.button.id == "pause_btn":
            self.action_pause_resume()
        elif event.button.id == "save_btn":
            self.action_save_settings()
        elif event.button.id == "clear_btn":
            self.action_clear_log()

    def action_clear_log(self) -> None:
        """Clear the download log."""
        log = self.query_one("#download_log", Log)
        log.clear()
        self.update_status("Log cleared")
    
    def action_save_settings(self) -> None:
        """Save current settings to config file."""
        self.save_config()

    def action_pause_resume(self) -> None:
        """Pause or resume the download process."""
        if not self.is_downloading or not self.download_process:
            return
        
        import signal
        
        if self.is_paused:
            # Resume
            try:
                self.download_process.send_signal(signal.SIGCONT)
                self.is_paused = False
                pause_btn = self.query_one("#pause_btn", Button)
                pause_btn.label = "Pause"
                self.update_status("▶️ Resumed")
                self.update_current_action("▶️ Download resumed")
                self.log_message("Download resumed")
            except Exception as e:
                self.log_message(f"Error resuming: {e}")
        else:
            # Pause
            try:
                self.download_process.send_signal(signal.SIGSTOP)
                self.is_paused = True
                pause_btn = self.query_one("#pause_btn", Button)
                pause_btn.label = "Resume"
                self.update_status("⏸️ Paused")
                self.update_current_action("⏸️ Download paused")
                self.log_message("Download paused")
            except Exception as e:
                self.log_message(f"Error pausing: {e}")

    def update_status(self, message: str) -> None:
        """Update the status bar."""
        status = self.query_one("#status", Static)
        status.update(message)

    def log_message(self, message: str) -> None:
        """Add a message to the log."""
        log = self.query_one("#download_log", Log)
        log.write_line(message)

    def action_download(self) -> None:
        """Start the download process."""
        # Prevent starting new download if one is in progress
        if self.is_downloading:
            self.update_status("⚠️ Download already in progress")
            self.log_message("ERROR: A download is already in progress")
            return
        
        url_input = self.query_one("#url_input", Input)
        output_dir = self.query_one("#output_dir", Input)
        format_select = self.query_one("#format_select", Select)
        quality_input = self.query_one("#quality_input", Input)

        url = url_input.value.strip()
        output = output_dir.value.strip()
        audio_format = format_select.value
        quality = quality_input.value.strip()

        if not url:
            self.update_status("❌ Error: URL is required")
            self.log_message("ERROR: Please enter a URL")
            return

        if not output:
            output = str(Path.home() / "Music")

        # Expand user path
        output = os.path.expanduser(output)

        # Build the command
        output_template = f"{output}/%(uploader)s/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s"
        
        command = [
            "yt-dlp",
            "-x",  # Extract audio
            "--audio-format", audio_format,
            "--audio-quality", quality,
            "--embed-thumbnail",
            "--embed-metadata",
            "-o", output_template,
            url
        ]

        self.is_downloading = True
        self.is_paused = False
        
        # Enable pause button, disable download button
        pause_btn = self.query_one("#pause_btn", Button)
        download_btn = self.query_one("#download_btn", Button)
        pause_btn.disabled = False
        pause_btn.label = "Pause"
        download_btn.disabled = True
        
        self.update_status("⏳ Downloading...")
        self.log_message(f"Starting download from: {url}")
        self.log_message(f"Output directory: {output}")
        self.log_message(f"Format: {audio_format}, Quality: {quality}")
        self.log_message(f"Command: {' '.join(command)}")
        self.log_message("-" * 60)

        # Run in a separate thread to avoid blocking the UI
        thread = threading.Thread(
            target=self.run_download,
            args=(command,),
            daemon=True
        )
        thread.start()

    def run_download(self, command: list) -> None:
        """Run the download command in a subprocess with enhanced status parsing."""
        playlist_name = None
        playlist_total = 0
        current_item = 0
        current_filename = None
        
        try:
            self.download_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Stream output line by line and parse it
            for line in self.download_process.stdout:
                line = line.strip()
                if not line:
                    continue
                
                # Log the raw output
                self.call_from_thread(self.log_message, line)
                
                # Parse different yt-dlp status messages
                
                # Extracting URL
                if "Extracting URL:" in line:
                    self.call_from_thread(self.update_current_action, "🔍 Extracting URL...")
                    self.call_from_thread(self.update_status, "⏳ Extracting URL...")
                    self.call_from_thread(self.update_current_file, "")
                
                # YouTube Music redirect warning
                elif "YouTube Music is not directly supported" in line:
                    self.call_from_thread(self.update_current_action, "↪️ Redirecting to YouTube...")
                
                # Downloading webpage/playlist
                elif "Downloading webpage" in line or "Downloading API JSON" in line:
                    self.call_from_thread(self.update_current_action, "📥 Fetching playlist data...")
                
                # Playlist information
                elif match := re.search(r'Downloading playlist: (.+)', line):
                    playlist_name = match.group(1)
                    self.call_from_thread(self.update_current_action, f"📋 Found playlist: {playlist_name}")
                    self.call_from_thread(self.update_status, f"📋 Playlist: {playlist_name}")
                
                # Playlist item count
                elif match := re.search(r'Downloading (\d+) items? of (\d+)', line):
                    available = int(match.group(1))
                    total = int(match.group(2))
                    playlist_total = available
                    info = f"Items: {available} available"
                    if available < total:
                        unavailable = total - available
                        info += f" ({unavailable} unavailable)"
                    self.call_from_thread(self.update_playlist_info, info)
                    self.call_from_thread(self.update_progress, 0, playlist_total)
                
                # Downloading item
                elif match := re.search(r'Downloading item (\d+) of (\d+)', line):
                    current_item = int(match.group(1))
                    total = int(match.group(2))
                    playlist_total = total
                    self.call_from_thread(self.update_current_action, f"⬇️ Downloading track {current_item} of {total}")
                    self.call_from_thread(self.update_status, f"⏳ Downloading {current_item}/{total}")
                    self.call_from_thread(self.update_progress, current_item - 1, total)
                
                # Extracting individual video - capture the title
                elif match := re.search(r'\[youtube\] Extracting URL: https://[^\s]+', line):
                    self.call_from_thread(self.update_current_action, f"🎵 Extracting track info...")
                
                # Video title (shown after extraction)
                elif match := re.search(r'\[youtube\] ([^:]+): Downloading (?:webpage|ios player API JSON|android player API JSON)', line):
                    video_id = match.group(1)
                    # Video ID is captured, title will come in [download] Destination line
                
                # Destination file path - this contains the actual filename
                elif match := re.search(r'\[download\] Destination: (.+)', line):
                    filepath = match.group(1)
                    # Extract just the filename from the path
                    filename = os.path.basename(filepath)
                    # Remove file extension for cleaner display
                    filename_without_ext = os.path.splitext(filename)[0]
                    current_filename = filename_without_ext
                    self.call_from_thread(self.update_current_file, filename_without_ext)
                
                # Download progress percentage
                elif match := re.search(r'\[download\]\s+(\d+\.?\d*)%', line):
                    percent = float(match.group(1))
                    if playlist_total > 0:
                        # Calculate overall progress
                        item_progress = (current_item - 1) + (percent / 100)
                        self.call_from_thread(self.update_progress, int(item_progress), playlist_total)
                
                # Already downloaded
                elif "[download]" in line and "has already been downloaded" in line:
                    self.call_from_thread(self.update_current_action, "✓ Track already downloaded (skipping)")
                    if match := re.search(r'has already been downloaded', line):
                        # Try to extract filename from the line
                        if current_filename:
                            self.call_from_thread(self.update_current_file, f"{current_filename} (already downloaded)")
                
                # Post-processing (converting)
                elif "[ExtractAudio]" in line:
                    self.call_from_thread(self.update_current_action, "🔄 Converting to audio format...")
                    if "Destination:" in line and (match := re.search(r'Destination: (.+)', line)):
                        filepath = match.group(1)
                        filename = os.path.basename(filepath)
                        filename_without_ext = os.path.splitext(filename)[0]
                        self.call_from_thread(self.update_current_file, filename_without_ext)
                
                # Embedding thumbnail
                elif "[EmbedThumbnail]" in line:
                    self.call_from_thread(self.update_current_action, "🖼️ Embedding thumbnail...")
                
                # Embedding metadata
                elif "[Metadata]" in line or "Adding metadata" in line:
                    self.call_from_thread(self.update_current_action, "📝 Embedding metadata...")
                
                # Deleting original file
                elif "Deleting original file" in line:
                    self.call_from_thread(self.update_current_action, "🧹 Cleaning up...")
                
                # Warnings
                elif "WARNING:" in line:
                    # Extract just the warning message
                    warning_msg = line.split("WARNING:", 1)[1].strip()
                    if "unavailable videos are hidden" in warning_msg:
                        self.call_from_thread(self.update_playlist_info, 
                            f"⚠️ Some videos unavailable - {warning_msg}")
                
                # Errors
                elif "ERROR:" in line:
                    self.call_from_thread(self.update_current_action, f"❌ Error occurred")
                    self.call_from_thread(self.update_status, "❌ Error during download")

            self.download_process.wait()

            # Reset buttons
            def reset_buttons():
                self.is_downloading = False
                self.is_paused = False
                pause_btn = self.query_one("#pause_btn", Button)
                download_btn = self.query_one("#download_btn", Button)
                pause_btn.disabled = True
                pause_btn.label = "Pause"
                download_btn.disabled = False

            if self.download_process.returncode == 0:
                self.call_from_thread(reset_buttons)
                self.call_from_thread(self.update_current_action, "✅ All downloads complete!")
                self.call_from_thread(self.update_status, "✅ Download complete!")
                self.call_from_thread(self.update_current_file, "")
                if playlist_total > 0:
                    self.call_from_thread(self.update_progress, playlist_total, playlist_total)
                    self.call_from_thread(self.update_playlist_info, 
                        f"✅ Successfully downloaded {playlist_total} tracks")
                self.call_from_thread(self.log_message, "=" * 60)
                self.call_from_thread(self.log_message, "Download completed successfully!")
            else:
                self.call_from_thread(reset_buttons)
                self.call_from_thread(self.update_current_action, f"❌ Download failed")
                self.call_from_thread(self.update_status, f"❌ Failed (exit code: {self.download_process.returncode})")
                self.call_from_thread(self.update_current_file, "")
                self.call_from_thread(self.log_message, f"ERROR: Download failed with exit code {self.download_process.returncode}")

        except FileNotFoundError:
            def reset_buttons():
                self.is_downloading = False
                self.is_paused = False
                pause_btn = self.query_one("#pause_btn", Button)
                download_btn = self.query_one("#download_btn", Button)
                pause_btn.disabled = True
                pause_btn.label = "Pause"
                download_btn.disabled = False
            
            self.call_from_thread(reset_buttons)
            self.call_from_thread(self.update_current_action, "❌ yt-dlp not found")
            self.call_from_thread(self.update_status, "❌ yt-dlp not found")
            self.call_from_thread(self.update_current_file, "")
            self.call_from_thread(self.log_message, "ERROR: yt-dlp not found. Please install it:")
            self.call_from_thread(self.log_message, "  pip install yt-dlp")
            self.call_from_thread(self.log_message, "  or: sudo pacman -S yt-dlp")
        except Exception as e:
            def reset_buttons():
                self.is_downloading = False
                self.is_paused = False
                pause_btn = self.query_one("#pause_btn", Button)
                download_btn = self.query_one("#download_btn", Button)
                pause_btn.disabled = True
                pause_btn.label = "Pause"
                download_btn.disabled = False
            
            self.call_from_thread(reset_buttons)
            self.call_from_thread(self.update_current_action, f"❌ Error: {str(e)}")
            self.call_from_thread(self.update_status, f"❌ Error: {str(e)}")
            self.call_from_thread(self.update_current_file, "")
            self.call_from_thread(self.log_message, f"ERROR: {str(e)}")


def main():
    """Run the app."""
    app = MusicDownloader()
    app.run()


if __name__ == "__main__":
    main()