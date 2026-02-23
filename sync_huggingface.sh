#!/bin/bash
# SysCRED - Sync to HuggingFace Space
# Usage: ./sync_huggingface.sh
# This script copies the latest code into the huggingface_space/ directory
# and optionally pushes to HuggingFace using git.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HF_DIR="$SCRIPT_DIR/huggingface_space"

echo "🔄 Syncing SysCRED to HuggingFace Space..."

# Copy requirements
cp "$SCRIPT_DIR/requirements-full.txt" "$HF_DIR/requirements.txt"
echo "  ✅ requirements.txt"

# Copy syscred module
rm -rf "$HF_DIR/syscred"
cp -r "$SCRIPT_DIR/syscred" "$HF_DIR/syscred"
find "$HF_DIR/syscred" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
echo "  ✅ syscred/"

# Copy ontology
rm -rf "$HF_DIR/ontology"
cp -r "$SCRIPT_DIR/ontology" "$HF_DIR/ontology"
echo "  ✅ ontology/"

# Copy env example
cp "$SCRIPT_DIR/.env.example" "$HF_DIR/.env.example"
echo "  ✅ .env.example"

echo ""
echo "✅ HuggingFace Space directory ready at: $HF_DIR"
echo ""
echo "To push to HuggingFace:"
echo "  cd $HF_DIR"
echo "  git init (if not already)"
echo "  git remote add hf https://huggingface.co/spaces/DomLoyer/syscred"
echo "  git add -A && git commit -m 'Sync from main'"
echo "  git push hf main"
