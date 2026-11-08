#!/usr/bin/env python3
"""Minimal JSON-RPC client for Kodi (TCP 9090, through adb forward)."""
import json
import socket
import sys


def call(method, params=None, host="127.0.0.1", port=9090, timeout=60):
    req = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        req["params"] = params
    s = socket.create_connection((host, port), timeout=timeout)
    s.sendall(json.dumps(req).encode())
    buf = b""
    dec = json.JSONDecoder()
    while True:
        chunk = s.recv(65536)
        if not chunk:
            break
        buf += chunk
        try:
            text = buf.decode()
            pos = 0
            while pos < len(text):
                obj, end = dec.raw_decode(text, pos)
                pos = end
                while pos < len(text) and text[pos].isspace():
                    pos += 1
                if obj.get("id") == 1:
                    s.close()
                    return obj
        except ValueError:
            continue
    s.close()
    return None


if __name__ == "__main__":
    m = sys.argv[1]
    p = json.loads(sys.argv[2]) if len(sys.argv) > 2 else None
    print(json.dumps(call(m, p), indent=1, ensure_ascii=False))
