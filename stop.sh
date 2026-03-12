#!/bin/bash

# Stop GPU Monitor Platform

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Stopping GPU Monitor Platform..."

# Stop scheduler
if [ -f .scheduler.pid ]; then
    SCHEDULER_PID=$(cat .scheduler.pid)
    if ps -p $SCHEDULER_PID > /dev/null 2>&1; then
        echo "Stopping scheduler (PID: $SCHEDULER_PID)..."
        kill $SCHEDULER_PID
        rm .scheduler.pid
        echo "Scheduler stopped"
    else
        echo "Scheduler not running"
        rm .scheduler.pid
    fi
else
    echo "No scheduler PID file found"
    # Try to find and kill scheduler process
    pkill -f "python.*scheduler.py" && echo "Scheduler stopped" || echo "No scheduler process found"
fi

# Stop Django server
echo "Stopping web server..."
pkill -f "python.*manage.py runserver" && echo "Web server stopped" || echo "No web server process found"

echo "Platform stopped"
