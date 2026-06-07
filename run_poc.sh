#!/bin/bash
set -e

echo "Starting Chia Full Node in background..."
. ./activate
chia start node > node_output.log 2>&1

# Wait for node to start and listen on port 8444
echo "Waiting for node to start..."
timeout 60 bash -c 'until lsof -t -i:8444; do sleep 1; done' || (echo "Node failed to start" && exit 1)

NODE_PID=$(pgrep -f "chia_full_node")
echo "Node started with PID: $NODE_PID"

echo "Running PoC..."
python3 poc_dos.py &
POC_PID=$!

echo "Monitoring memory usage of the node..."
for i in {1..20}; do
    if ! ps -p $NODE_PID > /dev/null; then
        echo "Node process not found. It might have crashed!"
        break
    fi
    MEM=$(ps -o rss= -p $NODE_PID)
    echo "Node RSS: $((MEM / 1024)) MB"
    sleep 2
done

echo "Cleaning up..."
kill $POC_PID 2>/dev/null || true
chia stop node
kill $NODE_PID 2>/dev/null || true

echo "PoC finished. Check node_output.log and debug.log for details."
