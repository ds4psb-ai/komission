#!/bin/zsh
set -euo pipefail

NODE_SCRIPT="/Users/ted/komission/scripts/switch_chatgpt_repo.js"

if ! command -v node >/dev/null 2>&1; then
  echo "Status: node is required but not found."
  exit 1
fi

node "${NODE_SCRIPT}"
