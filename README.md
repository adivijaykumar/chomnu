# Chomnu

A lightweight Markdown reader for Linux, Windows, and macOS. Double-click any `.md` file to open it in a clean native window with full rendering support — math, diagrams, syntax highlighting, dark mode.

## Features

- **Math** — inline (`$x^2$`) and display (`$$\int f\,dx$$`) via MathJax
- **Diagrams** — Mermaid flowcharts, sequence diagrams, pie charts
- **Syntax highlighting** — fenced code blocks via Pygments
- **Dark mode** — follows your system appearance
- **File watching** — updates live when the file changes on disk
- **Offline** — all assets bundled, no internet required

## Install

### 1. Clone and set up

```bash
git clone https://github.com/yourusername/chomnu
cd chomnu
pip install -r requirements.txt
bash scripts/download-assets.sh
```

### 2. Run

```bash
python3 app.py path/to/file.md
# or just
python3 app.py   # opens a file picker
```

### Linux — set as default app for .md files

```bash
# Install to /opt/chomnu
sudo cp -r . /opt/chomnu

# Register the desktop entry
sudo cp chomnu.desktop /usr/share/applications/
sudo update-desktop-database

# Set as default for Markdown files
xdg-mime default chomnu.desktop text/markdown
```

Now double-clicking any `.md` file in your file manager opens it in Chomnu.

### Windows — set as default app

1. Right-click any `.md` file → Open with → Choose another app
2. Browse to `app.py` (or a packaged `.exe` if using PyInstaller)
3. Check "Always use this app"

### macOS

Works the same way — pywebview uses WKWebView natively. You can set it as default via System Settings → General → Default applications, or just run from terminal.

## Dependencies

| Package | Purpose |
|---|---|
| `pywebview` | Native window + webview per OS |
| `Markdown` | Markdown → HTML |
| `pymdown-extensions` | Math protection (arithmatex) |
| `Pygments` | Syntax highlighting |

## Testing with Docker (Linux)

```bash
docker run -it --rm \
  -v $(pwd):/chomnu \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  ubuntu:24.04 bash

# Inside container:
apt-get update && apt-get install -y python3 python3-pip python3-gi \
  gir1.2-webkit2-4.1 libgtk-4-dev python3-tk
cd /chomnu
pip install -r requirements.txt
bash scripts/download-assets.sh
python3 app.py sample.md
```

## License

MIT
