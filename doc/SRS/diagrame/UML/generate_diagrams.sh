#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SVG_DIR="${SCRIPT_DIR}/SVGs"
PNG_DIR="${SCRIPT_DIR}/PNGs"
PDF_DIR="${SCRIPT_DIR}/PDFs"

mkdir -p "$SVG_DIR" "$PNG_DIR" "$PDF_DIR"

if ! command -v plantuml >/dev/null 2>&1; then
  echo "Error: plantuml is not installed or not in PATH."
  echo "Install PlantUML or add it to PATH, then rerun this script."
  exit 1
fi

cd "$SCRIPT_DIR"
shopt -s nullglob
uml_files=( *.uml )

if [ ${#uml_files[@]} -eq 0 ]; then
  echo "No .uml files found in ${SCRIPT_DIR}"
  exit 0
fi

for uml_file in "${uml_files[@]}"; do
  echo "Rendering ${uml_file}..."
  plantuml -tsvg -o "SVGs" "$uml_file"
  plantuml -tpng -o "PNGs" "$uml_file"
  if ! plantuml -tpdf -o "PDFs" "$uml_file" 2>/dev/null; then
    echo "Warning: PDF generation failed for ${uml_file}"
  fi
done

echo "Done. Outputs:"
echo "  SVGs: ${SVG_DIR}"
echo "  PNGs: ${PNG_DIR}"
echo "  PDFs: ${PDF_DIR}"
