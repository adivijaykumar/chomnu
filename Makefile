CONDA_RUN = conda run -n chomnu
INSTALL_DIR = $(HOME)/.local/bin
OS := $(shell uname)
# Lazily evaluated (=, not :=) so the subprocess only runs when CONDA_PYTHON is
# actually expanded — i.e. during 'make install' on macOS, not on every invocation.
CONDA_PYTHON = $(shell conda run -n chomnu which python 2>/dev/null || echo "python3")
# abspath + MAKEFILE_LIST gives the repo root regardless of where make is invoked from.
REPO_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

.PHONY: run test assets build install install-linux clean

# Run from source (development)
run:
	$(CONDA_RUN) python app.py $(FILE)

# Install dev dependencies (Playwright + browser — run once after cloning)
install-dev:
	$(CONDA_RUN) pip install -r requirements-dev.txt
	$(CONDA_RUN) playwright install webkit

# Run tests (renderer unit tests + UI tests via Playwright)
test:
	$(CONDA_RUN) python -m pytest tests/ -v

# Download MathJax + Mermaid bundles
assets:
	bash scripts/download-assets.sh

# Build a PyInstaller binary — Linux and Windows only.
# macOS uses a shell-script .app via 'make install' (no PyInstaller needed).
build:
	$(CONDA_RUN) pip install pyinstaller -q
	$(CONDA_RUN) pyinstaller \
		--name Chomnu \
		--windowed \
		--add-data "assets:assets" \
		--clean \
		-y \
		app.py
	@echo ""
	@echo "Built: dist/Chomnu (Linux) or dist/Chomnu.exe (Windows)"
	@echo "Run 'make install' to install the chomnu CLI command."

# Install: on macOS create a lightweight shell-script .app (no PyInstaller needed —
# avoids the code-signing failures caused by PyInstaller's non-standard bundle layout
# on macOS 13+). On Linux, build a PyInstaller binary as before.
install:
	@mkdir -p $(INSTALL_DIR)
ifeq ($(OS), Darwin)
	@echo "Creating Chomnu.app in /Applications..."
	@rm -rf /Applications/Chomnu.app
	@mkdir -p /Applications/Chomnu.app/Contents/MacOS
	@cp macos/Info.plist /Applications/Chomnu.app/Contents/Info.plist
	@printf '#!/bin/bash\nexec $(CONDA_PYTHON) $(REPO_DIR)/app.py "$$@"\n' \
		> /Applications/Chomnu.app/Contents/MacOS/Chomnu
	@chmod +x /Applications/Chomnu.app/Contents/MacOS/Chomnu
	@codesign --force --sign - /Applications/Chomnu.app
	@printf '#!/bin/bash\nexec /Applications/Chomnu.app/Contents/MacOS/Chomnu "$$@"\n' \
		> $(INSTALL_DIR)/chomnu
else
	$(CONDA_RUN) pip install pyinstaller -q
	$(CONDA_RUN) pyinstaller \
		--name Chomnu \
		--windowed \
		--add-data "assets:assets" \
		--clean -y app.py
	@echo "Installing binary to $(INSTALL_DIR)..."
	cp dist/Chomnu $(INSTALL_DIR)/chomnu
endif
	chmod +x $(INSTALL_DIR)/chomnu
	@echo ""
	@echo "Installed: $(INSTALL_DIR)/chomnu"
	@echo ""
	@if echo ":$$PATH:" | grep -q ":$(INSTALL_DIR):"; then \
		echo "  chomnu file.md  ✓ ready to use"; \
	else \
		echo "  Add this to your shell profile (~/.zshrc or ~/.bashrc):"; \
		echo "    export PATH=\"$(INSTALL_DIR):\$$PATH\""; \
	fi

# Linux only: also register .desktop file for double-click support
install-linux: install
	sed 's|Exec=.*|Exec=$(INSTALL_DIR)/chomnu %f|' chomnu.desktop \
		| sudo tee /usr/share/applications/chomnu.desktop
	sudo update-desktop-database
	xdg-mime default chomnu.desktop text/markdown
	@echo "Double-click on .md files now opens Chomnu."

clean:
	rm -rf build dist Chomnu.spec __pycache__ .pytest_cache
