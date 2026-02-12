#!/bin/bash
# Start script for Render - ensures proper Python path
export PYTHONPATH="${PYTHONPATH}:$(dirname $(pwd))"
cd backend
python -m uvicorn api_server:app --host 0.0.0.0 --port $PORT
