#!/bin/bash
# Start the SuperBowl Ad Pulse API

# Activate virtual environment if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run the new modular backend
echo "Starting SuperBowl Ad Pulse API on http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""

uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
