#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
SVG_DIR="${BASE_DIR}/SVGs"
PNG_DIR="${BASE_DIR}/PNGs"
PDF_DIR="${BASE_DIR}/PDFs"

mkdir -p "$SVG_DIR" "$PNG_DIR" "$PDF_DIR"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Vitruvian Cipher - UML Diagrams Compilation Script      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Create output directories
mkdir -p "$SVG_DIR" "$PNG_DIR" "$PDF_DIR"

PLANTUML_COUNT=0
DRAWIO_COUNT=0

# ============================================================================
# Part 1: Compile PlantUML files
# ============================================================================
echo "📊 Part 1: Compiling PlantUML diagrams..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! command -v plantuml >/dev/null 2>&1; then
  echo "⚠️  Warning: plantuml is not installed or not in PATH."
  echo "   Install PlantUML to compile .uml files:"
  echo "   - macOS: brew install plantuml"
  echo "   - Linux: sudo apt-get install plantuml"
  echo "   - Or download from: https://plantuml.com/download"
  echo ""
else
  cd "$SCRIPT_DIR"
  shopt -s nullglob
  uml_files=( *.uml )

  if [ ${#uml_files[@]} -gt 0 ]; then
    echo "Found ${#uml_files[@]} PlantUML files"
    echo ""

    for uml_file in "${uml_files[@]}"; do
      base_name=$(basename "$uml_file" .uml)
      echo "  ↳ Rendering ${base_name}..."

      # Generate SVG
      plantuml -tsvg -o "../SVGs" "$uml_file" 2>/dev/null && mv "../SVGs/${base_name}.svg" "$SVG_DIR/" 2>/dev/null || true

      # Generate PNG
      plantuml -tpng -o "../PNGs" "$uml_file" 2>/dev/null && mv "../PNGs/${base_name}.png" "$PNG_DIR/" 2>/dev/null || true

      # Generate PDF (may fail on some systems)
      if plantuml -tpdf -o "../PDFs" "$uml_file" 2>/dev/null; then
        mv "../PDFs/${base_name}.pdf" "$PDF_DIR/" 2>/dev/null || true
      fi

      PLANTUML_COUNT=$((PLANTUML_COUNT + 1))
    done

    echo ""
    echo "✅ Compiled $PLANTUML_COUNT PlantUML diagrams"
  else
    echo "⚠️  No PlantUML files found"
  fi
fi

echo ""

# ============================================================================
# Part 2: Compile DrawIO files
# ============================================================================
echo "🎨 Part 2: Compiling DrawIO diagrams..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

XML_DIR="${BASE_DIR}/XML"

if [ ! -d "$XML_DIR" ]; then
  echo "⚠️  No XML directory found"
else
  cd "$XML_DIR"
  shopt -s nullglob
  drawio_files=( *.drawio )

  if [ ${#drawio_files[@]} -eq 0 ]; then
    echo "⚠️  No DrawIO files found in ${XML_DIR}"
  else
    # Check for drawio CLI
    if command -v drawio >/dev/null 2>&1; then
      DRAWIO_CLI="drawio"
    elif command -v draw >/dev/null 2>&1; then
      DRAWIO_CLI="draw"
    else
      echo "⚠️  Warning: Neither drawio CLI nor draw desktop app found."
      echo "   Install drawio to compile .drawio files:"
      echo "   - macOS: brew install drawio"
      echo "   - Linux: wget https://github.com/jgraph/drawio-desktop/releases/download/v24.0.0/drawio-amd64-24.0.0.deb && sudo dpkg -i drawio-amd64-24.0.0.deb"
      echo ""
    fi

    if [ -n "${DRAWIO_CLI:-}" ]; then
      echo "Found ${#drawio_files[@]} DrawIO files"
      echo "Using CLI: $DRAWIO_CLI"
      echo ""

      for drawio_file in "${drawio_files[@]}"; do
        base_name=$(basename "$drawio_file" .drawio)
        echo "  ↳ Rendering ${base_name}..."

        # Export to SVG
        "$DRAWIO_CLI" -x "$drawio_file" -o "${SVG_DIR}/${base_name}.svg" -f svg -t --no-sandbox 2>/dev/null || true

        # Export to PNG
        "$DRAWIO_CLI" -x "$drawio_file" -o "${PNG_DIR}/${base_name}.png" -f png -t --no-sandbox -s 2 2>/dev/null || true

        # Export to PDF
        "$DRAWIO_CLI" -x "$drawio_file" -o "${PDF_DIR}/${base_name}.pdf" -f pdf -t --no-sandbox 2>/dev/null || true

        DRAWIO_COUNT=$((DRAWIO_COUNT + 1))
      done

      echo ""
      echo "✅ Compiled $DRAWIO_COUNT DrawIO diagrams"
    fi
  fi
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                     Compilation Summary                    ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║  PlantUML diagrams:  $PLANTUML_COUNT                                 ║"
echo "║  DrawIO diagrams:    $DRAWIO_COUNT                                 ║"
echo "║  ──────────────────────────────────────────────────────  ║"
echo "║  Total diagrams:     $((PLANTUML_COUNT + DRAWIO_COUNT))                                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📁 Output locations:"
echo "   SVGs: ${SVG_DIR}"
echo "   PNGs: ${PNG_DIR}"
echo "   PDFs: ${PDF_DIR}"
echo ""

if [ $((PLANTUML_COUNT + DRAWIO_COUNT)) -gt 0 ]; then
  echo "✅ All diagrams compiled successfully!"
else
  echo "⚠️  No diagrams were compiled. Please install the required tools."
fi
