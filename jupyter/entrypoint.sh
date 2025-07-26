#!/bin/bash
set -e

echo "Setting up Jupyter environment..."

# Set a default password if not provided
export JUPYTER_PASSWORD="${JUPYTER_PASSWORD:-jupyter123}"

echo "Generating hashed password using Python..."

HASHED_PASSWORD=$(python -c "from jupyter_server.auth import passwd; import os; print(passwd(os.environ['JUPYTER_PASSWORD']))")

echo "Password hash generated. Starting Jupyter Server..."

# Start Jupyter with the hashed password
exec "$@" --NotebookApp.password="$HASHED_PASSWORD"