#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
SVG_DIR="${BASE_DIR}/SVGs"
PNG_DIR="${BASE_DIR}/PNGs"
PDF_DIR="${BASE_DIR}/PDFs"

mkdir -p "$SVG_DIR" "$PNG_DIR" "$PDF_DIR"

# Check for drawio CLI
if command -v drawio >/dev/null 2>&1; then
  DRAWIO_CLI="drawio"
elif command -v xdotool >/dev/null 2>&1 && command -v draw >/dev/null 2>&1; then
  DRAWIO_CLI="draw"
else
  echo "Error: Neither drawio CLI nor draw desktop app found."
  echo ""
  echo "Install drawio CLI:"
  echo "  macOS: brew install drawio"
  echo "  Linux: wget https://github.com/jgraph/drawio-desktop/releases/download/v24.0.0/drawio-amd64-24.0.0.deb && sudo dpkg -i drawio-amd64-24.0.0.deb"
  echo "  Or download from: https://github.com/jgraph/drawio-desktop/releases"
  exit 1
fi

cd "$SCRIPT_DIR"
shopt -s nullglob
drawio_files=( *.drawio )

if [ ${#drawio_files[@]} -eq 0 ]; then
  echo "No .drawio files found in ${SCRIPT_DIR}"
  exit 0
fi

echo "Found ${#drawio_files[@]} DrawIO files"
echo "Using CLI: $DRAWIO_CLI"
echo ""

for drawio_file in "${drawio_files[@]}"; do
  base_name=$(basename "$drawio_file" .drawio)
  echo "Rendering ${drawio_file}..."

  # Export to SVG
  "$DRAWIO_CLI" -x "$drawio_file" -o "${SVG_DIR}/${base_name}.svg" -f svg -t --no-sandbox

  # Export to PNG
  "$DRAWIO_CLI" -x "$drawio_file" -o "${PNG_DIR}/${base_name}.png" -f png -t --no-sandbox -s 2

  # Export to PDF
  "$DRAWIO_CLI" -x "$drawio_file" -o "${PDF_DIR}/${base_name}.pdf" -f pdf -t --no-sandbox

  echo "  ✓ SVG: ${SVG_DIR}/${base_name}.svg"
  echo "  ✓ PNG: ${PNG_DIR}/${base_name}.png"
  echo "  ✓ PDF: ${PDF_DIR}/${base_name}.pdf"
done

echo ""
echo "Done! Generated:"
echo "  ${#drawio_files[@]} SVG files in ${SVG_DIR}"
echo "  ${#drawio_files[@]} PNG files in ${PNG_DIR}"
echo "  ${#drawio_files[@]} PDF files in ${PDF_DIR}"
