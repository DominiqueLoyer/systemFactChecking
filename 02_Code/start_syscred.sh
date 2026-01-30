#!/bin/bash
# SysCRED Startup Script
# ----------------------

# 1. Go to the code directory
cd "$(dirname "$0")"

# 2. Activate Virtual Environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Virtual environment not found! Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r syscred/requirements.txt
fi

# 3. Kill any existing process on port 5001 (to avoid 'Address already in use')
PID=$(lsof -ti:5001)
if [ -n "$PID" ]; then
  echo "Stopping existing server on port 5001 (PID: $PID)..."
  kill -9 $PID
fi

# 4. Start the server
echo "Starting SysCRED Server..."
echo "Access at: http://localhost:5001"
python syscred/backend_app.py
