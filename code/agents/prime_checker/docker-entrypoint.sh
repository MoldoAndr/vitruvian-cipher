#!/bin/bash
set -e

# Fix permissions for /data directory (volume mount)
if [ -d "/data" ]; then
    # If running as root, fix ownership
    if [ "$(id -u)" = "0" ]; then
        chown -R appuser:nogroup /data
        # Drop privileges and run as appuser
        exec gosu appuser "$0" "$@"
    fi
fi

# If running as appuser, just exec the main command
exec /app/prime-checker "$@"
