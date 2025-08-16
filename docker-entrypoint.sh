#!/bin/sh
# Exit immediately if a command exits with a non-zero status.
set -e

# Take ownership of the static directory for FAISS index.
chown -R appuser:appuser /app/static

# Create and take ownership of the audio directory.
mkdir -p /app/audio
chown -R appuser:appuser /app/audio

# Execute the main command (gunicorn) as the 'appuser'
exec gosu appuser "$@"