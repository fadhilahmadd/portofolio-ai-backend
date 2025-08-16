#!/bin/sh
# Exit immediately if a command exits with a non-zero status.
set -e

# Recursively take ownership of the entire static directory.
# This covers the faiss_index, docs, and the audio directory where files are saved.
chown -R appuser:appuser /app/static

# Execute the main command (gunicorn) as the 'appuser'
exec gosu appuser "$@"