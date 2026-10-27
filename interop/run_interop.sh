#!/usr/bin/env bash
# Runs the full cross-language interop proof: Python starts a session,
# Node.js resumes and continues it, Python resumes again to verify
# everything and tear it down — all through one shared JSON state file.
#
# Exits non-zero if any step fails, including the assertions in step 3.
set -euo pipefail
cd "$(dirname "$0")"

STATE_DIR="$(mktemp -d)"
STATE_PATH="$STATE_DIR/state.json"

echo "=== building the TypeScript SDK ==="
(cd ../ts && npm install --silent && npm run build --silent)

echo
echo "=== step 1: Python initiates the session ==="
SESSION_ID=$(python3 01_python_init.py "$STATE_PATH")
echo "session id: $SESSION_ID"

echo
echo "=== step 2: Node resumes it, reads Python's write, continues it ==="
node 02_node_continue.mjs "$STATE_PATH" "$SESSION_ID"

echo
echo "=== step 3: Python resumes again, verifies everything, tears down ==="
python3 03_python_verify_and_teardown.py "$STATE_PATH" "$SESSION_ID"

echo
echo "=== raw state.json (the entire handoff happened through this file) ==="
cat "$STATE_PATH"

rm -rf "$STATE_DIR"
