# Contributing to Chomnu

Thanks for your interest. Chomnu is a small project — contributions, bug reports, and feature ideas are all welcome.

## Development setup

```bash
git clone https://github.com/adivijaykumar/chomnu
cd chomnu

# Create the conda environment
conda create -n chomnu python=3.12 -y
conda run -n chomnu pip install -r requirements.txt

# Download the offline JS bundles (MathJax + Mermaid)
bash scripts/download-assets.sh
```

Run from source at any time:

```bash
make run FILE=path/to/file.md
# or:
conda run -n chomnu python app.py path/to/file.md
```

## Running the tests

```bash
# Install Playwright (first time only)
make install-dev

# Run all 93 tests
make test
```

The suite has two parts:

- **`tests/test_renderer.py`** (61 tests) — covers the Markdown→HTML pipeline. Runs headlessly, no display needed.
- **`tests/test_ui.py`** (32 tests) — drives a real headless WebKit browser via Playwright. Covers the search bar, zoom buttons, keyboard shortcuts, and theme toggle.

**Note:** the two asset tests (`test_mathjax_bundle_present`, `test_mermaid_bundle_present`) will fail until you run `bash scripts/download-assets.sh`. CI downloads them automatically.

## Project layout

```
app.py               — PyWebView window, file watcher, CLI entry point
renderer.py          — Markdown → HTML pipeline (the core logic)
assets/
  style.css          — all styling (light/dark themes, sidebar, search bar, controls)
  mathjax.min.js     — bundled offline (not in git; download via script)
  mermaid.min.js     — bundled offline (not in git; download via script)
macos/
  Info.plist         — app bundle metadata for the macOS shell-script .app
tests/
  test_renderer.py   — renderer unit tests (61 tests across 10 classes)
  test_ui.py         — Playwright WebKit UI tests (32 tests across 4 classes)
scripts/
  download-assets.sh — fetches JS bundles from jsDelivr CDN
Makefile             — run / test / build / install targets
```

## Making changes

- **Rendering logic** lives in `renderer.py`. The `render()` function is the single entry point; it returns a full HTML document string.
- **Styling** is in `assets/style.css`. Plain CSS — no preprocessor. Theme switching uses `data-theme` on `<html>`; the media query handles auto/OS mode.
- **Window and app behavior** is in `app.py`.
- **UI JavaScript** is the `_UI_JS` constant in `renderer.py`. It runs inside an IIFE on every rendered page.

Add or update tests for any change to `renderer.py`. For changes to the JS or CSS, add or update tests in `test_ui.py`.

## Submitting a pull request

1. Fork the repo and create a branch: `git checkout -b your-feature`
2. Make your changes and add tests
3. Verify the full suite passes: `make test`
4. Open a PR against `main` — describe what you changed and why

There's no formal style guide. Match the style of the surrounding code.

## Reporting bugs

Open a [GitHub issue](https://github.com/adivijaykumar/chomnu/issues) with:
- Your OS and Python version
- The Markdown input that triggers the bug (a minimal example if possible)
- What you expected vs. what happened

## Releasing (maintainers)

Tag a version and push — GitHub Actions does the rest:

```bash
git tag v1.2.3
git push --tags
```

The `release.yml` workflow builds binaries for Linux and Windows and attaches them to a GitHub Release automatically. macOS users install from source via `make install`.
