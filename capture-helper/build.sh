#!/bin/bash
# Builds the blender-capture helper (requires Xcode Command Line Tools).
#   xcode-select --install
set -euo pipefail
cd "$(dirname "$0")"

swiftc -O \
  -target arm64-apple-macos13.0 \
  main.swift \
  -o blender-capture

echo "Built: $(pwd)/blender-capture"
