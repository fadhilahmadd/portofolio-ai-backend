#!/bin/sh
set -e

# Ensure static dir ownership (if present)
if [ -d /app/static ]; then
  chown -R appuser:appuser /app/static || true
fi

# Create and own the audio directory (default to /tmp/audio in Cloud Run)
AUDIO_DIR="${AUDIO_DIR:-/tmp/audio}"
mkdir -p "$AUDIO_DIR"
chown -R appuser:appuser "$AUDIO_DIR" || true

# Drop privileges and exec the main command
exec gosu appuser "$@"
