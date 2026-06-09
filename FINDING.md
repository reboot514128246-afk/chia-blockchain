# [CRITICAL] Remote Unauthenticated Denial of Service (Memory Exhaustion & Event Loop Blocking)

## Vulnerable Code
- `chia/util/streamable.py` — `parse_list()`, `parse_bytes()`, `parse_str()`
- `chia/server/ws_connection.py:276` — `perform_handshake()`

## Root Cause
The `Streamable.parse_list`, `parse_bytes`, and `parse_str` functions read a 4-byte length prefix from the network and immediately enter a synchronous loop or perform a large memory allocation. There are no global or default bounds on these sizes during deserialization. While some API methods use `list_limits` via a decorator, many messages—including the critical `Handshake` message sent upon connection—are parsed without any limits.

An attacker can provide a length that fits within the maximum WebSocket message size (50MB) but causes the node to allocate millions of Python objects. Because parsing is synchronous and occurs on the main thread, this blocks the entire event loop and leads to memory exhaustion.

## Attack Path
1. Attacker establishes a TLS connection to a target node (e.g., Full Node on port 8444).
2. Attacker sends a `Handshake` message with the `capabilities` list size set to a large value (e.g., 5,000,000).
3. The node receives the message and calls `Handshake.from_bytes(message.data)`.
4. `Streamable.parse_list` reads the 5M length and begins a synchronous loop to allocate tuples.
5. The node's main event loop thread is blocked, and memory usage spikes, leading to a crash or complete unresponsive state.

## PoC
The PoC script `poc_dos.py` uses `aiohttp` to send a malicious `Handshake`.

```bash
# Automation script to verify the vulnerability
./run_poc.sh
```

## Impact
Any node on the network can be remotely crashed or hung by an unauthenticated peer. This allows for a total network shutdown with minimal resources.

## Fix
Enforce default limits in the `Streamable` parsing layer.

```python
<<<<<<< SEARCH
def parse_list(f: BinaryIO, parse_inner_type_f: ParseFunctionType) -> list[object]:
    full_list: list[object] = []
    # wjb assert inner_type != get_args(List)[0]
    list_size = parse_uint32(f)
    for list_index in range(list_size):
        full_list.append(parse_inner_type_f(f))
    return full_list
=======
def parse_list(f: BinaryIO, parse_inner_type_f: ParseFunctionType) -> list[object]:
    list_size = parse_uint32(f)
    if list_size > 100_000_000:
        raise ValueError("List size exceeds limit")
    full_list: list[object] = []
    for list_index in range(list_size):
        full_list.append(parse_inner_type_f(f))
    return full_list
>>>>>>> REPLACE
```

## Status
CONFIRMED
