# [CRITICAL] Remote Denial of Service via Unbounded List Deserialization in Handshake

## Vulnerable Code
`chia/util/streamable.py:440` — `parse_list()`
`chia/util/streamable.py:657` — `Streamable.parse()`

## Root Cause
The Chia networking protocol uses a custom serialization format called `Streamable`. When a class with a `list` field is parsed from bytes, the `parse_list` function reads a 4-byte length prefix and then iterates that many times to parse each element. There are no global or per-message limits on the number of elements in a list during the initial parsing phase.

Specifically, the `Handshake` message (and many others like `RespondPeers`, `RequestSESInfo`) contains list fields. An attacker can send a `Handshake` message with a large length prefix for the `capabilities` list. Even if the elements themselves are small (or empty strings), the Python interpreter allocates a list of that size, leading to rapid memory exhaustion and an Out-Of-Memory (OOM) crash of the full node.

While some API points have `list_limits` applied via the `@metadata.request` decorator, this check only happens *after* the `Handshake` class (or other message classes) has already been fully instantiated from bytes. The `Handshake.from_bytes(data)` call itself is vulnerable because it uses the default `parse_list` which does not respect any limits.

## Attack Path
1. Attacker initiates a TLS connection to a Chia Full Node (port 8444).
2. Attacker sends a malicious `Handshake` message.
3. The message claims to contain a very large number of elements (e.g., 10,000,000) in the `capabilities` list.
4. The server calls `Handshake.from_bytes(data)`, which reaches `parse_list` in `chia/util/streamable.py`.
5. `parse_list` reads the large length and starts a loop to append elements to a new list.
6. The server's memory is exhausted, causing the OS to kill the process or the Python interpreter to raise a `MemoryError`.
7. Result: The full node is dead (Denial of Service).

## PoC
```bash
./run_poc.sh
# Expected output: Node RSS: [High value] MB (e.g. > 200MB for a small payload)
```

## Impact
Any remote attacker can crash any publicly reachable Chia Full Node with a single unauthenticated message. This disrupts the blockchain network by taking nodes offline.

## Fix
Implement a mandatory `max_items` limit in `parse_list` and ensure all protocol messages define reasonable bounds for their list fields. Global defaults for list sizes should be enforced at the `Streamable` layer.

## Status
CONFIRMED
