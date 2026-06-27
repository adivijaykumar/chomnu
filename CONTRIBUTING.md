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
make test
# or:
conda run -n chomnu python -m pytest tests/ -v
```

The test suite covers the Markdown→HTML pipeline (`renderer.py`). It doesn't require a display — all tests run headlessly against the renderer logic.

**The two asset tests** (`test_mathjax_bundle_present`, `test_mermaid_bundle_present`) will fail if you haven't run `bash scripts/download-assets.sh` yet. CI downloads them automatically.

## Project layout

```
app.py          — PyWebView window, file watcher, CLI entry point
renderer.py     — Markdown → HTML pipeline (the core logic)
assets/
  style.css     — all styling (light + dark mode, sidebar, search bar)
  mathjax.min.js  — bundled offline (not in git, download via script)
  mermaid.min.js  — bundled offline (not in git, download via script)
tests/
  test_renderer.py — pytest suite (55 tests across 7 classes)
scripts/
  download-assets.sh — fetches JS bundles from jsDelivr CDN
Makefile        — run / test / build / install targets
```

## Making changes

- **Rendering logic** lives in `renderer.py`. The `render()` function is the entry point; it returns a full HTML document string.
- **Styling** is in `assets/style.css`. It's all plain CSS — no preprocessor.
- **Window/app behavior** is in `app.py`.

Add or update tests for any change to `renderer.py`. The tests in `test_renderer.py` are organized by feature area — add new test methods to the relevant existing class, or add a new class if you're adding a distinct feature.

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

The `release.yml` workflow builds binaries for macOS, Linux, and Windows and attaches them to a GitHub Release automatically.
