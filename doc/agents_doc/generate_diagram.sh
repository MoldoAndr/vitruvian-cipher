#!/bin/bash

# Script to generate PNG, SVG, and PDF diagrams from a given diagram.uml file
# Usage: ./generate_diagram.sh <path_to_diagram.uml>
# Example: ./generate_diagram.sh crypto_god/diagram.uml

# Check if argument is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <path_to_diagram.uml>"
    echo "Example: $0 crypto_god/diagram.uml"
    exit 1
fi

# Get the UML file path from argument
UML_FILE_PATH="$1"

# Check if the path is absolute or relative
if [[ "$UML_FILE_PATH" != /* ]]; then
    # Relative path - make it relative to current directory
    UML_FILE_PATH="$(pwd)/$UML_FILE_PATH"
fi

# Get the directory where the UML file is located
UML_DIR="$(dirname "$UML_FILE_PATH")"
UML_FILENAME="$(basename "$UML_FILE_PATH")"

# Define output files in the same directory as the UML file
PNG_FILE="$UML_DIR/diagram.png"
SVG_FILE="$UML_DIR/diagram.svg"
PDF_FILE="$UML_DIR/diagram.pdf"

# Check if the UML file exists
if [ ! -f "$UML_FILE_PATH" ]; then
    echo "Error: $UML_FILENAME not found in $UML_DIR"
    exit 1
fi

# Check if plantuml is available
if ! command -v plantuml &> /dev/null; then
    echo "Error: plantuml is not installed or not in PATH"
    echo "Please install plantuml first"
    exit 1
fi

echo "Generating diagrams from $UML_FILE_PATH..."
echo "Output directory: $UML_DIR"

# Change to the UML file directory to ensure relative paths work correctly
cd "$UML_DIR"

# Generate SVG
echo "Generating SVG..."
if plantuml -tsvg "$UML_FILENAME"; then
    echo "✓ SVG generated: $SVG_FILE"
else
    echo "✗ Failed to generate SVG"
    exit 1
fi

# Generate PNG
echo "Generating PNG..."
if plantuml -tpng "$UML_FILENAME"; then
    echo "✓ PNG generated: $PNG_FILE"
else
    echo "✗ Failed to generate PNG"
fi

# Generate PDF (may fail if dependencies are missing)
echo "Generating PDF..."
if plantuml -tpdf "$UML_FILENAME" 2>/dev/null; then
    echo "✓ PDF generated: $PDF_FILE"
else
    echo "⚠ PDF generation failed (missing dependencies)"
    echo "  You may need to install additional packages for PDF support"
fi

echo "Done!"