#!/bin/sh
# Exit immediately if a command exits with a non-zero status.
set -e

# Take ownership of the database file and FAISS index directory.
# This ensures the 'appuser' can write to them.
chown appuser:appuser /app/database.db
chown -R appuser:appuser /app/static/faiss_index

# Execute the main command (gunicorn) as the 'appuser'
exec su-exec appuser "$@"