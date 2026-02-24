#!/usr/bin/env bash
# format-frontend.sh
# Run Prettier formatting checks (and optionally auto-fix) on frontend files.
#
# Usage:
#   ./format-frontend.sh          # Check formatting only (exit 1 if issues found)
#   ./format-frontend.sh --fix    # Auto-fix formatting in place

set -euo pipefail

FRONTEND_DIR="$(dirname "$0")/frontend"

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "Installing frontend dev dependencies..."
    (cd "$FRONTEND_DIR" && npm install)
fi

if [ "${1:-}" = "--fix" ]; then
    echo "Formatting frontend files..."
    (cd "$FRONTEND_DIR" && npm run format)
    echo "Done. All frontend files formatted."
else
    echo "Checking frontend formatting..."
    (cd "$FRONTEND_DIR" && npm run format:check)
    echo "All frontend files are correctly formatted."
fi
