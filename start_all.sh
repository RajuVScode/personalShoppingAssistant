#!/bin/bash

echo "Starting Python backend on port 8000..."
python run_backend.py &
PYTHON_PID=$!

sleep 3

echo "Starting Node.js frontend on port 5000..."
npm run dev &
NODE_PID=$!

trap "kill $PYTHON_PID $NODE_PID 2>/dev/null" EXIT

wait
