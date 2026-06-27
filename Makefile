CONDA_RUN = conda run -n chomnu
INSTALL_DIR = $(HOME)/.local/bin
OS := $(shell uname)

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

# Build a native app bundle / binary via PyInstaller
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
	@echo "Built:"
	@echo "  macOS  → dist/Chomnu.app"
	@echo "  Linux  → dist/Chomnu"
	@echo "  Windows→ dist/Chomnu.exe"
	@echo "Run 'make install' to install the chomnu CLI command."

# Install: copy app to standard location + drop a CLI wrapper in ~/.local/bin
install: build
	@mkdir -p $(INSTALL_DIR)
ifeq ($(OS), Darwin)
	@echo "Copying Chomnu.app to /Applications..."
	cp -r dist/Chomnu.app /Applications/
	@printf '#!/bin/bash\nexec /Applications/Chomnu.app/Contents/MacOS/Chomnu "$$@"\n' \
		> $(INSTALL_DIR)/chomnu
else
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
