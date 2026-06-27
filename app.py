#!/usr/bin/env python3
import sys
import os
import threading
import time
import webview
import renderer

TITLE = "Chomnu"
WATCH_INTERVAL = 0.5  # seconds between file-change checks


def _render_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        return renderer.render(text)
    except Exception as e:
        return f"<html><body><pre style='color:red'>Error reading file:\n{e}</pre></body></html>"


def _watch(path, window):
    """Background thread: reload window when file changes on disk."""
    last_mtime = None
    while True:
        try:
            mtime = os.path.getmtime(path)
            if last_mtime is not None and mtime != last_mtime:
                html = _render_file(path)
                window.load_html(html)
            last_mtime = mtime
        except FileNotFoundError:
            pass
        time.sleep(WATCH_INTERVAL)


def open_file(path=None):
    if path is None:
        # Show native file picker before the window opens
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(
            title="Open Markdown file",
            filetypes=[("Markdown", "*.md *.markdown"), ("All files", "*.*")],
        )
        root.destroy()
        if not path:
            sys.exit(0)

    path = os.path.abspath(path)
    title = f"{os.path.basename(path)} — {TITLE}"
    html = _render_file(path)

    window = webview.create_window(
        title,
        html=html,
        width=860,
        height=960,
        min_size=(400, 300),
        easy_drag=False,   # allow text selection instead of dragging the window
    )

    # File watcher runs in background once the window is ready
    def on_shown():
        t = threading.Thread(target=_watch, args=(path, window), daemon=True)
        t.start()

    window.events.shown += on_shown
    webview.start()


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    open_file(path)
