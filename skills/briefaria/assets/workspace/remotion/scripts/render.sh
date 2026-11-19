#!/bin/bash
# Usage:
#   ./scripts/render.sh animatic path/to/manifest.json [output.mp4]
#   ./scripts/render.sh final path/to/manifest.json [output.mp4]

set -e

MODE="${1:?Usage: render.sh <animatic|final> <manifest-path> [output-path]}"
MANIFEST="$(realpath "${2:?Manifest path required}")"
OUTPUT="${3:-}"

COMP_ID="Animatic"
if [ "$MODE" = "final" ]; then
  COMP_ID="Final"
fi

MANIFEST_DIR="$(dirname "$MANIFEST")"

if [ -z "$OUTPUT" ]; then
  if [ "$MODE" = "animatic" ]; then
    OUTPUT="$MANIFEST_DIR/animatic.mp4"
  else
    mkdir -p "$MANIFEST_DIR/final"
    OUTPUT="$MANIFEST_DIR/final/final_$(date +%Y%m%d).mp4"
  fi
fi

# Ensure output directory exists
mkdir -p "$(dirname "$OUTPUT")"
OUTPUT="$(cd "$(dirname "$OUTPUT")" && pwd)/$(basename "$OUTPUT")"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REMOTION_DIR="$(dirname "$SCRIPT_DIR")"
PUBLIC_DIR="$REMOTION_DIR/public"
mkdir -p "$PUBLIC_DIR"
ASSET_DIR="$(mktemp -d "$PUBLIC_DIR/render-XXXXXX")"
SYMLINK="$ASSET_DIR/project"
cleanup() {
  rm -f "$SYMLINK"
  rmdir "$ASSET_DIR"
}
trap cleanup EXIT
ln -s "$MANIFEST_DIR" "$SYMLINK"

ASSET_PREFIX="$(basename "$ASSET_DIR")/project"
PROPS=$(node "$SCRIPT_DIR/resolve-manifest.js" "$MANIFEST" "$ASSET_PREFIX")

# Render
cd "$REMOTION_DIR"
npx remotion render src/index.ts "$COMP_ID" "$OUTPUT" --props="$PROPS"

echo "Rendered: $OUTPUT"
