#!/usr/bin/env bash
# Downloads MathJax and Mermaid bundles into assets/ for offline use.
# Run once after cloning: bash scripts/download-assets.sh

set -e
ASSETS="$(dirname "$0")/../assets"

echo "Downloading MathJax 3 (tex-svg-full)..."
curl -fsSL \
  "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg-full.js" \
  -o "$ASSETS/mathjax.min.js"

echo "Downloading Mermaid..."
curl -fsSL \
  "https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js" \
  -o "$ASSETS/mermaid.min.js"

echo "Done. Assets saved to assets/"
