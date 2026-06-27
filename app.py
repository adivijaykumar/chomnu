#!/usr/bin/env python3
import sys
import os
import threading
import time
import webview
import renderer

TITLE = "Chomnu"
WATCH_INTERVAL = 0.5  # seconds between file-change checks

# Kept alive so the monitor isn't garbage-collected while the app runs
_cmd_shortcut_monitor = None


def _install_cmd_shortcuts(window):
    """macOS only: intercept Cmd+F/=/−/0 at the app level before WKWebView consumes them.

    WKWebView handles Cmd+F (native find) and Cmd+=/− (native zoom) in the
    responder chain before JavaScript ever sees the keydown event. An NSEvent
    local monitor fires earlier and lets us route those keys to our own JS
    functions instead, giving users the familiar Cmd shortcuts they expect on Mac.

    PyObjC ships as a transitive dependency of PyWebView on macOS, so no extra
    package is needed.
    """
    global _cmd_shortcut_monitor
    if sys.platform != "darwin":
        return
    try:
        from AppKit import NSEvent, NSEventModifierFlagCommand
        NSEventMaskKeyDown = 1 << 10  # NSEventType.keyDown = 10

        _key_map = {"f": "showSearch", "=": "zoomIn", "+": "zoomIn", "-": "zoomOut", "0": "resetZoom"}

        def _handler(event):
            if event.modifierFlags() & NSEventModifierFlagCommand:
                key = event.charactersIgnoringModifiers()
                fn = _key_map.get(key)
                if fn:
                    window.evaluate_js(f"window.chomnu && window.chomnu.{fn}()")
                    return None  # consume — don't forward to WKWebView
            return event  # pass everything else through

        _cmd_shortcut_monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
            NSEventMaskKeyDown, _handler
        )
    except Exception:
        pass  # PyObjC unavailable or error — Ctrl shortcuts remain functional


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

    # File watcher + macOS Cmd-shortcut monitor start once the window is ready.
    # on_shown fires on the main (GUI) thread, which is required for NSEvent monitors.
    def on_shown():
        _install_cmd_shortcuts(window)
        t = threading.Thread(target=_watch, args=(path, window), daemon=True)
        t.start()

    window.events.shown += on_shown
    webview.start()


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    open_file(path)
