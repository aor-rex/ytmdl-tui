# 🎵 youTube music Downloader

A terminal ui for downloading music from YouTube Music with metadata, built with [Textual](https://github.com/Textualize/textual) and [yt-dlp](https://github.com/yt-dlp/yt-dlp).

---

## Features

- Download individual tracks or entire playlists from YouTube Music
- Automatically embeds metadata (title, artist, album) and thumbnails
- Supports multiple audio formats: MP3, M4A, FLAC, WAV, OPUS
- Real-time download progress with per-track and playlist-level tracking
- Pause and resume downloads mid-session
---

## Requirements

- Python 3.8+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [Textual](https://github.com/Textualize/textual)

---

## Installation

```bash
git clone https://github.com/aor-rex/ytmdl-tui.git
cd ytmdl-tui
pip install -r requirements.txt
pip install .
```

---

## Usage

run `ytmdl-tui` in your terminal, paste a youtube music URL into the URL field, and press **download** (or `d`).

Both playlist URLs and individual track URLs are supported:

```
https://music.youtube.com/playlist?list=...
https://music.youtube.com/watch?v=...
https://www.youtube.com/watch?v=...
```

### Output Structure

Downloaded files are organized automatically by uploader and playlist:

```
~/Music/
└── Artist Name/
    └── Playlist Name/
        ├── 01 - Track Title.mp3
        ├── 02 - Track Title.mp3
        └── ...
```

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `d` | Start download |
| `p` | Pause / Resume |
| `s` | Save settings |
| `c` | Clear log |
| `q` | Quit |

---

## Configuration

Settings are saved automatically to `~/.config/ytdl-tui/config.json` when you press **Save Settings** (or `s`). On next launch, your last-used output directory, format, quality, and theme will be restored.


## Themes

| Name | Description |
|------|-------------|
| `default` | Textual dark |
| `light` | Textual light |
| `nord` | Nord palette |
| `gruvbox` | Gruvbox warm tones |
| `catppuccin` | Catppuccin Mocha |
| `dracula` | Dracula |
| `tokyo-night` | Tokyo Night |
| `rose-pine` | Rosé Pine |

Themes can be changed live from the dropdown and take effect immediately.

---

## Troubleshooting

**`yt-dlp not found`** — Make sure yt-dlp is installed and on your `PATH`. Try running `yt-dlp --version` in your terminal to verify.

**thumbnail embedding fails** — Requires `ffmpeg`. Install it via your system package manager (`brew install ffmpeg`, `sudo apt install ffmpeg`, etc.).

**Some playlist tracks are unavailable** — YouTube Music may restrict certain tracks by region. The downloader will skip unavailable tracks and continue with the rest.

**Download appears to hang** — Some playlists require fetching metadata for many tracks before downloading begins. Check the log panel for activity.

