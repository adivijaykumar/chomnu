CONDA_RUN = conda run -n chomnu

.PHONY: run test build install-linux clean

# Run from source (development)
run:
	$(CONDA_RUN) python app.py $(FILE)

# Run tests
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
	@echo "  macOS  → dist/Chomnu.app   (drag to /Applications)"
	@echo "  Linux  → dist/Chomnu       (single binary)"
	@echo "  Windows→ dist/Chomnu.exe"

# Linux only: install .desktop file so double-click works
install-linux: build
	sudo cp -r dist/Chomnu /opt/chomnu
	sed 's|Exec=.*|Exec=/opt/chomnu/Chomnu %f|' chomnu.desktop \
		| sudo tee /usr/share/applications/chomnu.desktop
	sudo update-desktop-database
	xdg-mime default chomnu.desktop text/markdown
	@echo "Done — double-click any .md file to open in Chomnu."

clean:
	rm -rf build dist Chomnu.spec __pycache__ .pytest_cache
