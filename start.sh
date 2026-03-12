#!/bin/bash

# Start GPU Monitor Platform

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Start scheduler in background
echo "Starting scheduler..."
nohup python scheduler.py > logs/scheduler.log 2>&1 &
SCHEDULER_PID=$!
echo $SCHEDULER_PID > .scheduler.pid
echo "Scheduler started (PID: $SCHEDULER_PID)"

# Start Django server
echo "Starting web server on http://0.0.0.0:8888"
python manage.py runserver 0.0.0.0:8888
