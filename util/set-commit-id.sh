#!/bin/bash
# 2012-03-06 Aurelio Jargas, Public Domain

OUTPUT_FILE="../static/js/commit_id.js"

# Make sure we're on the project root folder
cd $(dirname "$0")

# Savet the current git commit hash
commit_id=$(git log -1 --format="%H")
echo "var commit_id = '$commit_id';" > "$OUTPUT_FILE"

# Show the file contents, just to confirm
cat "$OUTPUT_FILE"
