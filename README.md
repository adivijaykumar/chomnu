# Chomnu

A lightweight Markdown reader for macOS, Linux, and Windows. Double-click any `.md` file — or run `chomnu file.md` — to open it in a clean native window with full rendering support.

[![Tests](https://github.com/adivijaykumar/chomnu/actions/workflows/test.yml/badge.svg)](https://github.com/adivijaykumar/chomnu/actions/workflows/test.yml)

## Download

Pre-built binaries are attached to every [GitHub Release](https://github.com/adivijaykumar/chomnu/releases):

| Platform | File |
|---|---|
| Linux | `Chomnu-linux-x86_64` — single binary, `chmod +x` and run |
| Windows | `Chomnu-windows-x86_64.exe` — double-click to run |

> **macOS:** Install from source (see below). PyInstaller bundles cannot be
> ad-hoc signed on macOS 13+ due to stricter code-signing enforcement; the
> source install creates a lightweight shell-script `.app` that signs cleanly.

## Features

- **Math** — inline (`$x^2$`) and display (`$$\int f\,dx$$`) via MathJax, fully offline
- **Diagrams** — Mermaid flowcharts, sequence diagrams, pie charts
- **Syntax highlighting** — fenced code blocks via Pygments (100+ languages)
- **Table of contents** — fixed sidebar with active-section tracking; auto-hides when no headings
- **Search** — Ctrl+F opens a floating search bar with match count and navigation
- **Zoom** — Ctrl+= / Ctrl+- to scale text; Ctrl+0 to reset
- **Theme toggle** — `◐` button cycles auto / light / dark; auto follows your OS appearance
- **Print / PDF** — Ctrl+P prints cleanly (sidebar and controls hidden)
- **Live reload** — updates the window when the file changes on disk
- **CLI** — `chomnu file.md` opens from any terminal

---

## Installation

### macOS

**Requirements:** Python 3.10+, conda

```bash
git clone https://github.com/adivijaykumar/chomnu
cd chomnu

# Create environment and install Python deps
conda create -n chomnu python=3.12 -y
conda run -n chomnu pip install -r requirements.txt

# Download MathJax + Mermaid bundles (offline rendering)
bash scripts/download-assets.sh

# Create Chomnu.app in /Applications and install the `chomnu` CLI command
make install
```

This creates a shell-script `Chomnu.app` in `/Applications` (ad-hoc signed, opens
directly from Finder) and installs a `chomnu` wrapper at `~/.local/bin/chomnu`.

If `~/.local/bin` is not in your PATH, add this to `~/.zshrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

**Set as default app for .md files:**

Right-click any `.md` file in Finder → **Get Info** → **Open With** → select
**Chomnu** → click **Change All**.

---

### Linux (Ubuntu / Debian)

**Requirements:** Python 3.10+, pip, curl

```bash
git clone https://github.com/adivijaykumar/chomnu
cd chomnu

pip install -r requirements.txt
bash scripts/download-assets.sh

# Build binary, install CLI + double-click file association
make install-linux
```

This copies the binary to `~/.local/bin/chomnu` and registers `chomnu.desktop`
so double-clicking `.md` files in Nautilus / Dolphin / Thunar opens Chomnu.

If `~/.local/bin` is not in your PATH, add to `~/.bashrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

**Other distros:** the build requires `python3-tk` for the file picker on GTK
desktops:

```bash
# Arch
sudo pacman -S tk

# Fedora / RHEL
sudo dnf install python3-tkinter
```

---

### Windows

**Requirements:** Python 3.10+ (from [python.org](https://python.org))

**Git Bash:**

```bash
git clone https://github.com/adivijaykumar/chomnu
cd chomnu

pip install -r requirements.txt
bash scripts/download-assets.sh

pip install pyinstaller
pyinstaller --name Chomnu --windowed --add-data "assets;assets" --clean -y app.py
```

The built app is at `dist\Chomnu\Chomnu.exe`. Add `dist\Chomnu` to your PATH
via System Settings → Environment Variables to get the `chomnu` command.

**PowerShell:**

```powershell
git clone https://github.com/adivijaykumar/chomnu
cd chomnu

pip install -r requirements.txt

Invoke-WebRequest "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg-full.js" `
  -OutFile assets\mathjax.min.js
Invoke-WebRequest "https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js" `
  -OutFile assets\mermaid.min.js

pip install pyinstaller
pyinstaller --name Chomnu --windowed --add-data "assets;assets" --clean -y app.py
```

**Set as default app for .md files:** right-click any `.md` file → **Open with**
→ **Choose another app** → browse to `dist\Chomnu\Chomnu.exe` → check **Always
use this app**.

---

## Usage

```bash
chomnu file.md          # open a specific file
chomnu                  # open a file picker
```

The window live-reloads whenever the file is saved. Text is selectable and
copyable with the standard keyboard shortcuts (⌘C / Ctrl+C).

---

## Development

```bash
# Run from source (no build needed)
make run FILE=path/to/file.md

# Run tests
make test
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full dev setup instructions.

---

## Dependencies

| Package | Purpose |
|---|---|
| `pywebview` | Native window + webview (WKWebView / WebKitGTK / WebView2) |
| `Markdown` | Markdown → HTML |
| `pymdown-extensions` | Math protection (`arithmatex`) |
| `Pygments` | Syntax highlighting |
| MathJax 3 | TeX math rendering (bundled, offline) |
| Mermaid | Diagram rendering (bundled, offline) |

---

## License

GNU General Public License v3.0 — see [LICENSE](LICENSE).
