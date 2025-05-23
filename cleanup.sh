#!/bin/bash

echo "🧹 Lab Recorder Cleanup Script"
echo "=================================="

# Find and kill Lab Recorder related processes
echo "🔍 Finding Lab Recorder processes..."

# Search for processes containing our patterns (more flexible)
PROCESSES=$(ps aux | grep -E "(dummy_sender\.py|dummy_receiver\.py|main\.py.*\.xdf|lab.recorder)" | grep -v grep)

if [ -z "$PROCESSES" ]; then
    echo "✅ No Lab Recorder processes found"
else
    echo "Found processes:"
    echo "$PROCESSES"
    echo ""
    echo "💀 Killing processes..."
    
    # Extract PIDs and kill them
    echo "$PROCESSES" | awk '{print $2}' | while read pid; do
        if [ ! -z "$pid" ]; then
            echo "  Killing PID $pid..."
            kill -TERM "$pid" 2>/dev/null
            sleep 0.5
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                echo "    Force killing PID $pid..."
                kill -KILL "$pid" 2>/dev/null
            fi
        fi
    done
fi

# Kill processes using port 22345
echo ""
echo "🔌 Checking port 22345..."
PORT_PIDS=$(lsof -ti tcp:22345 2>/dev/null)

if [ -z "$PORT_PIDS" ]; then
    echo "✅ Port 22345 is free"
else
    echo "Found processes using port 22345:"
    for pid in $PORT_PIDS; do
        echo "  Killing PID $pid using port 22345..."
        kill -TERM "$pid" 2>/dev/null
        sleep 0.5
        if kill -0 "$pid" 2>/dev/null; then
            kill -KILL "$pid" 2>/dev/null
        fi
    done
fi

# Wait and verify cleanup
echo ""
echo "⏳ Verifying cleanup..."
sleep 2

REMAINING=$(ps aux | grep -E "(dummy_sender\.py|dummy_receiver\.py|main\.py.*\.xdf)" | grep -v grep)
PORT_CHECK=$(lsof -ti tcp:22345 2>/dev/null)

if [ ! -z "$REMAINING" ]; then
    echo "⚠️  Warning: Some processes still running:"
    echo "$REMAINING"
    echo ""
    echo "You may need to kill these manually:"
    echo "$REMAINING" | awk '{print "  kill -9 " $2}'
else
    echo "✅ All Lab Recorder processes cleaned up!"
fi

if [ ! -z "$PORT_CHECK" ]; then
    echo "⚠️  Warning: Port 22345 still in use"
else
    echo "✅ Port 22345 is free"
fi

echo ""
echo "🎉 Cleanup complete!"
echo ""
echo "You can now run:"
echo "  python tools/dummy_sender.py &"
echo "  python main.py -f your_file.xdf" 